#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplicação da Proposta 1 em região NÃO utilizada para ajuste dos modelos.

Uma passagem completa pelos rasters, Quickshift independente em cada janela de
até 256x256 pixels. Sem usar classes locais para treinar ou selecionar modelo.
Calcula as mesmas três características numéricas da Area1:
(mean_intensity=V de HSV em RGB do multiespectral,
 mean_edges=Canny no NIR/10000,
 mean_ndvi=(NIR-vermelho)/(NIR+vermelho+1e-8)).
Exporta mosaicos georreferenciados por classificador e segmentos.csv.gz.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
from contextlib import ExitStack
from pathlib import Path

import joblib
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window, transform as win_transform
from skimage.color import rgb2hsv
from skimage.feature import canny
from skimage.segmentation import quickshift

FEATURES = ("mean_intensity", "mean_edges", "mean_ndvi")
LABELS = {"arvore": 1, "grama": 2}
FIELDS = ("segmento_id", "quadrante", "sid", "n_pixels", "x", "y", *FEATURES)


def geo_mask(ds, window: Window, geom):
    h, w = int(window.height), int(window.width)
    if geom is None:
        return np.ones((h, w), dtype=bool)
    return geometry_mask(geom, (h, w), win_transform(window, ds.transform), invert=True)


def feature_means(seg: np.ndarray, values: np.ndarray, valid: np.ndarray):
    ids = seg.ravel().astype(np.int32)
    mask = valid.ravel()
    n = int(ids.max()) + 1
    cnt = np.bincount(ids[mask], minlength=n)
    means = []
    for k in range(values.shape[0]):
        sums = np.bincount(ids[mask], weights=values[k].ravel()[mask].astype("float64"), minlength=n)
        means.append(np.divide(sums, cnt,
                               out=np.full(n, np.nan, dtype=np.float64), where=cnt > 0))
    return cnt, np.column_stack(means)


def features_originales(multis, seg, valid):
    # A sequência reproduz o cálculo de atributos dos 812 quadrantes no V2.
    nir = multis[3].astype("float32")
    red = multis[0].astype("float32")
    ndvi = (nir - red) / (nir + red + 1e-8)
    hsv_brilho = rgb2hsv(np.moveaxis(multis[:3], 0, -1))[..., 2].astype("float32")
    canny_nir = canny(nir / 10000.0, sigma=1).astype("float32")
    channels = np.stack([hsv_brilho, canny_nir, ndvi], axis=0)
    return feature_means(seg, channels, valid)


def load_models(path):
    manifest_path = path / "manifesto_modelos.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Modelos da Area1 ausentes: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("features") != list(FEATURES) or data.get("classes") != list(LABELS):
        raise ValueError("A assinatura de atributos/rótulos diverge do classificador.")
    models = {}
    for title, info in data["modelos"].items():
        filename = path / info["arquivo"]
        if not filename.is_file():
            raise FileNotFoundError(f"Modelo não encontrado: {filename}")
        # Segurança: joblib só deve carregar modelos gerados localmente pelo script
        # treinar_area1.py. Nunca baixar/abrir joblib de origem desconhecida.
        models[title] = joblib.load(filename)
    if len(models) != 8:
        raise ValueError(f"São esperados oito classificadores; encontrados {len(models)}")
    return models, data


def output_model_name(filename):
    return Path(filename).stem


def region_aoi(path, crs):
    if path is None:
        return None
    import geopandas as gpd
    from shapely.geometry import mapping
    g = gpd.read_file(path)
    if g.empty or g.crs is None:
        raise ValueError("Vetor AOI vazio ou sem CRS definido.")
    g = g.to_crs(crs)
    return [mapping(geom) for geom in g.geometry if geom is not None and not geom.is_empty]


def file_fingerprint(path):
    """Fingerprint estável mesmo após extrair o mesmo ZIP em nova sessão Colab.

    O mtime muda a cada download/extração e não identifica o conteúdo: usar
    SHA256 integral impede retomar mosaicos produzidos por outro raster.
    """
    path=Path(path)
    digest=hashlib.sha256()
    with path.open("rb") as reader:
        while True:
            block=reader.read(8*1024*1024)
            if not block:
                break
            digest.update(block)
    return {"nome":path.name,"bytes":path.stat().st_size,
            "sha256":digest.hexdigest()}


def build_signature(region, rgb, multi, aoi, models_path, allow_warp):
    model_bytes = (models_path / "manifesto_modelos.json").read_bytes()
    return dict(regiao=region, rgb=file_fingerprint(rgb), multiespectral=file_fingerprint(multi),
                aoi=file_fingerprint(aoi) if aoi else None, tamanho_janela=256,
                features=list(FEATURES), quickshift={"kernel_size": 3, "max_dist": 5,
                                                     "ratio": 0.04, "rng": 42},
                modelo_manifesto_sha256=hashlib.sha256(model_bytes).hexdigest(),
                permitir_reprojecao=allow_warp)


def ensure_rasters(dst, rgb_ds, model_files, resume):
    dst.mkdir(parents=True, exist_ok=True)
    profile = rgb_ds.profile.copy()
    profile.update(driver="GTiff", count=1, dtype="uint8", nodata=0,
                   compress="deflate", tiled=True, blockxsize=256, blockysize=256,
                   BIGTIFF="IF_SAFER")
    outputs = {}
    for name, model_file in model_files.items():
        p = dst / ("classificacao_" + output_model_name(model_file) + ".tif")
        if p.exists():
            if not resume:
                raise FileExistsError(f"Saída já existe; use outro diretório ou --retomar: {p}")
            with rasterio.open(p) as src:
                if src.width != rgb_ds.width or src.height != rgb_ds.height or src.crs != rgb_ds.crs:
                    raise ValueError(f"Mosaico de checkpoint incompatível: {p}")
        else:
            if resume:
                raise FileNotFoundError(f"Mosaico ausente em retomada: {p}")
            with rasterio.open(p, "w", **profile):
                pass
        outputs[name] = p
    ids = dst / "segmento_id.tif"
    profile.update(dtype="uint32")
    if ids.exists() and not resume:
        raise FileExistsError(f"Saída já existe: {ids}")
    if not ids.exists():
        if resume:
            raise FileNotFoundError(f"Segmentos de checkpoint ausentes: {ids}")
        with rasterio.open(ids, "w", **profile):
            pass
    return outputs, ids


def predict_tile(rgb: np.ndarray, ms: np.ndarray, valid: np.ndarray,
                 transform, tile_id: int, models):
    h, w = valid.shape
    if not valid.any() or h < 3 or w < 3:
        blank = np.zeros((h, w), np.uint32)
        return [], blank, {name: blank.astype("uint8") for name in models}
    if not np.isfinite(rgb).all() or not np.isfinite(ms).all():
        raise ValueError("Raster contém NaN/inf na janela. Verifique o arquivo.")
    # Sem padronizar a imagem: os parâmetros são iguais aos dos quadrantes Area1.
    seg = quickshift(rgb, kernel_size=3, max_dist=5, ratio=0.04, rng=42)
    nseg = int(seg.max()) + 1
    if nseg > 65535 or tile_id >= 65535:
        raise RuntimeError("IDs excedem a representação uint32 prevista.")
    cnt, values = features_originales(ms, seg, valid)
    yy, xx = np.indices((h, w), dtype="float32")
    _, pos = feature_means(seg, np.stack([xx, yy]), valid)
    a, b, c, d, e, f = tuple(transform)[:6]
    c_x = c + a * (pos[:, 0] + .5) + b * (pos[:, 1] + .5)
    c_y = f + d * (pos[:, 0] + .5) + e * (pos[:, 1] + .5)
    good = np.flatnonzero((cnt > 0) & np.isfinite(values).all(axis=1))
    tag = (tile_id * 65536 + seg.astype("uint32") + 1)
    tag[~valid] = 0
    rows = [(int(tile_id*65536 + int(sid) + 1), int(tile_id), int(sid), int(cnt[sid]),
             float(c_x[sid]), float(c_y[sid]), *[float(v) for v in values[sid]])
            for sid in good]
    outputs = {}
    for name, model in models.items():
        labels = np.zeros(nseg, dtype="uint8")
        if len(good):
            predicted = model.predict(values[good])
            if not set(predicted).issubset(LABELS):
                raise ValueError(f"Classificador {name} retornou rótulos desconhecidos")
            labels[good] = np.array([LABELS[z] for z in predicted], dtype="uint8")
        mask = labels[seg]
        mask[~valid] = 0
        outputs[name] = mask
    return rows, tag, outputs


def count_tile_predictions(tag, predictions):
    """Conta segmentos únicos e pixels por classe prevista em cada janela.

    Segmentos (unidades do modelo) e pixels (área prevista) são contagens
    diferentes; nenhuma das duas é medida de acerto sem referência local.
    """
    stats={}
    valid=tag>0
    for model,classified in predictions.items():
        if classified.shape!=tag.shape:
            raise ValueError("Máscara prevista incompatível com IDs de segmentos")
        if not set(np.unique(classified)).issubset({0,1,2}):
            raise ValueError("Há códigos de classe inesperados na predição")
        arvores=(classified==1)&valid
        gramas=(classified==2)&valid
        if np.any((classified!=0)&~valid):
            raise ValueError("Previsão fora dos pixels válidos da segmentação")
        count_a=int(np.unique(tag[arvores]).size)
        count_g=int(np.unique(tag[gramas]).size)
        if np.intersect1d(np.unique(tag[arvores]),np.unique(tag[gramas])).size:
            raise ValueError("Mesmo segmento previsto como árvore e gramínea")
        stats[model]={
            "segmentos_previstos_arvore":count_a,
            "segmentos_previstos_grama":count_g,
            "pixels_previstos_arvore":int(arvores.sum()),
            "pixels_previstos_grama":int(gramas.sum()),
        }
    return stats


def write_rows_atomic(p: Path, rows):
    tmp = p.with_suffix(p.suffix + ".partial")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(FIELDS)
        writer.writerows(rows)
    os.replace(tmp, p)


def combine_csv(tile_dir, result):
    files = sorted(tile_dir.glob("tile_*.csv.gz"))
    tmp = result.with_suffix(".partial")
    with gzip.open(tmp, "wt", newline="", encoding="utf-8") as dest:
        writer = csv.writer(dest)
        writer.writerow(FIELDS)
        for file in files:
            with gzip.open(file, "rt", newline="", encoding="utf-8") as src:
                rows = csv.reader(src)
                header = next(rows)
                if tuple(header) != FIELDS:
                    raise RuntimeError(f"Colunas inesperadas: {file}")
                writer.writerows(rows)
    os.replace(tmp, result)


def previews(rgb_path, outputs, out, max_dim=1400):
    """Pré-visualizações reduzidas: RGB, Quickshift, árvore, grama e sobreposição."""
    from matplotlib import pyplot as plt
    from matplotlib.colors import to_rgb
    with rasterio.open(rgb_path) as ds:
        k = min(1., max_dim / max(ds.width, ds.height))
        width, height = max(1, int(ds.width*k)), max(1, int(ds.height*k))
        rgb = np.moveaxis(ds.read([1,2,3], out_shape=(3,height,width),
                                  resampling=Resampling.bilinear).astype(float),0,-1)
    values=rgb[np.isfinite(rgb)]
    if not len(values):
        raise ValueError("Não foi possível criar visualização: RGB sem valores finitos")
    lo, hi = np.percentile(values, [2,98])
    base = np.clip((rgb-lo)/max(hi-lo,1e-8),0,1)
    plt.imsave(out/"imagem_rgb_reduzida.png",base)
    ids_path=out/"segmento_id.tif"
    if ids_path.is_file():
        with rasterio.open(ids_path) as src:
            ids=src.read(1,out_shape=(height,width),resampling=Resampling.nearest)
        edges=np.zeros((height,width),dtype=bool)
        edges[:,1:] |= (ids[:,1:]!=ids[:,:-1])
        edges[1:,:] |= (ids[1:,:]!=ids[:-1,:])
        edges &= ids>0
        seg_preview=base.copy()
        seg_preview[edges]=to_rgb("#43D4F8")
        plt.imsave(out/"quickshift_segmentos_reduzidos.png",seg_preview)
    for name,path in outputs.items():
        with rasterio.open(path) as ds:
            mask=ds.read(1,out_shape=(height,width),resampling=Resampling.nearest)
        suffix=output_model_name(path.name).replace("classificacao_","")
        combined=base.copy()
        trees=base.copy()
        grasses=base.copy()
        combined[mask==1]=combined[mask==1]*.55+np.array(to_rgb("#2C9C57"))*.45
        combined[mask==2]=combined[mask==2]*.55+np.array(to_rgb("#E4C04F"))*.45
        trees[mask==1]=trees[mask==1]*.4+np.array(to_rgb("#2C9C57"))*.6
        grasses[mask==2]=grasses[mask==2]*.4+np.array(to_rgb("#E4C04F"))*.6
        plt.imsave(out/("sobreposicao_"+suffix+".png"),combined)
        plt.imsave(out/("arvores_"+suffix+".png"),trees)
        plt.imsave(out/("gramineas_"+suffix+".png"),grasses)

def run(region, rgb, multi, models_dir, output, aoi=None, allow_warp=False,
        resume=False, make_previews=True, limit_tiles=None):
    if not rgb.exists() or not multi.exists():
        raise FileNotFoundError("Rasters RGB e RGB+NIR devem ser informados com --rgb e --multi.")
    models, manifest = load_models(models_dir)
    filenames = {name: manifest["modelos"][name]["arquivo"] for name in models}
    signature = build_signature(region, rgb, multi, aoi, models_dir, allow_warp)
    output.mkdir(parents=True, exist_ok=True)
    config_file = output / "configuracao_execucao.json"
    if config_file.exists():
        if not resume:
            raise FileExistsError("Pasta já utilizada. Use --retomar com os mesmos dados ou outra pasta.")
        if json.loads(config_file.read_text(encoding="utf-8")) != signature:
            raise ValueError("Arquivos, parâmetros ou modelos mudaram; não é seguro retomar.")
    else:
        if resume:
            raise FileNotFoundError("Não há checkpoint para retomar.")
        config_file.write_text(json.dumps(signature, ensure_ascii=False, indent=2), encoding="utf-8")
    with rasterio.open(rgb) as rgbds, rasterio.open(multi) as multids, ExitStack() as stack:
        if rgbds.count < 3 or multids.count < 4:
            raise ValueError("É obrigatório RGB (3 bandas) e multiespectral com NIR (4 bandas). "
                             "Sem NIR, NDVI e Canny originais não são reproduzíveis; não inventar.")
        if rgbds.crs is None or multids.crs is None:
            raise ValueError("Rasters devem ter CRS válido.")
        geoms = region_aoi(aoi, rgbds.crs)
        aligned = (rgbds.crs == multids.crs and
                   rgbds.width == multids.width and
                   rgbds.height == multids.height and
                   rgbds.transform.almost_equals(multids.transform))
        if aligned:
            msds = multids
        elif allow_warp:
            msds = stack.enter_context(WarpedVRT(multids, crs=rgbds.crs,
                  transform=rgbds.transform, width=rgbds.width, height=rgbds.height,
                  resampling=Resampling.bilinear))
        else:
            raise ValueError("Grades RGB/NIR desalinhadas. Audite georreferenciamento e "
                             "use --alinhar-multiespectral se quiser reprojetar explicitamente.")
        outputs, ids = ensure_rasters(output, rgbds, filenames, resume)
        nrows = math.ceil(rgbds.height/256)
        ncols = math.ceil(rgbds.width/256)
        tile_dir = output / "tiles"
        tile_dir.mkdir(exist_ok=True)
        completed = 0
        for ri, row in enumerate(range(0,rgbds.height,256)):
            for ci, col in enumerate(range(0,rgbds.width,256)):
                tile_id = ri * ncols + ci
                if limit_tiles is not None and completed >= limit_tiles:
                    break
                done = tile_dir / f"tile_{tile_id:06d}.ok"
                class_stats=tile_dir / f"tile_{tile_id:06d}.classes.json"
                if done.exists():
                    if not class_stats.is_file():
                        raise RuntimeError(f"Checkpoint sem contagem de classes: {done}")
                    continue
                w = min(256,rgbds.width-col)
                h = min(256,rgbds.height-row)
                win = Window(col,row,w,h)
                valid = geo_mask(rgbds,win,geoms)
                rgb_m = np.moveaxis(rgbds.read([1,2,3],window=win),0,-1)
                ms_m = msds.read([1,2,3,4],window=win)
                valid &= (rgbds.read_masks(1,window=win)>0)
                valid &= (msds.read_masks(4,window=win)>0)
                rows, tag, pred = predict_tile(rgb_m,ms_m,valid,
                                               win_transform(win,rgbds.transform),
                                               tile_id,models)
                # Fechar cada escrita antes de assinalar o checkpoint.
                with rasterio.open(ids,"r+") as dest:
                    dest.write(tag,1,window=win)
                for name, path in outputs.items():
                    with rasterio.open(path,"r+") as dest:
                        dest.write(pred[name],1,window=win)
                write_rows_atomic(tile_dir / f"tile_{tile_id:06d}.csv.gz",rows)
                tile_counts=count_tile_predictions(tag,pred)
                tmp_stats=class_stats.with_suffix(".partial")
                tmp_stats.write_text(json.dumps(tile_counts,ensure_ascii=False),encoding="utf-8")
                os.replace(tmp_stats,class_stats)
                done.write_text("ok\n",encoding="utf-8")
                completed += 1
                if completed % 25 == 0:
                    print(f"{region}: {completed} novos quadrantes nesta execução",flush=True)
            if limit_tiles is not None and completed >= limit_tiles:
                break
    count_done = len(list(tile_dir.glob("tile_*.ok")))
    total = nrows*ncols
    complete = count_done == total
    class_summary={}
    if complete:
        class_files=sorted(tile_dir.glob("tile_*.classes.json"))
        if len(class_files)!=total:
            raise RuntimeError(f"Contagem de classes incompleta: {len(class_files)}/{total}")
        for item in class_files:
            counts=json.loads(item.read_text(encoding="utf-8"))
            if set(counts)!=set(models):
                raise ValueError(f"Contagem de modelos divergente: {item}")
            for model,stats in counts.items():
                aggregate=class_summary.setdefault(model,{
                    "segmentos_previstos_arvore":0,"segmentos_previstos_grama":0,
                    "pixels_previstos_arvore":0,"pixels_previstos_grama":0})
                for k in aggregate:
                    aggregate[k]+=int(stats[k])
        import pandas as pd
        pd.DataFrame([{"modelo":name,**stats} for name,stats in class_summary.items()]).to_csv(
            output/"resumo_classes_previstas.csv",index=False)
        combine_csv(tile_dir, output/"segmentos.csv.gz")
        if make_previews:
            previews(rgb,outputs,output)
    report = {
        "regiao": region, "estado": "concluido" if complete else "parcial",
        "quadrantes_previstos": total, "quadrantes_concluidos": count_done,
        "tamanho_janela_px": 256, "modelos": list(models),
        "features": list(FEATURES), "labels": LABELS,
        "multiespectral_alinhado_sem_reprojecao": aligned,
        "reprojecao_explicita": bool(not aligned and allow_warp),
        "referencias_externas_usadas_em_treino": False,
        "contagens_segmentos_e_pixels_por_classificador":class_summary if complete else None,
        "resumo_classes_previstas":str(output/"resumo_classes_previstas.csv") if complete else None,
        "significado_contagens":"Previsões SEM rótulos locais: não são árvores verificadas, nem F1.",
        "validacao_externa": "NÃO REALIZADA AQUI; exige rótulos locais independentes",
        "mapas": {name: str(p) for name,p in outputs.items()},
        "segmentos": str(output/"segmento_id.tif")
    }
    (output/"manifesto_execucao.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"STATUS {region}: {count_done}/{total} quadrantes. Avaliação quantitativa requer rótulos locais.")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regiao",required=True)
    p.add_argument("--rgb",type=Path,required=True)
    p.add_argument("--multi",type=Path,required=True)
    p.add_argument("--modelos",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--aoi",type=Path)
    p.add_argument("--alinhar-multiespectral",action="store_true",
                   help="WarpedVRT na grade RGB, mudando explicitamente a grade de origem")
    p.add_argument("--retomar",action="store_true")
    p.add_argument("--sem-previews",action="store_true")
    p.add_argument("--limite-quadrantes",type=int,
                   help="Para teste rápido; execução incompleta NÃO é resultado final")
    args=p.parse_args()
    run(args.regiao,args.rgb,args.multi,args.modelos,args.out,args.aoi,
        args.alinhar_multiespectral,args.retomar,not args.sem_previews,
        args.limite_quadrantes)


if __name__=="__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare alturas modeladas Meta/WRI CHMv2 e ETH Zurich 2020 nos mesmos 257 pontos.

Nao substitui alturas de campo. Tenta COG oficial ETH e, em caso de erro,
o servico ArcGIS publicado com o mesmo mapa ETH (ImageServer).
"""
from __future__ import annotations
import argparse, json, math, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ETH_TILE = "ETH_GlobalCanopyHeight_10m_2020_S30W054_Map.tif"
ETH_URL = (
    "https://libdrive.ethz.ch/index.php/s/cO8or7iOe5dT2Rt/download"
    "?path=%2F%203deg_cogs&files=" + ETH_TILE
)
ARCGIS = ("https://tiledimageservices.arcgis.com/P3ePLMYs2RVChkJx/"
          "arcgis/rest/services/10m_Tree_Canopy_Height/ImageServer")

def ler_cog(pontos):
    import rasterio
    from rasterio.windows import from_bounds
    # O share ETH nao aceita HEAD: usar abertura HTTP sem HEAD e Range COG.
    vsi = "/vsicurl?use_head=no&max_retry=4&url=" + urllib.parse.quote(ETH_URL, safe="")
    env = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
               CPL_VSIL_CURL_USE_HEAD="NO",
               GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2",
               GDAL_CACHEMAX=128)
    with rasterio.Env(**env):
        with rasterio.open(vsi) as src:
            if src.count != 1 or src.crs is None:
                raise RuntimeError("COG ETH tem banda ou CRS inesperado")
            if src.crs.to_epsg() != 4326:
                raise RuntimeError("EPSG incorreto ETH: " + str(src.crs))
            bounds = (float(pontos.longitude.min()) - .002,
                      float(pontos.latitude.min()) - .002,
                      float(pontos.longitude.max()) + .002,
                      float(pontos.latitude.max()) + .002)
            w = from_bounds(*bounds, transform=src.transform)
            w = w.round_offsets().round_lengths()
            arr = src.read(1, window=w, masked=True)
            local_tf = src.window_transform(w)
            nodata = src.nodata
            print("ETH COG:", src.crs, "size:", src.width, src.height,
                  "res:", src.res, "nodata:", nodata,
                  "crop:", arr.shape, flush=True)
            if arr.size == 0:
                raise RuntimeError("Janela vazia fora do COG ETH")
            results=[]
            for p in pontos.itertuples(index=False):
                col,row = (~local_tf)*(float(p.longitude),float(p.latitude))
                rr,cc=int(math.floor(row)),int(math.floor(col))
                val = float(arr[rr,cc]) if 0<=rr<arr.shape[0] and 0<=cc<arr.shape[1] and not np.ma.is_masked(arr[rr,cc]) else np.nan
                if val==255 or not np.isfinite(val) or val<0:
                    val=np.nan
                results.append(val)
            valid=np.isfinite(results)
            if sum(valid)<30:
                raise RuntimeError("COG retornou menos de 30 pontos: confira arquivo/CRS")
            return results, dict(fonte_acesso="COG oficial ETH Zurich",
                    url=ETH_URL, tile=ETH_TILE,
                    nodata_original=nodata, resolucao_graus=list(src.res),
                    n_pontos_validos=int(sum(valid)))

def ler_arcgis(pontos):
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    # Servico ArcGIS Living Atlas usa o mesmo produto ETH Zurich 2020.
    session=requests.Session()
    meta=session.get(ARCGIS,params={"f":"json"},timeout=30)
    meta.raise_for_status()
    desc=meta.json()
    if "error" in desc or "ETH" not in str(desc.get("description","")+desc.get("serviceDescription","")+desc.get("name","")+" "+desc.get("copyrightText","")+" "+desc.get("title","")).upper() and "canopy" not in str(desc).lower():
        raise RuntimeError("Nao foi possivel verificar a origem do ImageServer ETH")
    results=[np.nan]*len(pontos)
    def query(i,p):
        r=requests.get(ARCGIS+"/identify",params={
            "f":"json","geometry":json.dumps({"x":float(p.longitude),"y":float(p.latitude),"spatialReference":{"wkid":4326}}),
            "geometryType":"esriGeometryPoint","returnGeometry":"false","pixelSize":json.dumps({"x":.0000833333,"y":.0000833333})
            },timeout=35)
        r.raise_for_status()
        data=r.json()
        if "error" in data:
            raise RuntimeError(str(data["error"]))
        v=data.get("value")
        if isinstance(v,(float,int,str)) and str(v).strip() not in ["NoData","None","Null",""]:
            try:
                x=float(v)
                if np.isfinite(x) and 0<=x<255:return i,x
            except ValueError: pass
        return i,np.nan
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures=[pool.submit(query,i,p) for i,p in enumerate(pontos.itertuples(index=False))]
        for ft in as_completed(futures):
            i,val=ft.result()
            results[i]=val
    count=int(np.isfinite(results).sum())
    if count<30:
        raise RuntimeError("ImageServer ETH retornou menos de 30 valores reais (acesso/mascara)")
    return results,dict(fonte_acesso="Esri ArcGIS ImageServer do ETH Zurich 2020",url=ARCGIS,
                        n_pontos_validos=count,metadados={k:desc.get(k) for k in ("name","description","copyrightText","pixelSizeX","pixelSizeY")})

def correlation(x,y,kind="pearson"):
    s=pd.DataFrame({"x":x,"y":y}).dropna()
    if len(s)<3 or s.x.nunique()<2 or s.y.nunique()<2:return None
    return float(s.x.corr(s.y,method=kind))

def stats(s):
    x=pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:return dict(n=0)
    return dict(n=int(len(x)),mediana_m=float(x.median()),media_m=float(x.mean()),
                q25_m=float(x.quantile(.25)),q75_m=float(x.quantile(.75)),
                zeros=int((x==0).sum()),maximo_m=float(x.max()))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--meta",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    data=pd.read_csv(args.meta)
    fields=["ponto_id","latitude","longitude","altura_meta_pixel_m","altura_meta_max_5m_m"]
    if not set(fields).issubset(data.columns) or len(data)!=257 or data.ponto_id.nunique()!=257:
        raise ValueError("Precisamos dos 257 registros originais e das medidas Meta!")
    if data.latitude.between(-30,-27).sum()!=257 or data.longitude.between(-54,-51).sum()!=257:
        raise ValueError("Os pontos nao parecem pertencer ao quadrante S30W054 da ETH")
    pontos=data[["ponto_id","latitude","longitude"]].copy()
    erros={}
    try:
        heights,details=ler_cog(pontos)
    except Exception as e:
        erros["COG_ETH"]=str(e)
        print("Falha no COG ETH:",repr(e),flush=True)
        heights,details=ler_arcgis(pontos)
    result=data.copy()
    result["altura_eth_2020_pixel_m"]=pd.to_numeric(heights,errors="coerce")
    result["diferenca_eth_menos_meta_pixel_m"]=result["altura_eth_2020_pixel_m"]-result["altura_meta_pixel_m"]
    result["diferenca_eth_menos_meta_max_5m_m"]=result["altura_eth_2020_pixel_m"]-result["altura_meta_max_5m_m"]
    paired=result[["altura_meta_pixel_m","altura_eth_2020_pixel_m"]].dropna()
    positive=paired[(paired.altura_meta_pixel_m>0)&(paired.altura_eth_2020_pixel_m>0)]
    delta=paired.altura_eth_2020_pixel_m-paired.altura_meta_pixel_m
    summary={
        "consultado_em_utc":datetime.now(timezone.utc).isoformat(),
        "area":"Area1, Caxias do Sul, RS","pontos_originais":257,
        "metodo":"amostragem de estimativas modeladas no pixel de cada coordenada; bases com resolucoes diferentes",
        "meta":"Meta/WRI CHMv2 (pixel de cerca de 1m, cenas de diversas datas)",
        "eth":"ETH Zurich Global Canopy Height 2020 (10m nominal)",
        "fonte_eth":details,"erros_de_acesso":erros,
        "meta_pixel":stats(result.altura_meta_pixel_m),
        "meta_max_5m":stats(result.altura_meta_max_5m_m),
        "eth_pixel":stats(result.altura_eth_2020_pixel_m),
        "pares_validos":int(len(paired)),"pares_ambos_positivos":int(len(positive)),
        "eth_menos_meta_pixel_mediana_m":float(delta.median()) if len(delta) else None,
        "eth_menos_meta_pixel_media_m":float(delta.mean()) if len(delta) else None,
        "erro_absoluto_mediano_entre_fontes_m":float(delta.abs().median()) if len(delta) else None,
        "correlacao_pearson_meta_eth":correlation(paired.altura_meta_pixel_m,paired.altura_eth_2020_pixel_m),
        "correlacao_spearman_meta_eth":correlation(paired.altura_meta_pixel_m,paired.altura_eth_2020_pixel_m,"spearman"),
        "correlacao_pearson_ambos_positivos":correlation(positive.altura_meta_pixel_m,positive.altura_eth_2020_pixel_m),
        "aviso":"Diferencas entre modelos nao medem erro contra altura real. Pixels de 1m e 10m nao sao equivalentes; zeros e datas tambem variam."
    }
    args.out.mkdir(parents=True,exist_ok=True)
    out_csv=args.out/"v3_meta_eth_alturas_estimadas_257_arvores.csv"
    result.to_csv(out_csv,index=False,encoding="utf-8-sig")
    (args.out/"v3_meta_eth_resumo_257.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(7,6))
        ax.scatter(paired.altura_meta_pixel_m,paired.altura_eth_2020_pixel_m,alpha=.42,s=22)
        maximum=max(30,paired.to_numpy().max(initial=0))
        ax.plot([0,maximum],[0,maximum],ls="--",color="gray",lw=1)
        ax.set(xlabel="Meta/WRI CHMv2: altura estimada no pixel (m)",
               ylabel="ETH 2020: altura estimada no pixel (m)",
               title="Area1 — estimativas de dossel em 257 pontos (nao alturas reais)")
        fig.tight_layout()
        fig.savefig(args.out/"v3_meta_eth_dispersao.png",dpi=150)
        plt.close(fig)
    except Exception as e: print("Grafico nao foi gerado:",str(e),flush=True)
    report=f"""# V3 — Comparação de alturas estimadas Meta/WRI e ETH Zurich para os mesmos 257 pontos

**Execução registrada:** {summary['consultado_em_utc']}.

**Fontes:** [Meta/WRI CHMv2](https://registry.opendata.aws/dataforgood-fb-forestsv2/) e
[ETH Global Canopy Height 2020](https://langnico.github.io/globalcanopyheight/). Ambas
são **mapas de altura modelada do dossel**, não medidas de campo da mesma árvore.

**Origem ETH dos dados:** {details['fonte_acesso']} ({details['url']}).

| Indicador | Meta/WRI (pixel de ~1 m) | ETH Zurich (pixel de ~10 m) |
|---|---:|---:|
| Pontos com estimativa disponível | {summary['meta_pixel'].get('n',0)} | {summary['eth_pixel'].get('n',0)} |
| Mediana (m) | {summary['meta_pixel'].get('mediana_m','NA'):.2f} | {summary['eth_pixel'].get('mediana_m','NA'):.2f} |
| Média (m) | {summary['meta_pixel'].get('media_m','NA'):.2f} | {summary['eth_pixel'].get('media_m','NA'):.2f} |
| Estimativas nulas (zero) | {summary['meta_pixel'].get('zeros','NA')} | {summary['eth_pixel'].get('zeros','NA')} |

**Pares válidos:** {summary['pares_validos']} dos 257; **ambos positivos:** {summary['pares_ambos_positivos']}.
**Diferença mediana ETH − Meta:** {summary['eth_menos_meta_pixel_mediana_m']:.2f} m;
**diferença absoluta mediana entre fontes:** {summary['erro_absoluto_mediano_entre_fontes_m']:.2f} m.
Correlação Pearson entre estimativas pareadas: {summary['correlacao_pearson_meta_eth']}.
Correlação Spearman entre estimativas pareadas: {summary['correlacao_spearman_meta_eth']}.

**Atenção:** as duas fontes usam modelos, datas e resoluções diferentes. A comparação
de pixels não mede a altura real de 257 árvores nem a precisão individual de cada
produto. O máximo da Meta em 5 m consta do CSV para sensibilidade, mas pode representar
outro indivíduo e não é diretamente comparável ao pixel de 10 m da ETH.
Não calcular MAE/RMSE interpretando um dos mapas como verdade de campo.

**Arquivos:** [tabela pareada](v3_meta_eth_alturas_estimadas_257_arvores.csv);
[resumo estruturado](v3_meta_eth_resumo_257.json);
[dispersão](v3_meta_eth_dispersao.png).
"""
    (args.out/"v3_meta_eth_comparacao_257.md").write_text(report,encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("Gerado:",out_csv)
if __name__=="__main__":
    main()

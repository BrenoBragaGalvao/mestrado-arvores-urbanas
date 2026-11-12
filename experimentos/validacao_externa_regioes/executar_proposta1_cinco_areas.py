#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orquestra a Proposta 1 em Area1 + quatro regiões no Google Colab.

INTEGRIDADE CIENTÍFICA:
- O treinamento e as divisões espaciais são exclusivamente na Area1.
- Nenhuma referência das outras cidades entra no treinamento.
- Nunca supor que '4 bandas' implique NIR: requer metadado explícito OU
  documento de aquisição fornecido pelo pesquisador, registrado em JSON.
- Nenhum F1-macro externo sem referências locais independentes.
- Sagrada Família não usa pontos originais Area1 como teste independente.
- Rasters originais nunca são publicados no repositório; modelos e mapas vão
  somente para pastas novas do Drive, com checkpoint após cada quadrante.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import rasterio

HERE=Path(__file__).resolve().parent
SOURCES={
 "sagrada_familia_caxias":{
   "filename":"SAGRADA_FAMÍLIA_CAXIAS DO SUL.zip",
   "id":"1S5gKEFuGyKZtvq4Q33xcCkndwLIrUg91",
   "bytes":1771082301},
 "centro_novo_hamburgo":{
   "filename":"CENTRO_NOVO HAMBURGO.zip",
   "id":"1UufzP5quG1tRDgfkuwzJ9evwvIHgitYT",
   "bytes":2388874067},
 "lomba_grande_novo_hamburgo":{
   "filename":"LOMBA_GRANDE_NOVO_HAMBURGO.zip",
   "id":"1N5peFz-NauAYeNgBcauFyX9reJpnROQ6",
   "bytes":3117343825},
 "cristo_rei_sao_leopoldo":{
   "filename":"CRISTO_REI_SÃO_LEOPOLDO.rar",
   "id":"1HR1PYH8T38SviYIgcOKb5y0QAag9QdKU",
   "bytes":1563064317},
}
REQUIRED_A0=("AOI_RGB_NEW.tif","AOI_NEW_MULTI.tif","AOI_new.shp",
             "AOI_new.shx","AOI_new.dbf","AOI_new.prj","Arvores.gpkg","Grama.gpkg")


def record_status(dest:Path, data:dict):
    dest.mkdir(parents=True,exist_ok=True)
    path=dest/"estado_cinco_areas.json"
    history={}
    if path.is_file():
        history=json.loads(path.read_text(encoding="utf-8"))
    history.update(data)
    history["atualizado_utc"]=datetime.now(timezone.utc).isoformat()
    temp=path.with_suffix(".partial")
    temp.write_text(json.dumps(history,ensure_ascii=False,indent=2),encoding="utf-8")
    os.replace(temp,path)
    return history


def call(*args):
    print("+", " ".join(str(x) for x in args),flush=True)
    subprocess.run([str(x) for x in args],check=True)


def locate_area1(root:Path, explicit:Path|None):
    candidates=[explicit] if explicit is not None else [
      root/"Projetos/Segmentacao_Breno/Area1",
      root/"Segmentacao_Breno/Area1",root/"Area1"]
    for p in candidates:
        if p and all((p/f).is_file() for f in REQUIRED_A0):
            return p
    raise FileNotFoundError(
        "Area1 original não localizada. Esperados RGB/NIR TIFF, AOI SHP e "
        "Arvores.gpkg/Grama.gpkg. Use --area1 para indicar o caminho exato.")


def verify_training(result:Path):
    path=result/"resumo_execucao_treinamento.json"
    model_dir=result/"modelos_fixos_area1"
    if not path.is_file():
        return None
    audit=json.loads(path.read_text(encoding="utf-8"))
    if audit.get("estado")!="AREA1_TREINADA_E_AUDITADA" or audit.get(
       "area1_segmentos_rotulados_unicos")!=505 or not audit.get(
       "nova_validacao_aninhada_concluida") or len(audit.get("modelos",[]))!=8:
        raise ValueError("O treinamento Area1 não foi verificado; não transferir modelos.")
    required=("random_forest","svm_rbf","regressao_logistica","extra_trees",
              "knn","hist_gradient_boosting","gaussian_naive_bayes","dummy")
    for model in required:
        if not (model_dir/(model+".joblib")).is_file():
            raise FileNotFoundError("Modelo Area1 faltante: "+model)
    return audit


def train_original_area1(area1:Path, dest:Path):
    cached=verify_training(dest)
    if cached is not None:
        print("Oito modelos Area1 e avaliação aninhada já conferidos.",flush=True)
        return cached
    call(sys.executable,HERE/"executar_treinamento_real_area1.py",
         "--area1",area1,"--out",dest)
    cached=verify_training(dest)
    if cached is None:
        raise RuntimeError("Treinamento não gerou manifesto verificável.")
    return cached


def check_download_size(destination:Path, expected:int):
    return destination.is_file() and destination.stat().st_size==expected


def transfer_public_or_drive(info:dict, folder:Path, dest:Path):
    expected=info["bytes"]
    if check_download_size(dest,expected):
        return dest
    dest.parent.mkdir(parents=True,exist_ok=True)
    candidate=folder/info["filename"]
    partial=dest.with_suffix(dest.suffix+".partial")
    if candidate.is_file():
        if candidate.stat().st_size!=expected:
            raise ValueError(f"Tamanho não confere no arquivo do Drive: {candidate}")
        with candidate.open("rb") as src,partial.open("wb") as out:
            shutil.copyfileobj(src,out,length=8*1024*1024)
    else:
        url=("https://drive.usercontent.google.com/download?id="+info["id"]+
             "&export=download&confirm=t")
        if partial.exists():
            partial.unlink()
        call("curl","--fail","--location","--retry","4","--retry-delay","5",
             "--connect-timeout","30","--output",partial,url)
    if partial.stat().st_size!=expected:
        raise RuntimeError(f"Transferência incompleta: {partial.stat().st_size}/{expected}")
    os.replace(partial,dest)
    return dest


def extract_geotiffs(archive:Path, directory:Path):
    directory.mkdir(parents=True,exist_ok=True)
    rgb=directory/"rgb.tif"
    multi=directory/"multi.tif"
    if rgb.is_file() and multi.is_file() and rgb.stat().st_size>1_000_000 and multi.stat().st_size>1_000_000:
        return rgb,multi
    if archive.suffix.lower()==".zip":
        with zipfile.ZipFile(archive) as z:
            files={}
            for e in z.infolist():
                name=e.filename.lower()
                if e.is_dir():
                    continue
                if name.endswith("_ortho_rgb.tif"):
                    files["rgb"]=e
                if name.endswith("_ortho_4bandas.tif"):
                    files["multi"]=e
            if len(files)!=2:
                raise ValueError(f"RGB/4 bandas não encontrados em {archive.name}")
            for key,info in files.items():
                if info.file_size>8*1024**3:
                    raise ValueError("TIFF excede limite de 8 GiB: "+info.filename)
                target=rgb if key=="rgb" else multi
                part=target.with_suffix(".tif.partial")
                if target.is_file() and target.stat().st_size==info.file_size:
                    continue
                with z.open(info) as src,part.open("wb") as dst:
                    shutil.copyfileobj(src,dst,length=8*1024*1024)
                if part.stat().st_size!=info.file_size:
                    raise IOError("Tamanho descompactado divergente: "+info.filename)
                os.replace(part,target)
    elif archive.suffix.lower()==".rar":
        if not shutil.which("7z"):
            raise RuntimeError("O arquivo RAR exige 7z. No Colab: apt-get install p7zip-full")
        call("7z","e","-y","-r",f"-o{directory}",archive,
             "*_ORTHO_RGB.tif","*_ORTHO_4BANDAS.tif")
        for suffix,target in (("_ortho_rgb.tif",rgb),("_ortho_4bandas.tif",multi)):
            files=[p for p in directory.iterdir() if p.is_file()
                   and p.name.lower().endswith(suffix)]
            if len(files)!=1:
                raise ValueError(f"RAR: esperado exatamente um TIFF {suffix}, encontrados {len(files)}")
            if target.is_file() and target!=files[0]:
                target.unlink()
            files[0].rename(target)
    else:
        raise ValueError("Formato regional não suportado: "+str(archive))
    if not rgb.is_file() or not multi.is_file():
        raise FileNotFoundError("Extração não gerou o par de ortoimagens.")
    return rgb,multi


def nir_evidence(code:str, multids, supplied:dict):
    if multids.count<4:
        return False,"Arquivo multiespectral com menos de quatro bandas"
    if multids.colorinterp[3].name.lower()=="alpha":
        return False,"Banda quatro é canal alfa/transparência, não NIR"
    strs=[str(x or "") for x in multids.descriptions]
    strs += [str(multids.tags(i)) for i in range(1,multids.count+1)]
    metadata=any(re.search(r"\b(nir|near[\s_-]*infrared|infravermelho)\b",s,re.I)
                 for s in strs)
    if metadata:
        return True,"NIR identificado explicitamente nos metadados espectrais"
    proof=supplied.get(code,{})
    if isinstance(proof,dict) and proof.get("confirmada") is True and isinstance(
       proof.get("fonte"),str) and len(proof["fonte"].strip())>=12:
        return True,"NIR confirmado por documento técnico: "+proof["fonte"][:300]
    return False,"Quarta banda não identificada como NIR. Falta documentação técnica."


def check_region_bands(code:str,rgb:Path,multi:Path,confirmation:dict):
    with rasterio.open(rgb) as a, rasterio.open(multi) as b:
        if a.crs is None or b.crs is None:
            raise ValueError(f"{code}: raster sem CRS.")
        if a.count<3:
            raise ValueError(f"{code}: RGB sem três bandas.")
        good,proof=nir_evidence(code,b,confirmation)
        if b.crs!=a.crs:
            return False,proof+"; CRS RGB e multiespectral diferentes"
        return good,proof


def ensure_space(scratch:Path,size:int):
    free=shutil.disk_usage(scratch).free
    # Leitura dos TIFFs costuma exigir muitos GiB além do ZIP.
    reserve=max(8_000_000_000,size*3)
    if free<reserve:
        raise RuntimeError(f"Espaço local insuficiente: {free/1e9:.1f} GB livres, "
                           f"recomendado ao menos {reserve/1e9:.1f} GB para a região.")


def run_region(code:str,info:dict,source_folder:Path,scratch:Path,
               base:Path,models:Path,region_out:Path,area1:Path,
               confirmations:dict,max_tiles:int|None):
    previous=region_out/"manifesto_execucao.json"
    if previous.is_file():
        existing=json.loads(previous.read_text(encoding="utf-8"))
        if existing.get("estado")=="concluido" and len(existing.get("mapas",{}))==8:
            if all((region_out/Path(x).name).is_file() for x in existing["mapas"].values()):
                print(f"{code}: 8 mapas completos já presentes. Nenhum reprocessamento.",flush=True)
                return {"estado":"concluido","motivo":"resultados existentes verificados",
                        "manifesto":str(previous)}
    work=scratch/code
    work.mkdir(parents=True,exist_ok=True)
    ensure_space(work,info["bytes"])
    zip_path=work/info["filename"]
    local=work/"ortos"
    try:
        transfer_public_or_drive(info,source_folder,zip_path)
        rgb,multi=extract_geotiffs(zip_path,local)
        good,why=check_region_bands(code,rgb,multi,confirmations)
        with rasterio.open(rgb) as rgb_ds,rasterio.open(multi) as multi_ds:
            grid_aligned=(rgb_ds.crs==multi_ds.crs and
                          rgb_ds.width==multi_ds.width and
                          rgb_ds.height==multi_ds.height and
                          rgb_ds.transform.almost_equals(multi_ds.transform))
            info_rasters={
                "rgb_dims":[rgb_ds.width,rgb_ds.height],
                "multi_dims":[multi_ds.width,multi_ds.height],
                "rgb_crs":str(rgb_ds.crs),"multi_crs":str(multi_ds.crs),
                "rgb_res":list(rgb_ds.res),"multi_res":list(multi_ds.res),
                "bandas_rgb":rgb_ds.count,"bandas_multi":multi_ds.count,
                "bandas_descricao":list(multi_ds.descriptions),
                "grades_alinhadas":grid_aligned,
                "nir_cientificamente_confirmado":good,
                "comprovacao_nir":why
            }
        region_out.mkdir(parents=True,exist_ok=True)
        (region_out/"auditoria_bandas.json").write_text(
            json.dumps(info_rasters,ensure_ascii=False,indent=2),encoding="utf-8")
        if not good:
            print(f"{code}: NÃO CLASSIFICADO — {why}",flush=True)
            return {"estado":"bloqueado_confirmacao_nir","motivo":why,
                    "auditoria":str(region_out/"auditoria_bandas.json")}
        # Audita sobreposição de Sagrada Família e Area1; NUNCA usa os
        # 510 pontos de treinamento como referência de teste externo.
        if code=="sagrada_familia_caxias":
            call(sys.executable,HERE/"auditar_sobreposicao_area1.py",
                 "--area1-aoi",area1/"AOI_new.shp",
                 "--arvores",area1/"Arvores.gpkg",
                 "--grama",area1/"Grama.gpkg",
                 "--rgb-regional",rgb,
                 "--regiao",code,"--exclusao-m","25",
                 "--out",region_out/"auditoria_sobreposicao")
        cmd=[sys.executable,str(HERE/"aplicar_regiao.py"),
             "--regiao",code,"--rgb",str(rgb),"--multi",str(multi),
             "--modelos",str(models),"--out",str(region_out)]
        if not grid_aligned:
            cmd+=["--alinhar-multiespectral"]
        if (region_out/"configuracao_execucao.json").is_file():
            cmd+=["--retomar"]
        if max_tiles is not None:
            cmd+=["--limite-quadrantes",str(max_tiles)]
        call(*cmd)
        manifest=json.loads((region_out/"manifesto_execucao.json").read_text(encoding="utf-8"))
        if manifest.get("estado")!="concluido":
            return {"estado":"parcial","quadrantes":manifest.get("quadrantes_concluidos")}
        # Sem rótulos novos, a saída inclui apenas mapas previstos;
        # gerar protocolo de anotação cega, não inventar F1.
        blind=base/"rotulacao"/code
        samples=blind/"amostras_para_anotar.gpkg"
        if not samples.is_file():
            cmd=[sys.executable,str(HERE/"preparar_rotulacao.py"),"gerar",
                 "--segmentos",str(region_out/"segmento_id.tif"),
                 "--n","200","--bloco-m","250","--out",str(blind)]
            if code=="sagrada_familia_caxias":
                cmd+=["--excluir-aoi",str(area1/"AOI_new.shp"),
                      "--buffer-exclusao-m","25"]
            call(*cmd)
        return {"estado":"predicoes_concluidas_sem_rotulos_externos",
                "manifesto":str(region_out/"manifesto_execucao.json"),
                "amostras_para_anotar":str(samples),
                "resumo_classes_previstas":str(region_out/"resumo_classes_previstas.csv")}
    finally:
        # Apaga APENAS uma pasta criada pela orquestração, para permitir que
        # o Colab tenha espaço para a próxima região (não toca no Drive).
        if work.is_dir() and work.resolve()!=scratch.resolve():
            shutil.rmtree(work)


def verify_external_labels(code:str,base:Path,area1:Path):
    """Calcula métricas só quando referências independentes já foram rotuladas."""
    verified=base/"rotulacao"/code/"rotulos_verificados"
    trees=verified/"Arvores.gpkg"
    grass=verified/"Grama.gpkg"
    region_out=base/"predicoes"/code
    manifest=region_out/"manifesto_execucao.json"
    if not trees.is_file() or not grass.is_file() or not manifest.is_file():
        return {"estado":"sem_rotulos_independentes","f1_externo":None}
    state=json.loads(manifest.read_text(encoding="utf-8"))
    if state.get("estado")!="concluido":
        return {"estado":"predicoes_parciais","f1_externo":None}
    metrics=base/"metricas"/code
    cmd=[sys.executable,str(HERE/"avaliar_regiao.py"),
         "--regiao",code,"--predicoes",str(region_out),
         "--arvores",str(trees),"--grama",str(grass),"--out",str(metrics)]
    if code=="sagrada_familia_caxias":
        cmd+=["--area1-aoi",str(area1/"AOI_new.shp"),
              "--buffer-exclusao-m","25"]
    call(*cmd)
    if not (metrics/"metricas_externas.csv").is_file():
        raise RuntimeError(f"{code}: avaliação concluída sem CSV de métricas")
    return {"estado":"validacao_externa_com_rotulos_independentes",
            "arquivo":str(metrics/"metricas_externas.csv")}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--drive-root",type=Path,default=Path("/content/drive/MyDrive"))
    p.add_argument("--area1",type=Path,help="Pasta dos dados originais da Area1")
    p.add_argument("--pacotes-drive",type=Path,
                   default=Path("/content/drive/MyDrive/Imagens do Mestrado"))
    p.add_argument("--out",type=Path,
                   default=Path("/content/drive/MyDrive/Projetos/Segmentacao_Breno/outputs/validacao_externa_regioes"))
    p.add_argument("--scratch",type=Path,default=Path("/content/validacao_externa_local"))
    p.add_argument("--confirmacoes-nir",type=Path,
                   help="JSON com 'confirmada':true E a fonte documental para cada região.")
    p.add_argument("--regioes",nargs="+",choices=list(SOURCES),
                   default=list(SOURCES))
    p.add_argument("--somente-area1",action="store_true")
    p.add_argument("--pular-area1-mapas",action="store_true")
    p.add_argument("--limite-quadrantes",type=int,
                   help="Teste de fumaça; NÃO declarar conclusão se usar este limite.")
    args=p.parse_args()
    if args.limite_quadrantes is not None and args.limite_quadrantes<1:
        p.error("--limite-quadrantes deve ser pelo menos 1")
    args.scratch.mkdir(parents=True,exist_ok=True)
    args.out.mkdir(parents=True,exist_ok=True)
    proof={}
    if args.confirmacoes_nir is not None:
        proof=json.loads(args.confirmacoes_nir.read_text(encoding="utf-8"))
    area1=locate_area1(args.drive_root,args.area1)
    training_out=args.out/"area1_treinamento_real"
    training=train_original_area1(area1,training_out)
    summary={"area1_treinamento":{"estado":"concluido",
             "segmentos_rotulados":training["area1_segmentos_rotulados_unicos"],
             "modelos":len(training["modelos"])}}
    record_status(args.out,summary)
    models=training_out/"modelos_fixos_area1"
    if not args.pular_area1_mapas:
        output=args.out/"predicoes"/"area1_caxias"
        if output.joinpath("manifesto_execucao.json").is_file():
            old=json.loads((output/"manifesto_execucao.json").read_text(encoding="utf-8"))
            if old.get("estado")=="concluido":
                summary["area1_mapa"]={"estado":"concluido","tipo":"mapa_in_sample_sem_F1"}
        if "area1_mapa" not in summary:
            cmd=[sys.executable,str(HERE/"aplicar_regiao.py"),
                 "--regiao","area1_caxias",
                 "--rgb",str(area1/"AOI_RGB_NEW.tif"),
                 "--multi",str(area1/"AOI_NEW_MULTI.tif"),
                 "--modelos",str(models),"--out",str(output)]
            with rasterio.open(area1/"AOI_RGB_NEW.tif") as a, rasterio.open(area1/"AOI_NEW_MULTI.tif") as b:
                if a.crs!=b.crs or a.shape!=b.shape or not a.transform.almost_equals(b.transform):
                    cmd+=["--alinhar-multiespectral"]
            if output.joinpath("configuracao_execucao.json").is_file():
                cmd+=["--retomar"]
            if args.limite_quadrantes is not None:
                cmd+=["--limite-quadrantes",str(args.limite_quadrantes)]
            call(*cmd)
            status=json.loads((output/"manifesto_execucao.json").read_text(encoding="utf-8"))
            summary["area1_mapa"]={"estado":status["estado"],
                     "tipo":"mapa_in_sample_sem_F1",
                     "nota":"As amostras Area1 fizeram parte do treino; não é teste externo."}
        record_status(args.out,summary)
    if args.somente_area1:
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return
    for code in args.regioes:
        try:
            out=args.out/"predicoes"/code
            response=run_region(code,SOURCES[code],args.pacotes_drive,args.scratch,
                                args.out,models,out,area1,proof,args.limite_quadrantes)
            summary[code]=response
            if response["estado"] in (
                "concluido","predicoes_concluidas_sem_rotulos_externos"):
                response["avaliacao"]=verify_external_labels(code,args.out,area1)
            record_status(args.out,{code:response})
        except Exception as e:
            state={"estado":"erro","tipo":type(e).__name__,"motivo":str(e)[:700]}
            record_status(args.out,{code:state})
            print(f"{code}: ERROR {type(e).__name__}: {e}",file=sys.stderr,flush=True)
            # Um erro de dados não deve ser encoberto como sucesso em cinco áreas.
            raise
    comparison=args.out/"comparacao_regioes"
    baseline=HERE.parents[1]/"docs/e4b_ablacao_aninhada_2026-11-03_tabelas.csv"
    if not baseline.is_file():
        raise FileNotFoundError(f"Baseline histórica da Area1 ausente: {baseline}")
    metrics_root=args.out/"metricas"
    metrics_root.mkdir(exist_ok=True)
    call(sys.executable,HERE/"consolidar_resultados.py",
         "--metricas-root",metrics_root,
         "--baseline",baseline,"--out",comparison)
    summary["consolidacao"]={"estado":"gerada",
                             "relatorio":str(comparison/"relatorio.md")}
    record_status(args.out,{"consolidacao":summary["consolidacao"]})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()

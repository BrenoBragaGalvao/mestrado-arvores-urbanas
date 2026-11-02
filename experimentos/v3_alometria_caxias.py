#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3 independente: alometria exploratória de árvores urbanas de Caxias do Sul.
Entradas: SOMENTE AOI_RGB_NEW.tif e Arvores.gpkg da Area1 já existente.
NÃO fornece altura real: a área de um superpixel Quickshift não é uma copa medida.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

COEF = {"C1": (.5,.7), "C2": (.6,.8), "C3": (2.5,.4),
        "C4": (4.,.5), "C5": (.4,.9), "C6": (1.35,.72)}
PDAU = "https://gcpstorage.caxias.rs.gov.br/documents/2020/09/c2d2ec2b-dfb4-4646-aadd-01eced79a722.pdf"
ESPECIES = [
 ("Eugenia uniflora","Pitangueira",6,12,None,30,"Porte bibliográfico; no município, pode ser menor"),
 ("Araucaria angustifolia","Araucária",20,50,None,6,"Porte geral de espécie, não exemplar da Area1"),
 ("Tibouchina sellowiana","Quaresmeira",4,15,8,77,"Na arborização do município raramente acima de 8 m"),
 ("Jacaranda micrantha","Caroba",10,25,None,41,"Porte descrito no PDAU"),
 ("Jacaranda mimosifolia","Jacarandá-mimoso",12,15,None,41,"Porte descrito no PDAU"),
 ("Tipuana tipu","Tipuana",12,16,None,78,"Porte descrito no PDAU"),
 ("Annona neosalicifolia","Araticum",None,20,10,4,"Na arborização urbana geralmente abaixo de 10 m"),
 ("Allophylus edulis","Chal-chal",6,10,None,4,"Porte descrito no PDAU"),
]

def potencial(area,a,b):
    return a*np.power(np.maximum(np.asarray(area,dtype=float),0),b)

def criar_referencias(out):
    df=pd.DataFrame(ESPECIES,columns=[
      "especie","nome_popular","h_min_m","h_max_m","max_urbano_m",
      "pagina_pdf","observacao"])
    df["fonte"]=PDAU
    df["aviso"]="Porte bibliográfico; não identifica nem mede árvore da Area1"
    df.to_csv(out/"v3_referencias_alturas_caxias.csv",index=False,encoding="utf-8-sig")
    return df

def obter_superpixels(rgb_path,trees_path,tile):
    import geopandas as gpd
    import rasterio
    from rasterio.windows import Window
    from skimage.segmentation import quickshift
    g=gpd.read_file(trees_path)
    if g.crs is None or g.empty:
        raise ValueError("Arvores.gpkg precisa conter pontos com CRS.")
    if not g.geometry.geom_type.eq("Point").all():
        raise ValueError("Esperados pontos em Arvores.gpkg, não polígonos de copa.")
    rows=[]
    with rasterio.open(rgb_path) as ds:
        if ds.count<3 or ds.crs is None:
            raise ValueError("RGB original precisa ter pelo menos três bandas e CRS.")
        area_pixel=abs(ds.transform.a*ds.transform.e-ds.transform.b*ds.transform.d)
        if area_pixel<=0: raise ValueError("Resolução inválida.")
        pontos=g.to_crs(ds.crs)
        grupos={}
        for k,geom in enumerate(pontos.geometry):
            r,c=ds.index(geom.x,geom.y)
            if not (0<=r<ds.height and 0<=c<ds.width):
                rows.append({"ponto_id":k,"status":"fora_do_raster","janela_px":tile})
                continue
            r0=(r//tile)*tile;c0=(c//tile)*tile
            grupos.setdefault((r0,c0),[]).append((k,r-r0,c-c0))
        for (r0,c0),locations in sorted(grupos.items()):
            h=min(tile,ds.height-r0);w=min(tile,ds.width-c0)
            raw=ds.read([1,2,3],window=Window(c0,r0,w,h))
            image=np.moveaxis(raw,0,-1)
            if image.size==0 or not np.isfinite(image).all() or np.max(image)==np.min(image):
                for k,_,_ in locations:
                    rows.append({"ponto_id":k,"status":"janela_invalida","janela_px":tile})
                continue
            labels=quickshift(image,kernel_size=3,max_dist=5,ratio=.04,convert2lab=True)
            labs,counts=np.unique(labels,return_counts=True)
            cdict=dict(zip(labs.tolist(),counts.tolist()))
            bordas=set(np.concatenate([labels[0,:],labels[-1,:],
               labels[:,0],labels[:,-1]]).tolist())
            for k,y,x in locations:
                sid=int(labels[y,x])
                rows.append({"ponto_id":k,"status":"ok","janela_px":tile,
                   "tile_row":r0,"tile_col":c0,
                   "segmento_id":f"r{r0}_c{c0}_s{sid}",
                   "pixels_superpixel":int(cdict[sid]),
                   "area_superpixel_m2":float(cdict[sid]*area_pixel),
                   "toca_borda":bool(sid in bordas),
                   "aviso":"Superpixel Quickshift NAO e copa delimitada"})
    return pd.DataFrame(rows).sort_values("ponto_id").reset_index(drop=True),list(g.columns)

def adicionar_indices(df):
    out=df.copy()
    a=pd.to_numeric(out.get("area_superpixel_m2"),errors="coerce")
    for key,(coef,expo) in COEF.items():
        out["indice_potencial_"+key]=potencial(a,coef,expo)
        out["indice_linear_"+key]=coef+expo*a
    out["C3_acima_limiar_7"]=out["indice_potencial_C3"]>7
    return out

def figuras(df,refs,dest):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    valid=df[df.status=="ok"]
    fig,ax=plt.subplots(figsize=(9,4.7))
    ax.hist(valid.indice_potencial_C3.dropna(),bins=20,edgecolor="white")
    ax.axvline(7,linestyle="--",label="Limiar empirico C3=7")
    ax.set(xlabel="Indice C3 (nao altura em metros)",ylabel="Pontos de referencia",
      title="Distribuicao do indice C3 em superpixels")
    ax.legend()
    fig.savefig(dest/"v3_histograma_indice_C3.png",dpi=150,bbox_inches="tight");plt.close(fig)

    fig,ax=plt.subplots(figsize=(9,4.7))
    areas=np.geomspace(1,600,160)
    for key,(a,b) in COEF.items():
        ax.plot(areas,potencial(areas,a,b),label=key)
    ax.set(xscale="log",xlabel="Area do superpixel (m²) - nao copa validada",
       ylabel="Indice empirico (nao altura validada)",title="Sensibilidade dos coeficientes C1-C6")
    ax.legend(ncol=3);fig.savefig(dest/"v3_sensibilidade_C1_C6.png",
       dpi=150,bbox_inches="tight");plt.close(fig)

    ref=refs.dropna(subset=["h_min_m","h_max_m"]).reset_index(drop=True)
    fig,ax=plt.subplots(figsize=(9,4.7))
    for i,row in ref.iterrows():
        ax.plot([row.h_min_m,row.h_max_m],[i,i],marker="|",linewidth=3)
        if pd.notna(row.max_urbano_m):
            ax.scatter([row.max_urbano_m],[i],marker="D",s=35)
    ax.set(yticks=range(len(ref)),yticklabels=ref.nome_popular,
       xlabel="Porte por especie no PDAU (m) - NAO individuos da Area1",
       title="Referencias de alturas por especie em Caxias do Sul")
    fig.savefig(dest/"v3_faixas_especies_caxias.png",
       dpi=150,bbox_inches="tight");plt.close(fig)

def executar(area,rgb,arvores,out,tile):
    out.mkdir(parents=True,exist_ok=True)
    ref=criar_referencias(out)
    rgb=Path(rgb) if rgb else area/"AOI_RGB_NEW.tif"
    arvores=Path(arvores) if arvores else area/"Arvores.gpkg"
    if not rgb.is_file() or not arvores.is_file():
        raise FileNotFoundError("Utilize a pasta Area1 original com AOI_RGB_NEW.tif e Arvores.gpkg.")
    points,cols=obter_superpixels(rgb,arvores,tile)
    df=adicionar_indices(points)
    df.to_csv(out/"v3_indices_superpixels_pontos.csv",index=False,encoding="utf-8-sig")
    valid=df[df.status=="ok"]
    if len(valid)==0:raise ValueError("Nenhum ponto foi associado.")
    vals=valid.indice_potencial_C3.to_numpy()
    res={"area":"Area1 de Caxias do Sul","pontos_originais":len(df),
       "pontos_validos":len(valid),"janelas_unicas":int(len(valid[["tile_row","tile_col"]].drop_duplicates())),
       "segmentos_distintos":int(valid.segmento_id.nunique()),
       "segmentos_na_borda":int(valid.toca_borda.sum()),
       "mediana_area_superpixel_m2":float(valid.area_superpixel_m2.median()),
       "mediana_indice_C3":float(np.median(vals)),
       "min_indice_C3":float(vals.min()),"max_indice_C3":float(vals.max()),
       "fracao_C3_maior_7":float(np.mean(vals>7)), "janela_px":tile,
       "colunas_dados_originais":cols,
       "interpretacao":"Indices empiricos; NAO alturas reais nem copa delimitada.",
       "evidencia_externa":"Faixas de especies do PDAU sem vinculo aos individuos da Area1",
       "fonte":PDAU}
    (out/"v3_resumo.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf-8")
    figuras(df,ref,out)
    return res

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--area",default="/content/drive/MyDrive/Area1")
    p.add_argument("--rgb",default=None)
    p.add_argument("--arvores",default=None)
    p.add_argument("--out",default="v3_resultados_alometria")
    p.add_argument("--tile",type=int,choices=[256,512],default=256)
    a=p.parse_args()
    print(json.dumps(executar(Path(a.area),a.rgb,a.arvores,Path(a.out),a.tile),
       indent=2,ensure_ascii=False))
if __name__=="__main__":main()

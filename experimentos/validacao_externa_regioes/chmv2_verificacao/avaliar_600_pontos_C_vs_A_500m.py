#!/usr/bin/env python3
"""Recalcula F1 CHMv2 nos MESMOS 600 pontos cegos usando LR Area1 original e filtrada.
Nunca usa CHMv2 de regiões externas para treinamento ou seleção de hiperparâmetros.
Os F1 externos são concordância automática com CHMv2, não validação humana.
"""
from pathlib import Path
from contextlib import ExitStack
from rasterio.windows import Window
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from skimage.color import rgb2hsv
from skimage.feature import canny
from sklearn.metrics import f1_score,accuracy_score,confusion_matrix
import os, time, json, zipfile, shutil, subprocess, hashlib
import numpy as np, pandas as pd, requests, rasterio

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'600_pontos_cegos_CHMv2_congelados.csv'
OUT=Path(os.environ.get('CHM_F1_OUTPUT','F1_600_C_VS_A_500m'));OUT.mkdir(exist_ok=True,parents=True)
TMP=OUT/'cache';TMP.mkdir(exist_ok=True)
REGIONS={
 'sagrada_familia_caxias':('1S5gKEFuGyKZtvq4Q33xcCkndwLIrUg91',1771082301,'.zip','18GwhiVAC_LT1rxZgmICTvz2VLjABFKQQ'),
 'lomba_grande_novo_hamburgo':('1N5peFz-NauAYeNgBcauFyX9reJpnROQ6',3117343825,'.zip','1ePRzJQColP1dvqJJv9P3LaSVo1LxE30w'),
 'cristo_rei_sao_leopoldo':('1HR1PYH8T38SviYIgcOKb5y0QAag9QdKU',1563064317,'.rar','1ih1_ti5svuc-ZIq-zOiuEa1ymYFjf239')}
MODEL={
'A':([.010725328092809516,.08223319610387517,.5460169878126475],
[.0013568288294366398,.06299865938304096,.10547839889636648],
[1.5406417358543503,-1.1950408195644397,1.049757743137724],-.08053042586837197),
'C':([.01066705282346412,.0773649088957711,.5597409352096173],
[.0013112548610879312,.06485456340171991,.09461235886398553],
[1.6508681883369405,-1.2836744130124456,.5665999147865749],.3899300983285226)}
FEATURES=['mean_intensity','mean_edges','mean_ndvi']
# Grade RGB original, recuperada do segmento_id.tif dos mapas auditados.
# Estas grades são necessárias para reproduzir o WarpedVRT histórico.
GRID={
 'sagrada_familia_caxias':(10422,10456,482066.4796141586,6777297.270391193),
 'lomba_grande_novo_hamburgo':(17423,16409,491242.3209731818,6713967.373159798),
 'cristo_rei_sao_leopoldo':(10410,10530,482650.7000000648,6707348.525005451)
}
MASKCSV=HERE/'600_pontos_mascaras_quickshift_originais.csv'

def download(fid,p,n=None):
    if p.is_file() and (n is None or p.stat().st_size==n):return p
    url=f'https://drive.usercontent.google.com/download?export=download&confirm=t&id={fid}'
    for attempt in range(3):
        try:
            temp=p.with_suffix(p.suffix+'.part')
            with requests.get(url,stream=True,timeout=(50,160)) as resp:
                resp.raise_for_status()
                assert not resp.headers.get('content-type','').startswith('text/html'),"Drive entregou HTML"
                with temp.open('wb') as w:
                    for chunk in resp.iter_content(4*1024*1024):
                        if chunk:w.write(chunk)
            if n and temp.stat().st_size!=n:raise ValueError(f'{p.name}: tamanho errado {temp.stat().st_size} != {n}')
            temp.replace(p)
            print('DOWNLOAD_OK',p.name,p.stat().st_size,flush=True)
            return p
        except Exception as e:
            print('DOWNLOAD_TENTATIVA',attempt,str(e)[:180],flush=True)
            p.with_suffix(p.suffix+'.part').unlink(missing_ok=True)
            if attempt==2:raise
            time.sleep(3*(attempt+1))
def extractzip(p,pattern,dest):
    with zipfile.ZipFile(p) as z:
        found=[m for m in z.infolist() if m.filename.lower().endswith(pattern.lower())]
        if len(found)!=1:raise ValueError(f'{pattern} em {p}: {len(found)}')
        with z.open(found[0]) as src,dest.open('wb') as dst:shutil.copyfileobj(src,dst,8*1024*1024)
    return dest
def extract_multi(p,out):
    if p.suffix=='.zip':return extractzip(p,'_ortho_4bandas.tif',out)
    subprocess.run([def get_features(region,part,conf):
    """Reconstrói o atributo diretamente de Multi original nos pixels do segmento congelado.
    As máscaras foram extraídas, testadas e vinculadas ao GeoTIFF de segmento original.
    Não depende de um novo mapa ou novas amostras.
    """
    import zlib,base64
    from rasterio.transform import Affine
    fid,size,ext,_mapid=conf
    work=TMP/region;work.mkdir(exist_ok=True)
    archive=download(fid,work/('original'+ext),size)
    multipath=extract_multi(archive,work/'multi.tif')
    archive.unlink()
    masks=pd.read_csv(MASKCSV,dtype={'segmento_id':str})
    masks=masks[masks.regiao==region]
    joined=part.merge(masks,on=['regiao','amostra_id','segmento_id'],validate='one_to_one',how='inner')
    if len(joined)!=200:raise ValueError('Máscara ausente para algum ponto: '+region)
    allrows=[]
    width,height,x0,y0=GRID[region]
    original_transform=Affine(.5,0,x0,0,-.5,y0)
    with rasterio.open(multipath) as src,ExitStack() as stack:
        if src.count!=4:raise ValueError('Esperadas quatro bandas multiespectrais')
        aligned=(src.crs.to_epsg()==31982 and src.width==width and src.height==height and src.transform.almost_equals(original_transform))
        ds=src if aligned else stack.enter_context(WarpedVRT(src,crs='EPSG:31982',transform=original_transform,width=width,height=height,resampling=Resampling.bilinear))
        tiles=joined.groupby(['tile_row','tile_col'])
        print('REGIAO',region,'n_pontos',len(part),'n_tiles_256px',tiles.ngroups,'warp',not aligned,flush=True)
        for (tr,tc),group in tiles:
            h=min(256,height-int(tr)*256);w=min(256,width-int(tc)*256)
            win=Window(int(tc)*256,int(tr)*256,w,h)
            bands=ds.read([3,2,1,4],window=win,masked=True)
            raw=bands.filled(0)
            nir=raw[3].astype('float32');red=raw[0].astype('float32')
            ndvi=(nir-red)/(nir+red+1e-8)
            hsv=rgb2hsv(np.moveaxis(raw[:3],0,-1))[...,2].astype('float32')
            edge=canny(nir/10000.0,sigma=1).astype('float32')
            valid=~np.ma.getmaskarray(bands).any(axis=0)
            for rec in group.to_dict('records'):
                if int(rec['tile_width'])!=w or int(rec['tile_height'])!=h:raise ValueError('Tile alterado')
                packed=base64.b64decode(rec['indices_zlib_base64'])
                indices=np.frombuffer(zlib.decompress(packed),dtype='<u2').astype(np.int64)
                if len(indices)!=int(rec['n_pixels_original']) or np.any(indices>=h*w):raise ValueError('Máscara inválida')
                mask=np.zeros((h*w,),dtype=bool);mask[indices]=True;mask=mask.reshape(h,w)
                mask &= valid
                if not mask.any():raise ValueError('Segmento ficou sem pixels espectrais: '+str(rec['amostra_id']))
                out={k:rec[k] for k in ['regiao','amostra_id','x','y','segmento_id','bloco_500m','predicao_modelo','B']}
                out['mean_intensity']=float(hsv[mask].mean(dtype=np.float64))
                out['mean_edges']=float(edge[mask].mean(dtype=np.float64))
                out['mean_ndvi']=float(ndvi[mask].mean(dtype=np.float64))
                out['n_pixels_segmento']=int(mask.sum())
                allrows.append(out)
    table=pd.DataFrame(allrows).sort_values('amostra_id')
    table.to_csv(OUT/(region+'_atributos_200.csv'),index=False)
    print('REGIAO_OK',region,len(table),flush=True)
    shutil.rmtree(work,ignore_errors=True)
    return table

.mean(dtype=np.float64)),
                   'mean_edges':float(edge[mask].mean(dtype=np.float64)),
                   'mean_ndvi':float(ndvi[mask].mean(dtype=np.float64)),
                   'n_pixels_segmento':int(mask.sum())}
                allrows.append(a)
    result=pd.DataFrame(allrows).sort_values('amostra_id')
    result.to_csv(OUT/(region+'_atributos_200.csv'),index=False)
    shutil.rmtree(work,ignore_errors=True)
    return result
def calc(g,key):
    q=g[g['B'].isin(['arvore','grama'])]
    y=q['B'].to_numpy();pred=q[key].to_numpy()
    cm=confusion_matrix(y,pred,labels=['arvore','grama'])
    return dict(n_total=int(len(g)),n_validos=int(len(q)),n_blocos_500=int(g.bloco_500m.nunique()),
        f1_macro=float(f1_score(y,pred,labels=['arvore','grama'],average='macro',zero_division=0)),
        acuracia=float(accuracy_score(y,pred)),
        aa=int(cm[0,0]),ag=int(cm[0,1]),ga=int(cm[1,0]),gg=int(cm[1,1]))
def main():
    data=pd.read_csv(SOURCE,dtype={'segmento_id':str})
    assert len(data)==600
    assert all(data.groupby('regiao').size()==200)
    pieces=[]
    for region,conf in REGIONS.items():
        pieces.append(get_features(region,data[data.regiao==region],conf))
    frame=pd.concat(pieces).reset_index(drop=True)
    values=frame[FEATURES].to_numpy(dtype='float64')
    frame['previsto_A_reprocessado'],frame['score_A']=predict(values,MODEL['A'])
    frame['previsto_C_filtrado'],frame['score_C']=predict(values,MODEL['C'])
    frame['confere_A_raster']=(frame.previsto_A_reprocessado==frame.predicao_modelo)
    frame.to_csv(OUT/'600_pontos_mesmos_atributos_e_previsoes.csv',index=False)
    n_diff=int((~frame.confere_A_raster).sum())
    metrics=[]
    for region,g in frame.groupby('regiao'):
        for model,key in [('A_raster_original','predicao_modelo'),('A_reprocessado','previsto_A_reprocessado'),('C_retreinado_371','previsto_C_filtrado')]:
            metrics.append(dict(regiao=region,modelo=model,**calc(g,key)))
    pd.DataFrame(metrics).to_csv(OUT/'COMPARACAO_F1_MACRO_500m_600_PONTOS.csv',index=False)
    manifest={'status':'CONFERIDO' if n_diff==0 else 'DIVERGENCIA_REPROCESSAMENTO',
        'pontos_originais':600,'diferencas_baseline_A':n_diff,
        'interpretacao':'F1 de concordancia com pseudo-rotulos CHMv2, nao validacao humana',
        'amostras':'600 pontos cegos da avaliacao anterior, fixos; 200 por regiao',
        'modelo_C':'LogisticRegression C=0.1 StandardScaler; Area1 371 segmentos de treino concordantes com CHMv2',
        'blocos':'500 m apenas para dependencia espacial; F1 agregado na amostra nao muda ao mudar blocos',
        'resultados':metrics}
    (OUT/'manifesto_comparacao.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
    print('RESULTADOS_COMPLETOS='+json.dumps(manifest,ensure_ascii=False),flush=True)
    if n_diff>0:print('ATENCAO: discrepancias A! Nao afirmar avaliacao exata de C sem inspecao',flush=True)
    else:print('600_PONTOS_VERIFICADOS',flush=True)
if __name__=='__main__':main()

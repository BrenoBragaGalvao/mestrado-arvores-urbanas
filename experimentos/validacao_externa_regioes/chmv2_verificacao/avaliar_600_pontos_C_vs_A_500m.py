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
    subprocess.run(['7z','e','-y',str(p),'-o'+str(p.parent/'unrar'),'*_ORTHO_4BANDAS.tif'],check=True)
    f=[x for x in (p.parent/'unrar').iterdir() if x.name.lower().endswith('_ortho_4bandas.tif')]
    if len(f)!=1:raise ValueError('Erro de extração RAR')
    f[0].rename(out);return out
def predict(X,params):
    mean,scale,coef,intercept=params
    z=((X-np.asarray(mean))/np.asarray(scale))@np.asarray(coef)+intercept
    return np.where(z>0,'grama','arvore'),z
def get_features(region,part,conf):
    fid,size,ext,mapid=conf
    work=TMP/region;work.mkdir(exist_ok=True)
    archive=download(fid,work/('original'+ext),size)
    mapzip=download(mapid,work/'mapas.zip')
    segpath=extractzip(mapzip,'segmento_id.tif',work/'segmentos.tif')
    oldpath=extractzip(mapzip,'classificacao_regressao_logistica.tif',work/'old.tif')
    multipath=extract_multi(archive,work/'multi.tif')
    archive.unlink() # liberar armazenamento de ZIP/RAR depois da extração
    allrows=[]
    with rasterio.open(segpath) as ids,rasterio.open(oldpath) as old,rasterio.open(multipath) as src,ExitStack() as stack:
        aligned=(src.crs==ids.crs and src.width==ids.width and src.height==ids.height and src.transform.almost_equals(ids.transform))
        ds=src if aligned else stack.enter_context(WarpedVRT(src,crs=ids.crs,transform=ids.transform,width=ids.width,height=ids.height,resampling=Resampling.bilinear))
        if ds.count!=4:raise ValueError('Esperadas quatro bandas multiespectrais')
        tiles={}
        for rec in part.to_dict('records'):
            row,col=ids.index(float(rec['x']),float(rec['y']))
            pointwin=Window(col,row,1,1)
            actual_id=int(ids.read(1,window=pointwin)[0,0])
            actual_old=int(old.read(1,window=pointwin)[0,0])
            if actual_id!=int(rec['segmento_id']) or actual_old not in (1,2):
                raise ValueError(f'ID de segmento divergente: {region} {rec["amostra_id"]}')
            pred_old='arvore' if actual_old==1 else 'grama'
            if pred_old!=rec['predicao_modelo']:raise ValueError('Predição original divergente!')
            tiles.setdefault((row//256,col//256),[]).append(rec)
        print('REGIAO',region,'n_pontos',len(part),'n_tiles_256px',len(tiles),'warp',not aligned,flush=True)
        for (tr,tc),recs in tiles.items():
            win=Window(tc*256,tr*256,min(256,ids.width-tc*256),min(256,ids.height-tr*256))
            pixels=ids.read(1,window=win)
            bands=ds.read([3,2,1,4],window=win,masked=True)
            b=bands.filled(0)
            nir=b[3].astype('float32');red=b[0].astype('float32')
            ndvi=(nir-red)/(nir+red+1e-8)
            hsv=rgb2hsv(np.moveaxis(b[:3],0,-1))[...,2].astype('float32')
            edge=canny(nir/10000.0,sigma=1).astype('float32')
            valid=~np.ma.getmaskarray(bands).any(axis=0)
            for rec in recs:
                mask=(pixels==int(rec['segmento_id'])) & valid
                if not mask.any():raise ValueError(f'Segmento sem pixels válidos {rec["amostra_id"]}')
                a={**rec,'mean_intensity':float(hsv[mask].mean(dtype=np.float64)),
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

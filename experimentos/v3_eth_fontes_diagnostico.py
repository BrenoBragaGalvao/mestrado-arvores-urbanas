"""Diagnostico nao intrusivo de endpoints publicos ETH Zurich (sem coletar dados)."""
import requests, json
from urllib.parse import urlencode
from pathlib import Path
base="https://libdrive.ethz.ch/index.php/s/cO8or7iOe5dT2Rt"
img="ETH_GlobalCanopyHeight_10m_2020_S30W054_Map.tif"
arc="https://tiledimageservices.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/10m_Tree_Canopy_Height/ImageServer"
locations=[
("share",base,None),
("download_3deg",base+"/download",dict(path="/ 3deg_cogs",files=img)),
("download_3deg_no_space",base+"/download",dict(path="/3deg_cogs",files=img)),
("download_3deg_alt",base+"/download",dict(path="/ 3deg_cogs",files="ETH_GlobalCanopyHeight_10m_2020_S27W054_Map.tif")),
("download_1deg",base+"/download",dict(path="/ 1deg_cogs",files="ETH_GlobalCanopyHeight_10m_2020_S30W052_Map.tif")),
("arcgis_service",arc,dict(f="json")),
("arcgis_identify",arc+"/identify",dict(f="json",geometry="-51.17681133,-29.176047",geometryType="esriGeometryPoint",sr="4326",returnGeometry="false")),
("arcgis_export",arc+"/exportImage",dict(f="json",bbox="-51.178,-29.178,-51.175,-29.174",bboxSR="4326",imageSR="4326",size="80,80",format="tiff")),
]
r=[]
for name,url,params in locations:
    try:
        res=requests.get(url,params=params,headers={"Range":"bytes=0-1023"} if "download" in name else {},timeout=18,stream=True,allow_redirects=True)
        payload=next(res.iter_content(600),b"")
        row=dict(name=name,status=res.status_code,url=res.url[:280],type=res.headers.get("Content-Type"),length=res.headers.get("Content-Length"),range=res.headers.get("Content-Range"),preview=payload[:240].decode("utf8","replace"))
        if name=="arcgis_service" and res.status_code==200:
            try:
                # second request: metadata is small
                info=requests.get(url,params=params,timeout=18).json()
                row.update({key:info.get(key) for key in ["name","capabilities","tileInfo","serviceDataType","pixelSizeX","pixelSizeY","bandCount","hasHistograms","copyrightText"] if key in info and key!="tileInfo"})
                row["tileInfo"]=bool(info.get("tileInfo"))
            except Exception: pass
        print(name,row,flush=True)
        r.append(row)
    except Exception as e:
        print(name,type(e).__name__,str(e)[:600],flush=True)
        r.append(dict(name=name,error=str(e)))
Path("docs/v3_alturas_publicas").mkdir(parents=True,exist_ok=True)
Path("docs/v3_alturas_publicas/v3_eth_diagnostico_acesso.json").write_text(json.dumps(r,ensure_ascii=False,indent=2))

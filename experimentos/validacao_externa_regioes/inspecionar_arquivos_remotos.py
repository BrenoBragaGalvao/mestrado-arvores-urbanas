#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventaria ZIP/RAR grandes por leituras HTTP Range, sem baixar arquivos inteiros.

Somente metadados. Requer compartilhamento público de leitura; nunca usa tokens
de Drive, cookies de navegador, contas ou segredos. Limita bytes transferidos
para evitar custo/transferência inesperada. Registra o resultado localmente.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import urllib.request
import urllib.error
import zipfile
from collections import OrderedDict
from pathlib import Path

URL_TEMPLATE = "https://drive.usercontent.google.com/download?id={id}&export=download&confirm=t"
PUBLIC_IDS = {
    "centro_novo_hamburgo": ("1UufzP5quG1tRDgfkuwzJ9evwvIHgitYT", "zip"),
    "lomba_grande_novo_hamburgo": ("1N5peFz-NauAYeNgBcauFyX9reJpnROQ6", "zip"),
    "cristo_rei_sao_leopoldo": ("1HR1PYH8T38SviYIgcOKb5y0QAag9QdKU", "rar"),
    "sagrada_familia_caxias": ("1S5gKEFuGyKZtvq4Q33xcCkndwLIrUg91", "zip")
}


class HTTPRangeReader(io.RawIOBase):
    BLOCK=262144
    def __init__(self, url: str, budget: int=32*1024*1024):
        self.url=url
        self.budget=int(budget)
        self.bytes_read_network=0
        self.blocks: OrderedDict[int,bytes]=OrderedDict()
        self.pos=0
        self.total_size=None
        first=self._http_range(0, min(2047,self.BLOCK-1))
        self.blocks[0]=first
        self.total_size=int(self.total_size)
        if len(first)==0:
            raise ValueError("Endpoint remoto não retornou bytes binários")

    def _http_range(self, start: int, end: int):
        if self.bytes_read_network + end-start+1 > self.budget:
            raise RuntimeError(f"Limite de auditoria excedido: {self.budget} bytes. Nenhum download completo.")
        request=urllib.request.Request(self.url,headers={
            "Range":f"bytes={start}-{end}",
            "User-Agent":"Mozilla/5.0",
            "Accept":"application/octet-stream"})
        with urllib.request.urlopen(request,timeout=50) as response:
            cr=response.headers.get("Content-Range","")
            if response.status!=206 or not cr.startswith("bytes "):
                mime=response.headers.get("Content-Type","?")
                raise PermissionError(f"Leitura Range indisponível: HTTP {response.status}, mime={mime}")
            match=re.match(r"bytes (\d+)-(\d+)/(\d+)",cr)
            if not match or int(match.group(1))!=start:
                raise IOError(f"Content-Range inválido: {cr}")
            self.total_size=int(match.group(3))
            data=response.read(end-start+1)
            if len(data)!=end-start+1:
                raise IOError(f"Resposta truncada: {len(data)} de {end-start+1} bytes")
            self.bytes_read_network+=len(data)
            return data

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset:int, whence:int=io.SEEK_SET):
        if whence==io.SEEK_SET:
            target=offset
        elif whence==io.SEEK_CUR:
            target=self.pos+offset
        elif whence==io.SEEK_END:
            target=self.total_size+offset
        else:
            raise ValueError("whence inválido")
        if not 0<=target<=self.total_size:
            raise ValueError(f"Seek fora do arquivo: {target}/{self.total_size}")
        self.pos=target
        return self.pos

    def _block(self, number:int):
        if number in self.blocks:
            data=self.blocks.pop(number)
            self.blocks[number]=data
            return data
        a=number*self.BLOCK
        b=min(a+self.BLOCK,self.total_size)-1
        data=self._http_range(a,b)
        self.blocks[number]=data
        if len(self.blocks)>8:
            self.blocks.popitem(last=False)
        return data

    def read(self, amount:int=-1):
        if amount is None or amount<0:
            amount=self.total_size-self.pos
        if amount>self.budget:
            raise RuntimeError("Leitura grande recusada. A auditoria nunca baixa o ZIP/RAR completo.")
        count=min(amount,self.total_size-self.pos)
        parts=[]
        while count:
            number=self.pos//self.BLOCK
            off=self.pos%self.BLOCK
            block=self._block(number)
            chunk=block[off:off+count]
            if not chunk:
                raise IOError("Bloco HTTP vazio")
            parts.append(chunk)
            count-=len(chunk)
            self.pos+=len(chunk)
        return b"".join(parts)

    def readinto(self,b):
        piece=self.read(len(b))
        b[:len(piece)]=piece
        return len(piece)


def remote_inventory(region:str, file_id:str, filetype:str, budget:int) -> dict:
    r=HTTPRangeReader(URL_TEMPLATE.format(id=file_id),budget=budget)
    report={"regiao":region,"formato":filetype,"tamanho_compactado_bytes":r.total_size,
            "conteudo_inspecionado_por_ranges":False,"entradas":[]}
    try:
        if filetype=="zip":
            with zipfile.ZipFile(r) as z:
                for entry in z.infolist():
                    report["entradas"].append({
                        "caminho":entry.filename, "is_dir":entry.is_dir(),
                        "bytes_descompactados":entry.file_size,
                        "bytes_compactados":entry.compress_size,
                        "extensao":Path(entry.filename).suffix.lower()
                    })
        elif filetype=="rar":
            try:
                import rarfile
            except ImportError as e:
                raise RuntimeError("Instale rarfile para inventariar RAR por Range") from e
            with rarfile.RarFile(r) as z:
                for entry in z.infolist():
                    report["entradas"].append({
                        "caminho":entry.filename,
                        "is_dir":entry.is_dir(),
                        "bytes_descompactados":entry.file_size,
                        "bytes_compactados":entry.compress_size,
                        "extensao":Path(entry.filename).suffix.lower()
                    })
        else:
            raise ValueError(f"Formato não suportado: {filetype}")
        report["conteudo_inspecionado_por_ranges"]=True
    except Exception as e:
        report["erro_tipo"]=type(e).__name__
        report["erro"]=str(e)[:400]
    report["bytes_transferidos_da_rede"]=r.bytes_read_network
    report["total_entradas"]=len(report["entradas"])
    report["arquivos_provaveis_raster"]=[
        a["caminho"] for a in report["entradas"]
        if a["extensao"] in {".tif",".tiff",".jp2",".vrt",".img"}
    ]
    report["arquivos_provaveis_vetor"]=[
        a["caminho"] for a in report["entradas"]
        if a["extensao"] in {".shp",".gpkg",".geojson"}
    ]
    report["aviso"]="Nomes de arquivos não confirmam NIR, CRS, dimensões nem rotulação."
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--limite-mb",type=int,default=32)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    results=[]
    for region,(id_,type_) in PUBLIC_IDS.items():
        try:
            entry=remote_inventory(region,id_,type_,args.limite_mb*1024*1024)
        except Exception as exc:
            entry={"regiao":region,"formato":type_,
                   "conteudo_inspecionado_por_ranges":False,
                   "erro_tipo":type(exc).__name__,"erro":str(exc)[:300]}
        results.append(entry)
        print(json.dumps({
            "regiao":region,"sucesso":entry.get("conteudo_inspecionado_por_ranges",False),
            "total_entradas":entry.get("total_entradas"),
            "rasters":entry.get("arquivos_provaveis_raster",[])[:30],
            "vetores":entry.get("arquivos_provaveis_vetor",[])[:30],
            "bytes_transferidos":entry.get("bytes_transferidos_da_rede"),
            "erro":entry.get("erro")
        },ensure_ascii=False),flush=True)
    (args.out/"inventario_zip_rar_remoto.json").write_text(
        json.dumps(results,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Arquivo de auditoria salvo; pacotes NÃO foram baixados integralmente.")


if __name__=="__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes sintéticos das cinco áreas: leitura, retomada, NIR e segurança."""
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from executar_proposta1_cinco_areas import (
    record_status, nir_evidence, extract_geotiffs,
    locate_area1, transfer_public_or_drive, SOURCES)


def test_quatro_regioes_definidas_sem_area1_confundida():
    assert set(SOURCES)=={
        "sagrada_familia_caxias","centro_novo_hamburgo",
        "lomba_grande_novo_hamburgo","cristo_rei_sao_leopoldo"}
    assert all(a["bytes"]>1_000_000_000 for a in SOURCES.values())


def test_4_bandas_nao_equivale_nir_sem_comprovacao():
    image=SimpleNamespace(
        count=4,descriptions=("RGB Red","Green","Blue",None),
        colorinterp=[
            SimpleNamespace(name="red"),SimpleNamespace(name="green"),
            SimpleNamespace(name="blue"),SimpleNamespace(name="undefined")],
        tags=lambda i: {"DESCRICAO":"NIR em outra banda"} if i==1 else {}
    )
    ok,reason=nir_evidence("centro_novo_hamburgo",image,{})
    assert ok is False
    assert "documentação" in reason
    image.descriptions=("Red","Green","Blue","Near Infrared")
    ok,reason=nir_evidence("centro_novo_hamburgo",image,{})
    assert ok and "metadados" in reason


def test_banda_alpha_ou_evidencia_nao_documentada_nao_permitida():
    sample=SimpleNamespace(count=4,descriptions=(None,None,None,None),
        colorinterp=[SimpleNamespace(name="undefined") for _ in range(3)]+[
            SimpleNamespace(name="alpha")],
        tags=lambda i:{})
    user={"centro_novo_hamburgo":{"confirmada":True,
                                 "fonte":"Especificação técnica do fornecedor do levantamento"}}
    assert nir_evidence("centro_novo_hamburgo",sample,user)[0] is False
    sample.colorinterp[3].name="undefined"
    assert nir_evidence("centro_novo_hamburgo",sample,
                        {"centro_novo_hamburgo":{"confirmada":True,"fonte":""}})[0] is False
    assert nir_evidence("centro_novo_hamburgo",sample,user)[0] is True


def test_zip_extrai_apenas_duas_ortos_sem_atrasar(tmp_path):
    zip_path=tmp_path/"pacote.zip"
    with zipfile.ZipFile(zip_path,"w") as src:
        src.writestr("subpasta/CENTRO_ORTHO_RGB.tif",b"rgb")
        src.writestr("subpasta/CENTRO_ORTHO_4BANDAS.tif",b"multi")
        src.writestr("subpasta/arquivo_extra_nao_necessario.bin",b"extra")
    out=tmp_path/"rasters"
    rgb,multi=extract_geotiffs(zip_path,out)
    assert rgb.read_bytes()==b"rgb"
    assert multi.read_bytes()==b"multi"
    assert not (out/"arquivo_extra_nao_necessario.bin").exists()


def test_transferencia_prefere_drive_sem_rede(tmp_path):
    files=tmp_path/"drive"
    files.mkdir()
    name="ficticio.zip"
    (files/name).write_bytes(b"12345")
    dest=tmp_path/"scratch"/name
    actual=transfer_public_or_drive({
        "filename":name,"bytes":5,"id":"unused"},files,dest)
    assert actual.read_bytes()==b"12345"
    assert actual.stat().st_size==5


def test_status_de_execucao_persiste_na_retomada(tmp_path):
    dest=tmp_path/"saida"
    record_status(dest,{"area1_treinamento":{"estado":"concluido"}})
    value=record_status(dest,{"centro_novo_hamburgo":{"estado":"bloqueado_confirmacao_nir"}})
    assert value["area1_treinamento"]["estado"]=="concluido"
    assert value["centro_novo_hamburgo"]["estado"]=="bloqueado_confirmacao_nir"
    assert "atualizado_utc" in json.loads(
        (dest/"estado_cinco_areas.json").read_text(encoding="utf-8"))


def test_nao_aceita_area1_sem_todos_arquivos_originais(tmp_path):
    with pytest.raises(FileNotFoundError):
        locate_area1(tmp_path,tmp_path/"area1_incompleta")


def test_ordenamento_verificado_vincula_o_hash_do_raster(tmp_path):
    import hashlib
    from executar_proposta1_cinco_areas import documented_order

    multi = tmp_path / "multi.tif"
    multi.write_bytes(b"imagem original")
    proof = {"confirmada": True, "ordem_R_G_B_NIR": [3, 2, 1, 4],
             "arquivo_multiespectral_sha256": hashlib.sha256(multi.read_bytes()).hexdigest()}
    assert documented_order(multi, proof) == (3, 2, 1, 4)
    multi.write_bytes(b"outro raster")
    with pytest.raises(ValueError, match="SHA-256"):
        documented_order(multi, proof)

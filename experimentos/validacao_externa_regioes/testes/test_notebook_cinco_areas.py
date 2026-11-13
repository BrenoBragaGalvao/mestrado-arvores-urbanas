#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida a estrutura do notebook único sem executar dados privados do Drive."""
import json
from pathlib import Path


def test_notebook_cinco_areas_e_codigo_sintaticamente_valido():
    notebook=Path(__file__).resolve().parents[1]/"proposta1_cinco_areas_colab.ipynb"
    nb=json.loads(notebook.read_text(encoding="utf-8"))
    assert nb["nbformat"]==4
    sources=[]
    for i,cell in enumerate(nb["cells"]):
        src="".join(cell["source"])
        if cell["cell_type"]=="code":
            compile(src,f"notebook_cinco_areas_celula_{i}","exec")
            sources.append(src)
    combined="\n".join(sources)
    assert "executar_proposta1_cinco_areas.py" in combined
    assert "SOMENTE_AREA1=False" in combined
    assert all(name in combined for name in (
        "sagrada_familia_caxias","centro_novo_hamburgo",
        "lomba_grande_novo_hamburgo","cristo_rei_sao_leopoldo"))
    assert "FONTE_NIR" in combined
    assert "p7zip-full" in combined  # Cristo Rei exige descompactador RAR
    assert "REGIOES" in combined
    assert "estado_cinco_areas.json" in combined
    assert "metricas_externas.csv" in combined

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Proposta 2: validação PAREADA de 12 árvores com três leituras HeightCzech.

Não coleta dados; não preenche medições ausentes; não calcula métricas sem
pelo menos três árvores medidas com a identidade confirmada. Os valores
CHMv2 e ETH permanecem congelados para evitar deslocamento retrospectivo.
Não há diagnóstico de risco elétrico nem medição dos cabos.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
from statistics import median
import sys

COLUMNS = (
    "id_arvore", "latitude", "longitude", "altura_chmv2_m", "altura_eth2020_m",
    "identificacao", "acesso_publico",
    "leitura_1_heightczech_m", "leitura_2_heightczech_m", "leitura_3_heightczech_m",
    "data_medicao", "distancia_horizontal_m", "smartphone",
    "versao_heightczech", "observacoes",
)
# Proveniência: amostra selecionada dos 25 registros CAND, conferida com
# AMOSTRA_12_PONTOS_METODOLOGIA_E_TABELA.md. ID original, WGS84, CHMv2, ETH.
BASELINE = (
    ("CAND-002", "-15.85344927", "-47.94901704", "12", "12"),
    ("CAND-004", "-15.85640769", "-47.95126177", "22", "17"),
    ("CAND-006", "-15.85769557", "-47.94820182", "12", "16"),
    ("CAND-007", "-15.85572076", "-47.94998299", "15", "14"),
    ("CAND-008", "-15.85791926", "-47.94967912", "21", "22"),
    ("CAND-012", "-15.85557351", "-47.94952372", "22", "13"),
    ("CAND-013", "-15.85250612", "-47.95129829", "8", "4"),
    ("CAND-015", "-15.85652138", "-47.95153397", "15", "16"),
    ("CAND-016", "-15.85475037", "-47.94763657", "20", "17"),
    ("CAND-019", "-15.85791200", "-47.94822363", "16", "16"),
    ("CAND-020", "-15.85495867", "-47.94825533", "29", "18"),
    ("CAND-023", "-15.85650280", "-47.94892150", "25", "18"),
)
IDENTIFICATIONS = {"PENDENTE", "CONFIRMADA", "INCERTA", "NAO_LOCALIZADA"}
ACCESS = {"PENDENTE", "SIM", "NAO"}
READINGS = (
    "leitura_1_heightczech_m", "leitura_2_heightczech_m",
    "leitura_3_heightczech_m",
)


def parse_positive(text: str, field: str) -> float:
    try:
        number = Decimal(text.replace(",", "."))
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Valor não numérico no campo {field}") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError(f"Valor não positivo ou não finito no campo {field}")
    return float(number)


def load(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("Cabeçalho da ficha foi alterado")
        rows = list(reader)

    if len(rows) != len(BASELINE):
        raise ValueError("Esperados exatamente 12 pontos selecionados")
    for record, original in zip(rows, BASELINE):
        if None in record or any(value is None for value in record.values()):
            raise ValueError("Quantidade de colunas diferente do formulário")
        preserved = tuple(record[key] for key in COLUMNS[:5])
        if preserved != original:
            raise ValueError(
                f"IDs, coordenadas ou alturas originais divergentes na posição {original[0]}"
            )
        if record["identificacao"] not in IDENTIFICATIONS:
            raise ValueError(f"Identificação inválida no ponto {original[0]}")
        if record["acesso_publico"] not in ACCESS:
            raise ValueError(f"Estado de acesso inválido no ponto {original[0]}")
        filled = [bool(record[col].strip()) for col in READINGS]
        if any(filled) and not all(filled):
            raise ValueError(f"Três leituras obrigatórias em {original[0]}")
        if all(filled):
            if record["identificacao"] != "CONFIRMADA" or record["acesso_publico"] != "SIM":
                raise ValueError(f"Identidade e acesso precisam ser confirmados em {original[0]}")
            for col in READINGS:
                parse_positive(record[col], col)
            if not record["distancia_horizontal_m"]:
                raise ValueError(f"Distância horizontal ausente em {original[0]}")
            parse_positive(record["distancia_horizontal_m"], "distancia_horizontal_m")
            if not record["data_medicao"]:
                raise ValueError(f"Data de medição ausente em {original[0]}")
            try:
                measured_at = date.fromisoformat(record["data_medicao"])
            except ValueError as exc:
                raise ValueError(f"Data de medição inválida em {original[0]}") from exc
            if measured_at > date.today():
                raise ValueError(f"Data futura em {original[0]}")
            if not record["smartphone"].strip() or not record["versao_heightczech"].strip():
                raise ValueError(f"Aparelho/versão HeightCzech ausente em {original[0]}")
        else:
            other = ["data_medicao", "distancia_horizontal_m",
                     "smartphone", "versao_heightczech"]
            if any(record[col].strip() for col in other):
                raise ValueError(f"Metadados sem três leituras em {original[0]}")
    return rows


def summarize(rows: list[dict[str, str]]) -> tuple[list[dict], dict]:
    per_tree = []
    measured = []
    for rec in rows:
        result = {
            "id_arvore": rec["id_arvore"],
            "latitude": rec["latitude"],
            "longitude": rec["longitude"],
            "chmv2_m": rec["altura_chmv2_m"],
            "eth2020_m": rec["altura_eth2020_m"],
            "estado": "SEM_MEDICAO",
            "altura_campo_mediana_m": "",
            "amplitude_3_leituras_m": "",
            "erro_chmv2_m": "",
            "erro_eth2020_m": "",
        }
        if all(rec[column].strip() for column in READINGS):
            values = [parse_positive(rec[key], key) for key in READINGS]
            height = float(median(values))
            signed_chm = float(rec["altura_chmv2_m"]) - height
            signed_eth = float(rec["altura_eth2020_m"]) - height
            result.update({
                "estado": "MEDICAO_OBSERVACIONAL",
                "altura_campo_mediana_m": round(height, 4),
                "amplitude_3_leituras_m": round(max(values) - min(values), 4),
                "erro_chmv2_m": round(signed_chm, 4),
                "erro_eth2020_m": round(signed_eth, 4),
            })
            measured.append((signed_chm, signed_eth))
        per_tree.append(result)

    n = len(measured)
    summary = {
        "proposta": "2",
        "amostra_planejada": 12,
        "arvores_medidas_pareadas": n,
        "arvores_sem_medicao": 12 - n,
        "status": ("AGUARDA_CAMPO" if n == 0 else
                   "MEDICOES_INSUFICIENTES" if n < 3 else
                   "PARCIAL_EXPLORATORIO" if n < 12 else
                   "MEDICOES_COMPLETAS_REQUER_REVISAO"),
        "referencia_campo": "mediana de tres leituras HeightCzech por arvore",
        "amostra_dirigida": True,
        "medicao_de_cabos_eletricos": False,
        "prova_de_risco_eletrico": False,
        "observacao": ("Comparações descritivas para as MESMAS árvores observadas. "
                       "HeightCzech não é verdade absoluta e não permite extrapolar "
                       "a amostra intencional às demais árvores do DF."),
        "metricas": None,
    }
    # Evita relatar desempenho agregado de 1–2 indivíduos como validação.
    if n >= 3:
        def scores(index: int) -> dict:
            errors = [pair[index] for pair in measured]
            return {
                "n": n,
                "mae_m": round(sum(abs(x) for x in errors) / n, 4),
                "rmse_m": round(math.sqrt(sum(x*x for x in errors) / n), 4),
                "vies_m": round(sum(errors) / n, 4),
            }
        summary["metricas"] = {
            "chmv2": scores(0),
            "eth2020": scores(1),
        }
    return per_tree, summary


def run(input_csv: Path, output_dir: Path) -> dict:
    rows = load(input_csv)
    per_tree, summary = summarize(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "comparacao_pareada_12_arvores.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fields = list(per_tree[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(per_tree)
    (output_dir / "resumo_validacao_campo.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--entrada", type=Path, default=Path(__file__).with_name(
        "pontos_12_coleta_heightczech.csv"
    ))
    cli.add_argument("--saida", type=Path, required=True)
    args = cli.parse_args(argv)
    try:
        result = run(args.entrada, args.saida)
    except (ValueError, OSError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

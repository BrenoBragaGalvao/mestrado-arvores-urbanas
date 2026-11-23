#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F1 externo da Regressão Logística congelada da Area1; três regiões, blocos 500 m.

As referências devem ser avaliadas por humano, às cegas, ANTES de unir
previsões. Este script não cria rótulos, não treina e não seleciona modelos.
São necessários 200 pontos revisados por região, 20 árvores e 20 gramíneas,
pelo menos 10 blocos de 500 m distintos e identificação do revisor e data.

Comando:
python validar_logistica_quatro_regioes_500m.py \
  --regiao sagrada_familia_caxias \
  --rotulos sagrada_familia_caxias_FORMULARIO_CEGO_500m.csv \
  --predicoes sagrada_familia_caxias_PREVISOES_NAO_MOSTRAR_AO_REVISOR.csv \
  --saida sagrada_familia_resultado.json
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, accuracy_score, f1_score

REGIOES = {"sagrada_familia_caxias", "lomba_grande_novo_hamburgo", "cristo_rei_sao_leopoldo"}
CLASSES = ["arvore", "grama"]

def avaliar(regiao, rotulos, predicoes, n_boot=1200):
    if regiao not in REGIOES:
        raise ValueError("Região não incluída na bateria de quatro imagens")
    labels = pd.read_csv(rotulos, keep_default_na=False)
    preds = pd.read_csv(predicoes, keep_default_na=False)
    expected = {"amostra_id", "classe_verificada", "revisor", "data_revisao"}
    private = {"amostra_id", "predicao_modelo", "bloco_500m", "segmento_id"}
    if not expected.issubset(labels) or not private.issubset(preds):
        raise ValueError("Colunas ausentes no formulário de revisão ou na tabela privada")
    if len(labels) != 200 or len(preds) != 200:
        raise ValueError("Esperados 200 pontos predefinidos por região")
    if labels.amostra_id.duplicated().any() or preds.amostra_id.duplicated().any():
        raise ValueError("IDs duplicados")
    if set(labels.amostra_id) != set(preds.amostra_id):
        raise ValueError("IDs dos formulários divergentes do sorteio original")
    if preds.segmento_id.duplicated().any() or (preds.segmento_id.astype(int) == 0).any():
        raise ValueError("Segmento repetido, ausente ou inválido")
    data = preds.merge(labels[["amostra_id", "classe_verificada", "revisor", "data_revisao"]],
                       on="amostra_id", how="inner", validate="one_to_one")
    for name in ("classe_verificada", "revisor", "data_revisao"):
        data[name] = data[name].astype(str).str.strip().str.lower() if name == "classe_verificada" else data[name].astype(str).str.strip()
    if not set(data.classe_verificada).issubset({"arvore", "grama", "outro", "incerto", ""}):
        raise ValueError("Rótulos inválidos")
    if not set(data.predicao_modelo).issubset(set(CLASSES)):
        raise ValueError("Previsões inválidas")
    verified = data[data.classe_verificada.isin(CLASSES)].copy()
    counts = verified.classe_verificada.value_counts()
    status = {"regiao": regiao, "n_pontos": 200,
              "n_blocos_500m": int(data.bloco_500m.nunique()),
              "n_referencias_arvore": int(counts.get("arvore", 0)),
              "n_referencias_grama": int(counts.get("grama", 0)),
              "n_sem_rotulo": int(data.classe_verificada.eq("").sum()),
              "n_outro": int(data.classe_verificada.eq("outro").sum()),
              "n_incerto": int(data.classe_verificada.eq("incerto").sum()),
              "n_blocos_verificados": int(verified.bloco_500m.nunique())}
    missing = data.classe_verificada.eq("").any()
    missing_meta = ((data.classe_verificada.ne("")) & (data.revisor.eq("") | data.data_revisao.eq(""))).any()
    if missing or missing_meta or min(counts.get("arvore", 0), counts.get("grama", 0)) < 20 or verified.bloco_500m.nunique() < 10:
        status.update({"situacao": "PENDENTE_VALIDACAO_INDEPENDENTE", "f1_macro_externo_500m": None,
                       "observacao": "Faltam rótulos humanos documentados para todo o protocolo ou amostras suficientes por classe/bloco."})
        return status
    p, r, f, support = precision_recall_fscore_support(
        verified.classe_verificada, verified.predicao_modelo,
        labels=CLASSES, zero_division=0)
    cm = confusion_matrix(verified.classe_verificada, verified.predicao_modelo, labels=CLASSES)
    status.update({"situacao": "CALCULADO_COM_ROTULOS_DECLARADOS_REVISADOS",
                   "f1_macro_externo_500m": float(f1_score(
                       verified.classe_verificada, verified.predicao_modelo,
                       labels=CLASSES, average="macro", zero_division=0)),
                   "acuracia": float(accuracy_score(verified.classe_verificada, verified.predicao_modelo)),
                   "f1_arvore": float(f[0]), "f1_grama": float(f[1]),
                   "precisao_arvore": float(p[0]), "precisao_grama": float(p[1]),
                   "revocacao_arvore": float(r[0]), "revocacao_grama": float(r[1]),
                   "matriz_confusao": cm.tolist(),
                   "ordem_classes_matriz": CLASSES})
    # Bootstrap por blocos: incerteza espacial; NÃO realiza novo treinamento.
    rng = np.random.default_rng(20261117)
    keys = verified.bloco_500m.unique()
    group = {key: verified[verified.bloco_500m == key] for key in keys}
    boots = []
    for _ in range(n_boot):
        sampled = pd.concat([group[k] for k in rng.choice(keys, len(keys), replace=True)], ignore_index=True)
        if set(sampled.classe_verificada) == set(CLASSES):
            boots.append(f1_score(sampled.classe_verificada, sampled.predicao_modelo,
                                  labels=CLASSES, average="macro", zero_division=0))
    if len(boots) >= n_boot // 3:
        status["ic95_bootstrap_blocos_500m"] = np.quantile(boots, [0.025, 0.975]).tolist()
    else:
        status["ic95_bootstrap_blocos_500m"] = None
    status["limite_metodologico"] = "Revisão humana é declarada no CSV; o software não comprova a identidade do revisor. F1 condicionado aos pontos com árvores/gramíneas confirmadas; não é acurácia em todas as coberturas."
    return status

def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--regiao", choices=sorted(REGIOES), required=True)
    a.add_argument("--rotulos", type=Path, required=True)
    a.add_argument("--predicoes", type=Path, required=True)
    a.add_argument("--saida", type=Path, required=True)
    args = a.parse_args()
    result = avaliar(args.regiao, args.rotulos, args.predicoes)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

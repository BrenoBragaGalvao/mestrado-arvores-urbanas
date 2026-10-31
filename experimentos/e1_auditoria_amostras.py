# Experimento E1 — auditoria de rótulos e reavaliação com os dados existentes
# Execute APÓS todas as células do Segmentacao_area_completa_v2_experimentos.ipynb.
# No Google Colab: %run -i /content/e1_auditoria_amostras.py
# Não baixa dados, não altera df original, não grava saídas e não modifica o notebook.
# O split por objeto não substitui validação espacial independente.
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

atributos_e1 = ["mean_intensity", "mean_edges", "mean_ndvi"]
if not all(col in df.columns for col in atributos_e1 + ["classe"]):
    raise ValueError("O DataFrame de treinamento df não contém as colunas esperadas.")
if len(gdf_arvore_seg_filter) != len(df):
    raise ValueError("A quantidade/ordem de registros do sjoin e do DataFrame difere.")

auditoria_e1 = df[atributos_e1 + ["classe"]].reset_index(drop=True).copy()
auditoria_e1["segmento_id"] = pd.Index(gdf_arvore_seg_filter.index).astype(str).to_numpy()
auditoria_e1["classe"] = auditoria_e1["classe"].astype(str).str.strip().str.lower()
contagem_labels_e1 = auditoria_e1.groupby("segmento_id")["classe"].nunique()
conflitantes_e1 = set(contagem_labels_e1[contagem_labels_e1 > 1].index)
repetidos_e1 = int((auditoria_e1["segmento_id"].value_counts() > 1).sum())

# Inspeciona possível duplicação cruzada no split original de 80/20 (seed 42).
idx_treino_e1, idx_teste_e1 = train_test_split(
    np.arange(len(auditoria_e1)), test_size=0.2, random_state=42
)
grupos_treino_e1 = set(auditoria_e1.iloc[idx_treino_e1]["segmento_id"])
grupos_teste_e1 = set(auditoria_e1.iloc[idx_teste_e1]["segmento_id"])
sobrepostos_e1 = grupos_treino_e1 & grupos_teste_e1

print("=== E1a | Auditoria dos rótulos existentes ===")
print("Registros objeto–rótulo:", len(auditoria_e1))
print("Segmentos únicos:", auditoria_e1["segmento_id"].nunique())
print("Segmentos repetidos:", repetidos_e1)
print("Segmentos com classes conflitantes:", len(conflitantes_e1))
print("Segmentos compartilhados no split histórico:", len(sobrepostos_e1))
print("Distribuição original:", auditoria_e1["classe"].value_counts().to_dict())

# Exclui ambiguidades e evita que o mesmo segmento tenha múltiplas linhas.
base_e1 = auditoria_e1[
    ~auditoria_e1["segmento_id"].isin(conflitantes_e1)
].drop_duplicates(subset=["segmento_id"]).copy()
for coluna_e1 in atributos_e1:
    base_e1[coluna_e1] = pd.to_numeric(base_e1[coluna_e1], errors="coerce")
base_e1 = base_e1.replace([np.inf, -np.inf], np.nan).dropna(
    subset=atributos_e1 + ["classe"]
).reset_index(drop=True)
if base_e1["classe"].nunique() != 2 or base_e1["classe"].value_counts().min() < 5:
    raise ValueError("A base depurada não possui amostras suficientes nas duas classes.")

print("\n=== E1b | Reavaliação RF, 5 divisões, sem novos dados ===")
print("Amostras por objeto independente:", len(base_e1))
print("Distribuição:", base_e1["classe"].value_counts().to_dict())
X_e1, y_e1 = base_e1[atributos_e1], base_e1["classe"]
linhas_e1 = []
for seed_e1 in [11, 21, 42, 73, 97]:
    itr_e1, ite_e1 = train_test_split(
        np.arange(len(base_e1)), test_size=0.2, random_state=seed_e1,
        stratify=y_e1
    )
    assert not (
        set(base_e1.iloc[itr_e1]["segmento_id"]) &
        set(base_e1.iloc[ite_e1]["segmento_id"])
    ), "Um segmento apareceu nos dois conjuntos."
    modelo_e1 = RandomForestClassifier(
        n_estimators=500, random_state=42, n_jobs=-1
    )
    modelo_e1.fit(X_e1.iloc[itr_e1], y_e1.iloc[itr_e1])
    yp_e1 = modelo_e1.predict(X_e1.iloc[ite_e1])
    linhas_e1.append({
        "semente": seed_e1,
        "n_treino": len(itr_e1),
        "n_teste": len(ite_e1),
        "acuracia": accuracy_score(y_e1.iloc[ite_e1], yp_e1),
        "acuracia_balanceada": balanced_accuracy_score(y_e1.iloc[ite_e1], yp_e1),
        "f1_macro": f1_score(y_e1.iloc[ite_e1], yp_e1, average="macro"),
        "f1_arvore": f1_score(
            y_e1.iloc[ite_e1], yp_e1, pos_label="arvore", zero_division=0
        ),
    })
resultados_e1 = pd.DataFrame(linhas_e1)
print(resultados_e1.to_string(index=False))
print("\nResumo (média, desvio-padrão):")
print(resultados_e1[["acuracia", "acuracia_balanceada", "f1_macro", "f1_arvore"]]
      .agg(["mean", "std"]).to_string())
print("\nNota: estes resultados não são diretamente comparáveis ao 0,87 histórico")
print("sem considerar as diferenças de amostras e protocolo de avaliação.")

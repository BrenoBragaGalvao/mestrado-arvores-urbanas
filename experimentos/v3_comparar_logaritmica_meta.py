#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3: alturas estimadas pela logaritmica calibrada vs. alturas Meta/WRI CHMv2.

Usa APENAS dados ja existentes na Area1, com 257 IDs verificados no GitHub.
Duas comparacoes separadas: pixel exato e maximo no raio de 5 metros.
Preserva previsoes fora da amostra (OOF) das validacoes espaciais 250/500m,
sem reajustar parametros nos pontos de teste. Parametros ajustados em TODOS
os 257 pontos sao usados APENAS para demonstracao, nao validacao.
A area A e do superpixel Quickshift, NAO copa individual comprovada.
MAE em relacao a Meta/WRI nao e MAE de altura REAL de campo.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def stats(y, pred):
    y = np.asarray(y, float)
    pred = np.asarray(pred, float)
    ok = np.isfinite(y) & np.isfinite(pred)
    a, b = y[ok], pred[ok]
    if not len(a):
        raise ValueError("Sem valores validos para teste.")
    d = b - a
    return {
        "n": int(len(a)),
        "media_referencia_meta_m": float(np.mean(a)),
        "mediana_referencia_meta_m": float(np.median(a)),
        "media_formula_m": float(np.mean(b)),
        "mediana_formula_m": float(np.median(b)),
        "mae_vs_meta_m": float(np.mean(np.abs(d))),
        "rmse_vs_meta_m": float(np.sqrt(np.mean(d * d))),
        "vies_formula_menos_meta_m": float(np.mean(d)),
        "mediana_erro_abs_vs_meta_m": float(np.median(np.abs(d))),
        "fracao_diferenca_ate_2m": float(np.mean(np.abs(d) <= 2)),
        "fracao_diferenca_ate_5m": float(np.mean(np.abs(d) <= 5)),
        "pearson": float(np.corrcoef(a, b)[0, 1]) if np.std(a) and np.std(b) else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pontos", type=Path, required=True)
    parser.add_argument("--predicoes", type=Path, required=True)
    parser.add_argument("--parametros", type=Path, required=True)
    parser.add_argument("--validacao", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    pts = pd.read_csv(args.pontos, encoding="utf-8-sig")
    preds = pd.read_csv(args.predicoes, encoding="utf-8-sig")
    cfg = json.loads(args.parametros.read_text(encoding="utf-8"))
    cv = pd.read_csv(args.validacao, encoding="utf-8-sig")

    expected = {"ponto_id", "latitude", "longitude", "area_superpixel_m2",
                "toca_borda_tile", "altura_meta_pixel_m", "altura_meta_max_5m_m"}
    if not expected.issubset(pts.columns) or len(pts) != 257 or pts.ponto_id.nunique() != 257:
        raise ValueError("Planilha de origem nao contem 257 pontos validos.")
    if len(preds) != 257 or preds.ponto_id.nunique() != 257:
        raise ValueError("Predicoes OOF nao possuem 257 pontos unicos.")
    joined = pts.merge(preds, on="ponto_id", validate="one_to_one", how="left",
                       suffixes=("", "_oof"))
    if len(joined) != 257 or joined.ponto_id.isna().any():
        raise ValueError("Perda de IDs no cruzamento.")
    joined = joined.sort_values("ponto_id").reset_index(drop=True)
    if not np.allclose(joined.area_superpixel_m2,
                       joined.area_superpixel_m2_oof, rtol=0, atol=1e-10):
        raise ValueError("Area alterada entre fontes.")
    if (joined.area_superpixel_m2 <= 0).any():
        raise ValueError("Area nao positiva.")
    A = joined.area_superpixel_m2.to_numpy(float)

    out = joined[["ponto_id", "latitude", "longitude", "area_superpixel_m2",
                  "toca_borda_tile", "altura_meta_pixel_m",
                  "altura_meta_max_5m_m"]].copy()
    out["superpixel_nao_equivale_copa"] = True

    output_stats = {}
    row_records = []
    for kind, target in (("pixel", "altura_meta_pixel_m"),
                         ("raio5", "altura_meta_max_5m_m")):
        pars = cfg[target]["formula_final"]["logaritmica"]["params"]
        if len(pars) != 2:
            raise ValueError("Formula logaritmica sem dois coeficientes.")
        a, b = [float(x) for x in pars]
        full = np.clip(a + b * np.log1p(A), 0, 40)
        col_final = kind + "_ajuste_total_logaritmica"
        if not np.allclose(full, joined[col_final].to_numpy(float),
                           rtol=1e-9, atol=1e-9):
            raise ValueError("Valores de ajuste total nao coincidem com parametros gravados.")
        out[f"log_{kind}_ajuste_total_m"] = full
        out[f"dif_{kind}_ajuste_total_m"] = full - out[target]
        y = out[target].to_numpy(float)
        output_stats[kind] = {
            "coeficientes": {"a": a, "b": b},
            "formula": "H_estimada=a+b*ln(1+A)",
            "dados": "altura modelada Meta/WRI, nao medida de campo",
            "ajuste_total_apenas_descritivo": stats(y, full),
        }
        for block in (250, 500):
            col = f"{kind}_{block}_logaritmica"
            if col not in joined:
                raise ValueError("Falta predicao fora do treino: " + col)
            oof = joined[col].to_numpy(float)
            if not np.isfinite(oof).all():
                raise ValueError("Previsao OOF ausente: " + col)
            out[f"log_{kind}_oof_{block}m_m"] = oof
            out[f"dif_{kind}_oof_{block}m_m"] = oof - y
            score = stats(y, oof)
            baseline = cv[(cv.alvo_meta == target) & (cv.bloco_m == block) &
                          (cv.modelo == "constante")]
            logrow = cv[(cv.alvo_meta == target) & (cv.bloco_m == block) &
                        (cv.modelo == "logaritmica")]
            if len(baseline) != 1 or len(logrow) != 1:
                raise ValueError("Metricas da validacao anteriores nao encontradas.")
            if abs(score["mae_vs_meta_m"] - float(logrow.mae_m.iloc[0])) > 1e-8:
                raise ValueError("MAE OOF nao coincide com validacao espacial existente.")
            score["mae_baseline_constante_m"] = float(baseline.mae_m.iloc[0])
            score["log_supera_baseline_mae"] = (
                score["mae_vs_meta_m"] < score["mae_baseline_constante_m"])
            output_stats[kind][f"validacao_espacial_{block}m"] = score
            row_records.append({"referencia": kind, "blocos_m": block,
                                "a_ajuste_final": a, "b_ajuste_final": b, **score})

    args.out.mkdir(parents=True, exist_ok=True)
    out_csv = args.out / "v3_logaritmica_257_alturas_vs_meta.csv"
    out.to_csv(out_csv, index=False, encoding="utf-8-sig", float_format="%.8f")
    pd.DataFrame(row_records).to_csv(
        args.out / "v3_logaritmica_resumo_validacao.csv", index=False,
        encoding="utf-8-sig", float_format="%.8f")
    (args.out / "v3_logaritmica_resumo.json").write_text(
        json.dumps(output_stats, ensure_ascii=False, indent=2), encoding="utf-8")

    fmt = lambda x: f"{float(x):.2f}".replace(".", ",")
    report = [
        "# V3 — Alturas logarítmicas e estimativas Meta/WRI, nos 257 pontos",
        "",
        "## Objetivo e advertência",
        "",
        "Comparar a **altura calculada pela fórmula logarítmica** com a **altura",
        "modelada pelo mapa Meta/WRI CHMv2** em todos os 257 pontos originais",
        "de árvores da Area1, Caxias do Sul. O mapa não representa medição de",
        "campo e a área usada é de um **superpixel**, não de uma copa individual",
        "delimitada. Portanto não se reivindica estimativa validada de altura real.",
        "",
        "## Fórmulas ajustadas aos 257 pontos",
        "",
        f"- Pixel Meta: H = {output_stats['pixel']['coeficientes']['a']:.8f} + {output_stats['pixel']['coeficientes']['b']:.8f} × ln(1+A)",
        f"- Meta raio 5 m: H = {output_stats['raio5']['coeficientes']['a']:.8f} + {output_stats['raio5']['coeficientes']['b']:.8f} × ln(1+A)",
        "",
        "A é a área do superpixel em m². **As fórmulas acima foram ajustadas com",
        "todos os 257 pontos, apenas para ilustrar uma previsão final por ponto.**",
        "Para estimar desempenho sem reutilizar os mesmos alvos, apresentar as",
        "**previsões fora do treinamento (OOF)** dos 5 folds espaciais (250/500 m",
        "e embargo de 25 m), conforme abaixo.",
        "",
        "## Validação espacial externa (predições OOF)",
        "",
        "| Referência Meta | Blocos | MAE log vs. Meta | RMSE log vs. Meta | MAE constante | Até 2 m | Até 5 m |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in row_records:
        report.append(
            f"| {('Pixel exato' if row['referencia']=='pixel' else 'Máximo raio 5 m')} "
            f"| {row['blocos_m']} m | {fmt(row['mae_vs_meta_m'])} m "
            f"| {fmt(row['rmse_vs_meta_m'])} m "
            f"| {fmt(row['mae_baseline_constante_m'])} m "
            f"| {fmt(100 * row['fracao_diferenca_ate_2m'])}% "
            f"| {fmt(100 * row['fracao_diferenca_ate_5m'])}% |"
        )
    report.extend([
        "",
        "**Interpretação:** em ambos os alvos e ambas as escalas, a logarítmica",
        "não superou o controle constante em MAE. O objetivo aqui é mostrar",
        "explicitamente a altura prevista de cada ponto e sua divergência em",
        "relação ao mapa Meta, sem declarar validade como altura real.",
        "",
        "## Primeiros 12 pontos (IDs fixos, sem escolha pelos resultados)",
        "",
        "| ID | Área (m²) | Meta pixel (m) | Log pixel ajuste total (m) | Log pixel OOF 250 m (m) | Meta raio 5 m (m) | Log raio 5 m ajuste total (m) | Log raio OOF 250 m (m) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for _, p in out.head(12).iterrows():
        report.append(
            "| " + str(int(p.ponto_id))
            + " | " + fmt(p.area_superpixel_m2)
            + " | " + fmt(p.altura_meta_pixel_m)
            + " | " + fmt(p.log_pixel_ajuste_total_m)
            + " | " + fmt(p.log_pixel_oof_250m_m)
            + " | " + fmt(p.altura_meta_max_5m_m)
            + " | " + fmt(p.log_raio5_ajuste_total_m)
            + " | " + fmt(p.log_raio5_oof_250m_m)
            + " |"
        )
    report.extend([
        "",
        "## Arquivos e rastreabilidade",
        "",
        "- CSV com **257 linhas, uma por árvore**, incluindo localização, área,",
        "  altura da Meta, altura logarítmica calculada com todos os pontos,",
        "  previsão fora da amostra (250 e 500 m) e diferenças: ",
        "  [v3_logaritmica_257_alturas_vs_meta.csv](v3_logaritmica_257_alturas_vs_meta.csv).",
        "- [Métricas OOF](v3_logaritmica_resumo_validacao.csv) e",
        "  [resumo JSON](v3_logaritmica_resumo.json).",
        "- [Gráfico de comparação no pixel](v3_logaritmica_meta_pixel.png) e",
        "  [gráfico de comparação em 5 m](v3_logaritmica_meta_raio5.png).",
        "- Script: [v3_comparar_logaritmica_meta.py](../../experimentos/v3_comparar_logaritmica_meta.py).",
        "",
        "**Limitações:** o modelo é calibrado contra outro modelo, não",
        "contra alturas reais. Valor zero no pixel não prova ausência de",
        "árvore; máximo em 5 m pode corresponder a outro indivíduo.",
        "Os coeficientes originais do notebook inicial não foram alterados.",
        "",
    ])
    (args.out / "v3_logaritmica_comparacao_meta.md").write_text(
        "\n".join(report), encoding="utf-8")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        for kind, label, target in [
            ("pixel", "Meta/WRI no pixel exato", "altura_meta_pixel_m"),
            ("raio5", "Meta/WRI: máximo em raio de 5 m",
             "altura_meta_max_5m_m")]:
            fig, ax = plt.subplots(figsize=(7.5, 6))
            ax.scatter(out[target], out[f"log_{kind}_oof_250m_m"],
                       s=22, alpha=.6, label="Predição logarítmica OOF (250 m)")
            mm = max(float(np.max(out[target])),
                     float(np.max(out[f"log_{kind}_oof_250m_m"])))
            ax.plot([0, mm], [0, mm], linestyle="--", linewidth=1,
                    color="gray", label="Igualdade 1:1")
            ax.set(xlabel=label + " (m)",
                   ylabel="Estimativa logarítmica em teste espacial (m)",
                   title="Area1: altura prevista vs. Meta (257 pontos)")
            ax.legend()
            fig.tight_layout()
            fig.savefig(args.out / f"v3_logaritmica_meta_{kind}.png", dpi=160)
            plt.close(fig)
    except ImportError:
        print("Matplotlib indisponivel; gráficos nao produzidos.")

    print(json.dumps(output_stats, ensure_ascii=False, indent=2))
    print("CSV:", out_csv)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Tests use fictional HeightCzech readings exclusively; never field evidence."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from validar_heightczech_12_arvores import BASELINE, COLUMNS, load, run


BASE = Path(__file__).with_name("pontos_12_coleta_heightczech.csv")


class FieldValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "medicoes_sinteticas.csv"
        self.output = Path(self.temp.name) / "resultados"
        with BASE.open(newline="", encoding="utf-8") as stream:
            self.rows = list(csv.DictReader(stream))

    def write(self):
        with self.path.open("w", newline="", encoding="utf-8") as stream:
            w = csv.DictWriter(stream, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(self.rows)

    def fill(self, index, heights, distance=12.0):
        row = self.rows[index]
        row["identificacao"] = "CONFIRMADA"
        row["acesso_publico"] = "SIM"
        for key, value in zip(
            ("leitura_1_heightczech_m", "leitura_2_heightczech_m",
             "leitura_3_heightczech_m"), heights
        ):
            row[key] = str(value)
        row["data_medicao"] = "2026-11-20"
        row["distancia_horizontal_m"] = str(distance)
        row["smartphone"] = "Modelo sintetico"
        row["versao_heightczech"] = "teste"

    def test_formulario_original_nao_tem_altura_de_campo(self):
        result = run(BASE, self.output)
        self.assertEqual(result["status"], "AGUARDA_CAMPO")
        self.assertEqual(result["arvores_medidas_pareadas"], 0)
        self.assertIsNone(result["metricas"])
        self.assertFalse(result["prova_de_risco_eletrico"])
        tab = list(csv.DictReader((self.output /
            "comparacao_pareada_12_arvores.csv").open(encoding="utf-8")))
        self.assertEqual(len(tab), 12)
        self.assertEqual({r["estado"] for r in tab}, {"SEM_MEDICAO"})
        self.assertEqual([r["id_arvore"] for r in tab],
                         [r[0] for r in BASELINE])

    def test_exemplo_sintetico_tres_medicoes_pareadas(self):
        self.fill(0, [10,12,14]) # mediana 12; CHMv2 12; ETH 12
        self.fill(1, [19,20,21]) # mediana 20; CHMv2 22; ETH 17
        self.fill(2, [10,11,12]) # mediana 11; CHMv2 12; ETH 16
        self.write()
        result = run(self.path, self.output)
        self.assertEqual(result["status"], "PARCIAL_EXPLORATORIO")
        self.assertEqual(result["arvores_medidas_pareadas"], 3)
        self.assertEqual(result["arvores_sem_medicao"], 9)
        self.assertEqual(result["metricas"]["chmv2"]["mae_m"], 1.0)
        self.assertEqual(result["metricas"]["eth2020"]["mae_m"], 2.6667)
        self.assertEqual(result["metricas"]["chmv2"]["vies_m"], 1.0)
        self.assertEqual(result["metricas"]["eth2020"]["vies_m"], 0.6667)
        saved = json.loads((self.output / "resumo_validacao_campo.json").read_text())
        self.assertEqual(saved["metricas"], result["metricas"])

    def test_um_ou_dois_registros_nao_geram_mae_global(self):
        self.fill(0, [10,12,14])
        self.write()
        summary = run(self.path, self.output)
        self.assertEqual(summary["status"], "MEDICOES_INSUFICIENTES")
        self.assertIsNone(summary["metricas"])

    def test_readings_partial_rejected(self):
        self.fill(0, [10,12,14])
        self.rows[0]["leitura_3_heightczech_m"] = ""
        self.write()
        with self.assertRaisesRegex(ValueError, "Três leituras"):
            load(self.path)

    def test_coordinates_and_model_predictions_are_frozen(self):
        self.rows[0]["altura_chmv2_m"] = "13"
        self.write()
        with self.assertRaisesRegex(ValueError, "divergentes"):
            load(self.path)
        self.rows[0]["altura_chmv2_m"] = "12"
        self.rows[0]["latitude"] = "-15.85340000"
        self.write()
        with self.assertRaisesRegex(ValueError, "divergentes"):
            load(self.path)

    def test_without_confirmed_identity_is_not_measurable(self):
        self.fill(0, [10,12,14])
        self.rows[0]["identificacao"] = "INCERTA"
        self.write()
        with self.assertRaisesRegex(ValueError, "Identidade e acesso"):
            load(self.path)

    def test_without_measured_distance_is_not_valid(self):
        self.fill(0, [10,12,14])
        self.rows[0]["distancia_horizontal_m"] = ""
        self.write()
        with self.assertRaisesRegex(ValueError, "Distância horizontal"):
            load(self.path)

    def test_duplicate_id_cannot_enter_the_sample(self):
        self.rows[1]["id_arvore"] = self.rows[0]["id_arvore"]
        self.write()
        with self.assertRaisesRegex(ValueError, "divergentes"):
            load(self.path)

    def test_field_data_cannot_be_substituted_by_model_values(self):
        self.rows[0]["altura_eth2020_m"] = "12.5"
        self.write()
        with self.assertRaisesRegex(ValueError, "divergentes"):
            load(self.path)


if __name__ == "__main__":
    unittest.main()

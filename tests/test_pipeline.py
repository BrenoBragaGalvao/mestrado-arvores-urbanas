"""Testes automatizados do fluxo do mestrado com dados sintéticos mínimos.

Estes testes NÃO substituem a validação do processamento integral dos rasters Area1
nem a validação científica com novas bases, amostras independentes ou alturas reais.
"""
import ast
import json
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio import features
from rasterio.io import MemoryFile
from rasterio.mask import mask
from rasterio.transform import from_origin
from shapely.geometry import Point, box, shape
from skimage.feature import canny
from skimage.segmentation import quickshift
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "Segmentacao_area_completa.ipynb"


class TestNotebookStructure(unittest.TestCase):
    def test_notebook_is_valid_and_code_compiles(self):
        with NOTEBOOK.open(encoding="utf-8") as f:
            notebook = json.load(f)
        self.assertEqual(notebook["nbformat"], 4)
        code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        self.assertGreaterEqual(len(code), 7)
        for index, cell in enumerate(code):
            text = "".join(cell["source"])
            clean = "\n".join(
                line for line in text.splitlines() if not line.lstrip().startswith("%")
            )
            with self.subTest(cell=index):
                compile(clean, f"celula_{index}.py", "exec")
        code_text = "\n".join("".join(c["source"]) for c in code)
        for needle in (
            "quickshift(", "features.shapes(", "KMeans(", "RandomForestClassifier(",
            "classification_report(", "stratify=y", "mean_ndvi", "canny(",
            "predicted_classe == 'arvore'", "altura_estimada_m",
            "gpd.sjoin_nearest(", "metricas_classificacao.json",
            "resumo_proximidade_postes.csv",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, code_text)
        self.assertFalse((ROOT / "Segmentacao_area_completa_2026.ipynb").exists())
        self.assertFalse((ROOT / "Segmentacao_classificacao.ipynb").exists())

    def test_documentation_references_current_notebook(self):
        for path in ("README.md", "data/README.md", "docs/allometria.md",
                     "docs/experimento_area_completa_2026-10-29.md"):
            with self.subTest(path=path):
                content = (ROOT / path).read_text(encoding="utf-8")
                self.assertNotIn("Segmentacao_area_completa_2026.ipynb", content)
        self.assertIn("Segmentacao_area_completa.ipynb",
                      (ROOT / "README.md").read_text(encoding="utf-8"))


class TestSyntheticGeospatialPipeline(unittest.TestCase):
    def test_segmentation_polygonization_and_kmeans(self):
        rng = np.random.default_rng(42)
        im = rng.integers(10, 245, size=(64, 64, 3), dtype=np.uint8)
        segments = quickshift(im, kernel_size=3, max_dist=5, ratio=0.04).astype("int32")
        self.assertEqual(segments.shape, (64, 64))
        transform = from_origin(0, 32, .5, .5)
        polygons = [shape(geom) for geom, _ in features.shapes(segments, transform=transform)]
        self.assertGreater(len(polygons), 0)
        area = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:31982")
        self.assertTrue(area.geometry.is_valid.all())
        n = min(len(area), 60)
        self.assertGreaterEqual(n, 6)
        atributos = np.column_stack(
            [np.arange(n, dtype=float), rng.normal(size=(n, 7))]
        )
        grupos = KMeans(n_clusters=6, random_state=42, n_init=10).fit_predict(atributos)
        self.assertEqual(len(grupos), n)
        self.assertEqual(len(set(grupos)), 6)

    def test_ndvi_brightness_canny_raster_mask(self):
        altura, largura = 48, 48
        im = np.zeros((4, altura, largura), dtype=np.uint16)
        im[0] = 1000
        im[1] = 1500
        im[2] = 1200
        im[3, :, :24] = 3000
        im[3, :, 24:] = 500
        ndvi = (im[3].astype("float32") - im[0]) / (
            im[3].astype("float32") + im[0] + 1e-8)
        brilho = np.max(im[:3], axis=0).astype("float32") / 65535
        bordas = canny(im[3] / 10000, sigma=1)
        self.assertGreater(float(ndvi[0, 0]), 0)
        self.assertLess(float(ndvi[0, -1]), 0)
        self.assertTrue(np.allclose(brilho, 1500 / 65535))
        self.assertEqual(bordas.shape, (altura, largura))
        profile = dict(driver="GTiff", height=altura, width=largura, count=3,
                       dtype="float32", crs="EPSG:31982",
                       transform=from_origin(0, 24, .5, .5))
        with MemoryFile() as mem:
            with mem.open(**profile) as dst:
                dst.write(np.stack([brilho, bordas.astype("float32"), ndvi]))
            with mem.open() as src:
                recorte, _ = mask(src, [box(1, 1, 10, 10).__geo_interface__], crop=True)
                self.assertEqual(recorte.shape[0], 3)
                self.assertTrue(np.isfinite(recorte).all())

    def test_deduplicate_labels_train_rf_height_and_postes(self):
        geom = [box(i * 3, 0, i * 3 + 2, 2) for i in range(20)]
        objetos = gpd.GeoDataFrame(geometry=geom, crs="EPSG:31982")
        coords = [Point(g.centroid.x, g.centroid.y) for g in geom]
        # O primeiro objeto recebe dois rótulos iguais: deve resultar em um objeto.
        labels = gpd.GeoDataFrame(
            {"Classe": ["arvore" if i % 2 == 0 else "grama" for i in range(20)] +
             ["arvore"]},
            geometry=coords + [coords[0]], crs="EPSG:31982")
        joined = gpd.sjoin(objetos, labels, how="inner", predicate="intersects")
        self.assertGreater(len(joined), len(objetos))
        grupos = joined.groupby(level=0)["Classe"].agg(lambda x: sorted(set(x)))
        idx = grupos[grupos.map(len) == 1].index
        self.assertEqual(len(idx), len(objetos))
        y = grupos.loc[idx].map(lambda x: x[0])
        atributos = pd.DataFrame({
            "mean_ndvi": [0.6 if i % 2 == 0 else 0.2 for i in range(20)],
            "mean_intensity": [0.4 if i % 2 == 0 else 0.8 for i in range(20)],
            "mean_edges": [0.3 if i % 2 == 0 else 0.1 for i in range(20)],
        })
        X_tr, X_te, y_tr, y_te = train_test_split(
            atributos, y, test_size=0.2, random_state=42, stratify=y)
        model = RandomForestClassifier(n_estimators=500, random_state=42)
        model.fit(X_tr, y_tr)
        y_pred = model.predict(X_te)
        self.assertEqual(len(y_pred), 4)
        self.assertGreaterEqual(accuracy_score(y_te, y_pred), 0.5)
        self.assertEqual(confusion_matrix(y_te, y_pred).shape, (2, 2))
        objetos["predicted_classe"] = model.predict(atributos)
        arvores = objetos.loc[objetos.predicted_classe == "arvore"].copy()
        self.assertFalse(arvores.empty)
        arvores["altura_estimada_m"] = 2.5 * arvores.geometry.area ** .4
        self.assertTrue(np.isfinite(arvores.altura_estimada_m).all())
        postes = gpd.GeoDataFrame(geometry=[Point(1, 1), Point(14, 1)],
                                  crs="EPSG:31982")
        for d in (1, 3, 5):
            vizinhos = gpd.sjoin_nearest(
                arvores, postes, how="inner", max_distance=d,
                distance_col="distancia_m")
            self.assertTrue((vizinhos.distancia_m <= d).all())
            self.assertLessEqual(vizinhos.index.nunique(), len(arvores))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes locais com dados sintéticos. NÃO são resultados científicos de regiões."""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aplicar_regiao import FEATURES, FIELDS, feature_means, predict_tile
from auditar_pacotes import archive_list, is_safe_member, unpack_zip_safely
from treinar_area1 import assign_groups, embargo_train, inner_splits, read_training_data


def test_member_validation():
    assert is_safe_member("regiao/rasters/imagem.tif")
    assert not is_safe_member("../desvio.txt")
    assert not is_safe_member("/etc/passwd")
    assert not is_safe_member("C:\\temp\\foo.txt")
    assert not is_safe_member("regiao/../../sair.txt")


def test_zip_list_and_safe_extract(tmp_path):
    input_file = tmp_path/"region.zip"
    with zipfile.ZipFile(input_file,"w") as z:
        z.writestr("folder/arquivo.txt","ok")
    rows = archive_list(input_file)
    assert rows[0]["caminho"]=="folder/arquivo.txt"
    unpack_zip_safely(input_file,tmp_path/"output")
    assert (tmp_path/"output/folder/arquivo.txt").read_text()=="ok"


def test_zip_refuses_traversal(tmp_path):
    input_file = tmp_path/"unsafe.zip"
    with zipfile.ZipFile(input_file,"w") as z:
        z.writestr("../escape.txt","bad")
    with pytest.raises(ValueError):
        unpack_zip_safely(input_file,tmp_path/"output")
    assert not (tmp_path/"escape.txt").exists()


def test_feature_means_produces_correct_shape():
    seg = np.array([[0,0],[1,1]],dtype="int32")
    vals = np.stack([np.array([[1,3],[2,4]]),np.array([[8,8],[6,6]])])
    cnt, feat = feature_means(seg, vals, np.ones((2,2),dtype=bool))
    np.testing.assert_array_equal(cnt,[2,2])
    np.testing.assert_allclose(feat,[[2,8],[3,6]])


def test_tile_predicts_without_fitting(tmp_path):
    import rasterio
    from rasterio.transform import from_origin
    from sklearn.dummy import DummyClassifier
    rng = np.random.default_rng(42)
    rgb = rng.integers(30,220,size=(32,32,3),dtype="uint8")
    multi = np.zeros((4,32,32),dtype="uint16")
    multi[:3] = np.moveaxis(rgb,2,0)
    multi[3] = np.full((32,32),4000,dtype="uint16")
    X = np.array([[.2,.01,.4],[.7,.1,.6]])
    y = np.array(["arvore","grama"])
    clf=DummyClassifier(strategy="constant",constant="arvore").fit(X,y)
    rows, tag, predictions = predict_tile(
        rgb,multi,np.ones((32,32),dtype=bool),
        from_origin(100,200,.5,.5),0,{"Dummy":clf})
    assert rows
    assert tag.shape == (32,32)
    assert tag.min()>0
    assert predictions["Dummy"].shape == (32,32)
    assert np.unique(predictions["Dummy"]).tolist()==[1]
    assert all(len(r)==len(FIELDS) for r in rows)


def test_group_splits_and_embargo(tmp_path):
    xx, yy = np.meshgrid(np.arange(20)*100.,np.arange(20)*100.)
    n=xx.size
    frame=pd.DataFrame({
        "id":[str(i) for i in range(n)],
        "classe":np.where((np.arange(n)%2)==0,"arvore","grama"),
        "x":xx.ravel(),"y":yy.ravel(),
        "mean_intensity":np.linspace(.1,.9,n),
        "mean_edges":np.linspace(.01,.15,n),
        "mean_ndvi":np.linspace(-.2,.8,n)
    })
    csv=tmp_path/"base.csv"
    frame.to_csv(csv,index=False)
    recovered=read_training_data(csv)
    groups=assign_groups(frame[["x","y"]].to_numpy(),500)
    assert len(set(groups))>=5
    folds=list(inner_splits(recovered,None))
    assert len(folds)>=4
    for scale,repeat,tr,te in folds:
        assert set(tr).isdisjoint(te)
        assert len(set(frame.classe.iloc[tr]))==2
        assert len(set(frame.classe.iloc[te]))==2
        if len(tr):
            xy=frame[["x","y"]].to_numpy()
            from scipy.spatial import cKDTree
            distances=cKDTree(xy[te]).query(xy[tr],k=1)[0]
            assert np.all(distances>25)


def test_model_label_signature():
    assert FEATURES == ("mean_intensity","mean_edges","mean_ndvi")

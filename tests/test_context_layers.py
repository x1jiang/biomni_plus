"""
Tests for Biomni-Plus context layers.
"""

from biomni_plus.context_layers import BiomniDataLakeLayer, BiomniKnowHowLayer, BiomniADLayer

def test_data_lake_layer():
    layer = BiomniDataLakeLayer(data_path="./data")
    text = layer.inject(None)
    assert text is not None
    assert "BIOMEDICAL DATA LAKE" in text

def test_know_how_layer():
    layer = BiomniKnowHowLayer()
    text = layer.inject(None)
    assert text is not None
    assert "PROTOCOL" in text

def test_ad_layer():
    layer = BiomniADLayer()
    text = layer.inject(None)
    assert text is not None
    assert "ALZHEIMER" in text

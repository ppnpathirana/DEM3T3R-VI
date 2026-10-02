import os
import pytest
import numpy as np
import torch

from backend.neural_depth import NeuralDepthEstimator
from backend.neural_segmentation import TerrainSegmenter
from backend.neural_driving import EndToEndPilot, DAVE2DrivingNet
from backend.tinyml_engine import TinyMLSensorClassifier
from backend.neural_suite import CropGuardNeuralSuite


def test_neural_depth_estimation():
    estimator = NeuralDepthEstimator(device="cpu")
    dummy_frame = np.ones((240, 320, 3), dtype=np.uint8) * 128
    
    depth, cmap, telem = estimator.estimate_depth(dummy_frame, return_colormap=True)
    
    assert depth.shape == (240, 320)
    assert cmap.shape == (240, 320, 3)
    assert 0.0 <= depth.min() <= depth.max() <= 1.0
    assert "corridor_distances_m" in telem
    assert telem["corridor_distances_m"]["center"] > 0.0


def test_semantic_terrain_segmentation():
    segmenter = TerrainSegmenter(device="cpu")
    dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    # Fill lower part with soil color
    dummy_frame[140:240, :] = [42, 110, 160]
    
    cmap, overlay, telem = segmenter.segment_terrain(dummy_frame, create_overlay=True)
    
    assert cmap.shape == (240, 320)
    assert overlay.shape == (240, 320, 3)
    assert set(np.unique(cmap)).issubset({0, 1, 2, 3})
    assert "path_offset_ratio" in telem
    assert -1.0 <= telem["path_offset_ratio"] <= 1.0


def test_end_to_end_neural_driving():
    pilot = EndToEndPilot(device="cpu")
    dummy_frame = np.ones((240, 320, 3), dtype=np.uint8) * 150
    
    res = pilot.predict_steering(dummy_frame)
    
    assert -1.0 <= res["steering_angle"] <= 1.0
    assert 0.0 <= res["throttle"] <= 1.0
    assert -255 <= res["motor_left"] <= 255
    assert -255 <= res["motor_right"] <= 255
    assert res["action"] in ["FORWARD", "STEER_LEFT", "STEER_RIGHT", "STOP"]


def test_tinyml_sensor_classification():
    clf = TinyMLSensorClassifier()
    
    # Drought test: high temp, very low soil moisture
    drought_res = clf.predict(temp=36.0, hum=40.0, press=1012.0, lux=35000.0, uv=1.5, soil=15.0)
    assert drought_res["prediction"] == "DROUGHT_HEAT_STRESS"
    assert drought_res["confidence"] >= 0.80
    
    # Pathogen test: high humidity, moderate temp
    pathogen_res = clf.predict(temp=26.0, hum=92.0, press=1008.0, lux=12000.0, uv=0.4, soil=75.0)
    assert pathogen_res["prediction"] == "PATHOGEN_HUMIDITY_RISK"
    assert pathogen_res["confidence"] >= 0.80


def test_tinyml_c_header_export(tmp_path):
    clf = TinyMLSensorClassifier()
    out_file = str(tmp_path / "test_tinyml.h")
    clf.export_c_header(out_file)
    
    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "tinyml_classify" in content
    assert "tinyml_w1" in content
    assert "tinyml_relu" in content


def test_neural_suite_integration():
    suite = CropGuardNeuralSuite(device="cpu")
    dummy_frame = np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8)
    
    res = suite.process_visuals(dummy_frame, generate_visualizations=False)
    assert res["depth"] is not None
    assert res["segmentation"] is not None
    assert res["pilot"] is not None
    assert res["latency_ms"] >= 0.0
    
    status = suite.get_status()
    assert len(status["models_active"]) == 4

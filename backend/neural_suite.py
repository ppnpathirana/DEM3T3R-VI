"""
DEM3T3R V1 Unified Deep Neural Network Suite Coordinator
Manages concurrent execution of:
  1. Monocular 3D Depth Estimator (CUDA FP16)
  2. Semantic Terrain & Furrow Segmenter (CUDA FP16)
  3. End-to-End Behavioral Driving Pilot (NVIDIA DAVE-2)
  4. TinyML Edge Sensor Anomaly Classifier
"""

import time
import numpy as np
import torch
from typing import Dict, Any, Tuple, Optional

from backend.neural_depth import NeuralDepthEstimator
from backend.neural_segmentation import TerrainSegmenter
from backend.neural_driving import EndToEndPilot
from backend.tinyml_engine import TinyMLSensorClassifier


class CropGuardNeuralSuite:
    def __init__(self, device: Optional[str] = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[NEURAL SUITE] Initializing DEM3T3R V1 Deep Neural Suite on: {self.device}")
        
        self.depth_estimator = NeuralDepthEstimator(device=self.device)
        self.terrain_segmenter = TerrainSegmenter(device=self.device)
        self.driving_pilot = EndToEndPilot(device=self.device)
        self.tinyml_classifier = TinyMLSensorClassifier()
        
        self.last_inference_time = 0.0
        self.last_latency_ms = 0.0

    def process_visuals(
        self,
        frame: np.ndarray,
        generate_visualizations: bool = False
    ) -> Dict[str, Any]:
        """
        Runs concurrent neural inference over the camera frame.
        """
        if frame is None or frame.size == 0:
            return {
                "depth": None,
                "segmentation": None,
                "pilot": None,
                "latency_ms": 0.0
            }

        start_t = time.perf_counter()

        # 1. 3D Depth Estimation
        _, depth_cmap, depth_telem = self.depth_estimator.estimate_depth(
            frame, return_colormap=generate_visualizations
        )

        # 2. Semantic Terrain & Row Centering
        _, seg_overlay, seg_telem = self.terrain_segmenter.segment_terrain(
            frame, create_overlay=generate_visualizations
        )

        # 3. End-to-End Neural Pilot
        pilot_telem = self.driving_pilot.predict_steering(frame)

        latency_ms = (time.perf_counter() - start_t) * 1000.0
        self.last_latency_ms = latency_ms
        self.last_inference_time = time.time()

        return {
            "depth": depth_telem,
            "depth_colormap": depth_cmap,
            "segmentation": seg_telem,
            "segmentation_overlay": seg_overlay,
            "pilot": pilot_telem,
            "latency_ms": round(latency_ms, 2),
            "device": self.device
        }

    def classify_telemetry(self, sensors: Dict[str, Any]) -> Dict[str, Any]:
        """Runs TinyML sensor anomaly classifier over real-time environmental metrics."""
        temp = float(sensors.get("temperature", 25.0))
        hum = float(sensors.get("humidity", 60.0))
        press = float(sensors.get("pressure", 1013.0))
        lux = float(sensors.get("light", 15000.0))
        uv = float(sensors.get("uvVoltage", 0.8))
        soil = float(sensors.get("soilMoisture", 45.0))

        return self.tinyml_classifier.predict(temp, hum, press, lux, uv, soil)

    def get_status(self) -> Dict[str, Any]:
        gpu_mem_mb = 0.0
        if torch.cuda.is_available():
            gpu_mem_mb = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)

        return {
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
            "gpu_memory_allocated_mb": gpu_mem_mb,
            "last_latency_ms": round(self.last_latency_ms, 2),
            "models_active": [
                "DepthEncoderDecoder (ASPP Depth)",
                "MobileSegmenterNet (Semantic Terrain)",
                "DAVE2DrivingNet (NVIDIA End-to-End)",
                "TinyMLNet (Edge Sensor Anomaly)"
            ]
        }

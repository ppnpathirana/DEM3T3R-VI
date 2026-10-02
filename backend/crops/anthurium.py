"""
@file: anthurium.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
DEM3T3R V1 Plugin for Anthurium disease detection.
"""
import os
from typing import List, Dict, Any
from backend.crops._base import CropModel

class AnthuriumCropModel(CropModel):
    def __init__(self):
        self._model = None
        self._crop = "anthurium"
        self._model_file = "anthurium.pt"
        self._diseases = ['anthurium_bacterial_blight', 'anthurium_anthracnose', 'anthurium_root_rot', 'healthy']
        self._confidence_threshold = 0.50
        self._description = "Anthurium foliage pathogen detector"

    def load(self, models_dir: str) -> bool:
        model_path = os.path.join(models_dir, self._model_file)
        if not os.path.exists(model_path):
            self._model = None
            return False
        try:
            from ultralytics import YOLO
            self._model = YOLO(model_path)
            return True
        except Exception as e:
            print(f"[AnthuriumCropModel] Failed to load {model_path}: {e}")
            self._model = None
            return False

    def predict(self, frame) -> List[Dict[str, Any]]:
        if self._model is None or frame is None:
            return []
        try:
            results = self._model.predict(frame, conf=self._confidence_threshold, verbose=False)
            detections = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0].item())
                    cls_name = self._model.names.get(cls_id, f"class_{cls_id}")
                    conf = float(box.conf[0].item())
                    xyxy = [round(v, 1) for v in box.xyxy[0].tolist()]
                    detections.append({
                        "class": cls_name,
                        "confidence": conf,
                        "bbox": xyxy,
                        "mask": None
                    })
            return detections
        except Exception as e:
            print(f"[AnthuriumCropModel] Predict error: {e}")
            return []

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "crop": self._crop,
            "model_file": self._model_file,
            "diseases": self._diseases,
            "confidence_threshold": self._confidence_threshold,
            "description": self._description
        }

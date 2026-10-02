"""
DEM3T3R V1 Plugin for Chilli disease detection.
"""
import os
from typing import List, Dict, Any
from backend.crops._base import CropModel

class ChilliCropModel(CropModel):
    def __init__(self):
        self._model = None
        self._crop = "chilli"
        self._model_file = "chilli.pt"
        self._diseases = ['chilli_leaf_curl', 'chilli_anthracnose', 'chilli_bacterial_spot', 'healthy']
        self._confidence_threshold = 0.50
        self._description = "Chilli pathogen & virus detector"

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
            print(f"[ChilliCropModel] Failed to load {model_path}: {e}")
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
            print(f"[ChilliCropModel] Predict error: {e}")
            return []

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "crop": self._crop,
            "model_file": self._model_file,
            "diseases": self._diseases,
            "confidence_threshold": self._confidence_threshold,
            "description": self._description
        }

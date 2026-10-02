"""
YOLO Detector - Real-time crop disease detection
Loads crop-specific models on demand
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ultralytics import YOLO
from config.settings import YOLO_MODELS_DIR, CROPS

class YOLODetector:
    def __init__(self):
        self.models = {}
        self.current_crop = None
        self.current_model = None
        
    def load_model(self, crop_name):
        """Load YOLO model for specific crop"""
        if crop_name not in CROPS:
            raise ValueError(f"Unknown crop: {crop_name}")
        
        if crop_name not in self.models:
            model_path = f"{YOLO_MODELS_DIR}/{crop_name.lower()}.pt"
            print(f"[YOLO] Loading model: {model_path}")
            self.models[crop_name] = YOLO(model_path)
        
        self.current_crop = crop_name
        self.current_model = self.models[crop_name]
        print(f"[YOLO] Active model: {crop_name}")
    
    def detect(self, frame):
        """Run detection on frame, return results"""
        if self.current_model is None:
            raise RuntimeError("No model loaded - call load_model() first")
        
        results = self.current_model(frame, verbose=False)
        return results
    
    def get_detections(self, frame, confidence_threshold=0.5):
        """Get filtered detections with bounding boxes"""
        results = self.detect(frame)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = float(box.conf[0])
                if conf >= confidence_threshold:
                    detections.append({
                        'bbox': box.xyxy[0].tolist(),
                        'confidence': conf,
                        'class': int(box.cls[0])
                    })
        
        return detections

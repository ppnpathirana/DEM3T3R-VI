"""
@file: _base.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Crop Model Base — Abstract base class for all crop disease detection plugins.

Every crop plugin must subclass CropModel and implement:
  - load(models_dir)  -> attempt to load the .pt model file
  - predict(frame)    -> run inference, return list of detection dicts
  - get_metadata()    -> return crop metadata dict
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class CropModel(ABC):
    """Abstract base class for all crop disease detection plugins."""

    @abstractmethod
    def load(self, models_dir: str) -> bool:
        """
        Load the YOLO model from models_dir.

        Args:
            models_dir: Directory containing .pt model files.

        Returns:
            True if model loaded successfully, False if file not found
            (graceful degradation -- do NOT raise).
        """

    @abstractmethod
    def predict(self, frame) -> List[Dict[str, Any]]:
        """
        Run inference on a single frame.

        Args:
            frame: numpy ndarray (H, W, 3) BGR image.

        Returns:
            List of detection dicts, each containing:
              {
                'class':      str,
                'confidence': float,
                'bbox':       [x1, y1, x2, y2],
                'mask':       None
              }
            Returns empty list (or mock entries for testing) if model not loaded.
        """

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Return plugin metadata.

        Returns:
            {
              'crop':                 str,
              'model_file':           str,
              'diseases':             List[str],
              'confidence_threshold': float,
              'description':          str
            }
        """

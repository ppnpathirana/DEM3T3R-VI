"""
@file: neural_driving.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
DEM3T3R V1 End-to-End Neural Behavioral Driving Network
Implements the NVIDIA DAVE-2 Deep Learning Autonomous Driving Architecture:
https://developer.nvidia.com/blog/deep-learning-self-driving-cars/

Maps raw camera images directly to steering angles and differential wheel PWM commands.
Includes an embedded SQLite dataset recorder for behavior cloning from manual driving runs.
"""

import cv2
import sqlite3
import time
import numpy as np
import torch
import torch.nn as nn
from typing import Tuple, Dict, Any, Optional


class DAVE2DrivingNet(nn.Module):
    """
    NVIDIA DAVE-2 End-to-End Convolutional Driving Network.
    5 Convolutional Layers + 3 Fully Connected Layers.
    """
    def __init__(self):
        super().__init__()
        # 3 strided 5x5 convolutions
        self.conv1 = nn.Conv2d(3, 24, kernel_size=5, stride=2)
        self.conv2 = nn.Conv2d(24, 36, kernel_size=5, stride=2)
        self.conv3 = nn.Conv2d(36, 48, kernel_size=5, stride=2)

        # 2 non-strided 3x3 convolutions
        self.conv4 = nn.Conv2d(48, 64, kernel_size=3, stride=1)
        self.conv5 = nn.Conv2d(64, 64, kernel_size=3, stride=1)

        self.dropout = nn.Dropout(0.2)

        # Compute adaptive pooling to ensure fixed FC layer size regardless of input dimension
        self.adaptive_pool = nn.AdaptiveAvgPool2d((4, 8))

        # Fully connected layers
        self.fc1 = nn.Linear(64 * 4 * 8, 100)
        self.fc2 = nn.Linear(100, 50)
        self.fc3 = nn.Linear(50, 10)
        self.out_steering = nn.Linear(10, 1) # Tanh -> [-1.0, +1.0]
        self.out_throttle = nn.Linear(10, 1) # Sigmoid -> [0.0, 1.0]

        self.elu = nn.ELU(inplace=True)
        self.tanh = nn.Tanh()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.elu(self.conv1(x))
        x = self.elu(self.conv2(x))
        x = self.elu(self.conv3(x))
        x = self.elu(self.conv4(x))
        x = self.elu(self.conv5(x))

        x = self.adaptive_pool(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)

        x = self.elu(self.fc1(x))
        x = self.elu(self.fc2(x))
        x = self.elu(self.fc3(x))

        steering = self.tanh(self.out_steering(x))
        throttle = self.sigmoid(self.out_throttle(x))
        return steering, throttle


class DrivingDatasetLogger:
    """Records camera frames and driver commands into an SQLite dataset for Behavior Cloning."""
    def __init__(self, db_path: str = "cropguard_driving_dataset.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS driving_samples (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp   REAL    NOT NULL,
                    image_jpeg  BLOB    NOT NULL,
                    motor_left  INTEGER NOT NULL,
                    motor_right INTEGER NOT NULL,
                    steering    REAL    NOT NULL,
                    throttle    REAL    NOT NULL
                )
            ''')
            conn.commit()

    def log_sample(self, frame: np.ndarray, motor_left: int, motor_right: int):
        if frame is None or frame.size == 0:
            return
        # Normalize commands
        max_speed = 255.0
        throttle = float(max(0, motor_left + motor_right)) / (2.0 * max_speed)
        steering = float(motor_left - motor_right) / max_speed
        steering = max(-1.0, min(1.0, steering))

        # Compress to JPEG
        ret, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        if not ret:
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO driving_samples (timestamp, image_jpeg, motor_left, motor_right, steering, throttle) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (time.time(), buf.tobytes(), int(motor_left), int(motor_right), float(steering), float(throttle))
            )
            conn.commit()

    def count_samples(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("SELECT COUNT(*) FROM driving_samples")
                return cur.fetchone()[0]
        except Exception:
            return 0


class EndToEndPilot:
    def __init__(self, device: Optional[str] = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = DAVE2DrivingNet().to(self.device)
        self.model.eval()

        if self.device == "cuda":
            self.model.half()

        self.logger = DrivingDatasetLogger()

    @torch.no_grad()
    def predict_steering(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Runs camera image through DAVE-2 network to predict steering and wheel PWMs.
        """
        if frame is None or frame.size == 0:
            return {
                "steering_angle": 0.0,
                "throttle": 0.0,
                "motor_left": 0,
                "motor_right": 0,
                "action": "STOP",
                "device": self.device
            }

        h, w = frame.shape[:2]
        # Focus on the lower 60% ground corridor
        crop_top = int(h * 0.40)
        roi = frame[crop_top:h, :]

        # Resize to DAVE-2 standard input size: 200 width x 66 height
        resized = cv2.resize(roi, (200, 66))
        # Convert BGR to YUV (standard NVIDIA autonomous driving color space)
        yuv = cv2.cvtColor(resized, cv2.COLOR_BGR2YUV).astype(np.float32) / 255.0

        tensor = torch.from_numpy(yuv).permute(2, 0, 1).unsqueeze(0).to(self.device)
        if self.device == "cuda":
            tensor = tensor.half()

        steering_tensor, throttle_tensor = self.model(tensor)
        steering = float(steering_tensor.cpu().float().item())
        throttle = float(throttle_tensor.cpu().float().item())

        # Base PWM: 180 (cruising) scaled by throttle
        base_pwm = int(throttle * 220)
        # Steering offset: turn delta
        steer_delta = int(steering * 110)

        left_pwm = int(np.clip(base_pwm + steer_delta, -255, 255))
        right_pwm = int(np.clip(base_pwm - steer_delta, -255, 255))

        action = "FORWARD"
        if steering < -0.2:
            action = "STEER_LEFT"
        elif steering > 0.2:
            action = "STEER_RIGHT"

        return {
            "steering_angle": round(steering, 3),
            "throttle": round(throttle, 3),
            "motor_left": left_pwm,
            "motor_right": right_pwm,
            "action": action,
            "device": self.device,
            "dataset_samples_logged": self.logger.count_samples()
        }

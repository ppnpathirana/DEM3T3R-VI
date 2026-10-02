"""
@file: camera_stream.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
Camera Stream - Captures video from IP camera for YOLO detection
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import threading
import time

class CameraStream:
    def __init__(self, camera_url):
        """
        camera_url: IP camera URL
        Examples:
        - "http://192.168.8.100:8080/video" (IP Webcam app)
        - "rtsp://192.168.8.100:554/stream" (RTSP stream)
        """
        self.camera_url = camera_url
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        
    def start(self):
        """Start camera stream in background thread"""
        print(f"[CAMERA] Connecting to {self.camera_url}...")
        self.cap = cv2.VideoCapture(self.camera_url)
        
        if not self.cap.isOpened():
            print("[CAMERA] ✗ Failed to connect to camera")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        print("[CAMERA] ✓ Camera stream started")
        return True
    
    def _capture_loop(self):
        """Continuously capture frames from camera"""
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                print("[CAMERA] ⚠ Frame capture failed")
                time.sleep(0.1)
    
    def get_frame(self):
        """Get latest frame (thread-safe)"""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
    
    def stop(self):
        """Stop camera stream"""
        self.running = False
        if self.cap:
            self.cap.release()
        print("[CAMERA] Camera stream stopped")


if __name__ == "__main__":
    # Test camera connection
    from config.settings import CAMERA_URL
    
    cam = CameraStream(CAMERA_URL)
    if cam.start():
        print("[TEST] Camera connected successfully!")
        print("[TEST] Capturing frames for 10 seconds...")
        
        for i in range(100):
            frame = cam.get_frame()
            if frame is not None:
                print(f"[TEST] Frame {i}: {frame.shape}")
            time.sleep(0.1)
        
        cam.stop()
        print("[TEST] Test complete!")
    else:
        print("[TEST] ✗ Camera connection failed")

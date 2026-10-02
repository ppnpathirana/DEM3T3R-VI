"""
@file: mock_camera.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
Mock Camera - Generates fake video frames for YOLO testing
"""
import cv2
import numpy as np

class MockCamera:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        
    def get_frame(self):
        """Generate a fake frame with random noise"""
        frame = np.random.randint(0, 255, (self.height, self.width, 3), dtype=np.uint8)
        return frame
    
    def get_leaf_frame(self):
        """Generate a frame with a green leaf-like shape"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Green background
        frame[:, :] = [50, 150, 50]
        # Add some random spots (simulating disease)
        for _ in range(10):
            x = np.random.randint(100, self.width - 100)
            y = np.random.randint(100, self.height - 100)
            cv2.circle(frame, (x, y), np.random.randint(5, 20), (0, 0, 200), -1)
        return frame

if __name__ == "__main__":
    cam = MockCamera()
    frame = cam.get_leaf_frame()
    cv2.imshow("Mock Camera", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

"""
@file: desktop_app.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 Native Desktop Application Launcher.
Launches DEM3T3R V1 directly in a dedicated desktop application window without browser UI.
"""
import sys
import os
import webview

def main():
    url = "http://localhost:5173"
    window = webview.create_window(
        title="🌾 DEM3T3R V1 — Autonomous Pathogen Detection & Treatment Platform",
        url=url,
        width=1440,
        height=900,
        resizable=True,
        min_size=(1024, 700),
        background_color="#1a1222"
    )
    webview.start(private_mode=False)

if __name__ == "__main__":
    main()

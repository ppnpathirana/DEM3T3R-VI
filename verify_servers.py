"""
@file: verify_servers.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import urllib.request

for port in [5173, 5001]:
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}', timeout=2) as resp:
            data = resp.read(1500).decode('utf-8', errors='ignore')
            has_title = "DEM3T3R V1" in data
            print(f"Port {port}: HTTP {resp.status} - DEM3T3R V1 title found: {has_title}")
    except Exception as e:
        print(f"Port {port} error: {e}")

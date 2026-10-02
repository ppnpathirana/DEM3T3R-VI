"""
@file: inspect_code_html.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import re

with open(r'C:\Users\Pasindu\Pictures\stitch_cropguard_tactical_field_commander_os\code.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Search for live-stream-img
m = re.search(r'<img[^>]*id="live-stream-img"[^>]*>', text)
if m:
    print("Found live-stream-img:", m.group(0))

# 2. Check head for Socket.IO
print("Socket.io in head:", "socket.io" in text)

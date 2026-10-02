"""
@file: extract_scripts.py
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

scripts = re.findall(r'<script(?:\s+type="([^"]*)")?[^>]*>(.*?)</script>', text, re.DOTALL)
for i, (stype, body) in enumerate(scripts):
    print(f"--- Script {i} (type={stype}) ---")
    if 'tailwind' not in body and len(body.strip()) > 0:
        print(body[:2000])
        with open(f'stitch_script_{i}.js', 'w', encoding='utf-8') as sf:
            sf.write(body)

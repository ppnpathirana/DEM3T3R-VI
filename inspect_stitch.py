"""
@file: inspect_stitch.py
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

scripts = re.findall(r'<script.*?</script>', text, re.DOTALL)
print('Number of scripts:', len(scripts))

ids = re.findall(r'id="([^"]+)"', text)
print('IDs found:', ids)

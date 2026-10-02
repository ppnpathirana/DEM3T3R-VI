"""
@file: verify_dom_ids.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import re

with open('dist/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

dom_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
js_ids = set(re.findall(r'document\.getElementById\(["\']([^"\']+)["\']\)', html))

missing = js_ids - dom_ids
print(f"Total DOM IDs: {len(dom_ids)}")
print(f"Total JS getElementById IDs: {len(js_ids)}")
print(f"Missing IDs accessed by JS: {missing}")

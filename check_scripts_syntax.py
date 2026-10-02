"""
@file: check_scripts_syntax.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import re
import subprocess

with open('dist/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    s_clean = s.strip()
    if not s_clean:
        continue
    with open(f'test_script_{i}.js', 'w', encoding='utf-8') as f_out:
        f_out.write(s_clean)
    res = subprocess.run(['node', '--check', f'test_script_{i}.js'], capture_output=True, text=True)
    print(f"Script {i} syntax check: returncode={res.returncode}")
    if res.returncode != 0:
        print("STDERR:", res.stderr)

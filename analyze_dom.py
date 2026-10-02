"""
@file: analyze_dom.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import re

with open('pure_dom.html', 'r', encoding='utf-8') as f:
    html = f.read()

print(f"Total HTML chars: {len(html)}")

# Find header
header_match = re.search(r'(<header.*?</header>)', html, re.DOTALL)
if header_match:
    print("Header found, length:", len(header_match.group(1)))

# Find 3 columns:
# In code.html, let's see how the main layout is structured
main_match = re.search(r'(<main.*?</main>)', html, re.DOTALL)
if main_match:
    print("Main found, length:", len(main_match.group(1)))
else:
    print("No <main> tag, searching for top container divs")

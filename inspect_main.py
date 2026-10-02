"""
@file: inspect_main.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import re
from bs4 import BeautifulSoup

with open('pure_dom.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

main = soup.find('main')
if main:
    print(f"Main class: {main.get('class')}")
    cols = main.find_all('section', recursive=False)
    if not cols:
        cols = main.find_all('div', recursive=False)
    print(f"Number of direct children in main: {len(cols)}")
    for i, c in enumerate(cols):
        print(f"Child {i}: tag={c.name}, class={c.get('class')}")

footer = soup.find('footer')
if footer:
    print(f"Footer found, class={footer.get('class')}")

estop = soup.find(id='full-estop-overlay')
if estop:
    print("E-stop overlay found")

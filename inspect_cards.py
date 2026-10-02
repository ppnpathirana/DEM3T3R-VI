"""
@file: inspect_cards.py
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
sections = main.find_all('section', recursive=False)

for i, sec in enumerate(sections):
    print(f"\n=================== SECTION {i} ===================")
    cards = sec.find_all('div', recursive=False)
    for j, card in enumerate(cards):
        header_text = ""
        h_tag = card.find(['h2', 'h3', 'h4', 'span', 'p'])
        if h_tag:
            header_text = h_tag.get_text(strip=True)
        print(f"  Card {j}: class={card.get('class')[:3]}... title='{header_text[:40]}'")

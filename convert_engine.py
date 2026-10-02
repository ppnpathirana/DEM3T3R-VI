"""
@file: convert_engine.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import re
import os

with open("extracted_body.html", "r", encoding="utf-8") as f:
    raw = f.read()

def convert_comments(text):
    return re.sub(r"<!--(.*?)-->", r"{/* \\1 */}", text, flags=re.DOTALL)

jsx = convert_comments(raw)

replacements = [
    ("class=", "className="),
    ("for=", "htmlFor="),
    ("viewbox=", "viewBox="),
    ("stroke-width=", "strokeWidth="),
    ("stroke-linecap=", "strokeLinecap="),
    ("stroke-linejoin=", "strokeLinejoin="),
    ("stroke-dasharray=", "strokeDasharray="),
    ("stroke-dashoffset=", "strokeDashoffset="),
    ("preserveaspectratio=", "preserveAspectRatio="),
    ("<lineargradient", "<linearGradient"),
    ("</lineargradient>", "</linearGradient>"),
    ("stop-color=", "stopColor="),
    ("stop-opacity=", "stopOpacity="),
    ("clip-path=", "clipPath="),
    ("clip-rule=", "clipRule="),
    ("fill-rule=", "fillRule="),
    ("crossorigin=", "crossOrigin="),
    ("selected=\"\"", ""),
]

for old, new in replacements:
    jsx = jsx.replace(old, new)

jsx = re.sub(r"<input([^>]*?[^/])>", r"<input\\1 />", jsx)
jsx = re.sub(r"<img([^>]*?[^/])>", r"<img\\1 />", jsx)

with open("raw_jsx_body.txt", "w", encoding="utf-8") as out:
    out.write(jsx)
print("Wrote raw_jsx_body.txt length:", len(jsx))
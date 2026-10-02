import os

AUTHOR_NAME = "Pasindu Pathirana"
PROJECT_NAME = "DEM3T3R V1"
GITHUB_LINK = "https://github.com/ppnpathirana/DEM3T3R-VI"

TS_COMMENT = """/**
 * @file {filename}
 * @description Core component for DEM3T3R V1 architecture.
 * 
 * @project DEM3T3R V1
 * @author Pasindu Pathirana
 * @contact https://github.com/ppnpathirana/DEM3T3R-VI
 * @version 1.0.0
 * @date 2026
 * 
 * All rights reserved.
 */
"""

PY_COMMENT = """\"\"\"
@file: {filename}
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
\"\"\"
"""

INO_COMMENT = """/**
 * @file {filename}
 * @description Master firmware for the DEM3T3R V1 hardware controller.
 * 
 * @project DEM3T3R V1
 * @author Pasindu Pathirana
 * @contact https://github.com/ppnpathirana/DEM3T3R-VI
 * @version 1.0.0
 * @date 2026
 */
"""

def prepend_comment(filepath, file_ext):
    filename = os.path.basename(filepath)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return

    if "@author" in content:
        return

    if file_ext in ['.ts', '.tsx']:
        comment = TS_COMMENT.replace("{filename}", filename)
    elif file_ext == '.py':
        comment = PY_COMMENT.replace("{filename}", filename)
    elif file_ext in ['.ino', '.cpp', '.h']:
        comment = INO_COMMENT.replace("{filename}", filename)
    else:
        return
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(comment + "\n" + content)
    print(f"Added comment to: {filename}")

for root, _, files in os.walk("."):
    if any(ignore in root for ignore in ["node_modules", "venv", ".git", "dist", "__pycache__"]):
        continue
        
    for file in files:
        ext = os.path.splitext(file)[1]
        if ext in ['.py', '.ts', '.tsx', '.ino', '.cpp', '.h']:
            prepend_comment(os.path.join(root, file), ext)

print("\nSuccessfully added Author comments to all files!")

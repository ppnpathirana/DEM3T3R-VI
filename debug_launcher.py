"""
@file: debug_launcher.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

import subprocess
import time
import os

pythonw = r"C:\Users\Pasindu\AppData\Local\Programs\Python\Python311\pythonw.exe"
app_file = r"C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard\CropGuard_App.pyw"

# Run with python.exe so we see errors
python_exe = r"C:\Users\Pasindu\AppData\Local\Programs\Python\Python311\python.exe"
proc = subprocess.run([python_exe, app_file], capture_output=True, text=True, timeout=10)

print("Returncode:", proc.returncode)
print("STDOUT:", proc.stdout)
print("STDERR:", proc.stderr)

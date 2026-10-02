@echo off
title Stop CropGuard
taskkill /f /im python.exe > nul 2>&1
taskkill /f /im pythonw.exe > nul 2>&1
taskkill /f /im node.exe > nul 2>&1
echo ❌ CropGuard Swarm System stopped successfully!
timeout /t 2 > nul

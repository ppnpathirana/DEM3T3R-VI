$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut('C:\Users\Pasindu\Desktop\CropGuard AI.lnk')
$shortcut.TargetPath = 'C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard\CropGuard_Launcher.bat'
$shortcut.WorkingDirectory = 'C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard'
$shortcut.IconLocation = 'C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard\public\favicon.ico'
$shortcut.Save()
Write-Host "✅ Shortcut 'CropGuard AI' updated successfully to launch CropGuard_Launcher.bat!"

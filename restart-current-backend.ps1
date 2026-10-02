$listener = Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction Stop
$backendProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
if ($backendProcess.CommandLine -notmatch 'ws_server.py') { throw 'Port 5001 is not the expected CropGuard backend.' }
$runtimePath = $backendProcess.ExecutablePath
$runtimePath | Set-Content 'C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard\logs\backend-runtime.txt'
Stop-Process -Id $listener.OwningProcess -ErrorAction Stop
Start-Process -FilePath $runtimePath -ArgumentList '-u','backend/ws_server.py' -WorkingDirectory 'C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard' -WindowStyle Hidden -RedirectStandardOutput 'C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard\logs\backend-current.log' -RedirectStandardError 'C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard\logs\backend-current-error.log'

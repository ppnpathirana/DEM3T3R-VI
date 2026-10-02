import subprocess
import sys
import time
import requests
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
python_exe = sys.executable

print("[TEST RUNNER] Starting DEM3T3R V1 Backend...")
backend = subprocess.Popen(
    [python_exe, "backend/ws_server.py"],
    cwd=PROJECT_DIR,
    stdout=open("backend_launch.log", "a", encoding="utf-8"),
    stderr=subprocess.STDOUT
)

try:
    print("[TEST RUNNER] Waiting for HTTP 200 on http://127.0.0.1:5001/ ...")
    connected = False
    for i in range(50):
        try:
            r = requests.get("http://127.0.0.1:5001/", timeout=1)
            if r.status_code == 200:
                print(f"[TEST RUNNER] [OK] Backend is live after {i * 0.4:.1f}s!")
                connected = True
                break
        except Exception:
            pass
        time.sleep(0.4)

    if not connected:
        print("[TEST RUNNER] [ERROR] Backend failed to start within timeout.")
        sys.exit(1)

    import test_e2e_workable
    test_e2e_workable.run_test()

finally:
    backend.terminate()
    print("[TEST RUNNER] Test finished and backend cleaned up.")

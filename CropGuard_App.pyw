"""
🌾 DEM3T3R V1 — Ultra-Reliable Standalone Native Desktop Software Launcher.
Ensures the Python AI backend (ws_server.py) is fully booted and returning HTTP 200
before opening the native DirectX/WebView2 hardware-accelerated desktop application window.
"""
import sys
import os
import time
import subprocess
import urllib.request
import json
import html
import traceback

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)
WINDOW_TITLE = 'DEM3T3R V1'
LAUNCHER_LOG = os.path.join(PROJECT_DIR, 'logs', 'desktop_launcher.log')
os.makedirs(os.path.dirname(LAUNCHER_LOG), exist_ok=True)

# Guard against NoneType stdout/stderr when running via pythonw.exe
if sys.stdout is None:
    sys.stdout = open(LAUNCHER_LOG, 'a', encoding='utf-8', buffering=1)
if sys.stderr is None:
    sys.stderr = sys.stdout

BACKEND_URL = "http://127.0.0.1:5001/"
LOG_FILE = os.path.join(PROJECT_DIR, "backend_launch.log")

def check_http_live(url=BACKEND_URL + 'api/health', timeout=1.0):
    """Verify this is the DEM3T3R V1 service, not another application on port 5001."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CropGuard-Desktop/1.0"})
        # A system proxy must never intercept the local desktop backend check.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=timeout) as resp:
            return resp.status == 200 and json.load(resp).get('service') == 'cropguard'
    except Exception:
        return False

backend_proc = None

def ensure_servers():
    """Ensure ws_server.py (port 5001) is running and returning HTTP 200."""
    global backend_proc
    python_exe = sys.executable
    if "pythonw.exe" in python_exe.lower():
        python_exe = python_exe.lower().replace("pythonw.exe", "python.exe")

    # 1. Start Python backend if not active
    if not check_http_live():
        print("[LAUNCHER] Starting DEM3T3R V1 Backend (port 5001)...")
        log_handle = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
        log_handle.write(f"\n--- Launching backend at {time.ctime()} ---\n")
        backend_proc = subprocess.Popen(
            [python_exe, "-u", "backend/ws_server.py"],
            cwd=PROJECT_DIR,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        log_handle.close()

    # Wait with a real deadline, including HTTP request time.
    print("[LAUNCHER] Waiting for DEM3T3R V1 SCADA engine to become ready...")
    started = time.monotonic()
    while time.monotonic() - started < 120:
        if check_http_live():
            print(f"[LAUNCHER] [OK] Backend verified ready after {time.monotonic() - started:.1f}s.")
            return BACKEND_URL
        if backend_proc and backend_proc.poll() is not None:
            break
        time.sleep(0.5)

    # If backend didn't respond in time, show informative diagnostic window
    err_log_tail = ""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                err_log_tail = "".join(lines[-25:])
        except Exception:
            pass

    err_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <title>DEM3T3R V1 — Startup Diagnostic</title>
        <style>
            body {{ background: #08090C; color: #E4E1EB; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
            .card {{ background: #14151D; border: 1px solid rgba(255,51,75,0.4); border-radius: 16px; padding: 32px; max-width: 650px; width: 100%; box-shadow: 0 10px 40px rgba(0,0,0,0.8); text-align: center; }}
            h2 {{ color: #FF334B; margin-top: 0; font-size: 20px; }}
            p {{ color: #8C92A4; font-size: 13px; line-height: 1.6; }}
            pre {{ background: #090A0E; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 11px; text-align: left; overflow-x: auto; color: #00E5FF; max-height: 200px; }}
            button {{ background: #00E676; color: #000; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 16px; }}
            button:hover {{ background: #00c864; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>⚠️ DEM3T3R V1 Backend Initialization Timeout</h2>
            <p>The backend exited or did not become ready within 120 seconds. Below is the recent output from <code>backend_launch.log</code>:</p>
            <pre>{html.escape(err_log_tail) or "No recent logs captured."}</pre>
            <button onclick="location.href='http://127.0.0.1:5001/'">Retry Connecting</button>
        </div>
    </body>
    </html>
    """
    err_path = os.path.join(PROJECT_DIR, "startup_error.html")
    with open(err_path, "w", encoding="utf-8") as f:
        f.write(err_html)
    return f"file:///{os.path.abspath(err_path)}"

def window_geometry(screen_width, screen_height):
    """Fit the desktop window and its minimum size to the available screen."""
    width = min(1440, max(320, int(screen_width) - 48))
    height = min(900, max(240, int(screen_height) - 80))
    return width, height, (min(900, width), min(560, height))


def restore_existing_window():
    if os.name != 'nt':
        return False
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    user32.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
    user32.FindWindowW.restype = wintypes.HWND
    user32.ShowWindowAsync.argtypes = (wintypes.HWND, ctypes.c_int)
    user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
    handle = user32.FindWindowW(None, WINDOW_TITLE)
    if not handle:
        return False
    user32.ShowWindowAsync(handle, 9)  # Restore a minimized instance.
    user32.SetForegroundWindow(handle)
    print('[LAUNCHER] Restored the existing DEM3T3R V1 window.')
    return True


def main():
    if restore_existing_window():
        return
    import webview
    screens = webview.screens
    screen = next((item for item in screens if item.x == 0 and item.y == 0), screens[0]) if screens else None
    width, height, minimum = window_geometry(screen.width if screen else 1280, screen.height if screen else 800)
    splash = '''<!doctype html><html><body style="margin:0;background:#08090c;color:#e4e1eb;font:18px system-ui;display:grid;place-items:center;height:100vh">
    <div style="max-width:560px;padding:32px"><h1>DEM3T3R V1</h1>
    <p>Opening your dashboard…</p><p style="color:#99aaa4">Starting the robot services. The first launch can take up to two minutes.</p></div></body></html>'''
    window = webview.create_window(WINDOW_TITLE, html=splash, width=width, height=height,
                                  min_size=minimum, resizable=True, background_color='#08090C',
                                  x=(screen.x + 24) if screen else None,
                                  y=(screen.y + 24) if screen else None)

    def load_dashboard():
        try:
            window.events.shown.wait(15)
            window.show()
            target_url = ensure_servers()
            if target_url.startswith('http'):
                target_url += f'?_nocache={int(time.time())}'
            window.load_url(target_url)
            print(f'[LAUNCHER] Dashboard opened: {target_url}')
        except Exception:
            traceback.print_exc()
            window.load_html('<h1>DEM3T3R V1 could not start</h1><p>See logs/desktop_launcher.log for the error.</p>')

    webview.start(load_dashboard, private_mode=True)
    # Keep the shared backend available to other dashboards and the next launch.
    # Its disconnect handler stops outputs when the last dashboard leaves.
    print('[LAUNCHER] Desktop window closed.')

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stderr.flush()
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,
                f'DEM3T3R V1 could not open. Details were saved to:\n{LAUNCHER_LOG}',
                WINDOW_TITLE, 0x10)

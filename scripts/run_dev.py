from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_HEALTH = "http://127.0.0.1:8000/api/health"
WEB_URL = "http://127.0.0.1:5173"


def _wait_for_api(process: subprocess.Popen, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(API_HEALTH, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.4)
    return False


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        process.terminate()
    else:
        process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> int:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT))
    env.setdefault("PYTHONUNBUFFERED", "1")

    backend = [
        sys.executable,
        "-m",
        "uvicorn",
        "apps.api.app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]
    npm = "npm.cmd" if os.name == "nt" else "npm"
    web_dir = ROOT / "apps/web"

    if not (web_dir / "node_modules").exists():
        print("[SANKET AI] Frontend dependencies are missing.")
        print("Run setup_windows.bat (Windows) or setup_unix.sh (macOS/Linux).")
        return 2

    print("[SANKET AI] Starting local recognition API...")
    api = subprocess.Popen(backend, cwd=ROOT, env=env)

    if not _wait_for_api(api):
        print("\n[SANKET AI] Backend did not become healthy.")
        print("The browser was NOT opened because recognition would not work.")
        print("Review the backend error printed above, then rerun setup_windows.bat.")
        _stop(api)
        return api.returncode or 3

    print("[SANKET AI] API healthy: http://127.0.0.1:8000")
    print("[SANKET AI] Starting web interface...")
    web = subprocess.Popen([npm, "run", "dev"], cwd=web_dir, env=env)
    children = [api, web]

    try:
        time.sleep(1.3)
        if web.poll() is not None:
            print("[SANKET AI] Frontend failed to start.")
            return web.returncode or 4
        print(f"\n[SANKET AI] Ready: {WEB_URL}")
        print("Press Ctrl+C once to stop both services.")
        webbrowser.open(WEB_URL)
        while all(p.poll() is None for p in children):
            time.sleep(0.5)
        return next((p.returncode or 1 for p in children if p.poll() is not None), 1)
    except KeyboardInterrupt:
        return 0
    finally:
        for process in children:
            _stop(process)


if __name__ == "__main__":
    raise SystemExit(main())

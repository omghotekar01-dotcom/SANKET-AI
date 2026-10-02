from __future__ import annotations
import os, signal, subprocess, sys, time, webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    env=os.environ.copy(); env.setdefault('PYTHONPATH',str(ROOT))
    backend=[sys.executable,'-m','uvicorn','apps.api.app.main:app','--host','127.0.0.1','--port','8000','--reload']
    npm='npm.cmd' if os.name=='nt' else 'npm'
    web_dir=ROOT/'apps/web'
    if not (web_dir/'node_modules').exists():
        print('Frontend dependencies missing. Run: cd apps/web && npm install')
        return 2
    print('Starting SANKET AI API on http://127.0.0.1:8000')
    api=subprocess.Popen(backend,cwd=ROOT,env=env)
    print('Starting SANKET AI web on http://127.0.0.1:5173')
    web=subprocess.Popen([npm,'run','dev'],cwd=web_dir,env=env)
    children=[api,web]
    try:
        time.sleep(1.5)
        print('\nSANKET AI is starting. Press Ctrl+C to stop both processes.')
        webbrowser.open('http://127.0.0.1:5173')
        while all(p.poll() is None for p in children): time.sleep(.5)
        return next((p.returncode or 1 for p in children if p.poll() is not None),1)
    except KeyboardInterrupt:
        return 0
    finally:
        for p in children:
            if p.poll() is None:
                if os.name=='nt': p.terminate()
                else: p.send_signal(signal.SIGTERM)
        for p in children:
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill()

if __name__=='__main__': raise SystemExit(main())

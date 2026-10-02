from __future__ import annotations
import importlib.util, platform, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    print('SANKET AI environment check')
    print('Python:',sys.version.split()[0], platform.platform())
    ok=True
    if sys.version_info[:2] not in {(3,11),(3,12)}:
        print('WARN: Python 3.11 or 3.12 is recommended for current MediaPipe wheel compatibility.')
    for module in ['fastapi','uvicorn','numpy','cv2']:
        found=importlib.util.find_spec(module) is not None
        print(f'{module:12}', 'OK' if found else 'MISSING')
        ok &= found
    mp=importlib.util.find_spec('mediapipe') is not None
    print(f'{"mediapipe":12}', 'OK' if mp else 'MISSING — live landmarks unavailable until installed')
    for exe in ['node','npm']:
        found=shutil.which(exe) is not None
        print(f'{exe:12}', found and shutil.which(exe) or 'MISSING')
        ok &= found
    print('Model artifact:', 'FOUND' if (ROOT/'ml/artifacts/demo-v1/manifest.json').exists() else 'NOT YET TRAINED')
    print('Raw video storage default: OFF')
    return 0 if ok else 1

if __name__=='__main__': raise SystemExit(main())

from __future__ import annotations
import argparse, json
from pathlib import Path


def main():
    p=argparse.ArgumentParser(); p.add_argument('--artifact',default='ml/artifacts/demo-v1'); args=p.parse_args()
    path=Path(args.artifact)/'evaluation.json'
    if not path.exists(): raise SystemExit(f'No evaluation report at {path}')
    r=json.loads(path.read_text())
    t=r['test']; m=r['manifest']
    print(f"Model: {m['model_version']} | vocabulary={len(m['labels'])} | split={m['split']['mode']}")
    print(f"Test samples: {t['samples']} | top-1={t['top1_accuracy']:.3f} | macro-F1={t['macro_f1']:.3f}")
    print(f"Selective coverage={t['coverage']:.3f} | accepted accuracy={t['accepted_accuracy']:.3f} | threshold={t['threshold']:.2f}")
    if m['split'].get('limitation'): print('LIMITATION:',m['split']['limitation'])

if __name__=='__main__': main()

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.training.dataset import Sample, load_samples, split_samples, vectorize


def softmax_logits(distances: np.ndarray, temperature: float) -> np.ndarray:
    logits = -distances / max(temperature, 1e-5)
    logits -= np.max(logits)
    exp = np.exp(logits)
    return exp / np.sum(exp)


def fit_templates(train: list[Sample], labels: list[str], sequence_length: int) -> tuple[np.ndarray, np.ndarray]:
    vectors = {label: [] for label in labels}
    all_frames = []
    for sample in train:
        v = vectorize(sample, sequence_length)
        vectors[sample.label].append(v)
        all_frames.append(v)
    missing = [label for label, rows in vectors.items() if not rows]
    if missing:
        raise ValueError(f"Training split has no samples for classes: {missing}. Collect more signers/samples or change split.")
    templates = np.stack([np.mean(np.stack(vectors[label]), axis=0) for label in labels]).astype(np.float32)
    flat = np.concatenate(all_frames, axis=0)
    variance = np.var(flat, axis=0).astype(np.float32)
    weights = 1.0 / np.maximum(variance, 1e-3)
    weights = np.clip(weights / np.mean(weights), 0.25, 4.0).astype(np.float32)
    return templates, weights


def distances(seq: np.ndarray, templates: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return np.mean(((templates - seq[None,:,:]) ** 2) * weights[None,None,:], axis=(1,2))


def nll(samples: list[Sample], labels: list[str], templates, weights, sequence_length: int, temp: float) -> float:
    if not samples:
        return math.inf
    index = {label:i for i,label in enumerate(labels)}
    losses=[]
    for sample in samples:
        p=softmax_logits(distances(vectorize(sample, sequence_length),templates,weights),temp)
        losses.append(-math.log(max(float(p[index[sample.label]]),1e-8)))
    return float(np.mean(losses))


def evaluate(samples: list[Sample], labels: list[str], templates, weights, sequence_length: int, temp: float, threshold: float=0.0) -> dict:
    index={label:i for i,label in enumerate(labels)}
    cm=np.zeros((len(labels),len(labels)),dtype=int)
    confidences=[]; correct=[]; rejected=0
    for sample in samples:
        p=softmax_logits(distances(vectorize(sample,sequence_length),templates,weights),temp)
        pred=int(np.argmax(p)); conf=float(p[pred]); true=index[sample.label]
        confidences.append(conf); correct.append(pred==true)
        if conf < threshold: rejected += 1
        else: cm[true,pred]+=1
    per_class=[]
    f1s=[]
    for i,label in enumerate(labels):
        tp=int(cm[i,i]); fp=int(cm[:,i].sum()-tp); fn=int(cm[i,:].sum()-tp)
        precision=tp/(tp+fp) if tp+fp else 0.0; recall=tp/(tp+fn) if tp+fn else 0.0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        f1s.append(f1); per_class.append({"label":label,"precision":precision,"recall":recall,"f1":f1,"support":int(sum(1 for s in samples if s.label==label))})
    accepted=len(samples)-rejected
    accepted_correct=sum(1 for c,conf in zip(correct,confidences) if conf>=threshold and c)
    return {
        "samples":len(samples),"top1_accuracy":float(np.mean(correct)) if correct else 0.0,
        "macro_f1":float(np.mean(f1s)) if f1s else 0.0,"threshold":threshold,
        "coverage":accepted/len(samples) if samples else 0.0,
        "accepted_accuracy":accepted_correct/accepted if accepted else 0.0,
        "confusion_matrix":cm.tolist(),"per_class":per_class,
    }


def choose_threshold(val: list[Sample], labels, templates, weights, sequence_length, temp) -> tuple[float, dict]:
    best=(0.72, -1.0, None)
    for threshold in np.linspace(0.45,0.95,21):
        metrics=evaluate(val,labels,templates,weights,sequence_length,temp,float(threshold))
        score=metrics["accepted_accuracy"] * math.sqrt(max(metrics["coverage"],1e-6))
        if metrics["accepted_accuracy"] >= 0.80 and score > best[1]:
            best=(float(threshold),score,metrics)
    if best[2] is None:
        fallback=evaluate(val,labels,templates,weights,sequence_length,temp,0.72)
        return 0.72,fallback
    return best[0],best[2]


def main() -> int:
    parser=argparse.ArgumentParser(description="Train SANKET AI temporal template baseline from consented landmark samples.")
    parser.add_argument('--data',default='data/local/collected')
    parser.add_argument('--out',default='ml/artifacts/demo-v1')
    parser.add_argument('--config',default='ml/configs/template_baseline.json')
    parser.add_argument('--seed',type=int,default=42)
    args=parser.parse_args()
    config=json.loads((REPO_ROOT/args.config).read_text(encoding='utf-8'))
    samples=load_samples(REPO_ROOT/args.data)
    if len(samples) < 6:
        raise SystemExit("Need at least 6 consented landmark samples. Collect multiple takes/signers first.")
    counts=Counter(s.label for s in samples)
    too_small={k:v for k,v in counts.items() if v < int(config['minimum_samples_per_class'])}
    if too_small:
        raise SystemExit(f"Need at least {config['minimum_samples_per_class']} samples per class; insufficient: {too_small}")
    labels=sorted(counts)
    train,val,test,split_info=split_samples(samples,args.seed)
    sequence_length=int(config['sequence_length'])
    templates,weights=fit_templates(train,labels,sequence_length)
    grid=config['temperature_grid']; temp=min(grid,key=lambda t:nll(val,labels,templates,weights,sequence_length,float(t))) if val else 0.2
    threshold,val_selective=choose_threshold(val,labels,templates,weights,sequence_length,float(temp))
    test_metrics=evaluate(test,labels,templates,weights,sequence_length,float(temp),threshold)
    train_metrics=evaluate(train,labels,templates,weights,sequence_length,float(temp),0.0)

    out=REPO_ROOT/args.out; out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'model.npz',templates=templates,feature_weights=weights)
    manifest={
        "model_version":config['model_version'],"backend":"temporal_template","feature_schema":config['feature_schema'],
        "sequence_length":sequence_length,"labels":labels,"temperature":float(temp),
        "accept_threshold":threshold,"margin_threshold":0.12,"motion_threshold":0.0015,"tracking_threshold":0.48,
        "trained_at":datetime.now(timezone.utc).isoformat(),"dataset_samples":len(samples),"split":split_info,
    }
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    report={"manifest":manifest,"class_counts":counts,"train":train_metrics,"validation_selective":val_selective,"test":test_metrics,
            "claims_note":"Metrics apply only to this collected vocabulary, signer split and test conditions. Do not generalize them to unrestricted ISL."}
    (out/'evaluation.json').write_text(json.dumps(report,indent=2,default=lambda x:dict(x)),encoding='utf-8')
    (out/'MODEL_CARD.md').write_text(
        f"# SANKET AI model card — {manifest['model_version']}\n\n"
        f"Backend: temporal template baseline  \nVocabulary: {', '.join(labels)}  \nSamples: {len(samples)}  \n"
        f"Split mode: {split_info['mode']}  \nTest top-1: {test_metrics['top1_accuracy']:.3f}  \n"
        f"Test macro F1: {test_metrics['macro_f1']:.3f}  \nSelective accepted accuracy: {test_metrics['accepted_accuracy']:.3f} at coverage {test_metrics['coverage']:.3f}.\n\n"
        "## Limitations\nThis is a finite-vocabulary landmark model. It is not open-vocabulary continuous ISL translation. Metrics are valid only for the recorded data and split documented in evaluation.json.\n",
        encoding='utf-8')
    print(json.dumps({"artifact":str(out),"labels":labels,"threshold":threshold,"test":test_metrics,"split":split_info},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())

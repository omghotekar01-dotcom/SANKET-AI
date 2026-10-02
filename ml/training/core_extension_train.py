from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import random
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
import keras

from apps.api.app.services.feature_schema import resample_sequence

TARGETS = ("help", "no", "water", "where", "yes")
SEQUENCE_LENGTH = 48
FEATURE_DIM = 226
SEED = 42


def load_samples(data_dir: Path):
    rows = []
    for meta_path in sorted(data_dir.glob("*.json")):
        if meta_path.name == "dataset_manifest.json":
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        label = meta["label"]
        if label not in TARGETS:
            continue
        payload = np.load(data_dir / meta["feature_path"])
        seq = resample_sequence(payload["sequence"].astype(np.float32), SEQUENCE_LENGTH)
        rows.append((meta["sample_id"], label, meta.get("signer_id", "unknown"), seq))
    return rows


def stratified_split(rows):
    rng = random.Random(SEED)
    by_label = {label: [] for label in TARGETS}
    for row in rows:
        by_label[row[1]].append(row)
    train, val, test = [], [], []
    split_counts = {}
    for label in TARGETS:
        items = sorted(by_label[label], key=lambda r: r[0])
        rng.shuffle(items)
        if len(items) < 10:
            raise RuntimeError(f"{label} has only {len(items)} usable samples")
        n_test = max(2, round(len(items) * 0.18))
        n_val = max(2, round(len(items) * 0.18))
        test.extend(items[:n_test])
        val.extend(items[n_test:n_test+n_val])
        train.extend(items[n_test+n_val:])
        split_counts[label] = {
            "train": len(items[n_test+n_val:]),
            "val": n_val,
            "test": n_test,
        }
    return train, val, test, split_counts


def arrays(rows, index):
    x = np.stack([r[3] for r in rows]).astype(np.float32)
    y = np.asarray([index[r[1]] for r in rows], dtype=np.int32)
    return x, y


def augment(x, y):
    rng = np.random.default_rng(SEED)
    xs, ys = [x], [y]
    for _ in range(4):
        copy = x.copy()
        noise = rng.normal(0.0, 0.012, size=copy[:, :, :-4].shape).astype(np.float32)
        copy[:, :, :-4] += noise
        shifts = rng.integers(-2, 3, size=len(copy))
        for i, shift in enumerate(shifts):
            copy[i] = np.roll(copy[i], int(shift), axis=0)
        xs.append(copy)
        ys.append(y.copy())
    return np.concatenate(xs), np.concatenate(ys)


def metrics(probs, truth, labels, threshold=0.0, margin_threshold=0.0):
    cm = np.zeros((len(labels), len(labels)), dtype=int)
    accepted = []
    correct = []
    confidences = []
    margins = []
    for p, true in zip(probs, truth):
        order = np.argsort(p)[::-1]
        pred = int(order[0])
        conf = float(p[pred])
        margin = conf - (float(p[int(order[1])]) if len(order)>1 else 0.0)
        is_accepted = conf >= threshold and margin >= margin_threshold
        correct.append(pred == int(true))
        accepted.append(is_accepted)
        confidences.append(conf)
        margins.append(margin)
        if is_accepted:
            cm[int(true), pred] += 1
    per_class=[]; f1s=[]
    for i,label in enumerate(labels):
        tp=int(cm[i,i]); fp=int(cm[:,i].sum()-tp); fn=int(cm[i,:].sum()-tp)
        precision=tp/(tp+fp) if tp+fp else 0.0
        recall=tp/(tp+fn) if tp+fn else 0.0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        f1s.append(f1)
        per_class.append({"label":label,"precision":precision,"recall":recall,"f1":f1,"support":int(np.sum(truth==i))})
    accepted_n=sum(accepted)
    accepted_correct=sum(1 for c,a in zip(correct,accepted) if c and a)
    return {
        "samples":len(truth),
        "top1_accuracy":float(np.mean(correct)) if len(truth) else 0.0,
        "macro_f1":float(np.mean(f1s)) if f1s else 0.0,
        "threshold":float(threshold),
        "margin_threshold":float(margin_threshold),
        "coverage":accepted_n/len(truth) if len(truth) else 0.0,
        "accepted_accuracy":accepted_correct/accepted_n if accepted_n else 0.0,
        "confusion_matrix":cm.tolist(),
        "per_class":per_class,
        "confidence_summary":{"min":float(np.min(confidences)),"median":float(np.median(confidences)),"max":float(np.max(confidences))},
        "margin_summary":{"min":float(np.min(margins)),"median":float(np.median(margins)),"max":float(np.max(margins))},
    }


def choose_gates(probs, truth, labels):
    best=None
    confs=np.max(probs,axis=1)
    sorted_probs=np.sort(probs,axis=1)
    margins=sorted_probs[:,-1]-sorted_probs[:,-2]
    conf_candidates=sorted(set([0.35,0.45,0.55,0.65,0.75,*[round(float(x),3) for x in confs]]))
    margin_candidates=sorted(set([0.0,0.03,0.06,0.10,0.15,*[round(float(x),3) for x in margins]]))
    for threshold in conf_candidates:
        for margin in margin_candidates:
            report=metrics(probs,truth,labels,threshold,margin)
            if report["coverage"] < 0.40:
                continue
            score=report["accepted_accuracy"]*math.sqrt(report["coverage"])+0.10*report["top1_accuracy"]
            candidate=(score,threshold,margin,report)
            if best is None or candidate[0]>best[0]:
                best=candidate
    if best is None:
        report=metrics(probs,truth,labels,0.35,0.0)
        return 0.35,0.0,report
    return float(best[1]),float(best[2]),best[3]


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",default="data/core_extension_landmarks")
    parser.add_argument("--out",default="ml/artifacts/core-extension-v1")
    args=parser.parse_args()

    random.seed(SEED); np.random.seed(SEED); keras.utils.set_random_seed(SEED)
    rows=load_samples(REPO_ROOT/args.data)
    labels=list(TARGETS); index={label:i for i,label in enumerate(labels)}
    train,val,test,split_counts=stratified_split(rows)
    x_train,y_train=arrays(train,index); x_val,y_val=arrays(val,index); x_test,y_test=arrays(test,index)

    mean=x_train.mean(axis=(0,1),keepdims=True).astype(np.float32)
    std=x_train.std(axis=(0,1),keepdims=True).astype(np.float32)
    std=np.maximum(std,0.03).astype(np.float32)
    x_train=(x_train-mean)/std; x_val=(x_val-mean)/std; x_test=(x_test-mean)/std
    x_aug,y_aug=augment(x_train,y_train)

    inputs=keras.Input(shape=(SEQUENCE_LENGTH,FEATURE_DIM),name="landmarks")
    x=keras.layers.Bidirectional(keras.layers.LSTM(64,return_sequences=True,dropout=0.15))(inputs)
    x=keras.layers.Bidirectional(keras.layers.LSTM(32,dropout=0.15))(x)
    x=keras.layers.Dense(64,activation="relu")(x)
    x=keras.layers.Dropout(0.25)(x)
    outputs=keras.layers.Dense(len(labels),activation="softmax",name="sign")(x)
    model=keras.Model(inputs,outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=8e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    callbacks=[
        keras.callbacks.EarlyStopping(monitor="val_loss",patience=18,restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss",factor=0.5,patience=7,min_lr=1e-5),
    ]
    history=model.fit(
        x_aug,y_aug,validation_data=(x_val,y_val),
        epochs=120,batch_size=12,verbose=2,callbacks=callbacks,
    )

    val_probs=np.asarray(model.predict(x_val,verbose=0),dtype=np.float32)
    threshold,margin,val_selective=choose_gates(val_probs,y_val,labels)
    test_probs=np.asarray(model.predict(x_test,verbose=0),dtype=np.float32)
    test_report=metrics(test_probs,y_test,labels,threshold,margin)
    train_probs=np.asarray(model.predict(x_train,verbose=0),dtype=np.float32)
    train_report=metrics(train_probs,y_train,labels,0.0,0.0)

    out=REPO_ROOT/args.out; out.mkdir(parents=True,exist_ok=True)
    model.save(out/"model.keras")
    np.savez_compressed(out/"normalization.npz",mean=mean,std=std)

    source_manifest=json.loads((REPO_ROOT/args.data/"dataset_manifest.json").read_text(encoding="utf-8"))
    manifest={
        "model_version":"sanket-core-extension-bilstm-v1",
        "backend":"bilstm",
        "feature_schema":"holistic-v1",
        "feature_dim":FEATURE_DIM,
        "sequence_length":SEQUENCE_LENGTH,
        "labels":labels,
        "accept_threshold":threshold,
        "margin_threshold":margin,
        "motion_threshold":0.0010,
        "tracking_threshold":0.48,
        "trained_at":datetime.now(timezone.utc).isoformat(),
        "training_origin":"public_core_extension_bilstm",
        "source":"vidit031/isl-isolated-40words (INCLUDE/CISLR/ISL500 subset)",
        "usage":"research/academic prototype",
        "raw_video_redistributed":False,
        "source_manifest":source_manifest,
        "split":{"mode":"deterministic_stratified_sample_holdout","seed":SEED,"counts":split_counts},
    }
    report={
        "manifest":manifest,
        "train":train_report,
        "validation_selective":val_selective,
        "test":test_report,
        "epochs_trained":len(history.history.get("loss",[])),
        "claims_note":"Five-class isolated-sign research extension; not unrestricted ISL and not signer-independent.",
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    (out/"evaluation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    (out/"MODEL_CARD.md").write_text(
        "# SANKET core extension BiLSTM v1\n\n"
        "Vocabulary: help, no, water, where, yes.\n\n"
        f"Test top-1: {test_report['top1_accuracy']:.3f}.  "
        f"Macro F1: {test_report['macro_f1']:.3f}.  "
        f"Accepted accuracy: {test_report['accepted_accuracy']:.3f} at "
        f"coverage {test_report['coverage']:.3f}.\n\n"
        "Research/academic prototype. Uses public aggregate clips including "
        "ISL500 research-use data; not a commercial-use artifact. Raw videos "
        "are not redistributed. Evaluation is not signer-independent.\n",
        encoding="utf-8",
    )
    print(json.dumps({"test":test_report,"validation_selective":val_selective,"split":split_counts},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

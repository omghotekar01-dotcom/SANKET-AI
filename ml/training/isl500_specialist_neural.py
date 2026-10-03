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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
import keras

from apps.api.app.services.feature_schema import resample_sequence

SEED = 42
SEQ_LEN = 48
NATIVE_DIM = 226
COMPACT_DIM = 166  # 2 hands (126) + selected pose (36) + 4 modality masks


def compact(seq: np.ndarray) -> np.ndarray:
    seq = resample_sequence(seq.astype(np.float32), SEQ_LEN)
    return np.concatenate([seq[:, :162], seq[:, -4:]], axis=1).astype(np.float32)


def load_rows(root: Path):
    rows=[]
    for meta_path in sorted(root.glob("*.json")):
        if meta_path.name=="dataset_manifest.json":
            continue
        meta=json.loads(meta_path.read_text(encoding="utf-8"))
        payload=np.load(root/meta["feature_path"])
        rows.append({
            "id":meta["sample_id"],
            "label":meta["label"],
            "signer":meta["signer_id"],
            "x":compact(payload["sequence"]),
        })
    return rows


def split_by_signer(rows):
    signers=sorted({r["signer"] for r in rows})
    if len(signers)<12:
        raise RuntimeError(f"Need >=12 distinct signers, found {len(signers)}")
    rng=random.Random(SEED)
    shuffled=signers[:]
    rng.shuffle(shuffled)
    test_signers=set(shuffled[:3])
    val_signers=set(shuffled[3:5])
    train_signers=set(shuffled[5:])
    train=[r for r in rows if r["signer"] in train_signers]
    val=[r for r in rows if r["signer"] in val_signers]
    test=[r for r in rows if r["signer"] in test_signers]
    return train,val,test,{
        "mode":"signer_disjoint_10_2_3",
        "train_signers":sorted(train_signers),
        "val_signers":sorted(val_signers),
        "test_signers":sorted(test_signers),
    }


def arrays(rows,index):
    return (
        np.stack([r["x"] for r in rows]).astype(np.float32),
        np.asarray([index[r["label"]] for r in rows],dtype=np.int32),
    )


def augment(x,y):
    rng=np.random.default_rng(SEED)
    xs=[x];ys=[y]
    coord_dim=162
    for _ in range(5):
        z=x.copy()
        z[:,:,:coord_dim]+=rng.normal(0,0.008,size=z[:,:,:coord_dim].shape).astype(np.float32)
        scales=rng.normal(1.0,0.025,size=(len(z),1,1)).astype(np.float32)
        z[:,:,:coord_dim]*=scales
        for i in range(len(z)):
            shift=int(rng.integers(-2,3))
            z[i]=np.roll(z[i],shift,axis=0)
            if rng.random()<0.35:
                drop=int(rng.integers(3,SEQ_LEN-3))
                z[i,drop]=0.5*(z[i,drop-1]+z[i,drop+1])
        xs.append(z);ys.append(y.copy())
    return np.concatenate(xs),np.concatenate(ys)


def classification_metrics(probs,truth,labels,threshold=0.0,margin_threshold=0.0):
    preds=np.argmax(probs,axis=1)
    order=np.sort(probs,axis=1)
    conf=order[:,-1]
    margin=order[:,-1]-order[:,-2]
    accepted=(conf>=threshold)&(margin>=margin_threshold)
    correct=preds==truth
    cm=np.zeros((len(labels),len(labels)),dtype=int)
    for t,p,a in zip(truth,preds,accepted):
        if a: cm[int(t),int(p)]+=1
    f1s=[];per=[]
    for i,label in enumerate(labels):
        tp=int(cm[i,i]);fp=int(cm[:,i].sum()-tp);fn=int(cm[i,:].sum()-tp)
        precision=tp/(tp+fp) if tp+fp else 0.0
        recall=tp/(tp+fn) if tp+fn else 0.0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        f1s.append(f1)
        per.append({"label":label,"precision":precision,"recall":recall,"f1":f1,"support":int(np.sum(truth==i))})
    nacc=int(accepted.sum())
    return {
        "samples":int(len(truth)),
        "top1_accuracy":float(correct.mean()),
        "macro_f1":float(np.mean(f1s)),
        "coverage":float(accepted.mean()),
        "accepted_accuracy":float(correct[accepted].mean()) if nacc else 0.0,
        "threshold":float(threshold),
        "margin_threshold":float(margin_threshold),
        "confusion_matrix":cm.tolist(),
        "per_class":per,
        "confidence_summary":{"min":float(conf.min()),"median":float(np.median(conf)),"max":float(conf.max())},
        "margin_summary":{"min":float(margin.min()),"median":float(np.median(margin)),"max":float(margin.max())},
    }


def choose_gates(probs,truth,labels):
    conf=np.max(probs,axis=1)
    sortedp=np.sort(probs,axis=1)
    margins=sortedp[:,-1]-sortedp[:,-2]
    thresholds=sorted(set([0.30,0.40,0.50,0.60,0.70,*[round(float(x),3) for x in conf]]))
    margin_cands=sorted(set([0.0,0.03,0.06,0.10,0.15,*[round(float(x),3) for x in margins]]))
    best=None
    for t in thresholds:
        for m in margin_cands:
            report=classification_metrics(probs,truth,labels,t,m)
            if report["coverage"]<0.50:
                continue
            score=report["accepted_accuracy"]*math.sqrt(report["coverage"])+0.15*report["top1_accuracy"]
            item=(score,t,m,report)
            if best is None or item[0]>best[0]: best=item
    if best is None:
        r=classification_metrics(probs,truth,labels,0.30,0.0)
        return 0.30,0.0,r
    return float(best[1]),float(best[2]),best[3]


def make_tcn(classes:int):
    inp=keras.Input((SEQ_LEN,COMPACT_DIM),name="landmarks")
    x=keras.layers.Conv1D(96,5,padding="same",activation="relu")(inp)
    x=keras.layers.BatchNormalization()(x)
    x=keras.layers.Dropout(0.18)(x)
    for dilation in (1,2,4):
        residual=x
        x=keras.layers.Conv1D(96,3,padding="same",dilation_rate=dilation,activation="relu")(x)
        x=keras.layers.BatchNormalization()(x)
        x=keras.layers.Dropout(0.18)(x)
        x=keras.layers.Add()([x,residual])
    x=keras.layers.GlobalAveragePooling1D()(x)
    x=keras.layers.Dense(96,activation="relu")(x)
    x=keras.layers.Dropout(0.25)(x)
    return keras.Model(inp,keras.layers.Dense(classes,activation="softmax")(x),name="tcn")


def make_gru(classes:int):
    inp=keras.Input((SEQ_LEN,COMPACT_DIM),name="landmarks")
    x=keras.layers.Bidirectional(keras.layers.GRU(72,return_sequences=True,dropout=0.15))(inp)
    x=keras.layers.Bidirectional(keras.layers.GRU(40,dropout=0.15))(x)
    x=keras.layers.Dense(96,activation="relu")(x)
    x=keras.layers.Dropout(0.25)(x)
    return keras.Model(inp,keras.layers.Dense(classes,activation="softmax")(x),name="bigru")


def make_conv_gru(classes:int):
    inp=keras.Input((SEQ_LEN,COMPACT_DIM),name="landmarks")
    x=keras.layers.Conv1D(96,5,padding="same",activation="relu")(inp)
    x=keras.layers.BatchNormalization()(x)
    x=keras.layers.MaxPool1D(2)(x)
    x=keras.layers.Conv1D(128,3,padding="same",activation="relu")(x)
    x=keras.layers.Bidirectional(keras.layers.GRU(48,dropout=0.15))(x)
    x=keras.layers.Dense(96,activation="relu")(x)
    x=keras.layers.Dropout(0.25)(x)
    return keras.Model(inp,keras.layers.Dense(classes,activation="softmax")(x),name="conv_gru")


def train_candidate(name,builder,x_train,y_train,x_val,y_val,classes):
    keras.utils.set_random_seed(SEED)
    model=builder(classes)
    model.compile(
        optimizer=keras.optimizers.Adam(7e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    callbacks=[
        keras.callbacks.EarlyStopping(monitor="val_loss",patience=22,restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss",factor=0.5,patience=8,min_lr=1e-5),
    ]
    hist=model.fit(x_train,y_train,validation_data=(x_val,y_val),epochs=140,batch_size=18,verbose=0,callbacks=callbacks)
    probs=np.asarray(model.predict(x_val,verbose=0),dtype=np.float32)
    raw=classification_metrics(probs,y_val,[str(i) for i in range(classes)])
    return model,{"name":name,"epochs":len(hist.history["loss"]),"val_accuracy":raw["top1_accuracy"]}


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",default="data/isl500_specialist")
    parser.add_argument("--out",default="ml/artifacts/isl500-specialist-v1")
    args=parser.parse_args()

    random.seed(SEED);np.random.seed(SEED);keras.utils.set_random_seed(SEED)
    rows=load_rows(ROOT/args.data)
    labels=sorted({r["label"] for r in rows})
    index={label:i for i,label in enumerate(labels)}
    train,val,test,split=split_by_signer(rows)
    x_train,y_train=arrays(train,index);x_val,y_val=arrays(val,index);x_test,y_test=arrays(test,index)

    mean=x_train.mean(axis=(0,1),keepdims=True).astype(np.float32)
    std=np.maximum(x_train.std(axis=(0,1),keepdims=True),0.025).astype(np.float32)
    x_train=(x_train-mean)/std;x_val=(x_val-mean)/std;x_test=(x_test-mean)/std
    x_aug,y_aug=augment(x_train,y_train)

    candidates=[]
    for name,builder in [("tcn",make_tcn),("bigru",make_gru),("conv_gru",make_conv_gru)]:
        model,summary=train_candidate(name,builder,x_aug,y_aug,x_val,y_val,len(labels))
        val_probs=np.asarray(model.predict(x_val,verbose=0),dtype=np.float32)
        val_raw=classification_metrics(val_probs,y_val,labels)
        summary["val_macro_f1"]=val_raw["macro_f1"]
        candidates.append((val_raw["top1_accuracy"],val_raw["macro_f1"],name,model,summary))

    candidates.sort(key=lambda x:(x[0],x[1]),reverse=True)
    _,_,selected_name,model,selected_summary=candidates[0]
    val_probs=np.asarray(model.predict(x_val,verbose=0),dtype=np.float32)
    threshold,margin,val_selective=choose_gates(val_probs,y_val,labels)
    test_probs=np.asarray(model.predict(x_test,verbose=0),dtype=np.float32)
    test_report=classification_metrics(test_probs,y_test,labels,threshold,margin)
    train_probs=np.asarray(model.predict(x_train,verbose=0),dtype=np.float32)
    train_report=classification_metrics(train_probs,y_train,labels)

    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
    model.save(out/"model.keras")
    np.savez_compressed(out/"normalization.npz",mean=mean,std=std)
    manifest={
        "model_version":"sanket-isl500-specialist-neural-v1",
        "backend":selected_name,
        "feature_schema":"holistic-compact-166-v1",
        "feature_dim":COMPACT_DIM,
        "sequence_length":SEQ_LEN,
        "labels":labels,
        "accept_threshold":threshold,
        "margin_threshold":margin,
        "motion_threshold":0.0010,
        "tracking_threshold":0.48,
        "training_origin":"public_isl500_signer_disjoint",
        "source":"ISL500/ISL-DATA research/academic-use subset",
        "usage":"research/academic prototype",
        "trained_at":datetime.now(timezone.utc).isoformat(),
        "split":split,
    }
    report={
        "manifest":manifest,
        "train":train_report,
        "validation_selective":val_selective,
        "test":test_report,
        "candidate_models":[x[4] for x in candidates],
        "claims_note":"Nine-class ISL500 specialist with signer-disjoint 10/2/3 split; not unrestricted ISL.",
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    (out/"evaluation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    (out/"MODEL_CARD.md").write_text(
        "# SANKET ISL500 reliable specialist neural v1\n\n"
        f"Backend: {selected_name}\n\n"
        f"Vocabulary: {', '.join(labels)}\n\n"
        f"Test top-1: {test_report['top1_accuracy']:.3f}; macro F1: {test_report['macro_f1']:.3f}; "
        f"accepted accuracy: {test_report['accepted_accuracy']:.3f} at coverage {test_report['coverage']:.3f}.\n\n"
        "Research/academic prototype trained on ISL500 subset. Final test signers were not used for training or validation.\n",
        encoding="utf-8",
    )
    print(json.dumps({"selected":selected_name,"candidates":[x[4] for x in candidates],"test":test_report,"split":split},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
import sys

import cv2
import numpy as np
from huggingface_hub import hf_hub_download
from mediapipe.python.solutions import holistic as mp_holistic

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from apps.api.app.config import settings
from apps.api.app.services.landmark_service import OPENHANDS_MINIMAL_27_INDICES
from apps.api.app.services.openhands_include_model import OpenHandsIncludeModel
from apps.api.app.services.vocabulary_service import normalize_label

HF_REPO="vidit031/isl-isolated-40words"
SAFE={"hello","thank_you","doctor","hospital","medicine","police","student","teacher"}


def canonical(word:str)->str:
    x=normalize_label(word)
    if x=="thankyou":
        return "thank_you"
    return x


def rows():
    path=hf_hub_download(HF_REPO,"metadata.csv",repo_type="dataset")
    with open(path,"r",encoding="utf-8-sig",newline="") as handle:
        return list(csv.DictReader(handle))


class Extractor:
    def __init__(self, complexity:int, flip:bool=False):
        self.flip=flip
        self.h=mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=complexity,
            smooth_landmarks=True,
            enable_segmentation=False,
            refine_face_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def close(self):
        self.h.close()

    @staticmethod
    def _list(container):
        return [] if container is None else list(container.landmark)

    def frame(self,bgr):
        if self.flip:
            bgr=cv2.flip(bgr,1)
        rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
        result=self.h.process(rgb)
        pose=self._list(result.pose_landmarks)
        left=self._list(result.left_hand_landmarks)
        right=self._list(result.right_hand_landmarks)

        points=np.zeros((75,2),dtype=np.float32)
        if pose:
            points[:33]=np.asarray([[p.x,p.y] for p in pose[:33]],dtype=np.float32)
        if left:
            points[33:54]=np.asarray([[p.x,p.y] for p in left[:21]],dtype=np.float32)
        if right:
            points[54:75]=np.asarray([[p.x,p.y] for p in right[:21]],dtype=np.float32)
        return points[list(OPENHANDS_MINIMAL_27_INDICES)].reshape(-1)

    def video(self,path:Path):
        cap=cv2.VideoCapture(str(path))
        out=[]
        while True:
            ok,frame=cap.read()
            if not ok:
                break
            out.append(self.frame(frame))
        cap.release()
        self.h.reset()
        if len(out)<4:
            return None
        return np.stack(out).astype(np.float32)


def select():
    grouped=defaultdict(list)
    for row in rows():
        source=(row.get("dataset") or "").strip()
        label=canonical((row.get("normalized_word") or row.get("word") or "").strip())
        review=(row.get("review_status") or "").strip().lower()
        if source!="INCLUDE" or label not in SAFE or not row.get("video_path"):
            continue
        if review and review not in {"accepted","ok"}:
            continue
        grouped[label].append(row)

    chosen={}
    for label in sorted(SAFE):
        items=sorted(
            grouped.get(label,[]),
            key=lambda r:(-(float(r.get("quality_score") or 0)),r.get("video_path") or ""),
        )
        chosen[label]=items[:2]
    print("COUNTS",json.dumps({k:len(v) for k,v in chosen.items()},sort_keys=True))
    return chosen


def evaluate(model,chosen,complexity:int,flip:bool):
    extractor=Extractor(complexity,flip)
    total=0;top1=0;top5=0;details=[]
    try:
        for expected,items in chosen.items():
            for row in items:
                local=Path(hf_hub_download(HF_REPO,row["video_path"],repo_type="dataset"))
                seq=extractor.video(local)
                if seq is None:
                    continue
                pred=model.predict(seq)
                order=np.argsort(pred.probabilities)[::-1]
                labels=[canonical(pred.labels[int(i)]) for i in order[:5]]
                conf=[float(pred.probabilities[int(i)]) for i in order[:5]]
                total+=1
                top1+=int(labels[0]==expected)
                top5+=int(expected in labels)
                details.append({
                    "expected":expected,
                    "top5":list(zip(labels,[round(x,4) for x in conf])),
                    "frames":len(seq),
                    "path":row["video_path"],
                })
    finally:
        extractor.close()
    return {
        "complexity":complexity,
        "flip":flip,
        "samples":total,
        "top1":top1/total if total else 0.0,
        "top5":top5/total if total else 0.0,
        "details":details,
    }


def main():
    model=OpenHandsIncludeModel(settings.openhands_dir)
    assert model.loaded,model.load_error
    chosen=select()
    results=[
        evaluate(model,chosen,2,False),
        evaluate(model,chosen,1,False),
        evaluate(model,chosen,2,True),
    ]
    print("SEMANTIC_RESULTS")
    print(json.dumps(results,indent=2))
    best=max(results,key=lambda x:(x["top1"],x["top5"]))
    # This probe is diagnostic; fail only if we could not obtain real samples.
    assert best["samples"]>=4,best
    return 0


if __name__=="__main__":
    raise SystemExit(main())

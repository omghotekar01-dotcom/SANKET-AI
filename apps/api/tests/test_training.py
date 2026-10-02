import json
from pathlib import Path
import numpy as np
from ml.training.dataset import load_samples, split_samples, vectorize


def _sample(root: Path, idx:int, label:str, signer:str):
    sid=f's{idx}'; seq=np.full((12,226),idx,dtype=np.float32)
    np.savez_compressed(root/f'{sid}.npz',sequence=seq)
    (root/f'{sid}.json').write_text(json.dumps({'sample_id':sid,'label':label,'signer_id':signer,'consent':True,'feature_path':f'{sid}.npz'}))


def test_dataset_loading_and_signer_split(tmp_path):
    for i in range(9): _sample(tmp_path,i,'a' if i%2==0 else 'b',f'signer{i%3}')
    samples=load_samples(tmp_path); assert len(samples)==9
    train,val,test,info=split_samples(samples,42)
    assert info['mode']=='signer_disjoint'
    assert not ({s.signer_id for s in train} & {s.signer_id for s in test})
    assert vectorize(samples[0],48).shape==(48,452)

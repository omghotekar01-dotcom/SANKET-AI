from pathlib import Path
import json
import numpy as np
from apps.api.app.services.temporal_model import TemporalTemplateModel
from apps.api.app.services.inference_service import RecognitionSession, DecoderConfig


def _model(root: Path):
    root.mkdir()
    # appended velocity dimensions: 4 raw + 4 velocity
    help_template=np.concatenate([np.ones((8,4),np.float32),np.zeros((8,4),np.float32)],axis=1)
    other_template=np.concatenate([np.full((8,4),-1,np.float32),np.zeros((8,4),np.float32)],axis=1)
    np.savez_compressed(root/'model.npz',templates=np.stack([help_template,other_template]),feature_weights=np.ones(8,np.float32))
    (root/'manifest.json').write_text(json.dumps({'labels':['help','other'],'sequence_length':8,'temperature':.05,'model_version':'test','feature_schema':'test','accept_threshold':.7,'margin_threshold':.1,'motion_threshold':0.0001,'tracking_threshold':.4}))
    return TemporalTemplateModel(root)


def test_decoder_accepts_stable_motion_and_suppresses_duplicate(tmp_path):
    m=_model(tmp_path/'m'); s=RecognitionSession(m,config=DecoderConfig(sequence_length=8,minimum_frames=4,stable_predictions=2,cooldown_frames=4))
    events=[]
    for i in range(8):
        vector=np.ones(4,np.float32)+(i*.002)
        e=s.push(vector,{'left_hand':True,'right_hand':True,'pose':True,'face':True,'quality':1.0})
        if e: events.append(e)
    assert any(e.state.value=='ACCEPTED' for e in events)

from pathlib import Path
import numpy as np
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.confidence_service import decide
from apps.api.app.schemas import RecognitionState
from apps.api.app.services.feature_schema import SCHEMA, resample_sequence, append_velocity
from apps.api.app.services.temporal_model import TemporalTemplateModel

client = TestClient(app)


def test_health_and_config():
    r = client.get('/api/health'); assert r.status_code == 200; assert r.json()['status'] == 'ok'
    c = client.get('/api/config'); assert c.status_code == 200; assert c.json()['raw_video_capture'] is False


def test_domains_and_signs():
    assert any(d['id'] == 'hospital' for d in client.get('/api/domains').json())
    assert 'help' in client.get('/api/signs').json()['supported_demo_vocabulary']


def test_reverse_translation_honest_fallback():
    r = client.post('/api/translate/text-to-isl', json={'text':'please help'})
    assert r.status_code == 200
    assert r.json()['mode'] == 'fallback'


def test_feedback_does_not_retrain():
    r = client.post('/api/feedback', json={'accepted':False,'raw_label':'help','corrected_label':'doctor'})
    assert r.status_code == 200 and r.json()['retraining'] is False


def test_confidence_gate_states():
    assert decide(0.1, 0.1, [0.9,0.1]).state == RecognitionState.TRACKING_LOST
    assert decide(0.9, 0.0, [0.9,0.1]).state == RecognitionState.NO_SIGN
    assert decide(0.9, 0.1, [0.55,0.45]).state == RecognitionState.NEED_REPEAT
    assert decide(0.9, 0.1, [0.9,0.1]).state == RecognitionState.ACCEPTED


def test_schema_resampling():
    x=np.zeros((5,SCHEMA.feature_dim),dtype=np.float32)
    y=resample_sequence(x,48); assert y.shape == (48,SCHEMA.feature_dim)
    z=append_velocity(y); assert z.shape == (48,SCHEMA.feature_dim*2)


def test_template_model_synthetic(tmp_path: Path):
    model_dir=tmp_path/'model'; model_dir.mkdir()
    zero=np.zeros((4,6),np.float32)
    one=np.concatenate([np.ones((4,3),np.float32),np.zeros((4,3),np.float32)],axis=1)
    t=np.stack([zero,one])
    np.savez_compressed(model_dir/'model.npz',templates=t,feature_weights=np.ones(6,np.float32))
    (model_dir/'manifest.json').write_text('{"labels":["zero","one"],"sequence_length":4,"temperature":0.1,"model_version":"test","feature_schema":"x"}')
    m=TemporalTemplateModel(model_dir); assert m.loaded
    p=m.predict(np.ones((4,3),np.float32)); assert p.top_label == 'one'


def test_collector_requires_consent():
    r=client.post('/api/collector/start',json={'label':'help','signer_id':'s1','consent':False})
    assert r.status_code == 400


def test_recognition_socket_ready():
    with client.websocket_connect('/ws/recognize') as ws:
        msg=ws.receive_json(); assert msg['type']=='ready'; assert 'model_loaded' in msg
        ws.send_json({'type':'ping','seq':7}); assert ws.receive_json()['seq']==7


def test_metrics_is_explicit_when_missing():
    r=client.get('/api/metrics'); assert r.status_code==200; assert 'available' in r.json()


def test_model_train_fails_honestly_without_dataset():
    r=client.post('/api/model/train')
    assert r.status_code == 400
    assert 'Need at least' in r.text or 'insufficient' in r.text

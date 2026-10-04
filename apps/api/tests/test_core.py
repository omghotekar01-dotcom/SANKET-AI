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
    payload = client.get('/api/signs').json()
    assert payload['core_total'] == 21
    assert payload['target_vocabulary'] == [
        'hello','thank_you','yes','no','help','doctor','hospital','water','pain',
        'medicine','police','fire','danger','accident','stop','where','name',
        'student','teacher','repeat','understand'
    ]
    assert set(payload['core_supported']).isdisjoint(payload['core_missing'])
    assert set(payload['core_supported']) | set(payload['core_missing']) == set(payload['target_vocabulary'])
    assert payload['supported_demo_vocabulary'] == payload['core_supported']


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


def test_core_vocabulary_normalization_and_coverage():
    from apps.api.app.services.vocabulary_service import core_coverage, normalize_label
    assert normalize_label('Thank You') == 'thank_you'
    result = core_coverage(['Hello', 'Thank you', 'Doctor'])
    assert result['supported'] == ['hello', 'thank_you', 'doctor']
    assert result['supported_count'] == 3
    assert result['total'] == 21
    assert 'help' in result['missing']


def test_domain_packs_are_externalized_and_normalized():
    from apps.api.app.services.context_service import DOMAIN_PACKS, DOMAINS, domain_descriptors, rerank
    assert set(DOMAINS) >= {'general','classroom','hospital','emergency','public_service'}
    assert any(item['id'] == 'hospital' and item['label'] == 'Hospital' for item in domain_descriptors())
    assert 'doctor' in DOMAIN_PACKS['hospital']['boost']
    probs = rerank(['doctor','teacher'], [0.5,0.5], 'hospital')
    assert probs[0] > probs[1]


def test_feedback_endpoint_persists_correction_without_auto_training():
    r = client.post('/api/feedback', json={
        'utterance_id':'turn-test',
        'raw_label':'hello',
        'accepted':False,
        'corrected_label':'help',
        'note':'test correction',
    })
    assert r.status_code == 200
    assert r.json()['stored'] is True
    assert r.json()['retraining'] is False


def test_language_catalog_and_marathi_canonicalization():
    langs = client.get('/api/languages')
    assert langs.status_code == 200
    assert {item['id'] for item in langs.json()} == {'en','mr','both'}

    from apps.api.app.services.language_service import canonicalize_text, detect_language
    assert detect_language('डॉक्टर') == 'mr'
    assert canonicalize_text('नमस्कार', 'auto')[2] == 'hello'
    assert canonicalize_text('शुभ सकाळ', 'mr')[2] == 'good morning'
    assert canonicalize_text('डॉक्टर पाणी', 'mr')[2] == 'doctor water'


def test_marathi_reverse_isl_uses_same_canonical_sign_lookup():
    r = client.post('/api/translate/text-to-isl', json={'text':'डॉक्टर','language':'mr'})
    assert r.status_code == 200
    body = r.json()
    assert body['input_language'] == 'mr'
    assert body['normalized_text'] == 'डॉक्टर'
    assert body['canonical_text'] == 'doctor'
    assert body['items'][0]['phrase'] == 'doctor'


class _FixedPrediction:
    def __init__(self, labels, probabilities):
        self.labels = labels
        self.probabilities = np.asarray(probabilities, dtype=np.float32)


class _FakeBootstrap:
    loaded = True
    is_bootstrap = True
    sequence_length = 2
    version = "fake"
    schema_version = "fake-schema"
    tracking_threshold = 0.1
    motion_threshold = 0.01
    accept_threshold = 0.60
    margin_threshold = 0.06

    def __init__(self, probabilities):
        self.labels = ["Happy", "Hello", "Doctor"]
        self._probabilities = probabilities

    def predict(self, sequence):
        return _FixedPrediction(self.labels, self._probabilities)


def test_reliable_core_rejects_high_confidence_happy_instead_of_guessing():
    from apps.api.app.services.inference_service import RecognitionSession, DecoderConfig
    session = RecognitionSession(
        _FakeBootstrap([0.90, 0.06, 0.04]),
        allowed_labels={"hello", "doctor"},
        config=DecoderConfig(sequence_length=2, minimum_frames=2, stable_predictions=1),
    )
    tracking = {"left_hand":True,"right_hand":False,"pose":True,"face":True,"quality":1.0}
    assert session.push(np.zeros(3, dtype=np.float32), tracking) is None
    event = session.push(np.ones(3, dtype=np.float32), tracking)
    assert event is not None
    assert event.state == RecognitionState.NEED_REPEAT
    assert event.label is None
    assert event.confidence < 0.60


def test_reliable_core_accepts_strong_allowed_class():
    from apps.api.app.services.inference_service import RecognitionSession, DecoderConfig
    session = RecognitionSession(
        _FakeBootstrap([0.05, 0.88, 0.07]),
        allowed_labels={"hello", "doctor"},
        config=DecoderConfig(sequence_length=2, minimum_frames=2, stable_predictions=1),
    )
    tracking = {"left_hand":True,"right_hand":False,"pose":True,"face":True,"quality":1.0}
    assert session.push(np.zeros(3, dtype=np.float32), tracking) is None
    event = session.push(np.ones(3, dtype=np.float32), tracking)
    assert event is not None
    assert event.state == RecognitionState.ACCEPTED
    assert event.label == "Hello"


def test_recognition_socket_defaults_to_reliable_core_scope():
    with client.websocket_connect('/ws/recognize') as ws:
        msg = ws.receive_json()
        assert msg['type'] == 'ready'
        assert msg['recognition_scope'] == 'core_safe'
        if msg.get('model_is_bootstrap'):
            assert msg['model_vocabulary_size'] == 8
            assert len(msg['scoped_vocabulary']) == 8


def test_signs_endpoint_separates_safe_and_experimental_vocabularies():
    payload = client.get('/api/signs').json()
    assert payload['default_recognition_scope'] == 'core_safe'
    if payload['model_is_bootstrap']:
        assert payload['live_vocabulary_size'] == 8
        assert payload['experimental_vocabulary_size'] == len(payload['experimental_vocabulary'])
        assert payload['experimental_vocabulary_size'] >= payload['live_vocabulary_size']
        assert 'Happy' not in payload['safe_live_vocabulary']


def test_openhands_clip_normalization_matches_shoulder_contract():
    from apps.api.app.services.openhands_include_model import OpenHandsIncludeModel
    seq = np.zeros((3, 54), dtype=np.float32)
    points = seq.reshape(3, 27, 2)
    points[:, 3] = [0.0, 0.0]
    points[:, 4] = [2.0, 0.0]
    normalized = OpenHandsIncludeModel._normalize_clip(seq)
    assert normalized.shape == (3, 27, 2)
    assert np.allclose(normalized[:, 3], [-0.5, 0.0])
    assert np.allclose(normalized[:, 4], [0.5, 0.0])


def test_openhands_minimal_landmark_layout_has_27_nodes():
    from apps.api.app.services.landmark_service import OPENHANDS_MINIMAL_27_INDICES
    assert len(OPENHANDS_MINIMAL_27_INDICES) == 27
    assert max(OPENHANDS_MINIMAL_27_INDICES) == 74


def test_openhands_temporal_interpolation_restores_model_density():
    from apps.api.app.services.openhands_include_model import OpenHandsIncludeModel
    seq = np.stack([
        np.linspace(0.0, 1.0, 54, dtype=np.float32) + i
        for i in range(24)
    ])
    dense = OpenHandsIncludeModel._temporal_interpolate(seq, 80)
    assert dense.shape == (80, 54)
    assert np.allclose(dense[0], seq[0])
    assert np.allclose(dense[-1], seq[-1])


class _FakeOpenHands:
    loaded = True
    is_bootstrap = True
    input_schema = "openhands"
    sequence_length = 24
    version = "fake-openhands"
    schema_version = "fake-openhands-schema"
    tracking_threshold = 0.1
    motion_threshold = 0.0008
    accept_threshold = 0.60
    margin_threshold = 0.06
    labels = ["Hello", "Doctor"]

    def __init__(self):
        self.calls = 0
        self.last_shape = None

    def predict(self, sequence):
        self.calls += 1
        self.last_shape = sequence.shape
        return _FixedPrediction(self.labels, [0.92, 0.08])


def test_openhands_session_captures_one_isolated_motion_segment():
    from apps.api.app.services.inference_service import RecognitionSession
    fake = _FakeOpenHands()
    session = RecognitionSession(fake, allowed_labels={"hello", "doctor"})
    tracking = {"left_hand":True,"right_hand":False,"pose":True,"face":True,"quality":1.0}

    base = np.zeros(54, dtype=np.float32)
    for _ in range(5):
        assert session.push(base.copy(), tracking) is None
    assert fake.calls == 0

    event = None
    for i in range(30):
        frame = np.full(54, (i + 1) * 0.01, dtype=np.float32)
        result = session.push(frame, tracking)
        if result is not None:
            event = result
            break
    assert event is not None
    assert event.state == RecognitionState.ACCEPTED
    assert event.label == "Hello"
    assert fake.calls == 1
    assert fake.last_shape == (24, 54)

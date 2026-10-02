from fastapi.testclient import TestClient
from apps.api.app.main import app

client=TestClient(app)

def test_two_peer_signaling():
    with client.websocket_connect('/ws/signaling/room-1') as a:
        assert a.receive_json()['type']=='joined'
        with client.websocket_connect('/ws/signaling/room-1') as b:
            assert b.receive_json()['type']=='joined'
            assert a.receive_json()['type']=='peer_joined'
            a.send_json({'type':'offer','payload':{'sdp':'x'}})
            msg=b.receive_json(); assert msg['type']=='offer' and msg['payload']['sdp']=='x'

import { useEffect, useRef, useState } from 'react'
import { WS_BASE } from '../lib/api'
import { localizeSign, type LanguageMode } from '../lib/language'

export function Call({language}:{language:LanguageMode}){
  const [room,setRoom]=useState(()=>Math.random().toString(36).slice(2,8))
  const [state,setState]=useState('Not connected')
  const [captionState,setCaptionState]=useState('Captions not started')
  const [localCaption,setLocalCaption]=useState('')
  const [remoteCaption,setRemoteCaption]=useState('')
  const local=useRef<HTMLVideoElement|null>(null), remote=useRef<HTMLVideoElement|null>(null)
  const capture=useRef<HTMLCanvasElement|null>(null)
  const stream=useRef<MediaStream|null>(null), pc=useRef<RTCPeerConnection|null>(null)
  const ws=useRef<WebSocket|null>(null), recognitionWs=useRef<WebSocket|null>(null)
  const captionTimer=useRef<number|null>(null), recognitionBusy=useRef(false)

  const stopCaptions=()=>{
    if(captionTimer.current)window.clearInterval(captionTimer.current)
    captionTimer.current=null;recognitionWs.current?.close();recognitionWs.current=null;recognitionBusy.current=false
    setCaptionState('Captions stopped')
  }
  const cleanup=()=>{
    stopCaptions();ws.current?.close();pc.current?.close();stream.current?.getTracks().forEach(t=>t.stop())
    ws.current=null;pc.current=null;stream.current=null;setState('Not connected')
  }
  useEffect(()=>cleanup,[])

  const startSanketCaptions=(media:MediaStream)=>{
    const rec=new WebSocket(`${WS_BASE}/ws/recognize`);rec.binaryType='arraybuffer';recognitionWs.current=rec
    rec.onmessage=async raw=>{
      const m=JSON.parse(raw.data)
      if(m.type==='ready')setCaptionState(m.model_loaded&&m.perception_available?'SANKET captions ready':'SANKET captions unavailable: model/perception not ready')
      if(m.type==='tracking'||m.type==='model_unavailable'||m.type==='perception_error')recognitionBusy.current=false
      if(m.type==='prediction'){
        recognitionBusy.current=false
        if(m.state==='ACCEPTED'&&m.display_text){
          const localized=localizeSign(m.display_text,language)
          setLocalCaption(localized);ws.current?.send(JSON.stringify({type:'caption',payload:{text:localized,canonical:m.display_text,confidence:m.confidence,source:'SANKET'}}))
        }
      }
    }
    rec.onerror=()=>setCaptionState('Caption recognizer connection failed')
    const video=document.createElement('video');video.srcObject=media;video.muted=true;video.playsInline=true;void video.play()
    captionTimer.current=window.setInterval(()=>{
      if(rec.readyState!==WebSocket.OPEN||recognitionBusy.current||video.readyState<2||!capture.current)return
      const canvas=capture.current;canvas.width=320;canvas.height=240;const ctx=canvas.getContext('2d');if(!ctx)return
      ctx.drawImage(video,0,0,320,240);recognitionBusy.current=true
      canvas.toBlob(async blob=>{if(blob&&rec.readyState===WebSocket.OPEN)rec.send(await blob.arrayBuffer());else recognitionBusy.current=false},'image/jpeg',.68)
      window.setTimeout(()=>{recognitionBusy.current=false},900)
    },120)
  }

  const connect=async()=>{
    cleanup()
    try{
      setState('Requesting camera/mic…')
      const media=await navigator.mediaDevices.getUserMedia({video:true,audio:true});stream.current=media
      if(local.current)local.current.srcObject=media
      const peer=new RTCPeerConnection({iceServers:[]});pc.current=peer;media.getTracks().forEach(t=>peer.addTrack(t,media))
      peer.ontrack=e=>{if(remote.current)remote.current.srcObject=e.streams[0]}
      peer.onicecandidate=e=>{if(e.candidate)ws.current?.send(JSON.stringify({type:'ice',payload:e.candidate}))}
      peer.onconnectionstatechange=()=>setState(peer.connectionState)
      const sock=new WebSocket(`${WS_BASE}/ws/signaling/${encodeURIComponent(room)}`);ws.current=sock
      sock.onmessage=async raw=>{
        const m=JSON.parse(raw.data)
        if(m.type==='joined')setState('Room ready')
        else if(m.type==='peer_joined'){const offer=await peer.createOffer();await peer.setLocalDescription(offer);sock.send(JSON.stringify({type:'offer',payload:offer}))}
        else if(m.type==='offer'){await peer.setRemoteDescription(m.payload);const answer=await peer.createAnswer();await peer.setLocalDescription(answer);sock.send(JSON.stringify({type:'answer',payload:answer}))}
        else if(m.type==='answer')await peer.setRemoteDescription(m.payload)
        else if(m.type==='ice')await peer.addIceCandidate(m.payload)
        else if(m.type==='caption')setRemoteCaption(m.payload?.canonical?localizeSign(String(m.payload.canonical),language):String(m.payload?.text||''))
        else if(m.type==='peer_left')setState('Peer left')
        else if(m.type==='room_full')setState('Room already has two peers')
      }
      sock.onerror=()=>setState('Signaling connection failed')
      startSanketCaptions(media)
    }catch(error){setState(error instanceof Error?error.message:'Unable to start call');cleanup()}
  }

  return <div className="content-page"><div className="page-title"><span className="eyebrow">EXPERIMENTAL WEBRTC + SANKET CAPTIONS</span><h1>Sign-language call</h1><p>Peer-to-peer media; accepted local SANKET predictions are sent as caption metadata. No recording by default.</p></div><div className="call-controls"><label>Room code<input value={room} onChange={e=>setRoom(e.target.value.replace(/[^a-zA-Z0-9-]/g,''))}/></label><button className="primary" onClick={connect}>Create / join</button><button className="danger" onClick={cleanup}>Leave</button><span className="call-state">Call: {state}</span><span className="call-state">{captionState}</span></div><div className="video-grid"><figure className="video-caption-wrap"><video ref={remote} autoPlay playsInline/><div className="caption-overlay" aria-live="polite">{remoteCaption||'Remote SANKET captions appear here'}</div><figcaption>Remote signer</figcaption></figure><figure className="video-caption-wrap"><video ref={local} autoPlay muted playsInline/><div className="caption-overlay self">{localCaption||'Your accepted caption'}</div><figcaption>You</figcaption></figure></div><canvas ref={capture} hidden/><div className="notice">Same-network/two-tab operation is the supported hackathon path. Internet-wide reliability normally needs a tested TURN service. If the recognition model is not loaded, the video call still works and captions visibly report unavailable.</div></div>
}

import { useCallback, useEffect, useRef, useState } from 'react'
import { WS_BASE } from '../lib/api'
import type { PredictionEvent, TrackingEvent, TrackingInfo, TranscriptTurn } from '../types'

const EMPTY_TRACKING: TrackingInfo = {left_hand:false,right_hand:false,pose:false,face:false,quality:0}

export function useRecognition(domain: string, collectorId?: string | null) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const overlayRef = useRef<HTMLCanvasElement | null>(null)
  const captureRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const timerRef = useRef<number | null>(null)
  const busyRef = useRef(false)
  const [running,setRunning] = useState(false)
  const [socketState,setSocketState] = useState('disconnected')
  const [tracking,setTracking] = useState<TrackingInfo>(EMPTY_TRACKING)
  const [prediction,setPrediction] = useState<PredictionEvent | null>(null)
  const [transcript,setTranscript] = useState<TranscriptTurn[]>([])
  const [message,setMessage] = useState('Ready to interpret')
  const [modelLoaded,setModelLoaded] = useState(false)
  const [perceptionAvailable,setPerceptionAvailable] = useState(false)
  const [landmarkLatency,setLandmarkLatency] = useState<number | null>(null)
  const [ttsEnabled,setTtsEnabled] = useState(true)

  const drawOverlay = useCallback((event: TrackingEvent) => {
    const canvas=overlayRef.current, video=videoRef.current
    if (!canvas || !video) return
    const w=video.clientWidth || 640, h=video.clientHeight || 480
    if (canvas.width !== w) canvas.width=w
    if (canvas.height !== h) canvas.height=h
    const ctx=canvas.getContext('2d'); if (!ctx) return
    ctx.clearRect(0,0,w,h)
    const draw=(points:number[][], radius:number) => {
      ctx.beginPath()
      for (const [x,y] of points) {
        ctx.moveTo((1-x)*w+radius,y*h)
        ctx.arc((1-x)*w,y*h,radius,0,Math.PI*2)
      }
      ctx.fillStyle='rgba(93, 225, 255, .9)'; ctx.fill()
    }
    draw(event.overlay.left_hand,3); draw(event.overlay.right_hand,3); draw(event.overlay.pose,4)
  },[])

  const speak = useCallback((text:string) => {
    if (!ttsEnabled || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const utterance=new SpeechSynthesisUtterance(text)
    utterance.rate=0.95; window.speechSynthesis.speak(utterance)
  },[ttsEnabled])

  const connectSocket = useCallback(() => {
    wsRef.current?.close()
    const query=collectorId ? `?collector_id=${encodeURIComponent(collectorId)}` : ''
    const ws=new WebSocket(`${WS_BASE}/ws/recognize${query}`)
    ws.binaryType='arraybuffer'; wsRef.current=ws; setSocketState('connecting')
    ws.onopen=()=>setSocketState('connected')
    ws.onclose=()=>{setSocketState('disconnected');busyRef.current=false}
    ws.onerror=()=>setMessage('Recognition connection error — camera can be stopped safely')
    ws.onmessage=(raw) => {
      let event:any
      try { event=JSON.parse(raw.data) } catch { return }
      if (event.type==='ready') {
        setModelLoaded(Boolean(event.model_loaded)); setPerceptionAvailable(Boolean(event.perception_available))
        if (!event.perception_available) setMessage(event.perception_reason || 'Perception unavailable')
        else if (!event.model_loaded) setMessage('Tracking ready · train/load a model for live sign recognition')
        return
      }
      if (event.type==='tracking') {
        const t=event as TrackingEvent; setTracking(t.tracking);setLandmarkLatency(t.landmark_latency_ms);drawOverlay(t);busyRef.current=false;return
      }
      if (event.type==='model_unavailable') { setMessage(event.message || 'Model unavailable');busyRef.current=false;return }
      if (event.type==='perception_error') { setMessage(event.message || 'Perception error');busyRef.current=false;return }
      if (event.type==='prediction') {
        const p=event as PredictionEvent;setPrediction(p);setMessage(p.reason || p.state);busyRef.current=false
        if (p.state==='ACCEPTED' && p.display_text) {
          setTranscript(prev=>[...prev,{id:crypto.randomUUID(),source:'ISL' as const,text:p.display_text!,confidence:p.confidence,at:Date.now()}].slice(-50))
          speak(p.display_text)
        }
      }
    }
  },[collectorId,drawOverlay,speak])

  useEffect(()=>{ if (running) connectSocket() },[collectorId]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(()=>{ wsRef.current?.send(JSON.stringify({type:'set_domain',domain})) },[domain])

  const start = useCallback(async()=>{
    if (running) return
    try {
      const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480},facingMode:'user'},audio:false})
      streamRef.current=stream
      if (videoRef.current) { videoRef.current.srcObject=stream; await videoRef.current.play() }
      connectSocket(); setRunning(true); setMessage('Camera active · place upper body and hands inside frame')
      const tick=async()=>{
        const video=videoRef.current, canvas=captureRef.current, ws=wsRef.current
        if (!video || !canvas || !ws || ws.readyState!==WebSocket.OPEN || busyRef.current || video.readyState<2) return
        canvas.width=320;canvas.height=240
        const ctx=canvas.getContext('2d');if(!ctx)return
        ctx.drawImage(video,0,0,320,240)
        busyRef.current=true
        canvas.toBlob(async blob=>{
          if (!blob || ws.readyState!==WebSocket.OPEN) {busyRef.current=false;return}
          ws.send(await blob.arrayBuffer())
          window.setTimeout(()=>{busyRef.current=false},800)
        },'image/jpeg',0.7)
      }
      timerRef.current=window.setInterval(tick,100)
    } catch (error) {
      setMessage(error instanceof Error ? `Camera unavailable: ${error.message}` : 'Camera unavailable')
    }
  },[connectSocket,running])

  const stop=useCallback(()=>{
    if(timerRef.current)window.clearInterval(timerRef.current);timerRef.current=null
    streamRef.current?.getTracks().forEach(t=>t.stop());streamRef.current=null
    wsRef.current?.close();wsRef.current=null;setRunning(false);setTracking(EMPTY_TRACKING);setMessage('Camera stopped · transcript preserved')
    const ctx=overlayRef.current?.getContext('2d');if(ctx&&overlayRef.current)ctx.clearRect(0,0,overlayRef.current.width,overlayRef.current.height)
  },[])

  useEffect(()=>()=>stop(),[stop])
  const reset=()=>{setTranscript([]);setPrediction(null);wsRef.current?.send(JSON.stringify({type:'reset'}))}

  return {videoRef,overlayRef,captureRef,running,start,stop,reset,socketState,tracking,prediction,transcript,setTranscript,message,modelLoaded,perceptionAvailable,landmarkLatency,ttsEnabled,setTtsEnabled}
}

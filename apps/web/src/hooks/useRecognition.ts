import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE, WS_BASE, apiHealth } from '../lib/api'
import type { PredictionEvent, TrackingEvent, TrackingInfo, TranscriptTurn } from '../types'

const EMPTY_TRACKING: TrackingInfo = {left_hand:false,right_hand:false,pose:false,face:false,quality:0}

export type BackendState = 'checking' | 'online' | 'offline'
export type CapabilityState = 'unknown' | 'ready' | 'unavailable'
export type ModelState = 'unknown' | 'loaded' | 'missing'

export function useRecognition(domain: string, collectorId?: string | null) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const overlayRef = useRef<HTMLCanvasElement | null>(null)
  const captureRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const timerRef = useRef<number | null>(null)
  const reconnectRef = useRef<number | null>(null)
  const busyRef = useRef(false)
  const shouldRunRef = useRef(false)

  const [running,setRunning] = useState(false)
  const [socketState,setSocketState] = useState('disconnected')
  const [backendState,setBackendState] = useState<BackendState>('checking')
  const [perceptionState,setPerceptionState] = useState<CapabilityState>('unknown')
  const [modelState,setModelState] = useState<ModelState>('unknown')
  const [modelBackend,setModelBackend] = useState('none')
  const [modelSource,setModelSource] = useState('none')
  const [modelIsBootstrap,setModelIsBootstrap] = useState(false)
  const [modelVocabularySize,setModelVocabularySize] = useState(0)
  const [tracking,setTracking] = useState<TrackingInfo>(EMPTY_TRACKING)
  const [prediction,setPrediction] = useState<PredictionEvent | null>(null)
  const [transcript,setTranscript] = useState<TranscriptTurn[]>([])
  const [message,setMessage] = useState('Checking local recognition service…')
  const [landmarkLatency,setLandmarkLatency] = useState<number | null>(null)
  const [ttsEnabled,setTtsEnabled] = useState(true)

  const applyModelMeta = useCallback((data:any) => {
    setModelState(data?.model_loaded ? 'loaded' : 'missing')
    setModelBackend(String(data?.model_backend || 'none'))
    setModelSource(String(data?.model_source || 'none'))
    setModelIsBootstrap(Boolean(data?.model_is_bootstrap))
    setModelVocabularySize(Number(data?.model_vocabulary_size || 0))
  },[])

  const applyHealth = useCallback((health:any) => {
    setBackendState('online')
    setPerceptionState(health?.perception_available ? 'ready' : 'unavailable')
    applyModelMeta(health)
  },[applyModelMeta])

  const refreshHealth = useCallback(async() => {
    try {
      const health = await apiHealth()
      applyHealth(health)
      return health
    } catch {
      setBackendState('offline')
      setPerceptionState('unknown')
      setModelState('unknown')
      return null
    }
  },[applyHealth])

  useEffect(()=>{
    void refreshHealth()
    const timer=window.setInterval(()=>{void refreshHealth()},5000)
    return()=>window.clearInterval(timer)
  },[refreshHealth])

  const drawOverlay = useCallback((event: TrackingEvent) => {
    const canvas=overlayRef.current, video=videoRef.current
    if (!canvas || !video) return
    const w=video.clientWidth || 960, h=video.clientHeight || 540
    if (canvas.width !== w) canvas.width=w
    if (canvas.height !== h) canvas.height=h
    const ctx=canvas.getContext('2d'); if (!ctx) return
    ctx.clearRect(0,0,w,h)

    const draw=(points:number[][], radius:number, alpha:number) => {
      ctx.beginPath()
      for (const [x,y] of points) {
        ctx.moveTo((1-x)*w+radius,y*h)
        ctx.arc((1-x)*w,y*h,radius,0,Math.PI*2)
      }
      ctx.fillStyle=`rgba(117, 178, 255, ${alpha})`
      ctx.fill()
    }
    draw(event.overlay.left_hand,2.6,.95)
    draw(event.overlay.right_hand,2.6,.95)
    draw(event.overlay.pose,3.2,.58)
  },[])

  const speak = useCallback((text:string) => {
    if (!ttsEnabled || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const utterance=new SpeechSynthesisUtterance(text)
    utterance.rate=0.96
    window.speechSynthesis.speak(utterance)
  },[ttsEnabled])

  const clearReconnect = () => {
    if (reconnectRef.current !== null) {
      window.clearTimeout(reconnectRef.current)
      reconnectRef.current=null
    }
  }

  const connectSocket = useCallback(() => {
    clearReconnect()
    const old=wsRef.current
    if (old) {
      old.onclose=null
      old.close()
    }

    const query=collectorId ? `?collector_id=${encodeURIComponent(collectorId)}` : ''
    const ws=new WebSocket(`${WS_BASE}/ws/recognize${query}`)
    ws.binaryType='arraybuffer'
    wsRef.current=ws
    setSocketState('connecting')

    ws.onopen=()=>{
      setSocketState('connected')
      setBackendState('online')
      ws.send(JSON.stringify({type:'set_domain',domain}))
    }

    ws.onerror=()=>{
      setBackendState('offline')
      setMessage(`Recognition service is offline at ${API_BASE}. Restart SANKET AI and this page will reconnect automatically.`)
    }

    ws.onclose=()=>{
      busyRef.current=false
      if (!shouldRunRef.current) {
        setSocketState('disconnected')
        return
      }
      setSocketState('reconnecting')
      reconnectRef.current=window.setTimeout(()=>connectSocket(),1400)
    }

    ws.onmessage=(raw) => {
      let event:any
      try { event=JSON.parse(raw.data) } catch { return }

      if (event.type==='ready') {
        setBackendState('online')
        setModelState(event.model_loaded ? 'loaded' : 'missing')
        setModelBackend(String(event.model_backend || 'none'))
        setModelSource(String(event.model_source || 'none'))
        setModelIsBootstrap(Boolean(event.model_is_bootstrap))
        setModelVocabularySize(Number(event.model_vocabulary_size || 0))
        setPerceptionState(event.perception_available ? 'ready' : 'unavailable')

        if (!event.perception_available) {
          setMessage(event.perception_reason || 'Vision runtime is not ready. Run START_SANKET.bat again.')
        } else if (!event.model_loaded) {
          setMessage('Vision is ready, but no recognition model is loaded.')
        } else if (event.model_is_bootstrap) {
          setMessage(`Ready — verified bootstrap recognizer active (${event.model_vocabulary_size || 50} signs).`)
        } else {
          setMessage(`Ready — local SANKET recognizer active (${event.model_vocabulary_size || 0} signs).`)
        }
        return
      }

      if (event.type==='tracking') {
        const t=event as TrackingEvent
        setTracking(t.tracking)
        setLandmarkLatency(t.landmark_latency_ms)
        drawOverlay(t)
        busyRef.current=false
        return
      }

      if (event.type==='model_unavailable') {
        setModelState('missing')
        setMessage('Tracking is working, but no recognition model is available.')
        busyRef.current=false
        return
      }

      if (event.type==='perception_error') {
        setPerceptionState('unavailable')
        setMessage(event.message || 'Vision processing failed.')
        busyRef.current=false
        return
      }

      if (event.type==='prediction') {
        const p=event as PredictionEvent
        setPrediction(p)
        setMessage(p.reason || p.state)
        busyRef.current=false
        if (p.state==='ACCEPTED' && p.display_text) {
          setTranscript(prev=>[...prev,{
            id:crypto.randomUUID(),
            source:'ISL' as const,
            text:p.display_text!,
            confidence:p.confidence,
            at:Date.now(),
          }].slice(-50))
          speak(p.display_text)
        }
      }
    }
  },[collectorId,domain,drawOverlay,speak])

  useEffect(()=>{
    if (running) connectSocket()
  },[collectorId])

  useEffect(()=>{
    if (wsRef.current?.readyState===WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({type:'set_domain',domain}))
    }
  },[domain])

  const start = useCallback(async()=>{
    if (running) return
    shouldRunRef.current=true
    setMessage('Starting camera and recognition…')

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('This browser does not expose camera access.')
      }
      const stream=await navigator.mediaDevices.getUserMedia({
        video:{width:{ideal:1280},height:{ideal:720},facingMode:'user'},
        audio:false,
      })
      streamRef.current=stream
      if (videoRef.current) {
        videoRef.current.srcObject=stream
        await videoRef.current.play()
      }

      setRunning(true)
      connectSocket()

      const tick=async()=>{
        const video=videoRef.current, canvas=captureRef.current, ws=wsRef.current
        if (!video || !canvas || !ws || ws.readyState!==WebSocket.OPEN || busyRef.current || video.readyState<2) return

        canvas.width=384
        canvas.height=216
        const ctx=canvas.getContext('2d')
        if(!ctx)return

        ctx.drawImage(video,0,0,384,216)
        busyRef.current=true
        canvas.toBlob(async blob=>{
          if (!blob || ws.readyState!==WebSocket.OPEN) {
            busyRef.current=false
            return
          }
          ws.send(await blob.arrayBuffer())
          window.setTimeout(()=>{busyRef.current=false},700)
        },'image/jpeg',0.72)
      }
      timerRef.current=window.setInterval(tick,100)
    } catch (error) {
      shouldRunRef.current=false
      setRunning(false)
      setMessage(error instanceof Error ? `Camera unavailable: ${error.message}` : 'Camera unavailable')
    }
  },[connectSocket,running])

  const stop=useCallback(()=>{
    shouldRunRef.current=false
    clearReconnect()
    if(timerRef.current)window.clearInterval(timerRef.current)
    timerRef.current=null

    streamRef.current?.getTracks().forEach(t=>t.stop())
    streamRef.current=null

    if (wsRef.current) {
      wsRef.current.onclose=null
      wsRef.current.close()
    }
    wsRef.current=null
    busyRef.current=false

    setRunning(false)
    setSocketState('disconnected')
    setTracking(EMPTY_TRACKING)
    setLandmarkLatency(null)
    setMessage('Camera is off. Your transcript is preserved.')

    const ctx=overlayRef.current?.getContext('2d')
    if(ctx&&overlayRef.current)ctx.clearRect(0,0,overlayRef.current.width,overlayRef.current.height)
  },[])

  useEffect(()=>()=>stop(),[stop])

  const reset=()=>{
    setTranscript([])
    setPrediction(null)
    wsRef.current?.send(JSON.stringify({type:'reset'}))
  }

  const reconnect=async()=>{
    await refreshHealth()
    if (running) connectSocket()
  }

  return {
    videoRef,overlayRef,captureRef,
    running,start,stop,reset,reconnect,refreshHealth,
    socketState,backendState,perceptionState,modelState,
    modelBackend,modelSource,modelIsBootstrap,modelVocabularySize,
    tracking,prediction,transcript,setTranscript,message,
    modelLoaded:modelState==='loaded',
    perceptionAvailable:perceptionState==='ready',
    landmarkLatency,ttsEnabled,setTtsEnabled,
  }
}

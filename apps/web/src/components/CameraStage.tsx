import type { RefObject } from 'react'
import type { TrackingInfo } from '../types'

type Props={
  videoRef:RefObject<HTMLVideoElement|null>
  overlayRef:RefObject<HTMLCanvasElement|null>
  captureRef:RefObject<HTMLCanvasElement|null>
  running:boolean
  tracking:TrackingInfo
  statusLabel?:string
  caption?:string|null
  onToggleCamera?:()=>void
  onReset?:()=>void
  onDemo?:()=>void
  ttsEnabled?:boolean
  onToggleTts?:()=>void
}

export function CameraStage({
  videoRef,overlayRef,captureRef,running,tracking,statusLabel,caption,
  onToggleCamera,onReset,onDemo,ttsEnabled,onToggleTts,
}:Props) {
  const controls=Boolean(onToggleCamera)
  return <div className="camera-stage" aria-label="Live signing camera">
    <video ref={videoRef} className="camera-video" muted playsInline aria-label="Your live camera preview" />
    <canvas ref={overlayRef} className="landmark-overlay" aria-hidden="true" />
    <canvas ref={captureRef} hidden />

    {!running && <div className="camera-empty">
      <div className="camera-empty-icon"><Glyph name="camera"/></div>
      <strong>Camera is off</strong>
      <span>Your video stays on this device unless you start a call.</span>
    </div>}

    {running && <div className="frame-guide" aria-hidden="true"><span>Keep hands and upper body in frame</span></div>}

    <div className="camera-topline">
      <div className={running?'live-chip live':'live-chip'}>
        <span className="live-dot"/>{running?'Live · not recording':'Camera off'}
      </div>
      <div className="signal-strip" aria-label="Tracking signals">
        <Signal name="Left" on={tracking.left_hand}/>
        <Signal name="Right" on={tracking.right_hand}/>
        <Signal name="Body" on={tracking.pose}/>
        <Signal name="Face" on={tracking.face}/>
      </div>
    </div>

    {running && <div className={caption?'stage-caption has-caption':'stage-caption'}>
      <span>{statusLabel || 'Listening for signs'}</span>
      {caption&&<strong>{caption}</strong>}
    </div>}

    {controls&&<div className="camera-toolbar" aria-label="Interpreter controls">
      <button className={running?'meeting-control danger-control':'meeting-control primary-control'} onClick={onToggleCamera} title={running?'Stop camera':'Start camera'}>
        <Glyph name="camera"/><span>{running?'Stop':'Camera'}</span>
      </button>
      <button className="meeting-control" onClick={onReset} title="Reset transcript and decoder"><Glyph name="reset"/><span>Reset</span></button>
      <button className="meeting-control" onClick={onDemo} title="Run labelled fallback replay"><Glyph name="play"/><span>Replay</span></button>
      <button className={ttsEnabled?'meeting-control active-control':'meeting-control'} onClick={onToggleTts} title="Toggle spoken accepted text"><Glyph name="volume"/><span>Voice</span></button>
    </div>}
  </div>
}

function Signal({name,on}:{name:string;on:boolean}) {
  return <span className={on?'signal on':'signal'}><i/>{name}</span>
}

function Glyph({name}:{name:'camera'|'reset'|'play'|'volume'}) {
  if(name==='camera')return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 10.5 20 7v10l-5-3.5v2A2.5 2.5 0 0 1 12.5 18h-7A2.5 2.5 0 0 1 3 15.5v-7A2.5 2.5 0 0 1 5.5 6h7A2.5 2.5 0 0 1 15 8.5v2Z"/></svg>
  if(name==='reset')return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4v6h6M5.5 16.5A8 8 0 1 0 6 7.2L4 10"/></svg>
  if(name==='play')return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 7 8 5-8 5V7Z"/></svg>
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 6 7 9H4v6h3l4 3V6Zm4.5 3a4 4 0 0 1 0 6M18 6.5a8 8 0 0 1 0 11"/></svg>
}

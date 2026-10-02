import type { RefObject } from 'react'
import type { TrackingInfo } from '../types'

export function CameraStage({videoRef,overlayRef,captureRef,running,tracking}:{
  videoRef:RefObject<HTMLVideoElement|null>;overlayRef:RefObject<HTMLCanvasElement|null>;captureRef:RefObject<HTMLCanvasElement|null>;running:boolean;tracking:TrackingInfo
}) {
  return <div className="camera-stage" aria-label="Live signing camera">
    <video ref={videoRef} className="camera-video" muted playsInline aria-label="Your live camera preview" />
    <canvas ref={overlayRef} className="landmark-overlay" aria-hidden="true" />
    <canvas ref={captureRef} hidden />
    {!running && <div className="camera-empty"><span className="camera-icon">◌</span><strong>Camera is off</strong><span>Start interpretation when you are ready.</span></div>}
    {running && <div className="frame-guide" aria-hidden="true" />}
    <div className="privacy-pill">{running?'● Camera active · not recording':'○ Camera off'}</div>
    <div className="signal-strip">
      <Signal name="LH" on={tracking.left_hand}/><Signal name="RH" on={tracking.right_hand}/><Signal name="BODY" on={tracking.pose}/><Signal name="FACE" on={tracking.face}/>
    </div>
  </div>
}
function Signal({name,on}:{name:string;on:boolean}) { return <span className={on?'signal on':'signal'}>{name}</span> }

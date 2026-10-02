import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useRecognition } from '../hooks/useRecognition'
import { CameraStage } from '../components/CameraStage'
import { StatusCard } from '../components/StatusCard'
import { Transcript } from '../components/Transcript'
import type { TranscriptTurn } from '../types'

export function Interpreter() {
  const [domain,setDomain]=useState('general')
  const [domains,setDomains]=useState<Array<{id:string;label:string}>>([])
  const [safeActions,setSafeActions]=useState(false)
  const [actionNotice,setActionNotice]=useState('')
  const [demoActive,setDemoActive]=useState(false)
  const [demoState,setDemoState]=useState('')
  const r=useRecognition(domain)
  useEffect(()=>{api<Array<{id:string;label:string}>>('/api/domains').then(setDomains).catch(()=>{})},[])
  useEffect(()=>{if(!safeActions||r.prediction?.state!=='ACCEPTED'||!r.prediction.label)return;const label=r.prediction.label;if(label==='stop'){setActionNotice('Safe action: stopped interpretation');r.stop()}else if(label==='repeat'){const last=r.transcript.at(-1)?.text;if(last&&'speechSynthesis'in window){window.speechSynthesis.speak(new SpeechSynthesisUtterance(last));setActionNotice('Safe action: repeated last accepted message')}}else if(label==='danger'){navigator.vibrate?.([160,80,160]);setActionNotice('Safe action: local visual/haptic danger alert')}},[r.prediction,safeActions])
  const demo=async()=>{
    const scenarios=await api<any[]>('/api/demo/scenarios');const scenario=scenarios[0]
    r.stop();r.setTranscript([]);setDemoActive(true);setDemoState('DEMO REPLAY STARTED')
    for (const e of scenario.events) {
      await new Promise(ok=>setTimeout(ok,e.delay_ms))
      setDemoState(`${e.state}${e.display_text?`: ${e.display_text}`:''}`)
      if(e.state==='ACCEPTED') r.setTranscript(prev=>[...prev,{id:crypto.randomUUID(),source:'DEMO',text:e.display_text,confidence:e.confidence,at:Date.now()} as TranscriptTurn])
    }
    setDemoState('DEMO REPLAY COMPLETE')
  }
  return <div className="page-grid">
    <section className="stack">
      <div className="hero-line"><div><span className="eyebrow">MULTIMODAL ISL INTERPRETER</span><h1>Point. Sign. Communicate.</h1><p>Hands + face + body + motion across time, with explicit uncertainty instead of forced guesses.</p></div><div className="domain-box"><label htmlFor="domain">Context</label><select id="domain" value={domain} onChange={e=>setDomain(e.target.value)}>{domains.map(d=><option key={d.id} value={d.id}>{d.label}</option>)}</select></div></div>
      {demoActive&&<div className="demo-banner" role="status"><strong>DEMO REPLAY</strong><span>{demoState}</span><button className="ghost" onClick={()=>setDemoActive(false)}>Dismiss</button></div>}
      <CameraStage {...r}/>
      <div className="control-row">
        {!r.running?<button className="primary" onClick={r.start}>Start camera</button>:<button className="danger" onClick={r.stop}>Stop camera</button>}
        <button className="secondary" onClick={r.reset}>Reset session</button>
        <button className="secondary" onClick={demo}>Run labelled demo replay</button>
        <label className="toggle"><input type="checkbox" checked={r.ttsEnabled} onChange={e=>r.setTtsEnabled(e.target.checked)}/> Speak accepted text</label>
        <label className="toggle"><input type="checkbox" checked={safeActions} onChange={e=>setSafeActions(e.target.checked)}/> Enable whitelisted in-app sign actions</label>
      </div>
      <div className="runtime-row"><span>Socket: <b>{r.socketState}</b></span><span>Perception: <b>{r.perceptionAvailable?'ready':'unavailable'}</b></span><span>Model: <b>{r.modelLoaded?'loaded':'not loaded'}</b></span><span>Tracking latency: <b>{r.landmarkLatency?`${r.landmarkLatency.toFixed(0)} ms`:'—'}</b></span></div>
      {actionNotice&&<div className="notice">{actionNotice} · No OS/shell actions are permitted.</div>}
      <StatusCard prediction={r.prediction} message={r.message}/>
    </section>
    <Transcript turns={r.transcript} onClear={r.reset}/>
  </div>
}

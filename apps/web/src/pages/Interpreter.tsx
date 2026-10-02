import { useEffect, useMemo, useState } from 'react'
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

  useEffect(()=>{
    if(!safeActions||r.prediction?.state!=='ACCEPTED'||!r.prediction.label)return
    const label=r.prediction.label
    if(label==='stop'){
      setActionNotice('Sign action: interpretation stopped')
      r.stop()
    }else if(label==='repeat'){
      const last=r.transcript.at(-1)?.text
      if(last&&'speechSynthesis'in window){
        window.speechSynthesis.speak(new SpeechSynthesisUtterance(last))
        setActionNotice('Sign action: repeated the last accepted message')
      }
    }else if(label==='danger'){
      navigator.vibrate?.([160,80,160])
      setActionNotice('Sign action: local visual/haptic danger alert')
    }
  },[r.prediction,safeActions])

  const demo=async()=>{
    try{
      const scenarios=await api<any[]>('/api/demo/scenarios')
      const scenario=scenarios[0]
      r.stop()
      r.setTranscript([])
      setDemoActive(true)
      setDemoState('Replay started')
      for (const e of scenario.events) {
        await new Promise(ok=>setTimeout(ok,e.delay_ms))
        setDemoState(`${e.state.replaceAll('_',' ')}${e.display_text?` · ${e.display_text}`:''}`)
        if(e.state==='ACCEPTED') r.setTranscript(prev=>[...prev,{
          id:crypto.randomUUID(),source:'DEMO',text:e.display_text,confidence:e.confidence,at:Date.now(),
        } as TranscriptTurn])
      }
      setDemoState('Replay complete')
    }catch{
      setDemoState('Replay needs the local API. Restart SANKET AI.')
      setDemoActive(true)
    }
  }

  const caption=useMemo(()=>{
    if(r.prediction?.state==='ACCEPTED'&&r.prediction.display_text)return r.prediction.display_text
    return ''
  },[r.prediction])

  const stageStatus=useMemo(()=>{
    if(r.backendState==='offline')return 'Recognition service offline'
    if(r.perceptionState==='unavailable')return 'Vision runtime needs setup'
    if(r.modelState==='missing')return 'Tracking ready · model needs training'
    if(r.prediction?.state==='NEED_REPEAT')return 'Please repeat the sign'
    if(r.prediction?.state==='TRACKING_LOST')return 'Move back into frame'
    if(r.prediction?.state==='NO_SIGN')return 'Ready for your next sign'
    return 'Listening for signs'
  },[r.backendState,r.perceptionState,r.modelState,r.prediction])

  return <div className="interpreter-page">
    <header className="session-header">
      <div>
        <span className="page-kicker">Live interpretation</span>
        <h1>Sign naturally. Get clear output.</h1>
        <p>Keep your upper body visible. SANKET only publishes a word when the visual evidence clears its confidence checks.</p>
      </div>
      <div className="session-header-actions">
        <HealthPill state={r.backendState}/>
        <label className="context-control">Context
          <select value={domain} onChange={e=>setDomain(e.target.value)}>
            {domains.length?domains.map(d=><option key={d.id} value={d.id}>{d.label}</option>):<option value="general">General</option>}
          </select>
        </label>
      </div>
    </header>

    {demoActive&&<div className="demo-banner" role="status"><span className="demo-dot"/> <strong>Labelled replay</strong><span>{demoState}</span><button className="text-button" onClick={()=>setDemoActive(false)}>Dismiss</button></div>}

    <div className="studio-layout">
      <section className="studio-main">
        <CameraStage
          {...r}
          statusLabel={stageStatus}
          caption={caption}
          onToggleCamera={r.running?r.stop:r.start}
          onReset={r.reset}
          onDemo={demo}
          ttsEnabled={r.ttsEnabled}
          onToggleTts={()=>r.setTtsEnabled(!r.ttsEnabled)}
        />

        <div className="studio-underbar">
          <StatusCard prediction={r.prediction} message={r.message}/>
          <section className="preference-card">
            <div>
              <span className="section-label">Session options</span>
              <strong>Assistive output</strong>
            </div>
            <label className="switch-row"><span><b>Speak accepted text</b><small>Use system text-to-speech after an accepted sign.</small></span><input type="checkbox" checked={r.ttsEnabled} onChange={e=>r.setTtsEnabled(e.target.checked)}/></label>
            <label className="switch-row"><span><b>Safe sign actions</b><small>Allow only Stop, Repeat and local Danger alerts.</small></span><input type="checkbox" checked={safeActions} onChange={e=>setSafeActions(e.target.checked)}/></label>
          </section>
        </div>

        {actionNotice&&<div className="inline-notice">{actionNotice}. No operating-system commands are allowed.</div>}
      </section>

      <aside className="studio-rail">
        <Transcript turns={r.transcript} onClear={r.reset}/>
        <section className="readiness-card">
          <div className="panel-head"><div><span className="section-label">System</span><h2>Readiness</h2></div><button className="text-button" onClick={r.reconnect}>Retry</button></div>
          <ReadinessRow label="Local API" state={r.backendState==='online'?'ready':r.backendState==='offline'?'error':'pending'} value={r.backendState==='online'?'Connected':r.backendState==='offline'?'Offline':'Checking'}/>
          <ReadinessRow label="Vision" state={r.perceptionState==='ready'?'ready':r.perceptionState==='unavailable'?'error':'pending'} value={r.perceptionState==='ready'?'MediaPipe ready':r.perceptionState==='unavailable'?'Needs setup':'Waiting for API'}/>
          <ReadinessRow label="Sign model" state={r.modelState==='loaded'?'ready':r.modelState==='missing'?'warn':'pending'} value={r.modelState==='loaded'?'Loaded':r.modelState==='missing'?'Needs training':'Waiting for API'}/>
          <ReadinessRow label="Tracking" state={r.landmarkLatency?'ready':'pending'} value={r.landmarkLatency?`${r.landmarkLatency.toFixed(0)} ms`:'—'}/>
          {r.backendState==='offline'&&<p className="readiness-help">Close this browser tab, run <code>run_dev.bat</code> from the project folder, then reopen SANKET AI.</p>}
          {r.backendState==='online'&&r.perceptionState==='unavailable'&&<p className="readiness-help">Run <code>setup_windows.bat</code> once more. The updated launcher now uses the same virtual environment where MediaPipe is installed.</p>}
          {r.perceptionState==='ready'&&r.modelState==='missing'&&<p className="readiness-help">The camera tracker is working. Use <b>Training studio</b> to record a few signs, then train the first real vocabulary.</p>}
        </section>
      </aside>
    </div>
  </div>
}

function HealthPill({state}:{state:'checking'|'online'|'offline'}){
  return <span className={`health-pill ${state}`}><i/>{state==='online'?'Service online':state==='offline'?'Service offline':'Checking service'}</span>
}

function ReadinessRow({label,state,value}:{label:string;state:'ready'|'error'|'warn'|'pending';value:string}){
  return <div className="readiness-row"><span><i className={state}/>{label}</span><strong>{value}</strong></div>
}

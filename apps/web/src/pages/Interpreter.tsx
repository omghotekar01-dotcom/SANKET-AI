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
  const [liveSigns,setLiveSigns]=useState<string[]>([])
  const [coreVocabulary,setCoreVocabulary]=useState<Array<{id:string;display:string;category:string}>>([])
  const [coreSupported,setCoreSupported]=useState<string[]>([])
  const [coreMissing,setCoreMissing]=useState<string[]>([])
  const [safeActions,setSafeActions]=useState(false)
  const [actionNotice,setActionNotice]=useState('')
  const [testTarget,setTestTarget]=useState('')
  const [testState,setTestState]=useState<'idle'|'waiting'|'passed'|'different'>('idle')
  const [testDetected,setTestDetected]=useState('')
  const [testConfidence,setTestConfidence]=useState<number|null>(null)
  const [demoActive,setDemoActive]=useState(false)
  const [demoState,setDemoState]=useState('')
  const [feedbackStatus,setFeedbackStatus]=useState('')
  const [showCorrection,setShowCorrection]=useState(false)
  const [correction,setCorrection]=useState('')
  const r=useRecognition(domain)

  useEffect(()=>{api<Array<{id:string;label:string}>>('/api/domains').then(setDomains).catch(()=>{})},[])

  useEffect(()=>{
    if(r.backendState!=='online')return
    api<any>('/api/signs')
      .then(data=>{
        const signs=Array.isArray(data.live_vocabulary)?data.live_vocabulary:[]
        setLiveSigns(signs)
        setCoreVocabulary(Array.isArray(data.core_vocabulary)?data.core_vocabulary:[])
        setCoreSupported(Array.isArray(data.core_supported)?data.core_supported:[])
        setCoreMissing(Array.isArray(data.core_missing)?data.core_missing:[])
        if(!testTarget && signs.length){
          const hello=signs.find((s:string)=>s.toLowerCase()==='hello')
          setTestTarget(hello || signs[0])
        }
      })
      .catch(()=>setLiveSigns([]))
  },[r.backendState,r.modelBackend,r.modelVocabularySize])

  useEffect(()=>{
    if(!testTarget || r.prediction?.state!=='ACCEPTED' || !r.prediction.display_text)return
    const normalize=(value:string)=>value.trim().toLowerCase().replaceAll('_',' ').replace(/\s+/g,' ')
    const detected=r.prediction.display_text
    setTestDetected(detected)
    setTestConfidence(r.prediction.confidence)
    setTestState(normalize(detected)===normalize(testTarget)?'passed':'different')
  },[r.prediction,testTarget])

  useEffect(()=>{
    if(!safeActions||r.prediction?.state!=='ACCEPTED'||!r.prediction.label)return
    const label=r.prediction.label.toLowerCase()
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


  const latestISL=[...r.transcript].reverse().find(turn=>turn.source==='ISL')
  const submitFeedback=async(accepted:boolean)=>{
    if(!latestISL)return
    const raw=latestISL.text.trim().toLowerCase().replace(/\s+/g,'_')
    const corrected=correction.trim().toLowerCase().replace(/[^a-z0-9 _-]/g,'').replace(/\s+/g,'_')
    if(!accepted&&!corrected){setFeedbackStatus('Enter the correct sign label first.');return}
    try{
      const result=await api<any>('/api/feedback',{
        method:'POST',
        body:JSON.stringify({
          utterance_id:latestISL.id,
          raw_label:raw,
          accepted,
          corrected_label:accepted?null:corrected,
          note:'live-interpreter-user-feedback',
        }),
      })
      setFeedbackStatus(result.stored?'Feedback stored locally. It does not retrain automatically.':'Feedback was not stored.')
      setShowCorrection(false);setCorrection('')
    }catch(error){
      setFeedbackStatus(error instanceof Error?error.message:String(error))
    }
  }

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
    if(r.modelState==='missing')return 'No recognition model loaded'
    if(r.prediction?.state==='NEED_REPEAT')return 'Please repeat the sign'
    if(r.prediction?.state==='TRACKING_LOST')return 'Move back into frame'
    if(r.prediction?.state==='NO_SIGN')return 'Ready for your next sign'
    if(r.modelIsBootstrap)return `Bootstrap recognizer · ${r.modelVocabularySize} signs`
    return 'Local SANKET recognizer'
  },[r.backendState,r.perceptionState,r.modelState,r.modelIsBootstrap,r.modelVocabularySize,r.prediction])

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

    {r.modelIsBootstrap&&<div className="model-provenance">
      <span className="model-provenance-badge">Bootstrap model</span>
      <span>50-word temporal ISL recognizer is active. These MIT-licensed external weights are a starting model; a SANKET-trained local model replaces them only after its held-out evaluation clears the project quality gate.</span>
    </div>}

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
            <label className="switch-row"><span><b>Safe sign actions</b><small>Allow only Stop, Repeat and local Danger alerts when those labels exist in the active model.</small></span><input type="checkbox" checked={safeActions} onChange={e=>setSafeActions(e.target.checked)}/></label>
          </section>
        </div>

        {actionNotice&&<div className="inline-notice">{actionNotice}. No operating-system commands are allowed.</div>}
      </section>

      <aside className="studio-rail">
        <Transcript turns={r.transcript} onClear={r.reset}/>

        <section className="feedback-card">
          <div><span className="section-label">Human correction</span><strong>Was the last accepted sign right?</strong></div>
          {latestISL
            ?<>
              <p>Last accepted: <b>{latestISL.text}</b>. Feedback is stored as metadata only and never changes model weights automatically.</p>
              <div className="control-row compact-controls">
                <button className="secondary" onClick={()=>void submitFeedback(true)}>Correct</button>
                <button className="secondary" onClick={()=>{setShowCorrection(v=>!v);setFeedbackStatus('')}}>Fix label</button>
              </div>
              {showCorrection&&<div className="feedback-fix-row"><input value={correction} onChange={e=>setCorrection(e.target.value)} placeholder="correct sign label"/><button className="primary" onClick={()=>void submitFeedback(false)}>Save correction</button></div>}
              {feedbackStatus&&<small>{feedbackStatus}</small>}
            </>
            :<p>Recognize a sign first; correction controls appear here after an accepted live ISL turn.</p>}
        </section>



        <section className="readiness-card">
          <div className="panel-head"><div><span className="section-label">System</span><h2>Readiness</h2></div><button className="text-button" onClick={r.reconnect}>Retry</button></div>
          <ReadinessRow label="Local API" state={r.backendState==='online'?'ready':r.backendState==='offline'?'error':'pending'} value={r.backendState==='online'?'Connected':r.backendState==='offline'?'Offline':'Checking'}/>
          <ReadinessRow label="Vision" state={r.perceptionState==='ready'?'ready':r.perceptionState==='unavailable'?'error':'pending'} value={r.perceptionState==='ready'?'Holistic ready':r.perceptionState==='unavailable'?'Needs setup':'Waiting for API'}/>
          <ReadinessRow
            label="Sign model"
            state={r.modelState==='loaded'?'ready':r.modelState==='missing'?'error':'pending'}
            value={r.modelState==='loaded'?(r.modelIsBootstrap?`Bootstrap · ${r.modelVocabularySize}`:`Local · ${r.modelVocabularySize}`):r.modelState==='missing'?'Unavailable':'Waiting for API'}
          />
          <ReadinessRow label="Tracking" state={r.landmarkLatency?'ready':'pending'} value={r.landmarkLatency?`${r.landmarkLatency.toFixed(0)} ms`:'—'}/>

          {r.backendState==='offline'&&<p className="readiness-help">Close this browser tab and double-click <code>START_SANKET.bat</code>.</p>}
          {r.backendState==='online'&&r.perceptionState==='unavailable'&&<p className="readiness-help">Double-click <code>START_SANKET.bat</code>; the launcher repairs the verified Holistic runtime automatically.</p>}
          {r.modelIsBootstrap&&<p className="readiness-help">Active source: <b>{r.modelSource}</b>. Use Training Studio when you want a project-specific recognizer trained from your own consented data.</p>}
        </section>



        <section className="core-vocabulary-card">
          <div className="panel-head">
            <div><span className="section-label">Project contract</span><h2>Core ISL vocabulary</h2></div>
            <strong className={coreMissing.length===0?'coverage-badge complete':'coverage-badge'}>
              {coreSupported.length}/{coreVocabulary.length || 21} live
            </strong>
          </div>
          <div className="core-progress" aria-label={`${coreSupported.length} of ${coreVocabulary.length || 21} required signs are live`}>
            <span style={{width:`${coreVocabulary.length?(coreSupported.length/coreVocabulary.length)*100:0}%`}}/>
          </div>
          <div className="core-sign-grid">
            {coreVocabulary.map(item=>{
              const live=coreSupported.includes(item.id)
              return <span key={item.id} className={live?'core-sign live':'core-sign missing'} title={live?'Recognizable by the active model':'Still requires verified training'}>
                <i/>{item.display}
              </span>
            })}
          </div>
          {coreMissing.length>0
            ?<p className="core-contract-note">Missing signs are shown honestly and are never treated as recognized output. Training Studio highlights them for collection.</p>
            :<p className="core-contract-note success">All 21 required project signs are backed by a live recognizer.</p>}
        </section>

        <section className="recognizer-test-card">
          <div className="panel-head">
            <div><span className="section-label">Guided test</span><h2>Recognizer test</h2></div>
            <button className="text-button" onClick={()=>{
              if(!liveSigns.length)return
              const current=Math.max(0,liveSigns.indexOf(testTarget))
              const next=liveSigns[(current+1)%liveSigns.length]
              setTestTarget(next)
              setTestState('idle')
              setTestDetected('')
              setTestConfidence(null)
            }}>Next</button>
          </div>
          <div className="recognizer-test-body">
            <label>Target sign
              <select value={testTarget} onChange={e=>{
                setTestTarget(e.target.value)
                setTestState('idle')
                setTestDetected('')
                setTestConfidence(null)
              }}>
                {liveSigns.map(sign=><option key={sign} value={sign}>{sign}</option>)}
              </select>
            </label>
            <div className="test-target">
              <span>Perform</span>
              <strong>{testTarget || '—'}</strong>
            </div>
            <button className="secondary full-width-test" disabled={!testTarget||r.modelState!=='loaded'} onClick={()=>{
              setTestState('waiting')
              setTestDetected('')
              setTestConfidence(null)
              if(!r.running)void r.start()
            }}>{r.running?'Reset test':'Start camera & test'}</button>
            {testState==='waiting'&&<div className="test-result waiting"><i/>Waiting for an accepted sign…</div>}
            {testState==='passed'&&<div className="test-result passed"><i/>PASS · {testDetected}{testConfidence!==null?` · ${Math.round(testConfidence*100)}%`:''}</div>}
            {testState==='different'&&<div className="test-result different"><i/>Detected {testDetected}{testConfidence!==null?` · ${Math.round(testConfidence*100)}%`:''}. Try {testTarget} again.</div>}
            <p className="test-help">This checks the active isolated-sign recognizer only. Hold a neutral pose briefly before and after the sign and keep your upper body visible.</p>
          </div>
        </section>

        <details className="vocabulary-card" open>
          <summary><span><span className="section-label">Active vocabulary</span><strong>{liveSigns.length} supported signs</strong></span><span className="summary-caret">⌄</span></summary>
          <div className="vocabulary-list">
            {liveSigns.length
              ?liveSigns.map(sign=><span key={sign}>{sign}</span>)
              :<p>No live vocabulary reported.</p>}
          </div>
        </details>
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

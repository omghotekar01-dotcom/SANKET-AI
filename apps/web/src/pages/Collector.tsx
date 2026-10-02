import { FormEvent, useEffect, useState } from 'react'
import { API_BASE, api } from '../lib/api'
import { useRecognition } from '../hooks/useRecognition'
import { CameraStage } from '../components/CameraStage'
import '../training.css'

const FALLBACK_CORE_SIGNS=['yes','no','help','water','pain','fire','danger','accident','stop','where','name','repeat','understand']

export function Collector(){
  const [label,setLabel]=useState('help')
  const [signer,setSigner]=useState('signer-01')
  const [consent,setConsent]=useState(false)
  const [collectorId,setCollectorId]=useState<string|null>(null)
  const [result,setResult]=useState<any>(null)
  const [training,setTraining]=useState(false)
  const [trainResult,setTrainResult]=useState<any>(null)
  const [coreMissing,setCoreMissing]=useState<string[]>(FALLBACK_CORE_SIGNS)
  const r=useRecognition('general',collectorId)

  const [clipPhrase,setClipPhrase]=useState('')
  const [clipFile,setClipFile]=useState<File|null>(null)
  const [clipVerified,setClipVerified]=useState(false)
  const [clipStatus,setClipStatus]=useState('')

  useEffect(()=>{if(collectorId && !r.running){void r.start()}},[collectorId])
  useEffect(()=>{
    if(r.backendState!=='online')return
    api<any>('/api/signs').then(data=>{
      const missing=Array.isArray(data.core_missing)?data.core_missing:[]
      setCoreMissing(missing.length?missing:FALLBACK_CORE_SIGNS)
    }).catch(()=>{})
  },[r.backendState,r.modelVocabularySize])

  const start=async(e:FormEvent)=>{
    e.preventDefault()
    setResult(null)
    try{
      const x=await api<any>('/api/collector/start',{
        method:'POST',
        body:JSON.stringify({label,signer_id:signer,consent,save_raw_video:false}),
      })
      setCollectorId(x.collector_id)
    }catch(error){
      setResult({error:error instanceof Error?error.message:String(error)})
    }
  }

  const stop=async()=>{
    r.stop()
    if(!collectorId)return
    try{
      const saved=await api<any>('/api/collector/stop',{
        method:'POST',
        body:JSON.stringify({collector_id:collectorId}),
      })
      setResult(saved)
    }catch(error){
      setResult({error:error instanceof Error?error.message:String(error)})
    }finally{
      setCollectorId(null)
    }
  }

  const train=async()=>{
    setTraining(true)
    setTrainResult(null)
    try{
      const trained=await api<any>('/api/model/train',{method:'POST'})
      setTrainResult(trained)
      await r.refreshHealth()
    }catch(error){
      setTrainResult({error:error instanceof Error?error.message:String(error)})
    }finally{
      setTraining(false)
    }
  }

  const uploadClip=async(e:FormEvent)=>{
    e.preventDefault()
    if(!clipFile||!clipPhrase.trim())return
    const form=new FormData()
    form.append('phrase',clipPhrase)
    form.append('source','team-recorded')
    form.append('license_note','Consented local recording')
    form.append('verified',String(clipVerified))
    form.append('file',clipFile)
    const res=await fetch(`${API_BASE}/api/sign-clips/register`,{method:'POST',body:form})
    setClipStatus(res.ok?'Clip saved locally':await res.text())
  }

  const evalReport=trainResult?.evaluation?.test

  return <div className="content-page">
    <div className="page-title">
      <span className="eyebrow">Training studio</span>
      <h1>Teach SANKET your demo vocabulary.</h1>
      <p>Record short consented landmark takes, then train and reload the local recognizer from this page. Raw video is not saved.</p>
    </div>

    <div className="training-layout">
      <section className="panel training-card">
        <div className="panel-head compact-head"><div><span className="section-label">Step 1</span><h2>Record a sign take</h2></div><span className={r.perceptionAvailable?'mini-status ready':'mini-status'}>{r.perceptionAvailable?'Vision ready':'Vision not ready'}</span></div>
        <form className="collector-form" onSubmit={start}>
          <label>Sign label
            <input value={label} onChange={e=>setLabel(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g,''))} pattern="[a-z0-9_-]+" disabled={Boolean(collectorId)}/>
          </label>
          <label>Signer ID
            <input value={signer} onChange={e=>setSigner(e.target.value)} disabled={Boolean(collectorId)}/>
          </label>
          <div className="suggested-signs" aria-label="Core signs that still need verified training">
            <span className="missing-signs-label">Core gaps · collect these first</span>
            {coreMissing.map(sign=><button type="button" key={sign} className={label===sign?'sign-chip selected':'sign-chip'} onClick={()=>setLabel(sign)} disabled={Boolean(collectorId)}>{sign.replaceAll('_',' ')}</button>)}
          </div>
          <label className="toggle consent-row"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)} disabled={Boolean(collectorId)}/> I have explicit consent to collect this person's landmark sample.</label>
          {!collectorId
            ?<button className="primary" disabled={!consent||!r.perceptionAvailable}>Begin take</button>
            :<button type="button" className="danger" onClick={stop}>Stop & save take</button>}
        </form>
        <div className="recording-tip"><b>Good take:</b> start neutral, perform the sign naturally, return neutral. Keep both hands and upper body visible for about 2–3 seconds.</div>
      </section>

      <section className="panel training-card">
        <div className="panel-head compact-head"><div><span className="section-label">Step 2</span><h2>Train the local model</h2></div></div>
        <p className="training-copy">For the first test, record at least 3 takes per sign. For a meaningful signer-disjoint test, use the same sign list with 3 or more people.</p>
        <button className="primary full-button" onClick={train} disabled={training||Boolean(collectorId)}>{training?'Training…':'Train model now'}</button>
        {trainResult?.loaded&&<div className="training-success"><strong>Model loaded</strong><span>{trainResult.model_version}</span>{evalReport&&<small>Test top-1 {(evalReport.top1_accuracy*100).toFixed(1)}% · Macro F1 {(evalReport.macro_f1*100).toFixed(1)}% · Coverage {(evalReport.coverage*100).toFixed(1)}%</small>}</div>}
        {trainResult?.error&&<div className="error-box training-error">{String(trainResult.error)}</div>}
      </section>
    </div>

    {collectorId&&<div className="collector-camera"><CameraStage {...r} statusLabel="Recording landmark take"/></div>}
    {result&&<div className={result.error?'error-box':'notice'}>{result.error?String(result.error):`Saved ${result.label} · ${result.frame_count} tracked frames · signer ${result.signer_id}`}</div>}

    <section className="panel wide reverse-lab">
      <div className="panel-head compact-head"><div><span className="section-label">Reverse communication</span><h2>Add a verified ISL phrase clip</h2></div></div>
      <p>Upload only a consented recording whose ISL form and meaning have been checked. Unverified uploads are stored but never presented as verified output.</p>
      <form className="collector-form" onSubmit={uploadClip}>
        <label>Phrase<input value={clipPhrase} onChange={e=>setClipPhrase(e.target.value)} placeholder="e.g. I need a doctor"/></label>
        <label>Video clip<input type="file" accept="video/webm,video/mp4" onChange={e=>setClipFile(e.target.files?.[0]||null)}/></label>
        <label className="toggle"><input type="checkbox" checked={clipVerified} onChange={e=>setClipVerified(e.target.checked)}/> ISL form/meaning has been verified by our team or reviewer.</label>
        <button className="secondary" disabled={!clipFile||!clipPhrase.trim()}>Store clip</button>
      </form>
      {clipStatus&&<div className="notice">{clipStatus}</div>}
    </section>
  </div>
}

import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Health } from '../types'

export function Diagnostics(){
  const [health,setHealth]=useState<Health|null>(null)
  const [metrics,setMetrics]=useState<any>(null)
  const [signs,setSigns]=useState<any>(null)
  const [error,setError]=useState('')

  const refresh=async()=>{
    try{
      setError('')
      const [h,m,s]=await Promise.all([
        api<Health>('/api/health'),
        api<any>('/api/metrics'),
        api<any>('/api/signs'),
      ])
      setHealth(h)
      setMetrics(m)
      setSigns(s)
    }catch(e){
      setError(String(e))
    }
  }

  const reload=async()=>{
    try{
      await api('/api/model/reload',{method:'POST'})
      await refresh()
    }catch(e){
      setError(String(e))
    }
  }

  useEffect(()=>{void refresh()},[])

  return <div className="content-page">
    <div className="page-title">
      <span className="eyebrow">Judge / developer view</span>
      <h1>Diagnostics</h1>
      <p>What is actually loaded on this machine, including whether recognition comes from external bootstrap weights or a locally trained SANKET artifact.</p>
    </div>

    <div className="diagnostic-grid">
      {health&&Object.entries(health).map(([k,v])=><article className="metric" key={k}><span>{k.replaceAll('_',' ')}</span><strong>{String(v??'—')}</strong></article>)}
    </div>

    <section className="panel wide">
      <div className="panel-head">
        <div><span className="eyebrow">Recognition model</span><h2>{health?.model_is_bootstrap?'Bootstrap model active':health?.model_loaded?'Local SANKET model active':'No model loaded'}</h2></div>
      </div>
      {health?.model_is_bootstrap&&<p className="diagnostic-note">The active 50-class BiLSTM is an MIT-licensed external bootstrap model. SANKET does not claim its training data or upstream performance as our own. Source: {health.model_source}. Exact active vocabulary: {signs?.live_vocabulary_size || 0} signs.</p>}
      {!health?.model_is_bootstrap&&health?.model_loaded&&<p className="diagnostic-note">A locally trained SANKET model is active and takes priority over the bootstrap recognizer.</p>}
    </section>

    <section className="panel wide">
      <div className="panel-head">
        <div><span className="eyebrow">Evaluation</span><h2>{metrics?.available?'SANKET-held-out evaluation':'No SANKET-held-out metric claimed'}</h2></div>
      </div>
      {metrics?.available
        ?<div className="diagnostic-grid"><Metric name="Vocabulary" value={metrics.report?.manifest?.labels?.length}/><Metric name="Split" value={metrics.report?.manifest?.split?.mode}/><Metric name="Test samples" value={metrics.report?.test?.samples}/><Metric name="Top-1" value={fmt(metrics.report?.test?.top1_accuracy)}/><Metric name="Macro F1" value={fmt(metrics.report?.test?.macro_f1)}/><Metric name="Accepted accuracy" value={fmt(metrics.report?.test?.accepted_accuracy)}/><Metric name="Coverage" value={fmt(metrics.report?.test?.coverage)}/></div>
        :<p className="diagnostic-note">{metrics?.message||'No local evaluation file is available.'}</p>}
    </section>

    {error&&<div className="error-box">{error}</div>}
    <div className="control-row"><button className="secondary" onClick={refresh}>Refresh health</button><button className="primary" onClick={reload}>Reload model</button></div>
  </div>
}

function fmt(v:any){return typeof v==='number'?`${(v*100).toFixed(1)}%`:'—'}
function Metric({name,value}:{name:string;value:any}){return <article className="metric"><span>{name}</span><strong>{String(value??'—')}</strong></article>}

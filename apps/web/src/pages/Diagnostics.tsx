import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Health } from '../types'

export function Diagnostics(){
  const [health,setHealth]=useState<Health|null>(null)
  const [metrics,setMetrics]=useState<any>(null)
  const [error,setError]=useState('')
  const refresh=async()=>{
    try{
      setError('')
      const [h,m]=await Promise.all([api<Health>('/api/health'),api<any>('/api/metrics')])
      setHealth(h);setMetrics(m)
    }catch(e){setError(String(e))}
  }
  const reload=async()=>{try{await api('/api/model/reload',{method:'POST'});await refresh()}catch(e){setError(String(e))}}
  useEffect(()=>{void refresh()},[])

  return <div className="content-page"><div className="page-title"><span className="eyebrow">JUDGE / DEVELOPER VIEW</span><h1>Diagnostics</h1><p>What is actually available on this machine—no hidden demo claims.</p></div>
    <div className="diagnostic-grid">{health&&Object.entries(health).map(([k,v])=><article className="metric" key={k}><span>{k.replaceAll('_',' ')}</span><strong>{String(v??'—')}</strong></article>)}</div>
    <section className="panel wide"><div className="panel-head"><div><span className="eyebrow">REAL EVALUATION</span><h2>{metrics?.available?'Loaded model report':'No evaluated artifact yet'}</h2></div></div>{metrics?.available?<div className="diagnostic-grid"><Metric name="Vocabulary" value={metrics.report?.manifest?.labels?.length}/><Metric name="Split" value={metrics.report?.manifest?.split?.mode}/><Metric name="Test samples" value={metrics.report?.test?.samples}/><Metric name="Top-1" value={fmt(metrics.report?.test?.top1_accuracy)}/><Metric name="Macro F1" value={fmt(metrics.report?.test?.macro_f1)}/><Metric name="Accepted accuracy" value={fmt(metrics.report?.test?.accepted_accuracy)}/><Metric name="Coverage" value={fmt(metrics.report?.test?.coverage)}/></div>:<p>{metrics?.message||'Train the landmark model first. No accuracy is displayed without a real evaluation file.'}</p>}</section>
    {error&&<div className="error-box">{error}</div>}<div className="control-row"><button className="secondary" onClick={refresh}>Refresh health</button><button className="primary" onClick={reload}>Reload model artifact</button></div>
  </div>
}
function fmt(v:any){return typeof v==='number'?`${(v*100).toFixed(1)}%`:'—'}
function Metric({name,value}:{name:string;value:any}){return <article className="metric"><span>{name}</span><strong>{String(value??'—')}</strong></article>}

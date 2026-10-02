import type { PredictionEvent } from '../types'

export function StatusCard({prediction,message}:{prediction:PredictionEvent|null;message:string}) {
  const state=prediction?.state || 'READY'
  const pct=prediction ? Math.round(prediction.confidence*100) : null
  const label=state.replaceAll('_',' ').toLowerCase()

  return <section className={`recognition-card state-${state.toLowerCase()}`} aria-live="polite" aria-atomic="true">
    <div className="recognition-card-head">
      <div><span className="section-label">Recognition</span><strong>{label.charAt(0).toUpperCase()+label.slice(1)}</strong></div>
      {pct!==null&&<span className="confidence-pill">{pct}%</span>}
    </div>
    <p>{message}</p>
    {prediction?.alternatives?.length ? <details className="alternatives-details">
      <summary>Other possible signs</summary>
      <div className="alternatives">{prediction.alternatives.map(a=><span key={a.label}>{a.label.replaceAll('_',' ')} <b>{Math.round(a.confidence*100)}%</b></span>)}</div>
    </details>:null}
  </section>
}

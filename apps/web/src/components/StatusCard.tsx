import type { PredictionEvent } from '../types'

export function StatusCard({prediction,message}:{prediction:PredictionEvent|null;message:string}) {
  const state=prediction?.state || 'READY'
  const pct=prediction ? Math.round(prediction.confidence*100) : null
  return <section className={`status-card state-${state.toLowerCase()}`} aria-live="polite" aria-atomic="true">
    <div className="eyebrow">INTERPRETATION STATE</div>
    <div className="status-row"><strong>{state.replace('_',' ')}</strong>{pct!==null&&<span>{pct}% confidence</span>}</div>
    <p>{message}</p>
    {prediction?.alternatives?.length ? <details><summary>Alternatives</summary><div className="alternatives">{prediction.alternatives.map(a=><span key={a.label}>{a.label.replace('_',' ')} {Math.round(a.confidence*100)}%</span>)}</div></details>:null}
  </section>
}

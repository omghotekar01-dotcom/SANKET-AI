import type { TranscriptTurn } from '../types'

export function Transcript({turns,onClear}:{turns:TranscriptTurn[];onClear:()=>void}) {
  return <section className="transcript-panel">
    <div className="panel-head">
      <div><span className="section-label">Conversation</span><h2>Live transcript</h2></div>
      <button className="text-button" onClick={onClear} disabled={!turns.length}>Clear</button>
    </div>
    <div className="transcript" role="log" aria-live="polite" aria-relevant="additions">
      {!turns.length && <div className="transcript-empty">
        <span className="empty-mark">“</span>
        <strong>No accepted signs yet</strong>
        <p>Only signs that pass the confidence checks appear here.</p>
      </div>}
      {turns.map(t=><article className="turn" key={t.id}>
        <div className="turn-meta"><span className="turn-source">{t.source}</span><time>{new Date(t.at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</time></div>
        <strong>{t.text}</strong>
        {t.confidence!==undefined&&<small>{Math.round(t.confidence*100)}% confidence</small>}
      </article>)}
    </div>
  </section>
}

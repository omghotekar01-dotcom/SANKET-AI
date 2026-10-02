import type { TranscriptTurn } from '../types'
export function Transcript({turns,onClear}:{turns:TranscriptTurn[];onClear:()=>void}) {
  return <section className="panel transcript-panel"><div className="panel-head"><div><span className="eyebrow">LIVE TRANSCRIPT</span><h2>Conversation</h2></div><button className="ghost" onClick={onClear}>Clear</button></div>
    <div className="transcript" role="log" aria-live="polite" aria-relevant="additions">
      {!turns.length && <div className="empty">Accepted messages will appear here. Frame-level guesses are never added.</div>}
      {turns.map(t=><article className="turn" key={t.id}><span className="turn-source">{t.source}</span><div><strong>{t.text}</strong>{t.confidence!==undefined&&<small>{Math.round(t.confidence*100)}% accepted confidence</small>}</div></article>)}
    </div>
  </section>
}

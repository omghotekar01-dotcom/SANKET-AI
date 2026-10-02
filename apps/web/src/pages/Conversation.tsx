import { FormEvent, useState } from 'react'
import { API_BASE, api } from '../lib/api'

export function Conversation(){
  const [text,setText]=useState('')
  const [result,setResult]=useState<any>(null)
  const [error,setError]=useState('')

  const submit=async(e:FormEvent)=>{
    e.preventDefault(); if(!text.trim())return
    setError('')
    try{setResult(await api('/api/translate/text-to-isl',{method:'POST',body:JSON.stringify({text})}))}
    catch(err){setError(String(err))}
  }
  const speak=()=>{
    if(!text||!('speechSynthesis'in window))return
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(text))
  }
  const listen=()=>{
    const W=window as any
    const SR=W.SpeechRecognition||W.webkitSpeechRecognition
    if(!SR){setError('Browser speech recognition is unavailable — type the message instead.');return}
    const rec=new SR(); rec.lang='en-IN'; rec.interimResults=false
    rec.onresult=(e:any)=>setText(e.results[0][0].transcript)
    rec.onerror=()=>setError('Speech recognition failed — typed input remains available.')
    rec.start()
  }

  return <div className="content-page"><div className="page-title"><span className="eyebrow">TWO-WAY COMMUNICATION</span><h1>Text / speech → verified ISL assets</h1><p>Phrase-first output. The app will not call unverified word concatenation fluent ISL.</p></div>
    <section className="panel wide"><form onSubmit={submit}><label htmlFor="reply">Message from non-signer</label><textarea id="reply" value={text} onChange={e=>setText(e.target.value)} placeholder="Type a message…"/><div className="control-row"><button className="primary">Translate to ISL</button><button type="button" className="secondary" onClick={listen}>Use speech input</button><button type="button" className="secondary" onClick={speak}>Speak typed text</button></div></form></section>
    {error&&<div className="error-box">{error}</div>}
    {result&&<section className="panel wide"><div className="panel-head"><div><span className="eyebrow">OUTPUT MODE</span><h2>{result.mode.replaceAll('_',' ')}</h2></div></div><p>{result.message}</p><div className="clip-grid">{result.items.map((i:any,idx:number)=><article className="clip-card" key={idx}><strong>{i.phrase}</strong><span>{i.mode.replaceAll('_',' ')}</span>{i.file?<video src={`${API_BASE}/sign_clips/${i.file}`} controls/>:<div className="clip-missing">Verified visual asset not bundled</div>}</article>)}</div></section>}
  </div>
}

import { FormEvent, useState } from 'react'
import { API_BASE, api } from '../lib/api'
import { inputLanguage, languageLabel, localizeSign, speakFreeText, type LanguageMode } from '../lib/language'

export function Conversation({language}:{language:LanguageMode}){
  const [text,setText]=useState('')
  const [result,setResult]=useState<any>(null)
  const [error,setError]=useState('')

  const submit=async(e:FormEvent)=>{
    e.preventDefault(); if(!text.trim())return
    setError('')
    try{
      setResult(await api('/api/translate/text-to-isl',{
        method:'POST',
        body:JSON.stringify({text,language:inputLanguage(language)}),
      }))
    }catch(err){setError(String(err))}
  }

  const listen=(locale:'en-IN'|'mr-IN')=>{
    const W=window as any
    const SR=W.SpeechRecognition||W.webkitSpeechRecognition
    if(!SR){setError('Browser speech recognition is unavailable — type the message instead.');return}
    const rec=new SR();rec.lang=locale;rec.interimResults=false
    rec.onresult=(e:any)=>setText(e.results[0][0].transcript)
    rec.onerror=()=>setError('Speech recognition failed — typed input remains available.')
    rec.start()
  }

  return <div className="content-page">
    <div className="page-title">
      <span className="eyebrow">TWO-WAY COMMUNICATION · {languageLabel(language)}</span>
      <h1>English / Marathi → verified ISL assets</h1>
      <p>English and Marathi words are mapped to the same canonical sign meaning before verified ISL lookup. Unknown words remain visibly unsupported; word concatenation is not claimed as fluent ISL grammar.</p>
    </div>
    <section className="panel wide"><form onSubmit={submit}>
      <label htmlFor="reply">Message from non-signer · English or मराठी</label>
      <textarea id="reply" value={text} onChange={e=>setText(e.target.value)} placeholder={language==='mr'?'मराठीत संदेश लिहा…':'Type in English or मराठी…'}/>
      <div className="control-row">
        <button className="primary">Translate to ISL</button>
        {language!=='mr'&&<button type="button" className="secondary" onClick={()=>listen('en-IN')}>Speak English</button>}
        {language!=='en'&&<button type="button" className="secondary" onClick={()=>listen('mr-IN')}>मराठीत बोला</button>}
        <button type="button" className="secondary" onClick={()=>speakFreeText(text,language)}>Speak typed text</button>
      </div>
    </form></section>
    {error&&<div className="error-box">{error}</div>}
    {result&&<section className="panel wide">
      <div className="panel-head"><div><span className="eyebrow">OUTPUT MODE</span><h2>{result.mode.replaceAll('_',' ')}</h2></div><span className="language-result-badge">{result.input_language==='mr'?'Marathi input':'English input'}</span></div>
      <p>{result.message}</p>
      {result.canonical_text&&result.canonical_text!==result.normalized_text&&<p className="canonical-note">Canonical ISL lookup: <b>{result.canonical_text}</b></p>}
      <div className="clip-grid">{result.items.map((i:any,idx:number)=><article className="clip-card" key={idx}>
        <strong>{localizeSign(i.phrase,language)}</strong>
        <span>{i.mode.replaceAll('_',' ')}</span>
        {i.file?<video src={`${API_BASE}/sign_clips/${i.file}`} controls/>:<div className="clip-missing">Verified visual asset not bundled</div>}
      </article>)}</div>
    </section>}
  </div>
}

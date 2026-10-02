import { useEffect, useState } from 'react'
import { Interpreter } from './pages/Interpreter'
import { Conversation } from './pages/Conversation'
import { Call } from './pages/Call'
import { Emergency } from './pages/Emergency'
import { Accessibility } from './pages/Accessibility'
import { Diagnostics } from './pages/Diagnostics'
import { Collector } from './pages/Collector'
import { languageLabel, type LanguageMode } from './lib/language'

type Page='interpret'|'conversation'|'call'|'emergency'|'accessibility'|'diagnostics'|'collect'

const PAGES:Array<{id:Page;label:string;short:string}>=[
  {id:'interpret',label:'Live interpreter',short:'LI'},
  {id:'conversation',label:'Two-way conversation',short:'TW'},
  {id:'call',label:'Video call',short:'VC'},
  {id:'emergency',label:'Emergency',short:'SOS'},
  {id:'accessibility',label:'Accessibility',short:'A11Y'},
  {id:'diagnostics',label:'System health',short:'SYS'},
  {id:'collect',label:'Training studio',short:'DATA'},
]

export default function App(){
  const [page,setPage]=useState<Page>('interpret')
  const [language,setLanguage]=useState<LanguageMode>(()=>{
    const saved=localStorage.getItem('sanket-language')
    if(saved==='en'||saved==='mr'||saved==='both')return saved
    return 'en'
  })
  useEffect(()=>localStorage.setItem('sanket-language',language),[language])

  const content={
    interpret:<Interpreter language={language}/>,
    conversation:<Conversation language={language}/>,
    call:<Call language={language}/>,
    emergency:<Emergency language={language}/>,
    accessibility:<Accessibility/>,
    diagnostics:<Diagnostics/>,
    collect:<Collector/>,
  }[page]
  const active=PAGES.find(p=>p.id===page)!

  return <div className="app-shell">
    <aside className="sidebar" aria-label="Primary navigation">
      <button className="brand" onClick={()=>setPage('interpret')} aria-label="Open SANKET AI live interpreter">
        <span className="brand-mark">S</span>
        <span className="brand-copy"><strong>SANKET</strong><small>Communication bridge</small></span>
      </button>
      <nav className="nav-list">
        {PAGES.map(p=><button key={p.id} className={page===p.id?'nav active':'nav'} onClick={()=>setPage(p.id)}>
          <span className="nav-short">{p.short}</span><span>{p.label}</span>
        </button>)}
      </nav>
      <div className="sidebar-footer"><span className="quiet-dot"/><span>Local-first prototype</span><small>Peaky Coders · Hacktopia 2026</small></div>
    </aside>

    <div className="app-main-shell">
      <header className="topbar">
        <div><span className="topbar-kicker">SANKET AI</span><strong>{active.label}</strong></div>
        <div className="topbar-actions">
          <label className="language-control" title="Communication output and speech language">
            <span>Language</span>
            <select value={language} onChange={e=>setLanguage(e.target.value as LanguageMode)} aria-label="Communication language">
              <option value="en">English</option>
              <option value="mr">मराठी</option>
              <option value="both">English + मराठी</option>
            </select>
          </label>
          <span className="language-active">{languageLabel(language)}</span>
          <div className="top-note"><span className="privacy-dot"/>Camera frames are not recorded by default</div>
        </div>
      </header>
      <main>{content}</main>
    </div>
  </div>
}

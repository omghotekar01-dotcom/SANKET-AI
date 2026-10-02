import { useState } from 'react'
import { Interpreter } from './pages/Interpreter'
import { Conversation } from './pages/Conversation'
import { Call } from './pages/Call'
import { Emergency } from './pages/Emergency'
import { Accessibility } from './pages/Accessibility'
import { Diagnostics } from './pages/Diagnostics'
import { Collector } from './pages/Collector'

type Page='interpret'|'conversation'|'call'|'emergency'|'accessibility'|'diagnostics'|'collect'
const PAGES:Array<{id:Page;label:string;icon:string}>=[{id:'interpret',label:'Interpret',icon:'◉'},{id:'conversation',label:'Conversation',icon:'↔'},{id:'call',label:'Call',icon:'▣'},{id:'emergency',label:'Emergency',icon:'!'},{id:'accessibility',label:'Accessibility',icon:'Aa'},{id:'diagnostics',label:'Diagnostics',icon:'◇'},{id:'collect',label:'Collect data',icon:'＋'}]
export default function App(){const [page,setPage]=useState<Page>('interpret');const content={interpret:<Interpreter/>,conversation:<Conversation/>,call:<Call/>,emergency:<Emergency/>,accessibility:<Accessibility/>,diagnostics:<Diagnostics/>,collect:<Collector/>}[page]
 return <div className="app-shell"><header className="topbar"><button className="brand" onClick={()=>setPage('interpret')}><span className="brand-mark">S</span><span><strong>SANKET AI</strong><small>PEAKY CODERS · HACKTOPIA 2026</small></span></button><div className="top-note">Local-first · Confidence-aware · Multimodal ISL</div></header><aside className="sidebar" aria-label="Primary navigation">{PAGES.map(p=><button key={p.id} className={page===p.id?'nav active':'nav'} onClick={()=>setPage(p.id)}><span>{p.icon}</span>{p.label}</button>)}</aside><main>{content}</main></div>}

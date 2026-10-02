import { useEffect, useRef, useState } from 'react'

const ITEMS=['HELP','DOCTOR','POLICE','FIRE','ACCIDENT','DANGER','WATER','PAIN']

type SoundClass='QUIET'|'LOUD_SOUND'|'ALARM_LIKE_TONE'

function classifySound(time:Uint8Array, freq:Uint8Array):{kind:SoundClass;score:number}{
  let energy=0
  for(const x of time){const centered=(x-128)/128;energy+=centered*centered}
  const rms=Math.sqrt(energy/Math.max(time.length,1))
  if(rms<0.075)return {kind:'QUIET',score:Math.min(1,rms/0.075)}

  let total=0,peak=0
  for(const x of freq){total+=x;peak=Math.max(peak,x)}
  const average=total/Math.max(freq.length,1)
  const tonal=average>0?peak/average:0
  if(rms>0.10&&peak>175&&tonal>2.15){
    return {kind:'ALARM_LIKE_TONE',score:Math.min(1,(rms/0.20+peak/255+tonal/4)/3)}
  }
  return {kind:'LOUD_SOUND',score:Math.min(1,rms/0.25)}
}

export function Emergency(){
  const [monitoring,setMonitoring]=useState(false)
  const [soundState,setSoundState]=useState<SoundClass>('QUIET')
  const [soundScore,setSoundScore]=useState(0)
  const [soundError,setSoundError]=useState('')
  const [lastAlert,setLastAlert]=useState('')
  const audio=useRef<AudioContext|null>(null)
  const analyser=useRef<AnalyserNode|null>(null)
  const microphone=useRef<MediaStream|null>(null)
  const raf=useRef<number|null>(null)
  const streak=useRef(0)
  const lastVibrate=useRef(0)

  const activate=(text:string)=>{
    if('speechSynthesis'in window)window.speechSynthesis.speak(new SpeechSynthesisUtterance(text))
    navigator.vibrate?.([120,70,120])
  }

  const publish=(kind:SoundClass,score:number)=>{
    setSoundState(kind);setSoundScore(score)
    if(kind==='ALARM_LIKE_TONE'){
      streak.current+=1
      if(streak.current>=8){
        setLastAlert('Alarm-like sustained tone detected locally')
        const now=Date.now()
        if(now-lastVibrate.current>3500){navigator.vibrate?.([220,90,220,90,220]);lastVibrate.current=now}
      }
    }else streak.current=0
  }

  const sample=()=>{
    const node=analyser.current
    if(!node)return
    const time=new Uint8Array(node.fftSize)
    const freq=new Uint8Array(node.frequencyBinCount)
    node.getByteTimeDomainData(time);node.getByteFrequencyData(freq)
    const result=classifySound(time,freq)
    publish(result.kind,result.score)
    raf.current=requestAnimationFrame(sample)
  }

  const stopMonitor=()=>{
    if(raf.current!==null)cancelAnimationFrame(raf.current)
    raf.current=null
    microphone.current?.getTracks().forEach(t=>t.stop());microphone.current=null
    void audio.current?.close();audio.current=null;analyser.current=null
    setMonitoring(false);streak.current=0
  }

  useEffect(()=>stopMonitor,[])

  const startMonitor=async()=>{
    stopMonitor();setSoundError('');setLastAlert('')
    try{
      const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false})
      const ctx=new AudioContext()
      const node=ctx.createAnalyser();node.fftSize=1024;node.smoothingTimeConstant=.72
      ctx.createMediaStreamSource(stream).connect(node)
      microphone.current=stream;audio.current=ctx;analyser.current=node
      setMonitoring(true);sample()
    }catch(error){
      setSoundError(error instanceof Error?error.message:'Microphone unavailable')
      stopMonitor()
    }
  }

  const selfTest=async()=>{
    setSoundError('');setLastAlert('')
    let ctx=audio.current
    let node=analyser.current
    let temporary=false
    if(!ctx||!node){
      ctx=new AudioContext();node=ctx.createAnalyser();node.fftSize=1024;node.smoothingTimeConstant=.55
      audio.current=ctx;analyser.current=node;temporary=true
      setMonitoring(true);sample()
    }
    const osc=ctx.createOscillator();osc.frequency.value=1040;osc.type='sine'
    osc.connect(node);osc.start()
    await new Promise(ok=>setTimeout(ok,1100))
    osc.stop();osc.disconnect()
    if(temporary){
      await new Promise(ok=>setTimeout(ok,250))
      stopMonitor()
    }
  }

  return <div className="content-page emergency-page">
    <div className="page-title"><span className="eyebrow">ASSISTIVE COMMUNICATION</span><h1>Emergency communication</h1><p>This interface helps communicate urgent needs. It does not dispatch or replace emergency services.</p></div>
    <div className="emergency-grid">{ITEMS.map(i=><button key={i} onClick={()=>activate(i)}><span>{i==='HELP'?'!':'●'}</span>{i}</button>)}</div>

    <section className="panel wide sound-alert-card" aria-live="polite">
      <div className="panel-head"><div><span className="section-label">Environmental sound awareness</span><h2>Local alarm-like sound alert</h2></div><span className={monitoring?'mini-status ready':'mini-status'}>{monitoring?'Listening locally':'Off'}</span></div>
      <p className="diagnostic-note">Experimental assistive classifier. It uses Web Audio FFT/time-domain features in this browser and never records or uploads microphone audio. It can confuse other loud tonal sounds with alarms, so do not use it as a safety-certified detector.</p>
      <div className="sound-meter-row">
        <div><span>Current class</span><strong>{soundState.replaceAll('_',' ')}</strong></div>
        <div><span>Classifier score</span><strong>{Math.round(soundScore*100)}%</strong></div>
        <div className={lastAlert?'sound-alert-live':''}><span>Visual alert</span><strong>{lastAlert||'No alert'}</strong></div>
      </div>
      <div className="control-row">
        {!monitoring?<button className="primary" onClick={startMonitor}>Start microphone monitor</button>:<button className="danger" onClick={stopMonitor}>Stop monitor</button>}
        <button className="secondary" onClick={selfTest}>Run classifier self-test</button>
      </div>
      {soundError&&<div className="error-box">{soundError}</div>}
    </section>

    <div className="notice">No external emergency call is sent by these buttons or sound alerts. Use local emergency services separately when required.</div>
  </div>
}

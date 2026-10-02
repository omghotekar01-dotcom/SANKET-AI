export type LanguageMode='en'|'mr'|'both'

type Entry={en:string;mr:string}

const LEXICON:Record<string,Entry>={
  'brother':{en:'Brother',mr:'भाऊ'},
  'deaf':{en:'Deaf',mr:'कर्णबधिर'},
  'doctor':{en:'Doctor',mr:'डॉक्टर'},
  'dream':{en:'Dream',mr:'स्वप्न'},
  'exercise':{en:'Exercise',mr:'व्यायाम'},
  'family':{en:'Family',mr:'कुटुंब'},
  'father':{en:'Father',mr:'वडील'},
  'friend':{en:'Friend',mr:'मित्र'},
  'good morning':{en:'Good morning',mr:'शुभ सकाळ'},
  'hello':{en:'Hello',mr:'नमस्कार'},
  'hospital':{en:'Hospital',mr:'रुग्णालय'},
  'house':{en:'House',mr:'घर'},
  'how are you':{en:'How are you?',mr:'तुम्ही कसे आहात?'},
  'i':{en:'I',mr:'मी'},
  'man':{en:'Man',mr:'पुरुष'},
  'medicine':{en:'Medicine',mr:'औषध'},
  'morning':{en:'Morning',mr:'सकाळ'},
  'mother':{en:'Mother',mr:'आई'},
  'night':{en:'Night',mr:'रात्र'},
  'patient':{en:'Patient',mr:'रुग्ण'},
  'police':{en:'Police',mr:'पोलीस'},
  'school':{en:'School',mr:'शाळा'},
  'sign':{en:'Sign',mr:'संकेत'},
  'sister':{en:'Sister',mr:'बहीण'},
  'sport':{en:'Sport',mr:'खेळ'},
  'student':{en:'Student',mr:'विद्यार्थी'},
  'teacher':{en:'Teacher',mr:'शिक्षक'},
  'thank you':{en:'Thank you',mr:'धन्यवाद'},
  'time':{en:'Time',mr:'वेळ'},
  'today':{en:'Today',mr:'आज'},
  'tomorrow':{en:'Tomorrow',mr:'उद्या'},
  'woman':{en:'Woman',mr:'स्त्री'},
  'yesterday':{en:'Yesterday',mr:'काल'},
  'alive':{en:'Alive',mr:'जिवंत'},
  'bad':{en:'Bad',mr:'वाईट'},
  'good':{en:'Good',mr:'चांगले'},
  'happy':{en:'Happy',mr:'आनंदी'},
  'he':{en:'He',mr:'तो'},
  'healthy':{en:'Healthy',mr:'निरोगी'},
  'it':{en:'It',mr:'ते'},
  'old':{en:'Old',mr:'वृद्ध'},
  'sad':{en:'Sad',mr:'दुःखी'},
  'she':{en:'She',mr:'ती'},
  'sick':{en:'Sick',mr:'आजारी'},
  'strong':{en:'Strong',mr:'मजबूत'},
  'they':{en:'They',mr:'ते'},
  'we':{en:'We',mr:'आम्ही'},
  'weak':{en:'Weak',mr:'कमकुवत'},
  'you':{en:'You',mr:'तुम्ही'},
  'young':{en:'Young',mr:'तरुण'},
  'yes':{en:'Yes',mr:'हो'},
  'no':{en:'No',mr:'नाही'},
  'help':{en:'Help',mr:'मदत'},
  'water':{en:'Water',mr:'पाणी'},
  'pain':{en:'Pain',mr:'वेदना'},
  'fire':{en:'Fire',mr:'आग'},
  'danger':{en:'Danger',mr:'धोका'},
  'accident':{en:'Accident',mr:'अपघात'},
  'stop':{en:'Stop',mr:'थांबा'},
  'where':{en:'Where',mr:'कुठे'},
  'name':{en:'Name',mr:'नाव'},
  'repeat':{en:'Repeat',mr:'पुन्हा करा'},
  'understand':{en:'Understand',mr:'समजले'},
}

export function signKey(value:string){
  return value.trim().toLowerCase().replaceAll('_',' ').replace(/\s+/g,' ')
}

export function localizeSign(value:string,mode:LanguageMode){
  const key=signKey(value)
  const entry=LEXICON[key]
  const en=entry?.en || value.replaceAll('_',' ')
  const mr=entry?.mr
  if(mode==='en')return en
  if(mode==='mr')return mr || en
  return mr?'${en} · ${mr}':en
}

export function speechItems(value:string,mode:LanguageMode){
  const key=signKey(value),entry=LEXICON[key]
  const en=entry?.en || value.replaceAll('_',' ')
  const mr=entry?.mr
  if(mode==='en')return [{text:en,lang:'en-IN'}]
  if(mode==='mr')return [{text:mr||en,lang:mr?'mr-IN':'en-IN'}]
  return mr?[{text:en,lang:'en-IN'},{text:mr,lang:'mr-IN'}]:[{text:en,lang:'en-IN'}]
}

export function speakSign(value:string,mode:LanguageMode){
  if(!('speechSynthesis'in window))return
  window.speechSynthesis.cancel()
  for(const item of speechItems(value,mode)){
    const utterance=new SpeechSynthesisUtterance(item.text)
    utterance.lang=item.lang
    utterance.rate=item.lang==='mr-IN'?0.92:0.96
    window.speechSynthesis.speak(utterance)
  }
}

export function speakFreeText(value:string,preferred:LanguageMode){
  if(!value.trim()||!('speechSynthesis'in window))return
  window.speechSynthesis.cancel()
  const hasMarathi=/[\u0900-\u097F]/.test(value)
  const utterance=new SpeechSynthesisUtterance(value)
  utterance.lang=hasMarathi||preferred==='mr'?'mr-IN':'en-IN'
  utterance.rate=utterance.lang==='mr-IN'?0.92:0.96
  window.speechSynthesis.speak(utterance)
}

export function languageLabel(mode:LanguageMode){
  return mode==='en'?'English':mode==='mr'?'मराठी':'English + मराठी'
}

export function inputLanguage(mode:LanguageMode):'en'|'mr'|'auto'{
  return mode==='both'?'auto':mode
}

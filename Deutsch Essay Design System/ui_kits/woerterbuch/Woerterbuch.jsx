/* global React */
const { useState, useRef, useLayoutEffect } = React;

// Pull primitives from the compiled design-system bundle.
const DS = window.DeutschEssayDesignSystem_3bc91c;
const { TopBar, Chip, SearchField, WordRow, LevelTag } = DS;

const BRUSH_BASE = '../../assets/brushes/';

/* ---- a small slice of the real dictionary data ---- */
const WORDS = [
  { art:'die', de:'Abhängigkeit', ru:'зависимость', pos:'noun', cat:'Technologie', level:'B1', genus:'Femininum', ipa:'[ˈapˌhɛŋɪçkaɪt]',
    def:'Ein Zustand, in dem jemand oder etwas von etwas anderem bestimmt oder benötigt wird.',
    pull:'Die Abhängigkeit von fossilen Brennstoffen ist eine globale Herausforderung.',
    rule:'von + Dativ', ruleEx:'die Abhängigkeit von der Technik',
    examples:[['Die Abhängigkeit von Technologie nimmt ständig zu.','Зависимость от технологий постоянно растёт.'],
              ['Eine starke Abhängigkeit von einem Anbieter ist riskant.','Сильная зависимость от поставщика рискованна.']] },
  { art:'der', de:'Algorithmus', ru:'алгоритм', pos:'noun', cat:'Technologie', level:'B2', genus:'Maskulinum', ipa:'[alɡoˈrɪtmʊs]',
    def:'Eine eindeutige Handlungsvorschrift zur Lösung eines Problems.',
    pull:'Ein guter Algorithmus spart Zeit und Ressourcen.',
    rule:'für + Akkusativ', ruleEx:'ein Algorithmus für die Suche',
    examples:[['Der Algorithmus entscheidet, was zuerst angezeigt wird.','Алгоритм решает, что показывается первым.'],
              ['Ein effizienter Algorithmus verarbeitet Millionen Daten.','Эффективный алгоритм обрабатывает миллионы данных.']] },
  { art:'die', de:'Auswirkung', ru:'последствие, влияние', pos:'noun', cat:'Technologie', level:'B1', genus:'Femininum', ipa:'[ˈaʊsˌvɪrkʊŋ]',
    def:'Eine Folge oder ein Effekt, der aus einer Handlung entsteht.',
    pull:'Die Auswirkungen des Klimawandels sind weltweit spürbar.',
    rule:'auf + Akkusativ', ruleEx:'die Auswirkung auf die Umwelt',
    examples:[['Jede Entscheidung hat eine Auswirkung auf die Zukunft.','Каждое решение влияет на будущее.']] },
  { de:'analysieren', ru:'анализировать', pos:'verb', cat:'Wissenschaft', level:'B2', genus:'Verb', ipa:'[analyˈziːʁən]',
    def:'Etwas systematisch und gründlich untersuchen, um es zu verstehen.',
    pull:'Wer Daten klug analysiert, trifft bessere Entscheidungen.',
    rule:'+ Akkusativ', ruleEx:'die Daten genau analysieren',
    examples:[['Wir müssen die Ergebnisse genau analysieren.','Нам нужно тщательно проанализировать результаты.']] },
  { art:'der', de:'Fortschritt', ru:'прогресс', pos:'noun', cat:'Wissenschaft', level:'B1', genus:'Maskulinum', ipa:'[ˈfɔʁtʃʁɪt]',
    def:'Eine positive Entwicklung hin zu einem besseren Zustand.',
    pull:'Wissenschaftlicher Fortschritt verbessert unser Leben.',
    rule:'bei / in + Dativ', ruleEx:'Fortschritte bei der Arbeit',
    examples:[['Der Fortschritt in der Medizin rettet Leben.','Прогресс в медицине спасает жизни.']] },
  { de:'nachhaltig', ru:'устойчивый, экологичный', pos:'adj', cat:'Umwelt', level:'C1', genus:'Adjektiv', ipa:'[ˈnaːxˌhaltɪç]',
    def:'So gestaltet, dass Ressourcen geschont und für künftige Generationen erhalten bleiben.',
    pull:'Nachhaltiges Handeln ist eine Investition in die Zukunft.',
    rule:'mit + Dativ', ruleEx:'nachhaltig mit Ressourcen umgehen',
    examples:[['Wir setzen auf nachhaltige Energiequellen.','Мы делаем ставку на устойчивые источники.']] },
  { art:'die', de:'Gesellschaft', ru:'общество', pos:'noun', cat:'Gesellschaft', level:'B1', genus:'Femininum', ipa:'[ɡəˈzɛlʃaft]',
    def:'Die Gesamtheit der Menschen, die zusammenleben und durch Normen verbunden sind.',
    pull:'Eine offene Gesellschaft schätzt Vielfalt.',
    rule:'in + Dativ', ruleEx:'in der Gesellschaft leben',
    examples:[['Die Gesellschaft steht vor großen Veränderungen.','Общество стоит перед большими изменениями.']] },
  { art:'die', de:'Nachhaltigkeit', ru:'устойчивость', pos:'noun', cat:'Umwelt', level:'C1', genus:'Femininum', ipa:'[ˈnaːxˌhaltɪçkaɪt]',
    def:'Ein Prinzip, bei dem Ressourcen so genutzt werden, dass sie erhalten bleiben.',
    pull:'Nachhaltigkeit ist kein Trend, sondern eine Notwendigkeit.',
    rule:'in + Dativ', ruleEx:'Nachhaltigkeit in der Wirtschaft',
    examples:[['Nachhaltigkeit sollte im Zentrum jeder Entscheidung stehen.','Устойчивость должна быть в центре решений.']] },
  { art:'die', de:'Verantwortung', ru:'ответственность', pos:'noun', cat:'Gesellschaft', level:'B2', genus:'Femininum', ipa:'[fɛɐ̯ˈʔantvɔʁtʊŋ]',
    def:'Die Pflicht, für die Folgen des eigenen Handelns einzustehen.',
    pull:'Mit Freiheit wächst die Verantwortung.',
    rule:'für + Akkusativ', ruleEx:'die Verantwortung für das Team',
    examples:[['Jeder trägt Verantwortung für die Umwelt.','Каждый несёт ответственность за среду.']] },
  { art:'die', de:'Herausforderung', ru:'вызов', pos:'noun', cat:'Gesellschaft', level:'B2', genus:'Femininum', ipa:'[hɛˈʁaʊsfɔʁdəʁʊŋ]',
    def:'Eine schwierige Aufgabe, die besondere Anstrengung verlangt.',
    pull:'Jede Herausforderung ist eine Chance zu wachsen.',
    rule:'für + Akkusativ', ruleEx:'eine Herausforderung für die Gesellschaft',
    examples:[['Der Klimawandel ist eine globale Herausforderung.','Изменение климата — глобальный вызов.']] },
  { de:'wesentlich', ru:'существенный, важный', pos:'adj', cat:'Wissenschaft', level:'B2', genus:'Adjektiv', ipa:'[ˈveːzn̩tlɪç]',
    def:'Von grundlegender Bedeutung; entscheidend für das Ganze.',
    pull:'Das Wesentliche bleibt dem Auge oft verborgen.',
    rule:'für + Akkusativ', ruleEx:'wesentlich für den Erfolg',
    examples:[['Das ist ein wesentlicher Unterschied.','Это существенное различие.']] },
  { art:'der', de:'Zusammenhang', ru:'взаимосвязь, контекст', pos:'noun', cat:'Wissenschaft', level:'C1', genus:'Maskulinum', ipa:'[t͡suˈzamənhaŋ]',
    def:'Die innere Beziehung zwischen mehreren Dingen oder Ereignissen.',
    pull:'Erst im Zusammenhang ergibt alles einen Sinn.',
    rule:'zwischen + Dativ', ruleEx:'der Zusammenhang zwischen Ursache und Wirkung',
    examples:[['Es gibt einen klaren Zusammenhang zwischen beiden.','Между обоими есть чёткая взаимосвязь.']] },
];

const CATS = ['Alle', 'Technologie', 'Gesellschaft', 'Wissenschaft', 'Umwelt'];
const LVL = { B1:{ n:22, c:'var(--rose)' }, B2:{ n:47, c:'var(--blue)' }, C1:{ n:20, c:'var(--lav)' } };
const TOTAL = 89;

function posLabel(w){ return w.pos==='verb'?'Verb':(w.pos==='adj'?'Adjektiv':'Substantiv'); }

/* ---------- distribution donut ---------- */
function Donut(){
  const order=['B1','B2','C1']; const C=2*Math.PI*46; let off=0;
  const segs=order.map(lv=>{ const len=LVL[lv].n/TOTAL*C; const el=(
    <circle key={lv} r="46" cx="60" cy="60" fill="none" stroke={LVL[lv].c} strokeWidth="14"
      strokeDasharray={`${len.toFixed(2)} ${(C-len).toFixed(2)}`} strokeDashoffset={(-off).toFixed(2)} />); off+=len; return el; });
  return (
    <div style={{ position:'relative', width:150, height:150, margin:'6px auto 0' }}>
      <svg viewBox="0 0 120 120" style={{ width:'100%', height:'100%' }}><g transform="rotate(-90 60 60)">{segs}</g></svg>
      <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}>
        <b style={{ fontFamily:'var(--font-serif)', fontSize:36, fontWeight:600, color:'var(--ink)', lineHeight:1 }}>{TOTAL}</b>
        <span style={{ fontSize:8, letterSpacing:'2px', textTransform:'uppercase', color:'var(--muted)', marginTop:3 }}>Wörter</span>
      </div>
    </div>
  );
}

/* ---------- detail sheet ---------- */
function DetailSheet({ w, onClose }){
  return (
    <section style={{ position:'relative', overflow:'hidden', background:'var(--card)', border:'1px solid var(--hair)',
      borderRadius:'var(--radius-xl)', boxShadow:'var(--shadow-sheet)' }}>
      <button onClick={onClose} aria-label="Schließen" style={{ position:'absolute', top:16, right:16, zIndex:5, width:34, height:34,
        borderRadius:'var(--radius-pill)', display:'flex', alignItems:'center', justifyContent:'center', background:'var(--card)',
        border:'1px solid var(--hair)', color:'var(--ink-soft)', cursor:'pointer' }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
      <div style={{ background:'var(--card)', borderBottom:'1px solid var(--hair)', borderRadius:'18px 18px 0 0', padding:'34px 50px 30px', textAlign:'center' }}>
        <div style={{ display:'flex', justifyContent:'center', alignItems:'center', gap:10, marginBottom:18 }}>
          <span style={{ fontSize:11.5, letterSpacing:'.2em', textTransform:'uppercase', color:'var(--ink-soft)', fontWeight:600 }}>
            <span style={{ color:'var(--ink)', fontWeight:700 }}>{posLabel(w)}</span> · {w.cat}</span>
          <LevelTag level={w.level} tinted />
        </div>
        <div style={{ fontFamily:'var(--font-serif)', fontSize:54, fontWeight:600, lineHeight:1, letterSpacing:'-.5px', color:'var(--ink)', marginBottom:12 }}>
          {w.art ? <span style={{ color:'var(--ink-soft)' }}>{w.art} </span> : null}{w.de}</div>
        <div style={{ display:'flex', justifyContent:'center', alignItems:'center', gap:16, marginBottom:14 }}>
          <span style={{ fontFamily:'var(--font-mono)', fontSize:14.5, color:'var(--ink-soft)' }}>{w.ipa}</span>
          <button style={{ display:'inline-flex', alignItems:'center', gap:6, background:'none', border:0, cursor:'pointer', color:'var(--rose)', fontSize:13, fontWeight:600 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M5 9v6h4l5 5V4L9 9H5z"/><path fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>
            Aussprache</button>
        </div>
        <div style={{ fontFamily:'var(--font-serif)', fontStyle:'italic', fontSize:28, lineHeight:1.2, color:'var(--ink-soft)' }}>{w.ru}</div>
      </div>
      <div style={{ padding:'30px 38px 34px' }}>
        <Lab>Bedeutung</Lab>
        <p style={{ fontSize:17, lineHeight:1.7, color:'var(--ink)', margin:'0 auto', maxWidth:'42ch', textAlign:'center' }}>{w.def}</p>
        <blockquote style={{ fontFamily:'var(--font-serif)', fontStyle:'italic', fontSize:20, lineHeight:1.5, color:'var(--ink-soft)', textAlign:'center', maxWidth:'40ch', margin:'18px auto 0' }}>
          <span style={{ display:'block', fontSize:40, lineHeight:0, color:'var(--rose)', opacity:.55, margin:'0 auto 16px' }}>“</span>{w.pull}</blockquote>

        <div style={{ marginTop:34 }}><Lab>Grammatik</Lab>
          <div style={{ display:'flex', justifyContent:'center', flexWrap:'wrap', marginBottom:28 }}>
            <Param k="Genus" v={w.genus} />
            <Param k="Wortart" v={posLabel(w)} border />
          </div>
          <div style={{ position:'relative', textAlign:'center', border:'1px solid var(--rose-soft)', borderRadius:'var(--radius-lg)', padding:'22px 26px',
            background:`linear-gradient(0deg, rgba(255,255,255,.40), rgba(255,255,255,.40)), url('../../assets/images/Verwendung.png') center/cover no-repeat` }}>
            <span style={{ display:'block', fontSize:10, letterSpacing:'.24em', textTransform:'uppercase', color:'var(--rose)', fontWeight:700, marginBottom:11 }}>Verwendung</span>
            <span style={{ display:'block', fontFamily:'var(--font-serif)', fontSize:31, fontWeight:600, color:'var(--ink)', lineHeight:1.04 }}>{w.rule}</span>
            <span style={{ display:'block', fontFamily:'var(--font-serif)', fontStyle:'italic', fontSize:17, color:'var(--ink-soft)', marginTop:9 }}>{w.ruleEx}</span>
          </div>
        </div>

        <div style={{ marginTop:34 }}><Lab>Beispiele</Lab>
          <div style={{ display:'flex', flexDirection:'column', gap:26 }}>
            {w.examples.map((ex,i)=>(
              <div key={i} style={{ display:'flex', gap:18, alignItems:'baseline' }}>
                <span style={{ flex:'none', width:24, fontFamily:'var(--font-serif)', fontSize:18, fontWeight:600, color:'var(--rose)' }}>{String(i+1).padStart(2,'0')}</span>
                <div style={{ flex:1, minWidth:0 }}>
                  <p style={{ margin:0, fontSize:15.5, lineHeight:1.6, color:'var(--ink)' }}>{ex[0]}</p>
                  <p style={{ margin:'7px 0 0', fontSize:14, lineHeight:1.55, color:'var(--ink-soft)', fontStyle:'italic' }}>{ex[1]}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
function Lab({ children }){
  return (<div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:14, fontSize:11, letterSpacing:'.24em',
    textTransform:'uppercase', color:'var(--ink-soft)', fontWeight:700, margin:'0 0 24px' }}>
    <span style={{ height:1, width:40, background:'var(--hair)' }} />{children}<span style={{ height:1, width:40, background:'var(--hair)' }} /></div>);
}
function Param({ k, v, border }){
  return (<div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:4, padding:'2px 24px', textAlign:'center',
    borderLeft: border ? '1px solid var(--hair)' : 'none' }}>
    <span style={{ fontSize:9.5, letterSpacing:'.14em', textTransform:'uppercase', color:'var(--ink-soft)', fontWeight:600 }}>{k}</span>
    <b style={{ fontSize:15.5, color:'var(--ink)', fontWeight:600 }}>{v}</b></div>);
}

/* ---------- the screen ---------- */
function Woerterbuch(){
  const [cat, setCat] = useState('Alle');
  const [q, setQ] = useState('');
  const [openIdx, setOpenIdx] = useState(-1);
  const open = openIdx >= 0;

  const filtered = WORDS.map((w,i)=>({ w, i })).filter(({ w })=>{
    const c = cat==='Alle' || w.cat===cat;
    const s = !q || w.de.toLowerCase().includes(q.toLowerCase()) || (w.ru||'').toLowerCase().includes(q.toLowerCase());
    return c && s;
  });

  return (
    <div>
      <TopBar items={[
        { label:'Dashboard' }, { label:'Schreiben' },
        { label:'Lernen', dropdown:true, active:true }, { label:'Verlauf' }, { label:'Pipeline' },
      ]} />

      {/* fixed left furniture */}
      <div className="bg-column" aria-hidden="true" />
      <div className="side-label">WÖRTERBUCH</div>

      <main style={{ position:'relative', zIndex:2, display: open ? 'grid' : 'block',
        gridTemplateColumns: open ? 'minmax(340px,1fr) minmax(420px,560px)' : 'none', gap:48,
        padding:'18px 244px 90px 100px' }}>
        <section>
          <div style={{ fontSize:11, letterSpacing:'.22em', color:'var(--rose)', fontWeight:600, textTransform:'uppercase', marginBottom:10 }}>Lernen</div>
          <h1 style={{ fontFamily:'var(--font-serif)', fontSize:76, fontWeight:600, lineHeight:.98, letterSpacing:'-.5px', margin:'0 0 14px', color:'var(--ink)' }}>Wörterbuch</h1>
          <p style={{ fontSize:14.5, color:'var(--ink-soft)', lineHeight:1.6, maxWidth:460, margin:0 }}>
            Ihr thematischer Wortschatz für präzises Deutsch. Wählen Sie ein Wort, um Bedeutung, Grammatik und Beispiele zu sehen.</p>

          <div style={{ margin:'28px 0 20px' }}>
            <SearchField value={q} onChange={e=>setQ(e.target.value)} placeholder="Suche nach Begriff oder Übersetzung (z. B. „Fortschritt“)" />
          </div>

          <div style={{ display:'flex', gap:9, flexWrap:'wrap', marginBottom:18 }}>
            {CATS.map(c=>(<Chip key={c} active={cat===c} onClick={()=>{ setCat(c); setOpenIdx(-1); }}>{c==='Alle'?`Alle · ${WORDS.length}`:c}</Chip>))}
          </div>

          <div style={{ display:'grid', gridTemplateColumns: open ? '1fr' : 'repeat(2,minmax(0,1fr))', gap:'10px 30px' }}>
            {filtered.map(({ w, i })=>(
              <WordRow key={i} {...w} active={i===openIdx} brushBase={BRUSH_BASE} onClick={()=>setOpenIdx(i)} />
            ))}
          </div>
        </section>

        {open ? (
          <section style={{ position:'sticky', top:90, alignSelf:'start' }}>
            <DetailSheet w={WORDS[openIdx]} onClose={()=>setOpenIdx(-1)} />
          </section>
        ) : null}
      </main>

      {/* fixed right rail */}
      <aside className="rail">
        <div>
          <div style={{ fontSize:9.5, letterSpacing:'2.5px', textTransform:'uppercase', color:'var(--muted)', textAlign:'center', fontWeight:600 }}>Verteilung nach Niveau</div>
          <Donut />
          <div style={{ display:'flex', flexDirection:'column', gap:10, marginTop:14 }}>
            {['B1','B2','C1'].map(lv=>(
              <div key={lv} style={{ display:'flex', alignItems:'center', gap:10, fontSize:12.5, padding:'4px 6px', borderRadius:9 }}>
                <span style={{ width:10, height:10, borderRadius:3, background:LVL[lv].c }} />
                <span style={{ fontWeight:600, color:'var(--ink-soft)', letterSpacing:'.3px' }}>{lv}</span>
                <span style={{ marginLeft:'auto', color:'var(--muted)' }}>{LVL[lv].n} Wörter</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ height:1, background:'var(--hair)' }} />
        <div style={{ textAlign:'center' }}>
          <b style={{ fontFamily:'var(--font-serif)', fontSize:32, fontWeight:600, color:'var(--ink)' }}>{TOTAL}</b>
          <span style={{ display:'block', fontSize:9, letterSpacing:'2px', textTransform:'uppercase', color:'var(--muted)', marginTop:5 }}>Wörter gelernt</span>
        </div>
        <div style={{ height:1, background:'var(--hair)' }} />
        <div style={{ fontFamily:'var(--font-serif)', fontStyle:'italic', fontSize:14, lineHeight:1.55, color:'var(--ink-soft)', textAlign:'center' }}>
          Die Grenzen meiner Sprache bedeuten die Grenzen meiner Welt.
          <span style={{ display:'block', marginTop:9, fontSize:8, fontStyle:'normal', letterSpacing:'2px', color:'var(--rose)', textTransform:'uppercase', fontFamily:'var(--font-sans)', fontWeight:700 }}>Wittgenstein</span>
        </div>
      </aside>
    </div>
  );
}

window.Woerterbuch = Woerterbuch;

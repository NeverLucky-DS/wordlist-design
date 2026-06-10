/* global React */
const { useState } = React;

const DS = window.DeutschEssayDesignSystem_3bc91c;
const { TopBar, Button, IconButton, Select, ProgressBar, ToolCard, SearchField, WASH } = DS;

const BRUSH_BASE = '../../assets/brushes/';

function brushFor(w){
  const t = w.pos==='verb' ? 'verb' : (w.pos==='adj' ? 'adj' : (w.art||'die'));
  return `url('${BRUSH_BASE}${WASH[w.level+'|'+t] || WASH['B1|die']}')`;
}

/* compact, horizontal dictionary row for the editor side panel */
function CompactRow({ w }){
  const [on, setOn] = useState(false);
  return (
    <div className="wb-row" onMouseEnter={()=>setOn(true)} onMouseLeave={()=>setOn(false)}
      style={{ position:'relative', display:'flex', alignItems:'center', gap:10, padding:'9px 11px', borderRadius:'var(--radius-lg)', cursor:'pointer', minHeight:42, overflow:'hidden' }}>
      <span aria-hidden="true" style={{ position:'absolute', left:0, top:'50%', transform:'translateY(-50%)', width:'62%', height:'122%', zIndex:0, pointerEvents:'none',
        background:`${brushFor(w)} no-repeat left center`, backgroundSize:'auto 116%', opacity:on?.95:.5,
        WebkitMaskImage:`linear-gradient(90deg, transparent 0, rgba(0,0,0,.5) 6px, #000 16px, #000 ${on?'77%':'21%'}, rgba(0,0,0,.4) ${on?'90%':'34%'}, transparent ${on?'100%':'44%'})`,
        maskImage:`linear-gradient(90deg, transparent 0, rgba(0,0,0,.5) 6px, #000 16px, #000 ${on?'77%':'21%'}, rgba(0,0,0,.4) ${on?'90%':'34%'}, transparent ${on?'100%':'44%'})`,
        transition:'opacity .45s ease' }} />
      <span style={{ position:'relative', zIndex:1, fontSize:14, color:'var(--ink)', fontWeight:500, flex:'none', textShadow:'0 0 4px rgba(255,255,255,.55)' }}>
        {w.art ? <span style={{ color:'var(--ink-mute)', fontWeight:400 }}>{w.art} </span> : null}{w.de}</span>
      <span style={{ position:'relative', zIndex:1, fontSize:13, color:'var(--ink-mute)', fontStyle:'italic', marginLeft:'auto', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{w.ru}</span>
      <button style={{ position:'relative', zIndex:1, flex:'none', width:24, height:24, borderRadius:7, border:0, background:'none', color:'var(--muted-2)', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer' }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M12 3l2.6 5.6 6.1.7-4.5 4.1 1.2 6L12 16.9 6.6 19.4l1.2-6L3.3 9.3l6.1-.7z"/></svg>
      </button>
    </div>
  );
}

const SECTIONS = [
  { n:'01', name:'Einleitung', words:36 },
  { n:'02', name:'Argument Eins', words:0 },
  { n:'03', name:'Argument Zwei', words:0 },
  { n:'04', name:'Schluss', words:0 },
];

const KLISCHEES = [
  ['Ein wichtiges Argument dafür ist, dass …','Важный аргумент в пользу этого — что …', true],
  ['Erstens lässt sich feststellen, dass …','Во-первых, можно констатировать, что …', false],
  ['Ein klarer Vorteil besteht darin, dass …','Явное преимущество состоит в том, что …', false],
];

const PANEL_WORDS = [
  { art:'die', de:'Technologie', ru:'технология', pos:'noun', level:'B1' },
  { art:'die', de:'Entwicklung', ru:'развитие', pos:'noun', level:'B1' },
  { art:'der', de:'Fortschritt', ru:'прогресс', pos:'noun', level:'B1' },
  { art:'der', de:'Algorithmus', ru:'алгоритм', pos:'noun', level:'B2' },
];

function Pomodoro(){
  const [running, setRunning] = useState(false);
  return (
    <div style={{ position:'relative', overflow:'hidden', borderRadius:'var(--radius-xl)', minHeight:218, color:'var(--ink)', border:'1px solid var(--accent-ln)',
      background:`radial-gradient(120% 90% at 12% 0%, var(--lav-soft) 0%, transparent 56%), radial-gradient(120% 100% at 100% 100%, var(--rose-soft) 0%, transparent 60%), var(--accent-bg)` }}>
      <div aria-hidden="true" style={{ position:'absolute', inset:0, zIndex:0, pointerEvents:'none', opacity:.45,
        background:`url('../../assets/images/abstract-watercolor-column.png') no-repeat -30px center`, backgroundSize:'auto 160%',
        WebkitMaskImage:'linear-gradient(180deg, rgba(0,0,0,.55) 0%, transparent 78%)', maskImage:'linear-gradient(180deg, rgba(0,0,0,.55) 0%, transparent 78%)' }} />
      <div style={{ position:'relative', zIndex:1, display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 18px 0' }}>
        <span style={{ fontSize:10.5, letterSpacing:'.16em', textTransform:'uppercase', fontWeight:700, color:'var(--accent-dk)' }}>Pomodoro-Timer</span>
        <div style={{ display:'flex', gap:4 }}>
          <button style={pomoMode(true)}>Fokus</button>
          <button style={pomoMode(false)}>Pause</button>
        </div>
      </div>
      <div style={{ position:'relative', zIndex:1, textAlign:'center', padding:'6px 18px 0' }}>
        <div style={{ fontFamily:'var(--font-serif)', fontSize:64, fontWeight:600, lineHeight:1, letterSpacing:'1px', color:'var(--ink)' }}>25:00</div>
        <div style={{ fontSize:12, letterSpacing:'.06em', color:'var(--ink-mute)', marginTop:2 }}>Fokuszeit</div>
      </div>
      <div style={{ position:'relative', zIndex:1, display:'flex', alignItems:'center', justifyContent:'center', gap:16, padding:'14px 0 20px' }}>
        <button onClick={()=>setRunning(false)} style={{ width:42, height:42, borderRadius:'var(--radius-pill)', border:'1px solid var(--accent-ln)', background:'rgba(255,255,255,.7)', color:'var(--accent-dk)', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer', backdropFilter:'blur(4px)' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>
        </button>
        <button onClick={()=>setRunning(r=>!r)} style={{ width:58, height:58, borderRadius:'var(--radius-pill)', border:0, cursor:'pointer', background:'var(--accent)', color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', boxShadow:'var(--shadow-accent)' }}>
          {running
            ? <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>
            : <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>}
        </button>
      </div>
    </div>
  );
}
function pomoMode(on){ return { fontSize:11, fontWeight:600, color: on?'#fff':'var(--ink-mute)', background: on?'var(--accent)':'rgba(255,255,255,.55)', border:'1px solid '+(on?'var(--accent)':'var(--accent-ln)'), borderRadius:20, padding:'4px 11px', cursor:'pointer', backdropFilter:'blur(4px)' }; }

function Editor(){
  const [active, setActive] = useState(1);
  const [text, setText] = useState('Einerseits haben Technologien viele Vorteile. Zum Beispiel können wir Informationen in nur wenigen Sekunden finden. Wenn ich eine Hausaufgabe machen muss, suche ich die Antwort bei Google. Außerdem helfen uns soziale Netzwerke, mit Freunden aus anderen Ländern zu kontaktieren.');
  const [kli, setKli] = useState(0);
  const words = text.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div>
      <TopBar items={[
        { label:'Dashboard' }, { label:'Schreiben', active:true },
        { label:'Lernen', dropdown:true }, { label:'Verlauf' }, { label:'Pipeline' },
      ]} />
      <div className="bg-column" aria-hidden="true" />
      <div className="side-label">SCHREIBEN</div>

      <div className="layout">
        {/* ---- left rail: essay map ---- */}
        <aside className="rail-left">
          <div style={{ display:'flex', gap:10 }}>
            <Button variant="secondary" style={{ flex:1 }} icon={<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>}>Neues Essay</Button>
            <IconButton label="Ordner" size="lg"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg></IconButton>
          </div>

          <div>
            <div className="rail-cap">Essay Map</div>
            <div className="essay-map">
              {SECTIONS.map((s,i)=>(
                <button key={i} className={`map-item${i===active?' active':''}`} onClick={()=>setActive(i)}>
                  <div className="map-num">{s.n} {s.name}</div>
                  <div className="map-words">{s.words} Wörter</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <ProgressBar value={words} max={250} label="Fortschritt" showCount />
          </div>

          <div className="niveau-box">
            <Select label="" value="B1" />
            <span className="niveau-lab">Niveau · B1</span>
          </div>
        </aside>

        {/* ---- center: writing surface ---- */}
        <div className="editor-card">
          <div className="doc-meta">
            <Select label="THEMA" value="Technologie" />
            <Select label="FORM" value="argumentativ" />
            <Select value="Vorlage" />
            <span style={{ marginLeft:'auto' }} />
            <button className="doc-notes"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 4h16v12H7l-3 3z"/></svg>Notizen</button>
          </div>

          <div className="doc-head">
            <div className="doc-eyebrow">Technologie</div>
            <div className="doc-title">Argument Eins</div>
            <div className="doc-sub">Das stärkste Argument zuerst</div>
          </div>

          <div className="doc-scroll">
            <div className="editable" contentEditable suppressContentEditableWarning
              onInput={e=>setText(e.currentTarget.textContent)}>{text}</div>
          </div>

          <div className="analyze-row">
            <Button variant="primary" size="lg" icon={<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"/></svg>}>Analysiere {SECTIONS[active].name}…</Button>
          </div>

          <div className="doc-foot">
            <span>{words} Wörter</span>
            <span className="saved"><span className="dot" />Automatisch gespeichert</span>
          </div>
        </div>

        {/* ---- right rail: three tools ---- */}
        <aside className="rail-right">
          <Pomodoro />

          <ToolCard title="Klischees" accent={SECTIONS[active].name.toUpperCase()}
            action={<div className="kli-pager">
              <button className="kli-nav" onClick={()=>setKli(k=>Math.max(0,k-1))}>‹</button>
              <span className="kli-count">{kli+1} / 2</span>
              <button className="kli-nav" onClick={()=>setKli(k=>Math.min(1,k+1))}>›</button>
            </div>}>
            {KLISCHEES.map((k,i)=>(
              <div key={i} className="kli">
                <div className="kli-de" dangerouslySetInnerHTML={{ __html: k[2] ? `<em>${k[0]}</em>` : k[0] }} />
                <div className="kli-ru">{k[1]}</div>
              </div>
            ))}
          </ToolCard>

          <ToolCard title="Wörterbuch" accent="TECHNOLOGIE">
            <div style={{ marginBottom:8 }}>
              <SearchField size="sm" placeholder="Suche nach Wort…" />
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:2 }}>
              {PANEL_WORDS.map((w,i)=>(<CompactRow key={i} w={w} />))}
            </div>
          </ToolCard>
        </aside>
      </div>
    </div>
  );
}

window.Editor = Editor;

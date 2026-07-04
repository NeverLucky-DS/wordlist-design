/* =====================================================================
   Deutsch Essay · Schreiben — page logic
   - Roadmap: data-driven organic path; leaves gather around the ACTIVE
     node and glide to the next one when the stage changes.
   - Tools: two launchers on the right open a roomy slide-in drawer
     (Wörterbuch with watercolor washes + word card, Schreibhilfen with
     paper slips) — both paginated.
   ===================================================================== */

'use strict';

const $  = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

function speak(t){
  if (!('speechSynthesis' in window)) return;
  const u = new SpeechSynthesisUtterance(t); u.lang = 'de-DE'; u.rate = .9;
  speechSynthesis.cancel(); speechSynthesis.speak(u);
}

/* =====================================================================
   Data — same demo content as the editor (backend hookup comes later)
   ===================================================================== */
const STAGES = [
  { id:'einleitung', title:'Einleitung',
    tipLead:'3–4 Sätze:', tip:'stelle das Thema vor und formuliere deine These.',
    kli:[
      {de:'In der heutigen Zeit ist <em>…</em> ein wichtiges Thema.', ru:'В наше время … — важная тема.'},
      {de:'Immer mehr Menschen beschäftigen sich mit <em>…</em>', ru:'Всё больше людей занимаются …'},
      {de:'Das Thema <em>…</em> gewinnt zunehmend an Bedeutung.', ru:'Тема … приобретает всё большее значение.'},
      {de:'Nicht zu bestreiten ist, dass <em>…</em>', ru:'Бесспорно, что …'},
      {de:'In den letzten Jahren hat sich <em>…</em> stark verändert.', ru:'За последние годы … сильно изменилось.'},
      {de:'Die Frage, ob <em>…</em>, wird oft diskutiert.', ru:'Вопрос о том, … , часто обсуждается.'},
    ]},
  { id:'arg1', title:'Argument Eins',
    tipLead:'These + Beispiel:', tip:'entwickle dein stärkstes Argument mit einer Begründung.',
    kli:[
      {de:'Ein wichtiges Argument dafür ist, dass <em>…</em>', ru:'Важный аргумент в пользу этого — что …'},
      {de:'Erstens lässt sich feststellen, dass <em>…</em>', ru:'Во-первых, можно констатировать, что …'},
      {de:'Ein klarer Vorteil besteht darin, dass <em>…</em>', ru:'Явное преимущество состоит в том, что …'},
      {de:'Hinzu kommt, dass <em>…</em>', ru:'К тому же …'},
      {de:'Dies zeigt sich besonders daran, dass <em>…</em>', ru:'Это особенно проявляется в том, что …'},
    ]},
  { id:'arg2', title:'Argument Zwei',
    tipLead:'Gegenseite:', tip:'nenne ein zweites Argument oder eine Gegenposition.',
    kli:[
      {de:'Andererseits darf man nicht vergessen, dass <em>…</em>', ru:'С другой стороны, нельзя забывать, что …'},
      {de:'Kritiker behaupten jedoch, dass <em>…</em>', ru:'Однако критики утверждают, что …'},
      {de:'Ein weiterer Aspekt ist, dass <em>…</em>', ru:'Ещё один аспект — что …'},
      {de:'Demgegenüber steht die Tatsache, dass <em>…</em>', ru:'Этому противостоит тот факт, что …'},
      {de:'Trotzdem sollte man bedenken, dass <em>…</em>', ru:'Тем не менее следует учитывать, что …'},
    ]},
  { id:'schluss', title:'Schluss',
    tipLead:'2–3 Sätze:', tip:'fasse zusammen und formuliere ein klares Fazit.',
    kli:[
      {de:'Zusammenfassend lässt sich sagen, dass <em>…</em>', ru:'Подводя итог, можно сказать, что …'},
      {de:'Abschließend bin ich der Meinung, dass <em>…</em>', ru:'В заключение я считаю, что …'},
      {de:'Meiner Ansicht nach <em>…</em>', ru:'На мой взгляд …'},
      {de:'In Zukunft wird <em>…</em> noch wichtiger werden.', ru:'В будущем … станет ещё важнее.'},
      {de:'Letztlich kommt es darauf an, dass <em>…</em>', ru:'В конечном счёте всё зависит от того, что …'},
    ]},
];

/* thematic vocabulary — same entries as the editor demo (Technologie) */
const WORDS = [
  {de:'Technologie',art:'die',pos:'noun',cat:'Technologie',level:'B1',ru:'технология',ipa:'[tɛçnoloˈɡiː]',
   genus:'Femininum',plural:'die Technologien',
   def:'Die Gesamtheit der Verfahren und Mittel, mit denen der Mensch sein Wissen praktisch nutzbar macht.',
   pull:'Ohne Technologie wäre der moderne Alltag kaum vorstellbar.',
   koll:['moderne Technologie','digitale Technologie','Technologie nutzen'],
   ex:[['Die <strong>Technologie</strong> verändert unsere Arbeitswelt grundlegend.','Технология коренным образом меняет наш рабочий мир.'],
       ['Neue <strong>Technologien</strong> entstehen heute schneller als je zuvor.','Новые технологии появляются сегодня быстрее, чем когда-либо.']]},
  {de:'Entwicklung',art:'die',pos:'noun',cat:'Technologie',level:'B1',ru:'развитие',ipa:'[ɛntˈvɪklʊŋ]',
   genus:'Femininum',plural:'die Entwicklungen',
   def:'Ein Prozess fortschreitender Veränderung, durch den etwas allmählich entsteht oder sich verbessert.',
   pull:'Die rasante Entwicklung der KI wirft neue Fragen auf.',
   koll:['technische Entwicklung','Entwicklung fördern','rasante Entwicklung'],
   ex:[['Die <strong>Entwicklung</strong> der Digitalisierung schreitet rasch voran.','Развитие цифровизации стремительно продвигается.'],
       ['Diese <strong>Entwicklung</strong> hat Vor- und Nachteile.','Это развитие имеет преимущества и недостатки.']]},
  {de:'Fortschritt',art:'der',pos:'noun',cat:'Technologie',level:'B1',ru:'прогресс',ipa:'[ˈfɔʁtʃʁɪt]',
   genus:'Maskulinum',plural:'die Fortschritte',
   def:'Eine positive Veränderung hin zu einem höheren, besseren oder weiter entwickelten Zustand.',
   pull:'Technischer Fortschritt ist nicht immer gleichbedeutend mit Lebensqualität.',
   koll:['technischer Fortschritt','Fortschritt machen','wissenschaftlicher Fortschritt'],
   ex:[['Der technische <strong>Fortschritt</strong> erleichtert viele Aufgaben.','Технический прогресс облегчает многие задачи.'],
       ['Nicht jeder <strong>Fortschritt</strong> dient dem Menschen.','Не всякий прогресс служит человеку.']]},
  {de:'Algorithmus',art:'der',pos:'noun',cat:'Technologie',level:'B2',ru:'алгоритм',ipa:'[alɡoˈʁɪtmʊs]',
   genus:'Maskulinum',plural:'die Algorithmen',
   def:'Eine eindeutige Handlungsvorschrift zur Lösung eines Problems oder einer Klasse von Problemen.',
   pull:'Ein guter Algorithmus spart Zeit und Ressourcen.',
   koll:['der Algorithmus entscheidet','einen Algorithmus entwickeln','komplexer Algorithmus'],
   ex:[['Der <strong>Algorithmus</strong> analysiert die Daten und liefert die Ergebnisse.','Алгоритм анализирует данные и предоставляет результаты.'],
       ['Ein effizienter <strong>Algorithmus</strong> verarbeitet Millionen Daten in Sekunden.','Эффективный алгоритм обрабатывает миллионы данных за секунды.']]},
  {de:'Digitalisierung',art:'die',pos:'noun',cat:'Technologie',level:'B2',ru:'цифровизация',ipa:'[diɡitaliˈziːʁʊŋ]',
   genus:'Femininum',plural:'die Digitalisierungen',
   def:'Die Umwandlung analoger Informationen und Abläufe in digitale Form.',
   pull:'Die Digitalisierung hat unseren Alltag grundlegend verändert.',
   koll:['die Digitalisierung vorantreiben','fortschreitende Digitalisierung'],
   ex:[['Die <strong>Digitalisierung</strong> verändert die Art, wie wir kommunizieren.','Цифровизация меняет то, как мы общаемся.'],
       ['Viele Branchen profitieren von der <strong>Digitalisierung</strong>.','Многие отрасли выигрывают от цифровизации.']]},
  {de:'Kommunikation',art:'die',pos:'noun',cat:'Technologie',level:'B2',ru:'коммуникация',ipa:'[kɔmunikaˈt͡si̯oːn]',
   genus:'Femininum',plural:'die Kommunikationen',
   def:'Der Austausch von Informationen zwischen zwei oder mehreren Beteiligten.',
   pull:'Digitale Kommunikation kennt keine Grenzen mehr.',
   koll:['digitale Kommunikation','Kommunikation verbessern'],
   ex:[['Die digitale <strong>Kommunikation</strong> verbindet Menschen weltweit.','Цифровая коммуникация связывает людей по всему миру.']]},
  {de:'Vorteil',art:'der',pos:'noun',cat:'Technologie',level:'B1',ru:'преимущество',ipa:'[ˈfoːɐ̯taɪ̯l]',
   genus:'Maskulinum',plural:'die Vorteile',
   def:'Ein günstiger Umstand, der jemandem oder etwas nützt.',
   pull:'Jede Technologie bringt Vorteile und Risiken zugleich.',
   koll:['einen Vorteil haben','klarer Vorteil','Vorteile bieten'],
   ex:[['Ein großer <strong>Vorteil</strong> der Technik ist die Zeitersparnis.','Большое преимущество техники — экономия времени.']]},
  {de:'Nachteil',art:'der',pos:'noun',cat:'Technologie',level:'B1',ru:'недостаток',ipa:'[ˈnaːxtaɪ̯l]',
   genus:'Maskulinum',plural:'die Nachteile',
   def:'Ein ungünstiger Umstand, der jemandem oder etwas schadet.',
   pull:'Der größte Nachteil ist die wachsende Abhängigkeit.',
   koll:['einen Nachteil haben','der Nachteil überwiegt'],
   ex:[['Ein <strong>Nachteil</strong> der Digitalisierung ist der Datenschutz.','Недостаток цифровизации — защита данных.']]},
  {de:'Netzwerk',art:'das',pos:'noun',cat:'Technologie',level:'B2',ru:'сеть',ipa:'[ˈnɛt͡svɛʁk]',
   genus:'Neutrum',plural:'die Netzwerke',
   def:'Ein System aus miteinander verbundenen Elementen, das den Austausch von Daten ermöglicht.',
   pull:'Ein stabiles Netzwerk ist die Grundlage moderner Kommunikation.',
   koll:['soziales Netzwerk','ein Netzwerk aufbauen'],
   ex:[['Das soziale <strong>Netzwerk</strong> verbindet Millionen von Nutzern.','Социальная сеть связывает миллионы пользователей.']]},
  {de:'Datenschutz',art:'der',pos:'noun',cat:'Technologie',level:'B2',ru:'защита данных',ipa:'[ˈdaːtn̩ʃʊt͡s]',
   genus:'Maskulinum',plural:'—',
   def:'Der Schutz personenbezogener Daten vor Missbrauch und unbefugtem Zugriff.',
   pull:'Datenschutz wird im digitalen Zeitalter immer wichtiger.',
   koll:['den Datenschutz gewährleisten','Datenschutz beachten'],
   ex:[['Der <strong>Datenschutz</strong> ist ein zentrales Thema der Digitalisierung.','Защита данных — центральная тема цифровизации.']]},
  {de:'Effizienz',art:'die',pos:'noun',cat:'Technologie',level:'C1',ru:'эффективность',ipa:'[ɛfiˈt͡si̯ɛnt͡s]',
   genus:'Femininum',plural:'—',
   def:'Das Verhältnis zwischen erreichtem Nutzen und dem dafür nötigen Aufwand.',
   pull:'Mehr Effizienz bedeutet nicht automatisch mehr Zufriedenheit.',
   koll:['die Effizienz steigern','hohe Effizienz'],
   ex:[['Neue Technologien erhöhen die <strong>Effizienz</strong> der Arbeit.','Новые технологии повышают эффективность труда.']]},
  {de:'künstlich',art:'',pos:'adj',cat:'Technologie',level:'B2',ru:'искусственный',ipa:'[ˈkʏnstlɪç]',
   genus:'Adjektiv',plural:'—',
   def:'Vom Menschen nachgebildet oder hergestellt; nicht natürlich entstanden.',
   pull:'Künstliche Intelligenz prägt zunehmend unseren Alltag.',
   koll:['künstliche Intelligenz','künstliches Licht'],
   ex:[['<strong>Künstliche</strong> Intelligenz übernimmt immer mehr Aufgaben.','Искусственный интеллект берёт на себя всё больше задач.']]},
];

/* watercolor washes — same level+type → colour logic as the Wörterbuch */
const WASH = {
  'B1|der':'B1_Der_Powdery-Blue_Horizontal-Soft.png','B1|die':'B1_Die_Powdery-Pink_BG-Wash.png',
  'B1|das':'B1_Das_Pale-Green_BG-Wash.png','B1|verb':'B1_Verbs_Sandy-Ochre_BG-Wash.png',
  'B1|adj':'B1_Adjectives_Lavender_BG-Wash.png',
  'B2|der':'B2_Der_Deep-Blue_BG-Wash.png','B2|die':'B2_Die_Magenta_BG-Wash.png',
  'B2|das':'B2_Das_Grass-Green_BG-Wash.png','B2|verb':'B2_Verbs_Terracotta_BG-Wash.png',
  'B2|adj':'B2_Adjectives_Amethyst_BG-Wash.png',
  'C1|der':'C1_Der_Indigo_BG-Wash.png','C1|die':'C1_Die_Burgundy_BG-Wash.png',
  'C1|das':'C1_Das_Emerald_BG-Wash.png','C1|verb':'C1_Verbs_Olive-Ochre_BG-Wash.png',
  'C1|adj':'C1_Adjectives_Plum_BG-Wash.png'
};
const typeKey = w => w.pos === 'verb' ? 'verb' : (w.pos === 'adj' ? 'adj' : w.art);
const brushOf = w => {
  const f = WASH[w.level + '|' + typeKey(w)] || '';
  return f ? `url('${new URL('worte/' + f, document.baseURI).href}')` : 'none';
};

/* full declension per word (N/G/D/A × Sg/Pl) — explicit, no auto-guessing */
const DEKL = {
  Technologie:     [['die Technologie','die Technologien'],['der Technologie','der Technologien'],['der Technologie','den Technologien'],['die Technologie','die Technologien']],
  Entwicklung:     [['die Entwicklung','die Entwicklungen'],['der Entwicklung','der Entwicklungen'],['der Entwicklung','den Entwicklungen'],['die Entwicklung','die Entwicklungen']],
  Fortschritt:     [['der Fortschritt','die Fortschritte'],['des Fortschritts','der Fortschritte'],['dem Fortschritt','den Fortschritten'],['den Fortschritt','die Fortschritte']],
  Algorithmus:     [['der Algorithmus','die Algorithmen'],['des Algorithmus','der Algorithmen'],['dem Algorithmus','den Algorithmen'],['den Algorithmus','die Algorithmen']],
  Digitalisierung: [['die Digitalisierung','—'],['der Digitalisierung','—'],['der Digitalisierung','—'],['die Digitalisierung','—']],
  Kommunikation:   [['die Kommunikation','—'],['der Kommunikation','—'],['der Kommunikation','—'],['die Kommunikation','—']],
  Vorteil:         [['der Vorteil','die Vorteile'],['des Vorteils','der Vorteile'],['dem Vorteil','den Vorteilen'],['den Vorteil','die Vorteile']],
  Nachteil:        [['der Nachteil','die Nachteile'],['des Nachteils','der Nachteile'],['dem Nachteil','den Nachteilen'],['den Nachteil','die Nachteile']],
  Netzwerk:        [['das Netzwerk','die Netzwerke'],['des Netzwerks','der Netzwerke'],['dem Netzwerk','den Netzwerken'],['das Netzwerk','die Netzwerke']],
  Datenschutz:     [['der Datenschutz','—'],['des Datenschutzes','—'],['dem Datenschutz','—'],['den Datenschutz','—']],
  Effizienz:       [['die Effizienz','—'],['der Effizienz','—'],['der Effizienz','—'],['die Effizienz','—']],
};
/* adjective comparison forms */
const STEIG = {
  'künstlich': ['künstlich','künstlicher','am künstlichsten'],
};

const WORD_TARGET = 250;
const WB_PAGE = 9, KLI_PAGE = 3;

const drafts = Object.fromEntries(STAGES.map(s => [s.id, '']));
let activeStage = STAGES[0].id;
const favs = new Set();

/* =====================================================================
   Roadmap — rendered once; stage changes only move classes & leaves
   ===================================================================== */
const roadmap = $('#roadmap');

const X_WAVE = [14, 76, 52, 6, 64, 28];
const NODE_GAP = 106, TOP_PAD = 34;

/* leaf cluster around the active node: FIXED offsets and rotations relative
   to every node — on a stage change the cluster glides over and makes one
   full turn on the way (the spin accumulates, so the resting pose is always
   the same) */
const LEAF_SPOTS = [
  { img:'roadmap-leaf-1.png', dx:-30, dy:-40, size:80, rot:-16, flip:false },
  { img:'roadmap-leaf-2.png', dx: 46, dy: 34, size:68, rot:210, flip:true  },
  { img:'roadmap-leaf-3.png', dx:-24, dy: 44, size:60, rot:128, flip:false },
];

/* small static leaves between the nodes — they never move or fade */
const MID_LEAVES = ['roadmap-leaf-3.png', 'roadmap-leaf-2.png', 'roadmap-leaf-1.png'];

let leafEls = [];
let leafSpin = 0;

function stageWordCount(id){
  const t = drafts[id].trim();
  return t ? t.split(/\s+/).length : 0;
}
function nodeCenters(){
  return STAGES.map((s, i) => ({
    x: X_WAVE[i % X_WAVE.length] + 17,
    y: TOP_PAD + i * NODE_GAP,
  }));
}
function smoothPath(pts){
  if (pts.length < 2) return '';
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++){
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    d += ` C ${p1.x + (p2.x - p0.x) / 6} ${p1.y + (p2.y - p0.y) / 6},` +
         ` ${p2.x - (p3.x - p1.x) / 6} ${p2.y - (p3.y - p1.y) / 6}, ${p2.x} ${p2.y}`;
  }
  return d;
}

/* point + tangent at t of one cubic segment (for the static mid-leaves) */
function cubicAt(p1, c1, c2, p2, t){
  const u = 1 - t;
  const x = u*u*u*p1.x + 3*u*u*t*c1.x + 3*u*t*t*c2.x + t*t*t*p2.x;
  const y = u*u*u*p1.y + 3*u*u*t*c1.y + 3*u*t*t*c2.y + t*t*t*p2.y;
  const dx = 3*u*u*(c1.x-p1.x) + 6*u*t*(c2.x-c1.x) + 3*t*t*(p2.x-c2.x);
  const dy = 3*u*u*(c1.y-p1.y) + 6*u*t*(c2.y-c1.y) + 3*t*t*(p2.y-c2.y);
  return { x, y, angle: Math.atan2(dy, dx) * 180 / Math.PI };
}

function buildRoadmap(){
  const pts = nodeCenters();
  const height = TOP_PAD + (STAGES.length - 1) * NODE_GAP + 44;
  roadmap.style.height = height + 'px';
  roadmap.innerHTML = '';

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'rm-svg');
  svg.setAttribute('viewBox', `0 0 ${roadmap.clientWidth || 300} ${height}`);
  svg.setAttribute('preserveAspectRatio', 'xMinYMin meet');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('class', 'rm-line');
  path.setAttribute('d', smoothPath(pts));
  svg.appendChild(path);
  roadmap.appendChild(svg);

  /* small static leaves halfway along each segment */
  for (let i = 0; i < pts.length - 1; i++){
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 };
    const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 };
    const pos = cubicAt(p1, c1, c2, p2, i % 2 ? 0.44 : 0.56);
    const side = i % 2 ? -1 : 1;
    const size = 30 + (i % 3) * 4;
    const leaf = document.createElement('img');
    leaf.src = 'images/' + MID_LEAVES[i % MID_LEAVES.length];
    leaf.alt = '';
    leaf.className = 'rm-leaf rm-leaf-mid';
    leaf.style.cssText =
      `width:${size}px;left:${pos.x - size/2 + side*14}px;top:${pos.y - size/2}px;` +
      `transform:rotate(${pos.angle + (side > 0 ? -64 : 122)}deg)${side < 0 ? ' scaleX(-1)' : ''};opacity:.75`;
    roadmap.appendChild(leaf);
  }

  /* persistent leaves — they glide between nodes via CSS transitions */
  leafEls = LEAF_SPOTS.map(spot => {
    const img = document.createElement('img');
    img.src = 'images/' + spot.img;
    img.alt = '';
    img.className = 'rm-leaf';
    roadmap.appendChild(img);
    return img;
  });

  STAGES.forEach((s, i) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'rm-node' + (s.id === activeStage ? ' active' : '');
    btn.style.left = (pts[i].x - 17) + 'px';
    btn.style.top = pts[i].y + 'px';
    btn.innerHTML =
      `<span class="rm-dot">${String(i + 1).padStart(2, '0')}</span>` +
      `<span class="rm-txt"><span class="rm-title">${s.title}</span>` +
      `<span class="rm-words">${stageWordCount(s.id)} Wörter</span></span>`;
    btn.addEventListener('click', () => setStage(s.id));
    roadmap.appendChild(btn);
  });

  placeLeaves(false);
}

/* position the leaf cluster around the active node; the accumulated spin
   makes the leaves turn a full circle while they travel */
function placeLeaves(){
  const idx = STAGES.findIndex(s => s.id === activeStage);
  const c = nodeCenters()[idx];
  LEAF_SPOTS.forEach((spot, i) => {
    const el = leafEls[i];
    el.style.width = spot.size + 'px';
    el.style.left = (c.x + spot.dx - spot.size / 2) + 'px';
    el.style.top  = (c.y + spot.dy - spot.size / 2) + 'px';
    el.style.transform = `rotate(${spot.rot + leafSpin}deg)${spot.flip ? ' scaleX(-1)' : ''}`;
    el.style.opacity = '.9';
  });
}

/* =====================================================================
   Sheet — editable area, tip, counters
   ===================================================================== */
const editable = $('#editable');
const stageTip = $('#stageTip');

function setStage(id){
  if (id === activeStage) { editable.focus(); return; }
  drafts[activeStage] = editable.innerText;
  activeStage = id;
  const s = STAGES.find(x => x.id === id);
  editable.innerText = drafts[id];
  $('#tipLead').textContent = s.tipLead;
  $('#tipText').textContent = s.tip;

  $$('.rm-node').forEach((n, i) =>
    n.classList.toggle('active', STAGES[i].id === id));
  leafSpin += 360;                     /* one graceful turn per transition */
  placeLeaves();
  updateCounters();

  /* an open Schreibhilfen card follows the stage */
  if (openedTool === 'hilfen') renderHilfen();
  editable.focus();
}

function totalWords(){
  drafts[activeStage] = editable.innerText;
  return STAGES.reduce((sum, s) => sum + stageWordCount(s.id), 0);
}

function updateCounters(){
  const total = totalWords();          /* syncs the active draft first */
  const cur = stageWordCount(activeStage);
  $('#wordCount').textContent = cur + ' Wörter';
  $('#progTotal').textContent = total;
  $('#progFill').style.width = Math.min(100, total / WORD_TARGET * 100) + '%';
  stageTip.classList.toggle('hidden', editable.innerText.trim().length > 0);
  $$('.rm-node').forEach((n, i) => {
    const w = n.querySelector('.rm-words');
    if (w) w.textContent = stageWordCount(STAGES[i].id) + ' Wörter';
  });
}
editable.addEventListener('input', updateCounters);

/* insert a formulation at the end of the current draft */
function insertText(t){
  editable.innerText = (editable.innerText.trim() + ' ' + t).trim() + ' ';
  updateCounters();
  editable.focus();
  const sel = window.getSelection();
  sel.selectAllChildren(editable);
  sel.collapseToEnd();
}

/* =====================================================================
   Tool cards — they expand downwards, in place (one open at a time)
   ===================================================================== */
let openedTool = null;              /* 'hilfen' | 'woerterbuch' | null */
let wbQuery = '', wbPage = 0, kliPage = 0;

function openTool(tool){
  if (openedTool === tool){ closeTools(); return; }
  openedTool = tool;
  if (tool === 'woerterbuch'){ wbPage = 0; renderWoerterbuch(); }
  else { kliPage = 0; renderHilfen(); }
  $$('.tool-card').forEach(c => c.classList.toggle('open', c.dataset.tool === tool));
}
function closeTools(){
  openedTool = null;
  $$('.tool-card').forEach(c => c.classList.remove('open'));
  closeCard();
}
$$('.tool-card .tool-head').forEach(btn =>
  btn.addEventListener('click', () => openTool(btn.closest('.tool-card').dataset.tool)));

/* ---------- shared pager ---------- */
function renderPager(el, count, page, onPage){
  el.innerHTML = '';
  if (count <= 1){ el.hidden = true; return; }
  el.hidden = false;
  const mk = (label, p, opts = {}) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'pg-btn' + (opts.active ? ' active' : '');
    b.innerHTML = label;
    b.disabled = !!opts.disabled;
    if (!opts.disabled && !opts.active) b.addEventListener('click', () => onPage(p));
    el.appendChild(b);
  };
  mk('‹', page - 1, { disabled: page === 0 });
  for (let i = 0; i < count; i++) mk(String(i + 1), i, { active: i === page });
  mk('›', page + 1, { disabled: page === count - 1 });
}

/* ---------- Wörterbuch ---------- */
function wbFiltered(){
  const q = wbQuery.trim().toLowerCase();
  return WORDS.filter(w => !q || w.de.toLowerCase().includes(q) || w.ru.toLowerCase().includes(q));
}

function renderWoerterbuch(){
  const items = wbFiltered();
  const pages = Math.max(1, Math.ceil(items.length / WB_PAGE));
  wbPage = Math.min(wbPage, pages - 1);
  const slice = items.slice(wbPage * WB_PAGE, wbPage * WB_PAGE + WB_PAGE);

  $('#wbBody').innerHTML = `
    <label class="wb-search">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
      <input id="wbSearch" type="text" placeholder="Suche nach Wort…" value="${esc(wbQuery)}">
    </label>
    <div class="wb-list" id="wbList"></div>`;

  const list = $('#wbList');
  if (!slice.length){
    list.innerHTML = `<div class="wb-empty">Keine Begriffe gefunden.</div>`;
  }
  slice.forEach(w => {
    const row = document.createElement('div');
    row.className = 'wb-row';
    row.style.setProperty('--brush', brushOf(w));
    const art = w.art ? `<span class="art">${esc(w.art)} </span>` : '';
    row.innerHTML = `
      <span class="wb-wash" aria-hidden="true"></span>
      <span class="wb-de">${art}${esc(w.de)}</span>
      <span class="wb-ru">${esc(w.ru)}</span>
      <button class="wb-star${favs.has(w.de) ? ' on' : ''}" type="button" aria-label="Merken">
        <svg viewBox="0 0 24 24" fill="${favs.has(w.de) ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 18.3 6.2 21.4l1.1-6.5L2.6 9.8l6.5-.9z"/></svg>
      </button>`;
    row.addEventListener('click', e => {
      if (e.target.closest('.wb-star')) return;
      $$('.wb-row').forEach(r => r.classList.remove('active'));
      row.classList.add('active');
      openCard(w, row);
    });
    row.querySelector('.wb-star').addEventListener('click', e => {
      e.stopPropagation();
      const star = e.currentTarget;
      if (favs.has(w.de)){ favs.delete(w.de); star.classList.remove('on'); star.querySelector('svg').setAttribute('fill','none'); }
      else { favs.add(w.de); star.classList.add('on'); star.querySelector('svg').setAttribute('fill','currentColor'); }
    });
    list.appendChild(row);
  });

  $('#wbSearch').addEventListener('input', e => {
    wbQuery = e.target.value; wbPage = 0;
    const pos = e.target.selectionStart;
    renderWoerterbuch();
    const inp = $('#wbSearch'); inp.focus(); inp.setSelectionRange(pos, pos);
  });

  renderPager($('#wbPager'), pages, wbPage, p => { wbPage = p; renderWoerterbuch(); });
}

/* ---------- Schreibhilfen ---------- */
function renderHilfen(){
  const s = STAGES.find(x => x.id === activeStage);
  const pages = Math.max(1, Math.ceil(s.kli.length / KLI_PAGE));
  kliPage = Math.min(kliPage, pages - 1);
  const slice = s.kli.slice(kliPage * KLI_PAGE, kliPage * KLI_PAGE + KLI_PAGE);

  $('#hilfenBody').innerHTML = `
    <div class="kli-cap">Klischees · <b>${esc(s.title)}</b></div>
    <div class="kli-list" id="kliList"></div>`;

  const list = $('#kliList');
  slice.forEach(k => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'kli';
    b.innerHTML = `<span class="kli-de">${k.de}</span>
      <span class="kli-ru">${esc(k.ru)}</span>
      <span class="kli-add">Einfügen ↵</span>`;
    b.addEventListener('click', () => {
      const tmp = document.createElement('div');
      tmp.innerHTML = k.de;
      insertText(tmp.textContent);
    });
    list.appendChild(b);
  });

  renderPager($('#hilfenPager'), pages, kliPage, p => { kliPage = p; renderHilfen(); });
}

/* =====================================================================
   Word-card popover — opens to the LEFT of the clicked row
   ===================================================================== */
let activeRow = null;

const ART_CLS = { der:'art-der', die:'art-die', das:'art-das' };

function cardHTML(w){
  const art = w.art ? `<span class="art ${ART_CLS[w.art] || ''}">${esc(w.art)}</span> ` : '';
  const longCls = ((w.art ? w.art.length + 1 : 0) + w.de.length) > 15 ? ' long' : '';

  /* Bedeutung = the first example, alive; the rest go to the Beispiele tab */
  const bedEx = (w.ex && w.ex[0]) ? w.ex[0][0] : esc(w.pull || '');
  const rest = (w.ex || []).slice(1);

  /* Grammatik key forms by part of speech */
  const dekl = DEKL[w.de];
  const steig = STEIG[w.de];
  let spec = '';
  if (w.pos === 'adj' && steig){
    spec = `<span class="g-s"><i>Steigerung</i>${esc(steig.join(' · '))}</span>`;
  } else {
    spec = [
      w.genus ? `<span class="g-s"><i>Genus</i>${esc(w.genus)}</span>` : '',
      w.plural && w.plural !== '—' ? `<span class="g-s"><i>Plural</i>${esc(w.plural)}</span>` : '',
      dekl ? `<span class="g-s"><i>Genitiv</i>${esc(dekl[1][0])}</span>` : '',
    ].join('');
  }
  const declBlock = dekl ? `
    <button class="decl-btn" id="declBtn" type="button">Deklination anzeigen
      <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
    </button>
    <div class="decl-tbl" id="declTbl" hidden><table>
      ${['Nominativ','Genitiv','Dativ','Akkusativ'].map((c, i) =>
        `<tr><th>${c}</th><td>${esc(dekl[i][0])}</td><td>${esc(dekl[i][1])}</td></tr>`).join('')}
    </table></div>` : '';

  const koll = (w.koll || []).map(k => `<span class="koll">${esc(k)}</span>`).join('');
  const examples = rest.map(([de, ru]) => `
    <div class="ex-body"><p class="ex-de">${de}</p>${ru ? `<p class="ex-ru">${ru}</p>` : ''}</div>`).join('');

  return `
    <div class="d-top">
      <div class="d-title">
        <span class="d-word${longCls}">${art}${esc(w.de)}</span>
        <span class="d-level">${esc(w.level)}</span>
      </div>
      <div class="d-icons">
        <button class="d-iconbtn" id="dHear" type="button" aria-label="Aussprache">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 9v6h4l5 5V4L9 9H5z"/><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>
        </button>
        <button class="d-iconbtn d-star${favs.has(w.de) ? ' on' : ''}" id="dStar" type="button" aria-label="Merken">
          <svg viewBox="0 0 24 24" fill="${favs.has(w.de) ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 18.3 6.2 21.4l1.1-6.5L2.6 9.8l6.5-.9z"/></svg>
        </button>
        <button class="d-iconbtn" id="dClose" type="button" aria-label="Schließen">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
      </div>
    </div>
    <p class="d-ru">${esc(w.ru)}</p>
    <div class="d-bed"><span class="d-lab">Bedeutung</span><p>${bedEx}</p></div>
    <div class="d-tabs">
      <button class="d-tab" data-mod="gram" type="button">Grammatik</button>
      <button class="d-tab" data-mod="bsp" type="button">Beispiele</button>
    </div>
    <div class="d-mod" id="modGram" hidden><div class="g-spec">${spec}</div>${declBlock}</div>
    <div class="d-mod" id="modBsp" hidden>
      ${koll ? `<div class="koll-row">${koll}</div>` : ''}
      ${examples ? `<div class="ex-list">${examples}</div>` : ''}
    </div>
    <div class="d-foot-pad"></div>`;
}

function positionCard(rowEl){
  const card = $('#wordCard');
  const cardW = Math.min(400, window.innerWidth - 32);
  card.style.width = cardW + 'px';
  const r = rowEl.getBoundingClientRect();
  let left = r.left - cardW - 30;
  if (left < 16) left = 16;
  card.style.left = left + 'px';
  const h = card.offsetHeight;
  let top = r.top + r.height / 2 - h / 2;
  top = Math.max(16, Math.min(top, window.innerHeight - h - 16));
  card.style.top = top + 'px';
}

function openCard(w, rowEl){
  const card = $('#wordCard');
  activeRow = rowEl;
  card.innerHTML = cardHTML(w);
  $('#wcOverlay').classList.add('open');

  card.style.top = '0px'; card.style.visibility = 'hidden';
  card.classList.add('open');
  requestAnimationFrame(() => {
    positionCard(rowEl);
    card.style.visibility = 'visible';
    requestAnimationFrame(updateLink);
  });

  card.querySelector('#dClose').onclick = closeCard;
  card.querySelector('#dHear').onclick = () => speak((w.art ? w.art + ' ' : '') + w.de);

  /* star — kept in sync with the row star in the list */
  card.querySelector('#dStar').onclick = e => {
    const btn = e.currentTarget;
    const on = !favs.has(w.de);
    if (on) favs.add(w.de); else favs.delete(w.de);
    btn.classList.toggle('on', on);
    btn.querySelector('svg').setAttribute('fill', on ? 'currentColor' : 'none');
    const rowStar = rowEl.querySelector('.wb-star');
    if (rowStar){
      rowStar.classList.toggle('on', on);
      rowStar.querySelector('svg').setAttribute('fill', on ? 'currentColor' : 'none');
    }
  };

  /* tabs — one module at a time; card is repositioned as its height changes */
  const tabs = Array.from(card.querySelectorAll('.d-tab'));
  const mods = { gram: card.querySelector('#modGram'), bsp: card.querySelector('#modBsp') };
  tabs.forEach(t => t.onclick = () => {
    const id = t.dataset.mod;
    const wasOn = t.classList.contains('on');
    tabs.forEach(x => x.classList.remove('on'));
    Object.values(mods).forEach(m => m.hidden = true);
    if (!wasOn){ t.classList.add('on'); mods[id].hidden = false; }
    positionCard(rowEl); updateLink();
  });

  /* full declension table, one level deeper */
  const declBtn = card.querySelector('#declBtn');
  if (declBtn){
    const tbl = card.querySelector('#declTbl');
    declBtn.onclick = () => {
      const show = tbl.hidden;
      tbl.hidden = !show;
      declBtn.classList.toggle('on', show);
      declBtn.firstChild.textContent = show ? 'Deklination verbergen' : 'Deklination anzeigen';
      positionCard(rowEl); updateLink();
    };
  }
}
function closeCard(){
  $('#wordCard').classList.remove('open');
  $('#wcOverlay').classList.remove('open');
  $$('.wb-row').forEach(r => r.classList.remove('active'));
  activeRow = null;
  $('#linkLine').setAttribute('hidden', '');
}
$('#wcOverlay').addEventListener('click', closeCard);
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  if ($('#wordCard').classList.contains('open')) closeCard();
  else if (openedTool) closeTools();
});

/* dashed connector: card headword ↔ list row */
function updateLink(){
  const line = $('#linkLine'), card = $('#wordCard');
  if (!card.classList.contains('open') || !activeRow){ line.setAttribute('hidden',''); return; }
  const titleEl = card.querySelector('.d-word');
  if (!titleEl){ line.setAttribute('hidden',''); return; }
  const tR = titleEl.getBoundingClientRect();
  const rR = activeRow.getBoundingClientRect();
  const x1 = tR.right + 8, y1 = tR.top + tR.height / 2;
  const x2 = rR.left - 6,  y2 = rR.top + rR.height / 2;
  const mx = (x1 + x2) / 2;
  $('#linkPath').setAttribute('d', `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`);
  $('#linkDot').setAttribute('cx', x1 - 4); $('#linkDot').setAttribute('cy', y1);
  $('#linkAnchor').setAttribute('cx', x2); $('#linkAnchor').setAttribute('cy', y2);
  line.removeAttribute('hidden');
}
window.addEventListener('scroll', updateLink, { passive:true });
window.addEventListener('resize', updateLink);

/* =====================================================================
   Pomodoro — pill in the top bar
   ===================================================================== */
const pomo = $('#pomo');
const POMO_START = 25 * 60;
let pomoLeft = POMO_START, pomoTimer = null;
const fmt = s => String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');

$('#pomoMain').addEventListener('click', () => {
  if (pomoTimer){
    clearInterval(pomoTimer); pomoTimer = null; pomo.classList.remove('running');
  } else {
    pomo.classList.add('running');
    pomoTimer = setInterval(() => {
      pomoLeft--;
      if (pomoLeft <= 0){ pomoLeft = 0; clearInterval(pomoTimer); pomoTimer = null; pomo.classList.remove('running'); }
      $('#pomoTime').textContent = fmt(pomoLeft);
    }, 1000);
  }
});
$('#pomoReset').addEventListener('click', () => {
  clearInterval(pomoTimer); pomoTimer = null; pomoLeft = POMO_START;
  $('#pomoTime').textContent = fmt(pomoLeft); pomo.classList.remove('running');
});

/* =====================================================================
   Niveau dropdown
   ===================================================================== */
const dd = $('#ddNiveau');
dd.querySelector('.dd-btn').addEventListener('click', () => dd.classList.toggle('open'));
dd.querySelectorAll('.dd-menu button').forEach(b => {
  b.addEventListener('click', () => {
    dd.querySelectorAll('.dd-menu button').forEach(x => x.classList.remove('sel'));
    b.classList.add('sel');
    $('#niveauLbl').textContent = b.textContent;
    dd.classList.remove('open');
  });
});
document.addEventListener('click', e => { if (!dd.contains(e.target)) dd.classList.remove('open'); });

/* =====================================================================
   init
   ===================================================================== */
$('#tipLead').textContent = STAGES[0].tipLead;
$('#tipText').textContent = STAGES[0].tip;
buildRoadmap();
updateCounters();
editable.focus();
window.addEventListener('resize', buildRoadmap);

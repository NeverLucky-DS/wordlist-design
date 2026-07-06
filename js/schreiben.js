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

/* brushOf, typeKey, WASH — js/words-data.js */

/* full declension per word (N/G/D/A × Sg/Pl) — explicit, no auto-guessing */
const DEKL = {
  Technologie:     [['die Technologie','die Technologien'],['der Technologie','der Technologien'],['der Technologie','den Technologien'],['die Technologie','die Technologien']],
  Entwicklung:     [['die Entwicklung','die Entwicklungen'],['der Entwicklung','der Entwicklungen'],['der Entwicklung','den Entwicklungen'],['die Entwicklung','die Entwicklungen']],
  Fortschritt:     [['der Fortschritt','die Fortschritte'],['des Fortschritts','der Fortschritte'],['dem Fortschritt','den Fortschritten'],['den Fortschritt','die Fortschritte']],
  Algorithmus:     [['der Algorithmus','die Algorithmen'],['des Algorithmus','der Algorithmen'],['dem Algorithmus','den Algorithmen'],['den Algorithmus','die Algorithmen']],
  Digitalisierung: [['die Digitalisierung','die Digitalisierungen'],['der Digitalisierung','der Digitalisierungen'],['der Digitalisierung','den Digitalisierungen'],['die Digitalisierung','die Digitalisierungen']],
  Kommunikation:   [['die Kommunikation','die Kommunikationen'],['der Kommunikation','der Kommunikationen'],['der Kommunikation','den Kommunikationen'],['die Kommunikation','die Kommunikationen']],
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

/* =====================================================================
   Store — essays in localStorage; synced to backend when API is up.
   Essay = the only editable thing. Snapshots and reports are immutable.
   ===================================================================== */
/* the theme catalogue will come from the pipeline DB (100+ entries) —
   the picker is built for that scale: search + pagination */
const THEMEN = [
  { id:'Technologie',  name:'Technologie',  sub:'Digitalisierung & Fortschritt' },
  { id:'Umwelt',       name:'Umwelt',       sub:'Klima & Nachhaltigkeit' },
  { id:'Gesellschaft', name:'Gesellschaft', sub:'Zusammenleben & Wandel' },
  { id:'Bildung',      name:'Bildung',      sub:'Schule & Lernen' },
  { id:'Gesundheit',   name:'Gesundheit',   sub:'Körper & Wohlbefinden' },
  { id:'Arbeit',       name:'Arbeit & Beruf', sub:'Karriere & Arbeitswelt' },
  { id:'Medien',       name:'Medien',       sub:'Presse & soziale Netzwerke' },
  { id:'Reisen',       name:'Reisen',       sub:'Mobilität & Tourismus' },
  { id:'Kultur',       name:'Kultur',       sub:'Kunst & Traditionen' },
  { id:'Sport',        name:'Sport',        sub:'Bewegung & Wettbewerb' },
  { id:'Familie',      name:'Familie',      sub:'Generationen & Beziehungen' },
  { id:'Ernährung',    name:'Ernährung',    sub:'Essen & Konsum' },
];

const STORE_KEY = 'deutschEssay.schreiben.v1';
function loadStore(){
  try { return JSON.parse(localStorage.getItem(STORE_KEY)) || null; }
  catch { return null; }
}
function saveStore(){
  try { localStorage.setItem(STORE_KEY, JSON.stringify(store)); } catch {}
}
const store = loadStore() || { essays: [], activeId: null };
const currentEssay = () => store.essays.find(e => e.id === store.activeId) || null;
const uid = p => p + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);

function newEssayObj(thema, aufgabe, niveau){
  return {
    id: uid('e'), thema, aufgabe, niveau,
    apiId: null,
    drafts: Object.fromEntries(STAGES.map(s => [s.id, ''])),
    snapshots: [],
    analysis: null,          /* latest Mistral analysis (no history) */
    partFeedback: {},
    created: Date.now(), updated: Date.now(),
  };
}

/* =====================================================================
   Backend bridge — essay text format matches mistral_analyzer PART_LABELS
   ===================================================================== */
const API_PART = {
  einleitung: 'einleitung',
  arg1: 'argument1',
  arg2: 'argument2',
  schluss: 'schluss',
};
function apiToStage(part) {
  if (part === 'argument1') return 'arg1';
  if (part === 'argument2') return 'arg2';
  if (part === 'einleitung') return 'einleitung';
  return 'schluss';
}
function buildEssayText() {
  return STAGES.map(s => `${s.title}:\n${(drafts[s.id] || '').trim()}`).join('\n\n');
}

let apiReady = false;
let apiSaveTimer = null;
let analyzing = false;

async function persistEssayToApi() {
  const e = currentEssay();
  if (!e || !apiReady || !window.SchreibenApi) return;
  const payload = {
    title: e.thema || 'Essay',
    text: buildEssayText(),
    essay_type: 'argumentativ',
    topic: (e.thema || '').toLowerCase(),
    level: e.niveau || 'B1',
  };
  try {
    if (e.apiId) {
      await SchreibenApi.updateEssay(e.apiId, payload);
    } else {
      const created = await SchreibenApi.createEssay(payload);
      e.apiId = created.id;
      saveStore();
      alog('essay created on backend · apiId =', created.id);
    }
  } catch (err) {
    aerr('API save failed', err);
    flashSaved('Speichern fehlgeschlagen');
    throw err;
  }
}

function scheduleApiPersist() {
  if (!apiReady) return;
  clearTimeout(apiSaveTimer);
  apiSaveTimer = setTimeout(() => {
    persistEssayToApi().catch(() => {});
  }, 1200);
}

const ALOG = '[schreiben:analyze]';
function alog(...args) { try { console.info(ALOG, ...args); } catch (_) {} }
function aerr(...args) { try { console.error(ALOG, ...args); } catch (_) {} }

async function initBackend() {
  if (!window.SchreibenApi) {
    aerr('SchreibenApi not loaded — is js/schreiben-api.js included before schreiben.js?');
    return;
  }
  try {
    apiReady = await SchreibenApi.health();
  } catch (err) {
    aerr('initBackend health check threw', err);
    apiReady = false;
  }
  alog('initBackend · apiReady =', apiReady);
}

/* Re-probe the backend when a request is about to run but apiReady is false —
   recovers from the common case where the page loaded before the backend was
   up (health raced at init and lost). Returns the fresh readiness. */
async function ensureBackendReady() {
  if (apiReady) return true;
  if (!window.SchreibenApi) return false;
  alog('apiReady is false — re-checking /health before giving up…');
  try {
    apiReady = await SchreibenApi.health();
  } catch (err) {
    aerr('ensureBackendReady health check threw', err);
    apiReady = false;
  }
  alog('ensureBackendReady · apiReady =', apiReady);
  return apiReady;
}

let saveTimer = null;
function schedulePersist(){
  const e = currentEssay();
  if (!e) return;
  e.updated = Date.now();
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveStore, 600);
  scheduleApiPersist();
}

let drafts = Object.fromEntries(STAGES.map(s => [s.id, '']));
let activeStage = STAGES[0].id;
const favs = new Set();

/* =====================================================================
   Roadmap — rendered once; stage changes only move classes & leaves
   ===================================================================== */
const roadmap = $('#roadmap');

const X_WAVE = [16, 96, 66, 8, 80, 32];
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
/* tension 1/4.2 (instead of the classic 1/6) gives the stem the rounder,
   bulging bows of the reference tree */
const TENSION = 4.2;
function smoothPath(pts){
  if (pts.length < 2) return '';
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++){
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    d += ` C ${p1.x + (p2.x - p0.x) / TENSION} ${p1.y + (p2.y - p0.y) / TENSION},` +
         ` ${p2.x - (p3.x - p1.x) / TENSION} ${p2.y - (p3.y - p1.y) / TENSION}, ${p2.x} ${p2.y}`;
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

  /* static leaves on the stem bends — a bigger one and a small partner on
     the opposite side, like the sprig pairs of the reference tree */
  for (let i = 0; i < pts.length - 1; i++){
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    const c1 = { x: p1.x + (p2.x - p0.x) / TENSION, y: p1.y + (p2.y - p0.y) / TENSION };
    const c2 = { x: p2.x - (p3.x - p1.x) / TENSION, y: p2.y - (p3.y - p1.y) / TENSION };
    const side = i % 2 ? -1 : 1;
    const pair = [
      { t: i % 2 ? 0.42 : 0.58, size: 40 + (i % 3) * 4, s: side,  op: .82 },
      { t: i % 2 ? 0.62 : 0.38, size: 27 + (i % 2) * 3, s: -side, op: .7  },
    ];
    pair.forEach((L, k) => {
      const pos = cubicAt(p1, c1, c2, p2, L.t);
      const leaf = document.createElement('img');
      leaf.src = 'images/' + MID_LEAVES[(i + k) % MID_LEAVES.length];
      leaf.alt = '';
      leaf.className = 'rm-leaf rm-leaf-mid';
      leaf.style.cssText =
        `width:${L.size}px;left:${pos.x - L.size/2 + L.s*15}px;top:${pos.y - L.size/2}px;` +
        `transform:rotate(${pos.angle + (L.s > 0 ? -64 : 122)}deg)${L.s < 0 ? ' scaleX(-1)' : ''};opacity:${L.op}`;
      roadmap.appendChild(leaf);
    });
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

/* editable holds the active draft ONLY in write mode; in review mode it holds
   the full annotated dump of every part, so reading it back would corrupt the
   draft. Always sync through this guard instead of touching drafts directly. */
function syncActiveDraft(){
  if (!reviewMode) drafts[activeStage] = editable.innerText;
}

/* faded fragments of the neighbouring parts above/below the current text */
function updateContext(){
  const idx = STAGES.findIndex(s => s.id === activeStage);
  const prev = idx > 0 ? drafts[STAGES[idx - 1].id].trim() : '';
  const next = idx < STAGES.length - 1 ? drafts[STAGES[idx + 1].id].trim() : '';
  $('#ctxPrev').hidden = !prev;
  $('#ctxNext').hidden = !next;
  if (prev) $('#ctxPrevText').textContent = prev;
  if (next) $('#ctxNextText').textContent = next;
}
$('#ctxPrev').addEventListener('click', () => {
  const idx = STAGES.findIndex(s => s.id === activeStage);
  if (idx > 0) setStage(STAGES[idx - 1].id);
});
$('#ctxNext').addEventListener('click', () => {
  const idx = STAGES.findIndex(s => s.id === activeStage);
  if (idx < STAGES.length - 1) setStage(STAGES[idx + 1].id);
});

function setStage(id){
  if (id === activeStage) { editable.focus(); return; }
  syncActiveDraft();
  closeAnnotationPopover();
  activeStage = id;
  const s = STAGES.find(x => x.id === id);
  renderStageEditable();
  $('#tipLead').textContent = s.tipLead;
  $('#tipText').textContent = s.tip;

  $$('.rm-node').forEach((n, i) =>
    n.classList.toggle('active', STAGES[i].id === id));
  leafSpin += 360;                     /* one graceful turn per transition */
  placeLeaves();
  updateContext();
  updateCounters();

  /* an open Schreibhilfen card follows the stage */
  if (openedTool === 'hilfen') renderHilfen();
  schedulePersist();

  /* caret at the end — you usually arrive to continue writing (write mode only) */
  if (!reviewMode){
    editable.focus();
    if (drafts[id]){
      const sel = window.getSelection();
      sel.selectAllChildren(editable);
      sel.collapseToEnd();
    }
  }
}

function totalWords(){
  syncActiveDraft();
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
editable.addEventListener('input', () => { updateCounters(); schedulePersist(); });

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

function openTool(tool, keep){
  if (openedTool === tool){
    if (keep){
      $$('.tool-card').forEach(c => c.classList.toggle('open', c.dataset.tool === tool));
      if (tool === 'analysen') renderAnalysen();
      return;
    }
    closeTools(); return;
  }
  openedTool = tool;
  if (tool === 'woerterbuch'){ wbPage = 0; renderWoerterbuch(); }
  else if (tool === 'analysen'){ anaPage = 0; renderAnalysen(); }
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
  /* the essay's Thema drives the vocabulary; fall back to everything */
  const e = currentEssay();
  const themed = e ? WORDS.filter(w => w.cat === e.thema) : [];
  const src = themed.length ? themed : WORDS;
  return src.filter(w => !q || w.de.toLowerCase().includes(q) || w.ru.toLowerCase().includes(q));
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

/* ---------- Analysen — immutable reports from Mistral stream ---------- */
const ANA_PAGE = 6;
let anaPage = 0;

function mlEsc(s) {
  return String(s ?? '').split('\n').map(esc).join('<br>');
}

/* Latest analysis only — overall grade, per-part scores, final summary.
   The per-error detail lives inline in the text (swap ⇄ button). */
function renderAnalysen(){
  const body = $('#anaBody');
  const e = currentEssay();
  const a = e && e.analysis;
  if (!a) {
    body.innerHTML = '<p class="ana-empty">Noch keine Analyse — schreibe deinen Text und klicke „Analysieren“. Die Korrekturen erscheinen dann direkt im Text.</p>';
    return;
  }

  const totalErrors = STAGES.reduce((n, s) => n + ((a.errorsByStage?.[s.id] || []).length), 0);
  const head = `
    <div class="ana-head">
      <span class="ana-grade">${esc(a.grade || '—')}</span>
      <span class="ana-score-val">${a.overall_score ?? '—'} / 100</span>
      <button type="button" class="ana-swaplink" id="anaSwapLink">⇄ Im Text ansehen</button>
    </div>
    <p class="ana-meta">${totalErrors} Hinweise · ${fmtDate(a.created)}</p>`;

  const partsInner = (a.part_reports || []).filter(pr => !pr.is_empty).map(pr => `
    <div class="ana-part">
      <div class="ana-part-top"><b>${esc(pr.label || pr.part)}</b><span>${pr.score}/100</span></div>
      ${pr.feedback_ru ? `<p>${mlEsc(pr.feedback_ru)}</p>` : ''}
    </div>`).join('');
  const parts = partsInner
    ? `<details class="ana-fold"><summary>Bewertung der Teile</summary>${partsInner}</details>`
    : '';

  const fs = a.final_summary;
  const summaryInner = fs ? `
    ${fs.structure_feedback_ru ? `<p><b>Struktur</b> — ${mlEsc(fs.structure_feedback_ru)}</p>` : ''}
    ${fs.topic_feedback_ru ? `<p><b>Thema</b> — ${mlEsc(fs.topic_feedback_ru)}</p>` : ''}
    ${fs.overall_comment_ru ? `<p>${mlEsc(fs.overall_comment_ru)}</p>` : ''}` : '';
  const summary = summaryInner.trim()
    ? `<details class="ana-fold"><summary>Struktur & Thema</summary><div class="ana-summary">${summaryInner}</div></details>`
    : '';

  body.innerHTML = `<div class="ana-detail">${head}${parts}${summary}</div>`;
  const link = $('#anaSwapLink');
  if (link) link.addEventListener('click', enterReview);
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
  const hasPlural = dekl && dekl.some(r => r[1] !== '—');
  if (w.pos === 'adj' && steig){
    spec = `<span class="g-s"><i>Steigerung</i>${esc(steig.join(' · '))}</span>`;
  } else {
    spec = [
      hasPlural ? `<span class="g-s"><i>Plural</i>${esc(w.plural)}</span>`
                : `<span class="g-s"><i>Plural</i>kein Plural</span>`,
      dekl ? `<span class="g-s"><i>Genitiv</i>${esc(dekl[1][0])}</span>` : '',
    ].join('');
  }
  /* singularia tantum get a single-column table — no dash noise */
  const declBlock = dekl ? `
    <button class="decl-btn" id="declBtn" type="button">Deklination anzeigen
      <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
    </button>
    <div class="decl-tbl" id="declTbl" hidden><table>
      ${['Nominativ','Genitiv','Dativ','Akkusativ'].map((c, i) =>
        `<tr><th>${c}</th><td>${esc(dekl[i][0])}</td>${hasPlural ? `<td>${esc(dekl[i][1])}</td>` : ''}</tr>`).join('')}
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
   Essay lifecycle — start state, essays list, binding, snapshots,
   analysis stubs
   ===================================================================== */
const sheet = document.querySelector('.sheet');
const THEME_PAGE = 6;
let startThema = THEMEN[0].id, startNiveau = 'B1';
let startQuery = '', startPage = 0;

function renderStart(){
  const grid = $('#startThemen');
  grid.innerHTML = '';
  const f = startQuery.trim().toLowerCase();
  const items = THEMEN.filter(t =>
    !f || t.name.toLowerCase().includes(f) || t.sub.toLowerCase().includes(f));
  const pages = Math.max(1, Math.ceil(items.length / THEME_PAGE));
  startPage = Math.min(startPage, pages - 1);
  const slice = items.slice(startPage * THEME_PAGE, startPage * THEME_PAGE + THEME_PAGE);

  if (!slice.length){
    grid.innerHTML = '<p class="themen-empty">Kein Thema gefunden.</p>';
  }
  slice.forEach(t => {
    const n = WORDS.filter(w => w.cat === t.id).length;
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'thema-card' + (t.id === startThema ? ' sel' : '') + (n ? '' : ' empty');
    b.innerHTML = `<b>${esc(t.name)}</b><i>${esc(t.sub)}</i>
      <span>${n ? n + ' Wörter im Paket' : 'Wortpaket folgt'}</span>`;
    b.addEventListener('click', () => { startThema = t.id; renderStart(); });
    grid.appendChild(b);
  });
  renderPager($('#startPager'), pages, startPage, p => { startPage = p; renderStart(); });
  $$('#startNiveau button').forEach(b =>
    b.classList.toggle('sel', b.textContent === startNiveau));
}
$('#startSearch').addEventListener('input', e => {
  startQuery = e.target.value; startPage = 0;
  renderStart();
});

/* ---------- essays list (the folder button) ---------- */
const countOf = t => { t = (t || '').trim(); return t ? t.split(/\s+/).length : 0; };
function fmtDate(t){
  const d = new Date(t);
  return d.toLocaleDateString('de-DE', { day:'2-digit', month:'2-digit' }) +
    ' · ' + d.toLocaleTimeString('de-DE', { hour:'2-digit', minute:'2-digit' });
}

function renderEssays(){
  const list = $('#essaysList');
  list.innerHTML = '';
  const items = [...store.essays].sort((a, b) => b.updated - a.updated);
  if (!items.length){
    list.innerHTML = '<p class="essays-empty">Noch keine Essays — beginne dein erstes über „Neues Essay“.</p>';
    return;
  }
  items.forEach(e => {
    const words = STAGES.reduce((s, st) => s + countOf(e.drafts[st.id]), 0);
    const row = document.createElement('button');
    row.type = 'button';
    row.className = 'essay-row' + (e.id === store.activeId ? ' current' : '');
    row.innerHTML = `
      <span class="er-main"><b>${esc(e.thema)}</b>${e.aufgabe ? `<i>${esc(e.aufgabe)}</i>` : ''}</span>
      <span class="er-meta">${esc(e.niveau)} · ${words} Wörter · ${e.snapshots.length} Var. · ${fmtDate(e.updated)}</span>`;
    row.addEventListener('click', () => {
      store.activeId = e.id;
      saveStore();
      setSheetMode('write');
      bindEssay(e);
      editable.focus();
    });
    list.appendChild(row);
  });
}

/* ---------- sheet modes: write | start | list ---------- */
function setSheetMode(mode){
  sheet.classList.toggle('starting', mode === 'start');
  sheet.classList.toggle('listing', mode === 'list');
  $('#startState').hidden = mode !== 'start';
  $('#essaysState').hidden = mode !== 'list';
  if (mode === 'start') renderStart();
  if (mode === 'list') renderEssays();
}

function refreshAll(){
  const s = STAGES.find(x => x.id === activeStage);
  renderStageEditable();
  $('#tipLead').textContent = s.tipLead;
  $('#tipText').textContent = s.tip;
  $$('.rm-node').forEach((n, i) =>
    n.classList.toggle('active', STAGES[i].id === activeStage));
  placeLeaves();
  updateContext();
  updateCounters();
  if (openedTool === 'woerterbuch') renderWoerterbuch();
  if (openedTool === 'hilfen') renderHilfen();
}

function bindEssay(e){
  drafts = e.drafts;
  activeStage = STAGES[0].id;
  reviewMode = false;
  closeAnnotationPopover();
  $('#sheetThema').hidden = false;
  $('#themaName').textContent = e.thema;
  $('#themaNiveau').textContent = e.niveau;
  $('#themaAufgabe').textContent = e.aufgabe || '';
  refreshAll();
  updateSwapBtn();
}

$('#startBegin').addEventListener('click', () => {
  const e = newEssayObj(startThema, $('#startAufgabe').value.trim(), startNiveau);
  store.essays.push(e);
  store.activeId = e.id;
  saveStore();
  $('#startAufgabe').value = '';
  setSheetMode('write');
  bindEssay(e);
  editable.focus();
});
$$('#startNiveau button').forEach(b =>
  b.addEventListener('click', () => { startNiveau = b.textContent; renderStart(); }));

document.querySelector('.btn-new').addEventListener('click', () => {
  const e = currentEssay();
  if (e){ syncActiveDraft(); saveStore(); }
  closeTools();
  setSheetMode('start');
});
/* the folder next to "Neues Essay" opens the past-essays list */
document.querySelector('.new-essay-row .btn-icon').addEventListener('click', () => {
  const e = currentEssay();
  if (e){ syncActiveDraft(); saveStore(); }
  closeTools();
  setSheetMode('list');
});

/* =====================================================================
   Inline annotation engine + swap (review) mode
   — errors are shown right in the text as coloured underlines; a click
     opens the correction card. Review mode is read-only: swap to see the
     marks, swap back to keep writing. (Ported/simplified from the old editor.)
   ===================================================================== */
let reviewMode = false;
let selectedAnnotation = null;   /* {stageId, error_id} */

function esc2(t){
  return String(t == null ? '' : t)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function textToHtml(v){
  return esc2(v)
    .replace(/\n/g, '<br>')
    .replace(/ {2}/g, ' &nbsp;')
    .replace(/(^ )|( $)/g, '&nbsp;');
}

/* backend annotation_kind / severity / type → one of 4 visual levels */
function annoKind(err){
  const k = String(err.annotation_kind || '').toLowerCase();
  if (k === 'critical') return 'critical';
  if (k === 'good_fragment' || k === 'good') return 'good';
  if (k === 'b2_potential') return 'correction';
  if (k === 'style' || k === 'suggestion') return 'style';
  const sev = String(err.severity || '').toLowerCase();
  const type = String(err.type || '').toLowerCase();
  if (sev === 'critical' || type === 'grammar') return 'critical';
  if (type === 'good' || type === 'strength') return 'good';
  if (type === 'vocabulary' || type === 'weak') return 'correction';
  if (sev === 'suggestion' || type === 'style') return 'style';
  return 'correction';
}

function errorKey(stageId, err){
  const base = `${stageId}:${err.excerpt || ''}:${err.start || 0}:${err.type || ''}`;
  let h = 0;
  for (let i = 0; i < base.length; i += 1) h = (h * 31 + base.charCodeAt(i)) | 0;
  return 'e' + Math.abs(h).toString(36);
}

function findExcerptIndex(text, excerpt, hint){
  const needle = String(excerpt || '').trim();
  if (!needle) return -1;
  let best = -1, bestDist = Infinity, idx = text.indexOf(needle);
  const h = Number.isFinite(hint) ? hint : 0;
  while (idx >= 0){
    const d = Math.abs(idx - h);
    if (d < bestDist){ best = idx; bestDist = d; }
    idx = text.indexOf(needle, idx + 1);
  }
  return best;
}

/* remove overlapping / nested spans (belt-and-suspenders to the backend) */
function removeOverlaps(errors){
  const rank = { critical: 0, medium: 1, suggestion: 2 };
  const sorted = [...errors].sort((a, b) => {
    const ra = rank[String(a.severity || 'medium').toLowerCase()] ?? 1;
    const rb = rank[String(b.severity || 'medium').toLowerCase()] ?? 1;
    if (ra !== rb) return ra - rb;
    return (a.end - a.start) - (b.end - b.start);
  });
  const kept = [];
  for (const e of sorted){
    if (!kept.some(k => e.start < k.end && k.start < e.end)) kept.push(e);
  }
  return kept.sort((a, b) => a.start - b.start);
}

/* anchor stored errors onto the CURRENT draft text by excerpt search */
function anchorErrors(text, errors){
  const out = [];
  const plain = String(text || '');
  if (!plain.trim()) return out;
  (errors || []).forEach(err => {
    const excerpt = String(err.excerpt || '').trim();
    let start, end;
    if (excerpt){
      const idx = findExcerptIndex(plain, excerpt, err.start);
      if (idx < 0) return;                       /* text changed — drop */
      start = idx; end = idx + excerpt.length;
    } else {
      start = Math.max(0, Math.min(Number(err.start) || 0, plain.length));
      end = Math.max(start + 1, Math.min(Number(err.end) || start + 1, plain.length));
      if (!plain.slice(start, end).trim()) return;
    }
    out.push({ ...err, start, end, error_id: err.error_id || errorKey(activeStage, err) });
  });
  return removeOverlaps(out);
}

function stageErrors(stageId){
  const es = currentEssay();
  if (!es || !es.analysis || !es.analysis.errorsByStage) return [];
  return es.analysis.errorsByStage[stageId] || [];
}

/* Marking, teacher-pen style — never a red block that replaces your words:
   - word-order move  → circle the word + a drawn arrow to where it belongs
   - ending change    → show only the corrected ending in red + wavy underline
   - anything else    → a calm wavy underline (the fix lives in the card)
   - praise           → a quiet green wavy underline                            */
const tok = s => String(s || '').trim().split(/\s+/).filter(Boolean);
const normTok = t => String(t).toLowerCase().replace(/[.,!?;:»«"'()]/g, '');

function isReorder(bad, fix){
  const a = tok(bad).map(normTok).filter(Boolean).sort();
  const b = tok(fix).map(normTok).filter(Boolean).sort();
  return a.length > 1 && a.length === b.length
    && a.join(' ') === b.join(' ') && bad.trim() !== fix.trim();
}

/* which single token relocated and to which slot (null if not a clean move) */
function findMove(ex, cor){
  for (let i = 0; i < ex.length; i += 1){
    const restEx = ex.filter((_, k) => k !== i).map(normTok).join(' ');
    for (let j = 0; j < cor.length; j += 1){
      if (normTok(cor[j]) !== normTok(ex[i])) continue;
      const restCor = cor.filter((_, k) => k !== j).map(normTok).join(' ');
      if (restEx === restCor) return { from: i, to: j };
    }
  }
  return null;
}

let mvSeq = 0;
function buildReorder(bad, fix, err, stageId){
  const ex = tok(bad), cor = tok(fix);
  const mv = findMove(ex, cor);
  if (!mv) return null;
  const { from, to } = mv;
  const n = ex.length;
  const idxs = []; for (let k = 0; k < n; k += 1) if (k !== from) idxs.push(k);
  const caretBefore = to < idxs.length ? idxs[to] : n;
  const id = 'mv' + (mvSeq += 1);
  const dst = `<span class="mv-dst" data-mv="${id}">​</span>`;
  let inner = '';
  for (let i = 0; i < n; i += 1){
    if (i === caretBefore) inner += dst;
    if (i === from) inner += `<span class="mv-src" data-mv="${id}">${esc2(ex[i])}</span>`;
    else inner += esc2(ex[i]);
    if (i < n - 1) inner += ' ';
  }
  if (caretBefore >= n) inner += dst;
  return `<span class="mvw" data-error-id="${err.error_id}" data-stage="${stageId}" data-mv="${id}">${inner}</span>`;
}

function commonPrefixLen(a, b){
  let i = 0; const m = Math.min(a.length, b.length);
  while (i < m && a[i] === b[i]) i += 1;
  return i;
}

/* bad→fix differ in exactly ONE token, by a short suffix (an inflection ending);
   returns the fix tokens + which token and its prefix/ending, else null */
function endingDiff(bad, fix){
  const a = bad.trim(), b = fix.trim();
  if (!b || a === b) return null;
  const ta = a.split(/\s+/), tb = b.split(/\s+/);
  if (ta.length !== tb.length) return null;
  let diffIdx = -1;
  for (let i = 0; i < ta.length; i += 1){
    if (ta[i] !== tb[i]){ if (diffIdx >= 0) return null; diffIdx = i; }
  }
  if (diffIdx < 0) return null;
  const wa = ta[diffIdx], wb = tb[diffIdx];
  const p = commonPrefixLen(wa, wb);
  if (!(p >= 2 && (wa.length - p) <= 4 && (wb.length - p) <= 4)) return null;
  return { tokens: tb, diffIdx, prefix: wb.slice(0, p), ending: wb.slice(p) };
}

/* corrected form with ONLY the changed ending in red + wavy underline */
function renderEndingFix(diff, attrs){
  const parts = diff.tokens.map((t, i) =>
    i === diff.diffIdx
      ? esc2(diff.prefix) + `<span class="fix-end">${esc2(diff.ending)}</span>`
      : esc2(t));
  return `<span class="und-end" ${attrs}>${parts.join(' ')}</span>`;
}

function renderOneError(text, err, stageId){
  const bad = text.slice(err.start, err.end);
  const kind = annoKind(err);
  const attrs = `data-error-id="${err.error_id}" data-stage="${stageId}"`;
  if (kind === 'good'){
    return `<span class="und good" data-annotation="good" ${attrs}>${textToHtml(bad)}</span>`;
  }
  const fix = String(err.correction || '').trim();
  if (fix && isReorder(bad, fix)){
    const rr = buildReorder(bad, fix, err, stageId);
    if (rr) return rr;
  }
  const diff = fix ? endingDiff(bad, fix) : null;
  if (diff){
    return renderEndingFix(diff, attrs);
  }
  return `<span class="und" data-annotation="${kind}" ${attrs}>${textToHtml(bad)}</span>`;
}

function renderAnnotatedHTML(text, anchored, stageId){
  let html = '', cursor = 0;
  anchored.forEach(err => {
    if (err.start < cursor) return;
    html += textToHtml(text.slice(cursor, err.start));
    html += renderOneError(text, err, stageId);
    cursor = err.end;
  });
  html += textToHtml(text.slice(cursor));
  return html;
}

/* draw a continuous arrow from each circled word to where it should move */
function drawMoveArrows(){
  editable.querySelectorAll('.mv-layer').forEach(l => l.remove());
  if (!reviewMode) return;
  const moves = editable.querySelectorAll('.mvw');
  if (!moves.length) return;
  const NS = 'http://www.w3.org/2000/svg';
  const edRect = editable.getBoundingClientRect();
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('class', 'mv-layer');
  svg.setAttribute('width', editable.scrollWidth);
  svg.setAttribute('height', editable.scrollHeight);
  svg.innerHTML = '<defs><marker id="mvHead" viewBox="0 0 10 10" refX="8" refY="5" '
    + 'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
    + '<path d="M0 0L10 5L0 10z" fill="#c0392b"/></marker></defs>';
  moves.forEach(mvw => {
    const id = mvw.getAttribute('data-mv');
    const src = mvw.querySelector('.mv-src');
    const dst = mvw.querySelector(`.mv-dst[data-mv="${id}"]`);
    if (!src || !dst) return;
    const sr = src.getBoundingClientRect(), dr = dst.getBoundingClientRect();
    const ox = editable.scrollLeft - edRect.left, oy = editable.scrollTop - edRect.top;
    const sx = sr.left + sr.width / 2 + ox, sy = sr.top + oy;
    const dx = dr.left + ox, dy = dr.top + oy;
    const topY = Math.min(sy, dy) - 13;             /* arc rides above the line */
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('d', `M ${sx} ${sy} Q ${(sx + dx) / 2} ${topY} ${dx} ${dy}`);
    path.setAttribute('class', 'mv-path');
    path.setAttribute('marker-end', 'url(#mvHead)');
    svg.appendChild(path);
  });
  editable.appendChild(svg);
}
window.addEventListener('resize', () => { if (reviewMode) drawMoveArrows(); });

/* the whole essay, every non-empty part with its heading, annotated */
function renderReviewFull(){
  const blocks = STAGES.map(s => {
    const text = drafts[s.id] || '';
    if (!text.trim()) return '';
    const anchored = anchorErrors(text, stageErrors(s.id));
    const n = anchored.length;
    return `<div class="rev-part" data-stage="${s.id}">
      <div class="rev-head">${esc2(s.title)}${n ? `<span class="rev-count">${n}</span>` : ''}</div>
      <div class="rev-text">${renderAnnotatedHTML(text, anchored, s.id)}</div>
    </div>`;
  }).filter(Boolean);
  return blocks.length
    ? blocks.join('')
    : `<div class="rev-empty">Noch kein Text geschrieben.</div>`;
}

/* decide plain-editable (write) vs full annotated read-only (review) */
function renderStageEditable(){
  if (reviewMode){
    editable.setAttribute('contenteditable', 'false');
    editable.classList.add('reviewing');
    editable.innerHTML = renderReviewFull();
    requestAnimationFrame(drawMoveArrows);
  } else {
    editable.setAttribute('contenteditable', 'true');
    editable.classList.remove('reviewing');
    editable.innerText = drafts[activeStage] || '';
  }
}

function hasAnyErrors(es){
  if (!es || !es.analysis || !es.analysis.errorsByStage) return false;
  return STAGES.some(s => (es.analysis.errorsByStage[s.id] || []).length);
}

function updateSwapBtn(){
  const btn = $('#btnSwap');
  if (!btn) return;
  const es = currentEssay();
  const on = !!(es && es.analysis);
  btn.disabled = !on;
  btn.classList.toggle('active', reviewMode);
  btn.title = !on
    ? 'Erst analysieren, dann die Korrekturen im Text ansehen'
    : (reviewMode ? 'Zurück zum Schreiben' : 'Korrekturen im Text ansehen');
}

function enterReview(){
  const es = currentEssay();
  if (!es || !es.analysis) return;
  syncActiveDraft();
  reviewMode = true;
  renderStageEditable();
  updateSwapBtn();
}

function toggleReview(){
  const es = currentEssay();
  if (!es || !es.analysis) return;
  closeAnnotationPopover();
  if (!reviewMode){
    enterReview();
  } else {
    reviewMode = false;
    renderStageEditable();
    updateSwapBtn();
    editable.focus();
  }
}

/* ---- correction card (popover) ---- */
function splitStrategies(text){
  return String(text || '').split(/\d\)\s+/g).map(s => s.trim()).filter(Boolean);
}
function normalizeExplanation(text){
  const lines = String(text || '').split('\n').map(l => l.trim()).filter(Boolean);
  const rows = lines.map(l => {
    const i = l.indexOf(':');
    if (i < 1) return null;
    return { label: l.slice(0, i).trim(), value: l.slice(i + 1).trim() };
  }).filter(Boolean);
  return rows.length ? rows : [{ label: 'Объяснение', value: String(text || '').trim() }];
}

const KIND_LABEL = {
  critical: 'Kritischer Fehler',
  correction: 'Korrektur',
  style: 'Stil-Hinweis',
  good: 'Gelungen',
};

/* the sentence that contains [start,end) within text */
function sentenceAround(text, start, end){
  const term = /[.!?\n]/;
  let s = start;
  while (s > 0 && !term.test(text[s - 1])) s--;
  while (s < start && /\s/.test(text[s])) s++;
  let e = end;
  while (e < text.length && !term.test(text[e])) e++;
  if (e < text.length) e++;                 /* include the terminator */
  return { s, e };
}

/* sentence HTML with the fragment [rs,re) wrapped; `replacement` swaps the text */
function markedSentence(sentence, rs, re, cls, replacement){
  const mid = replacement != null ? replacement : sentence.slice(rs, re);
  return esc2(sentence.slice(0, rs)) + `<mark class="${cls}">${esc2(mid)}</mark>` + esc2(sentence.slice(re));
}

function annotationCardHTML(err){
  const kind = annoKind(err);
  const explanation = normalizeExplanation(err.explanation_ru || '');
  const whatWrong = err.what_wrong_ru
    || (explanation.find(x => x.label.toLowerCase().includes('что')) || {}).value
    || (explanation[0] || {}).value || 'Есть неточность в формулировке.';
  const whyBad = err.why_bad_ru
    || (explanation.find(x => x.label.toLowerCase().includes('почему')) || {}).value || '';
  const hints = splitStrategies(err.how_to_fix_ru || '');
  const isGood = kind === 'good';

  /* the error in its sentence, and the corrected sentence */
  const text = String(err.__text || '');
  const excerpt = String(err.excerpt || '');
  const fix = String(err.correction || '').trim();
  const fixSentence = String(err.corrected_sentence_de || '').trim();
  let sentenceHTML = '';
  let fixedHTML = '';
  let origSentence = '';
  if (text && Number.isFinite(err.start) && Number.isFinite(err.end) && err.end > err.start){
    const { s, e } = sentenceAround(text, err.start, err.end);
    origSentence = text.slice(s, e).trim();
    const rs = err.start - s, re = err.end - s;
    sentenceHTML = markedSentence(text.slice(s, e), rs, re, 'ann-mark-err');
  }
  if (!isGood && fixSentence && fixSentence !== origSentence){
    /* whole corrected sentence from the model — no fragile reconstruction */
    fixedHTML = `<mark class="ann-mark-fix">${esc2(fixSentence)}</mark>`;
  } else if (!isGood && fix && fix !== excerpt && sentenceHTML){
    /* fallback: swap the fragment in place */
    const { s, e } = sentenceAround(text, err.start, err.end);
    fixedHTML = markedSentence(text.slice(s, e), err.start - s, err.end - s, 'ann-mark-fix', fix);
  }

  /* collapsible variants (read-only, no insert) */
  const variants = [];
  if (err.b1_variant_de){
    variants.push(`<div class="annotation-variant annotation-variant-b1">
      <span class="annotation-variant-level">B1</span><p>${esc2(err.b1_variant_de)}</p>
      ${err.b1_explain_ru ? `<p class="annotation-variant-explain">${esc2(err.b1_explain_ru)}</p>` : ''}
    </div>`);
  }
  if (err.b2_variant_de){
    variants.push(`<div class="annotation-variant annotation-variant-b2">
      <span class="annotation-variant-level">B2</span><p>${esc2(err.b2_variant_de)}</p>
      ${err.b2_explain_ru ? `<p class="annotation-variant-explain">${esc2(err.b2_explain_ru)}</p>` : ''}
    </div>`);
  }

  const moreBits = [];
  if (whyBad && !isGood) moreBits.push(`<div class="ann-block"><h4>Почему важно</h4><p>${esc2(whyBad)}</p></div>`);
  if (variants.length && !isGood) moreBits.push(`<div class="ann-block"><h4>Варианты формулировки</h4>${variants.join('')}</div>`);
  if (hints.length && !isGood) moreBits.push(`<div class="ann-block"><h4>Как улучшить</h4><ol class="annotation-tips">${hints.map(x => `<li>${esc2(x)}</li>`).join('')}</ol></div>`);
  if (err.rule) moreBits.push(`<div class="ann-block"><h4>Правило</h4><p class="annotation-rule">${esc2(err.rule)}</p></div>`);
  const moreHTML = moreBits.length
    ? `<details class="ann-more"><summary>Подробнее</summary>${moreBits.join('')}</details>`
    : '';

  return `<div class="annotation-card annotation-card--${kind}">
    <span class="annotation-kicker annotation-kicker--${kind}">${KIND_LABEL[kind] || 'Hinweis'}</span>
    ${sentenceHTML ? `<div class="ann-sentence ann-sentence--err">${sentenceHTML}</div>` : ''}
    ${fixedHTML ? `<div class="ann-sentence ann-sentence--fix">${fixedHTML}</div>` : ''}
    <p class="annotation-popover-lead">${esc2(whatWrong)}</p>
    ${moreHTML}
  </div>`;
}

function computePopoverPos(anchorRect, cardH){
  const gap = 20, width = 360, margin = 14;
  const spaceRight = window.innerWidth - anchorRect.right - gap - margin;
  const spaceLeft = anchorRect.left - gap - margin;
  const side = (spaceRight >= width || spaceRight >= spaceLeft) ? 'right' : 'left';
  let left = side === 'right' ? anchorRect.right + gap : anchorRect.left - gap - width;
  left = Math.max(margin, Math.min(left, window.innerWidth - width - margin));
  let top = anchorRect.top + anchorRect.height / 2 - cardH / 2;
  top = Math.max(margin, Math.min(top, window.innerHeight - cardH - margin));
  return { top, left };
}

function closeAnnotationPopover(){
  selectedAnnotation = null;
  const pop = $('#annPopover'), bd = $('#annBackdrop');
  if (pop) pop.setAttribute('hidden', '');
  if (bd) bd.setAttribute('hidden', '');
  document.querySelectorAll('#editable span[data-error-id].sel')
    .forEach(s => s.classList.remove('sel'));
}

function openAnnotationPopover(err, spanEl){
  const pop = $('#annPopover'), content = $('#annContent'), bd = $('#annBackdrop');
  if (!pop || !content) return;
  content.innerHTML = annotationCardHTML(err);
  pop.removeAttribute('hidden');
  if (bd) bd.removeAttribute('hidden');
  document.querySelectorAll('#editable span[data-error-id].sel')
    .forEach(s => s.classList.remove('sel'));
  spanEl.classList.add('sel');
  requestAnimationFrame(() => {
    const pos = computePopoverPos(spanEl.getBoundingClientRect(), pop.offsetHeight || 300);
    pop.style.top = pos.top + 'px';
    pop.style.left = pos.left + 'px';
  });
  selectedAnnotation = { stageId: activeStage, error_id: err.error_id };
}

function onAnnotationAction(action, text){
  if (action === 'insert'){
    reviewMode = false;
    renderStageEditable();
    insertText(text);
    closeAnnotationPopover();
    updateSwapBtn();
  }
}

function bindAnnotationEvents(){
  editable.addEventListener('click', (e) => {
    const span = e.target.closest('span[data-error-id]');
    if (!span) return;
    const stageId = span.getAttribute('data-stage') || activeStage;
    const err = anchorErrors(drafts[stageId] || '', stageErrors(stageId))
      .find(x => x.error_id === span.getAttribute('data-error-id'));
    if (err){ err.__text = drafts[stageId] || ''; openAnnotationPopover(err, span); }
  });
  const bd = $('#annBackdrop');
  if (bd) bd.addEventListener('click', closeAnnotationPopover);
  const closeBtn = $('#annClose');
  if (closeBtn) closeBtn.addEventListener('click', closeAnnotationPopover);
  const content = $('#annContent');
  if (content) content.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-annotation-action]');
    if (!btn) return;
    onAnnotationAction(
      btn.getAttribute('data-annotation-action'),
      decodeURIComponent(btn.getAttribute('data-annotation-text') || ''),
    );
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAnnotationPopover();
  });
  const swap = $('#btnSwap');
  if (swap) swap.addEventListener('click', toggleReview);
}

/* ---------- snapshots & Mistral analysis (SSE via SchreibenApi) ---------- */
function applyPartFeedback(event) {
  const e = currentEssay();
  if (!e || !event || !event.part) return;
  const stageId = apiToStage(event.part);
  if (!e.partFeedback) e.partFeedback = {};
  if (event.feedback_ru) {
    e.partFeedback[stageId] = event.feedback_ru;
    if (stageId === activeStage) {
      $('#tipLead').textContent = 'Feedback:';
      $('#tipText').textContent = event.feedback_ru;
    }
  }
}

function scopePayload(scope, full) {
  if (scope === 'full') return { ...full, scoped: false };
  const apiPart = API_PART[scope];
  const partReport = (full.part_reports || []).find(p => p.part === apiPart);
  return {
    ...full,
    scoped: true,
    overall_score: partReport ? partReport.score : 0,
    part_reports: partReport ? [partReport] : [],
    errors: (full.errors || []).filter(err => err.part === apiPart),
    final_summary: null,
  };
}

async function runAnalysis(scope) {
  const es = currentEssay();
  if (!es) { aerr('runAnalysis: no active essay'); return; }
  if (analyzing) { alog('runAnalysis: already running, ignoring click'); return; }
  alog('runAnalysis start · scope =', scope, '· essay =', es.id, '· apiId =', es.apiId);

  if (!window.SchreibenApi) {
    aerr('runAnalysis: SchreibenApi missing');
    flashSaved('Backend nicht erreichbar');
    return;
  }
  if (!(await ensureBackendReady())) {
    aerr('runAnalysis: backend not reachable (health failed)');
    flashSaved('Backend nicht erreichbar');
    return;
  }

  analyzing = true;
  setAnaState('pending');
  syncActiveDraft();
  const btnFull = $('#btnAnalyze');
  const btnPart = $('#btnAnalyzePart');
  btnFull.disabled = true;
  btnPart.disabled = true;

  let snapshotId = null;
  if (scope === 'full') {
    const snap = takeSnapshot('Analyse');
    snapshotId = snap ? snap.id : null;
  } else {
    saveStore();
  }

  try {
    flashSaved('Speichern…');
    await persistEssayToApi();
    if (!es.apiId) throw new Error('Essay nicht gespeichert');

    const apiPart = scope === 'full' ? null : (API_PART[scope] || null);
    alog('essay persisted · apiId =', es.apiId, '— starting stream · part =', apiPart || 'all');
    let donePayload = null;
    await SchreibenApi.streamAnalyze(es.apiId, (event) => {
      if (!event || !event.type) return;
      if (event.type === 'part_start') {
        alog('part_start', event.part);
        flashSaved(`Analysiere ${event.label || event.part}…`);
        return;
      }
      if (event.type === 'part_done') {
        alog('part_done', event.part, '· score', event.score, '· errors', (event.errors || []).length);
        applyPartFeedback(event);
      }
      if (event.type === 'done') {
        alog('done · grade', event.grade, '· score', event.overall_score, '· errors', (event.errors || []).length);
        donePayload = {
          overall_score: event.overall_score,
          grade: event.grade,
          errors: event.errors || [],
          part_reports: event.part_reports || [],
          final_summary: event.final_summary || null,
          model: event.model || '',
        };
      }
    }, apiPart);

    if (!donePayload) throw new Error('Keine Analyse-Antwort');

    /* group the flat error list by stage, tag each with a stable id */
    const byStage = Object.fromEntries(STAGES.map(s => [s.id, []]));
    (donePayload.errors || []).forEach(err => {
      const stageId = apiToStage(err.part);
      if (!byStage[stageId]) return;
      byStage[stageId].push({ ...err, error_id: errorKey(stageId, err) });
    });

    if (scope === 'full' || !es.analysis) {
      es.analysis = {
        errorsByStage: byStage,
        part_reports: donePayload.part_reports || [],
        final_summary: donePayload.final_summary || null,
        grade: donePayload.grade,
        overall_score: donePayload.overall_score,
        model: donePayload.model || '',
        created: Date.now(),
      };
    } else {
      /* scoped part run — replace only that stage, keep the rest */
      es.analysis.errorsByStage[scope] = byStage[scope] || [];
      const others = (es.analysis.part_reports || []).filter(r => apiToStage(r.part) !== scope);
      es.analysis.part_reports = [...others, ...(donePayload.part_reports || [])];
      es.analysis.created = Date.now();
    }
    delete es.reports;            /* drop the old timestamped history */
    delete es.activeReportId;
    saveStore();

    const errCount = (donePayload.errors || []).length;
    flashSaved(scope === 'full'
      ? `Analysiert · ${donePayload.grade} (${donePayload.overall_score}) · ${errCount} Hinweise`
      : `Teil analysiert · ${errCount} Hinweise`);
    alog('runAnalysis complete · scope', scope, '· errors', errCount);
    enterReview();                /* flip the sheet to show marks in the text */
    renderAnalysen();             /* refresh the summary panel */
    setAnaState('done');
  } catch (err) {
    aerr('runAnalysis failed', err);
    flashSaved(`Analyse fehlgeschlagen: ${err && err.message ? err.message : 'Unbekannter Fehler'}`);
    setAnaState('error');
  } finally {
    analyzing = false;
    btnFull.disabled = false;
    btnPart.disabled = false;
    alog('runAnalysis end · analyzing =', analyzing);
  }
}
function takeSnapshot(label){
  const e = currentEssay();
  if (!e) return null;
  syncActiveDraft();
  const snap = { id: uid('s'), label, drafts: { ...drafts }, created: Date.now() };
  e.snapshots.push(snap);
  saveStore();
  return snap;
}
function flashSaved(msg){
  const el = $('#savedMsg');
  const old = el.textContent;
  el.textContent = msg;
  setTimeout(() => { el.textContent = old; }, 1600);
}

/* ---- analysis request state indicator (footer) ---- */
const ANA_ICON = {
  idle:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9 10h.01M15 10h.01"/><path d="M8.8 14.2c.8.9 1.9 1.4 3.2 1.4s2.4-.5 3.2-1.4"/></svg>',
  pending: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9" opacity=".22"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>',
  done:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9 10h.01M15 10h.01"/><path d="M8.5 13.8c.9 1.1 2.1 1.7 3.5 1.7s2.6-.6 3.5-1.7"/></svg>',
  error:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9 10h.01M15 10h.01"/><path d="M8.8 15.4c.8-.9 1.9-1.4 3.2-1.4s2.4.5 3.2 1.4"/></svg>',
};
const ANA_TITLE = { idle:'Bereit', pending:'Analysiere…', done:'Analyse fertig', error:'Analyse fehlgeschlagen' };
let anaTickId = null, anaResetId = null, anaT0 = 0;

function fmtElapsed(ms){
  const s = Math.floor(ms / 1000);
  return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
}
function setAnaState(state){
  const box = $('#anaStatus');
  if (!box) return;
  clearInterval(anaTickId); anaTickId = null;
  clearTimeout(anaResetId); anaResetId = null;
  box.dataset.state = state;
  box.title = ANA_TITLE[state] || '';
  box.querySelector('.ana-status-ico').innerHTML = ANA_ICON[state] || ANA_ICON.idle;
  const txt = box.querySelector('.ana-status-txt');
  if (state === 'pending'){
    anaT0 = Date.now();
    txt.textContent = '0:00';
    anaTickId = setInterval(() => { txt.textContent = fmtElapsed(Date.now() - anaT0); }, 500);
  } else {
    txt.textContent = state === 'done' ? 'Fertig' : (state === 'error' ? 'Fehler' : '');
  }
  if (state === 'done' || state === 'error'){
    anaResetId = setTimeout(() => setAnaState('idle'), state === 'done' ? 2600 : 3600);
  }
}
$('#btnSnapshot').addEventListener('click', () => {
  if (!currentEssay()) return;
  takeSnapshot('Manuell');
  flashSaved('Variante gemerkt ✓');
});
$('#btnAnalyzePart').addEventListener('click', () => runAnalysis(activeStage));
$('#btnAnalyze').addEventListener('click', () => runAnalysis('full'));

/* =====================================================================
   init
   ===================================================================== */
bindAnnotationEvents();
setAnaState('idle');
initBackend().then(() => {
  buildRoadmap();
  const initial = currentEssay();
  if (initial){
    setSheetMode('write');
    bindEssay(initial);
    editable.focus();
  } else {
    $('#tipLead').textContent = STAGES[0].tipLead;
    $('#tipText').textContent = STAGES[0].tip;
    updateContext();
    updateCounters();
    setSheetMode('start');
  }
});
window.addEventListener('resize', buildRoadmap);

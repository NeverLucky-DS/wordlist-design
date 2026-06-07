/* =====================================================================
   Deutsch Essay · Editor (Schreiben) — interactions
   Self-contained: keeps the working Wörterbuch (app.js) untouched.
   No backend — section text lives in memory for the session.
   ===================================================================== */
(() => {
"use strict";

/* ---------- thematic vocabulary (Technologie) ---------------------------
   Rich enough to render the warm word-card. `pull` = the highlighted quote,
   `verw` = Verwendung/government line, `koll` = collocations. */
const WORDS = [
  {de:"Technologie",art:"die",pos:"noun",cat:"Technologie",level:"B1",ru:"технология",ipa:"[tɛçnoloˈɡiː]",
   genus:"Femininum",plural:"die Technologien",
   def:"Die Gesamtheit der Verfahren und Mittel, mit denen der Mensch sein Wissen praktisch nutzbar macht.",
   pull:"Ohne Technologie wäre der moderne Alltag kaum vorstellbar.",
   koll:["moderne Technologie","digitale Technologie","Technologie nutzen"],
   ex:[["Die <strong>Technologie</strong> verändert unsere Arbeitswelt grundlegend.","Технология коренным образом меняет наш рабочий мир."],
       ["Neue <strong>Technologien</strong> entstehen heute schneller als je zuvor.","Новые технологии появляются сегодня быстрее, чем когда-либо."]]},

  {de:"Entwicklung",art:"die",pos:"noun",cat:"Technologie",level:"B1",ru:"развитие",ipa:"[ɛntˈvɪklʊŋ]",
   genus:"Femininum",plural:"die Entwicklungen",
   def:"Ein Prozess fortschreitender Veränderung, durch den etwas allmählich entsteht oder sich verbessert.",
   pull:"Die rasante Entwicklung der KI wirft neue Fragen auf.",
   koll:["technische Entwicklung","Entwicklung fördern","rasante Entwicklung"],
   ex:[["Die <strong>Entwicklung</strong> der Digitalisierung schreitet rasch voran.","Развитие цифровизации стремительно продвигается."],
       ["Diese <strong>Entwicklung</strong> hat Vor- und Nachteile.","Это развитие имеет преимущества и недостатки."]]},

  {de:"Fortschritt",art:"der",pos:"noun",cat:"Technologie",level:"B1",ru:"прогресс",ipa:"[ˈfɔʁtʃʁɪt]",
   genus:"Maskulinum",plural:"die Fortschritte",
   def:"Eine positive Veränderung hin zu einem höheren, besseren oder weiter entwickelten Zustand.",
   pull:"Technischer Fortschritt ist nicht immer gleichbedeutend mit Lebensqualität.",
   koll:["technischer Fortschritt","Fortschritt machen","wissenschaftlicher Fortschritt"],
   ex:[["Der technische <strong>Fortschritt</strong> erleichtert viele Aufgaben.","Технический прогресс облегчает многие задачи."],
       ["Nicht jeder <strong>Fortschritt</strong> dient dem Menschen.","Не всякий прогресс служит человеку."]]},

  {de:"Algorithmus",art:"der",pos:"noun",cat:"Technologie",level:"B2",ru:"алгоритм",ipa:"[alɡoˈʁɪtmʊs]",
   genus:"Maskulinum",plural:"die Algorithmen",
   def:"Eine eindeutige Handlungsvorschrift zur Lösung eines Problems oder einer Klasse von Problemen.",
   pull:"Ein guter Algorithmus spart Zeit und Ressourcen.",
   koll:["der Algorithmus entscheidet","einen Algorithmus entwickeln","komplexer Algorithmus"],
   ex:[["Der <strong>Algorithmus</strong> analysiert die Daten und liefert die Ergebnisse.","Алгоритм анализирует данные и предоставляет результаты."],
       ["Ein effizienter <strong>Algorithmus</strong> verarbeitet Millionen Daten in Sekunden.","Эффективный алгоритм обрабатывает миллионы данных за секунды."]]},

  {de:"Digitalisierung",art:"die",pos:"noun",cat:"Technologie",level:"B2",ru:"цифровизация",ipa:"[diɡitaliˈziːʁʊŋ]",
   genus:"Femininum",plural:"die Digitalisierungen",
   def:"Die Umwandlung analoger Informationen und Abläufe in digitale Form.",
   pull:"Die Digitalisierung hat unseren Alltag grundlegend verändert.",
   koll:["die Digitalisierung vorantreiben","fortschreitende Digitalisierung"],
   ex:[["Die <strong>Digitalisierung</strong> verändert die Art, wie wir kommunizieren.","Цифровизация меняет то, как мы общаемся."],
       ["Viele Branchen profitieren von der <strong>Digitalisierung</strong>.","Многие отрасли выигрывают от цифровизации."]]},

  {de:"Kommunikation",art:"die",pos:"noun",cat:"Technologie",level:"B2",ru:"коммуникация",ipa:"[kɔmunikaˈt͡si̯oːn]",
   genus:"Femininum",plural:"die Kommunikationen",
   def:"Der Austausch von Informationen zwischen zwei oder mehreren Beteiligten.",
   pull:"Digitale Kommunikation kennt keine Grenzen mehr.",
   koll:["digitale Kommunikation","Kommunikation verbessern"],
   ex:[["Die digitale <strong>Kommunikation</strong> verbindet Menschen weltweit.","Цифровая коммуникация связывает людей по всему миру."]]},

  {de:"Vorteil",art:"der",pos:"noun",cat:"Technologie",level:"B1",ru:"преимущество",ipa:"[ˈfoːɐ̯taɪ̯l]",
   genus:"Maskulinum",plural:"die Vorteile",
   def:"Ein günstiger Umstand, der jemandem oder etwas nützt.",
   pull:"Jede Technologie bringt Vorteile und Risiken zugleich.",
   koll:["einen Vorteil haben","klarer Vorteil","Vorteile bieten"],
   ex:[["Ein großer <strong>Vorteil</strong> der Technik ist die Zeitersparnis.","Большое преимущество техники — экономия времени."]]},

  {de:"Nachteil",art:"der",pos:"noun",cat:"Technologie",level:"B1",ru:"недостаток",ipa:"[ˈnaːxtaɪ̯l]",
   genus:"Maskulinum",plural:"die Nachteile",
   def:"Ein ungünstiger Umstand, der jemandem oder etwas schadet.",
   pull:"Der größte Nachteil ist die wachsende Abhängigkeit.",
   koll:["einen Nachteil haben","der Nachteil überwiegt"],
   ex:[["Ein <strong>Nachteil</strong> der Digitalisierung ist der Datenschutz.","Недостаток цифровизации — защита данных."]]},

  {de:"Netzwerk",art:"das",pos:"noun",cat:"Technologie",level:"B2",ru:"сеть",ipa:"[ˈnɛt͡svɛʁk]",
   genus:"Neutrum",plural:"die Netzwerke",
   def:"Ein System aus miteinander verbundenen Elementen, das den Austausch von Daten ermöglicht.",
   pull:"Ein stabiles Netzwerk ist die Grundlage moderner Kommunikation.",
   koll:["soziales Netzwerk","ein Netzwerk aufbauen"],
   ex:[["Das soziale <strong>Netzwerk</strong> verbindet Millionen von Nutzern.","Социальная сеть связывает миллионы пользователей."]]},

  {de:"Datenschutz",art:"der",pos:"noun",cat:"Technologie",level:"B2",ru:"защита данных",ipa:"[ˈdaːtn̩ʃʊt͡s]",
   genus:"Maskulinum",plural:"—",
   def:"Der Schutz personenbezogener Daten vor Missbrauch und unbefugtem Zugriff.",
   pull:"Datenschutz wird im digitalen Zeitalter immer wichtiger.",
   koll:["den Datenschutz gewährleisten","Datenschutz beachten"],
   ex:[["Der <strong>Datenschutz</strong> ist ein zentrales Thema der Digitalisierung.","Защита данных — центральная тема цифровизации."]]},

  {de:"Effizienz",art:"die",pos:"noun",cat:"Technologie",level:"C1",ru:"эффективность",ipa:"[ɛfiˈt͡si̯ɛnt͡s]",
   genus:"Femininum",plural:"—",
   def:"Das Verhältnis zwischen erreichtem Nutzen und dem dafür nötigen Aufwand.",
   pull:"Mehr Effizienz bedeutet nicht automatisch mehr Zufriedenheit.",
   koll:["die Effizienz steigern","hohe Effizienz"],
   ex:[["Neue Technologien erhöhen die <strong>Effizienz</strong> der Arbeit.","Новые технологии повышают эффективность труда."]]},

  {de:"künstlich",art:"",pos:"adj",cat:"Technologie",level:"B2",ru:"искусственный",ipa:"[ˈkʏnstlɪç]",
   genus:"Adjektiv",plural:"—",
   def:"Vom Menschen nachgebildet oder hergestellt; nicht natürlich entstanden.",
   pull:"Künstliche Intelligenz prägt zunehmend unseren Alltag.",
   koll:["künstliche Intelligenz","künstliches Licht"],
   ex:[["<strong>Künstliche</strong> Intelligenz übernimmt immer mehr Aufgaben.","Искусственный интеллект берёт на себя всё больше задач."]]},
];

/* ---------- brush washes — same level+type → colour logic as Wörterbuch */
const WASH = {
  "B1|der":"B1_Der_Powdery-Blue_Horizontal-Soft.png","B1|die":"B1_Die_Powdery-Pink_BG-Wash.png",
  "B1|das":"B1_Das_Pale-Green_BG-Wash.png","B1|verb":"B1_Verbs_Sandy-Ochre_BG-Wash.png",
  "B1|adj":"B1_Adjectives_Lavender_BG-Wash.png",
  "B2|der":"B2_Der_Deep-Blue_BG-Wash.png","B2|die":"B2_Die_Magenta_BG-Wash.png",
  "B2|das":"B2_Das_Grass-Green_BG-Wash.png","B2|verb":"B2_Verbs_Terracotta_BG-Wash.png",
  "B2|adj":"B2_Adjectives_Amethyst_BG-Wash.png",
  "C1|der":"C1_Der_Indigo_BG-Wash.png","C1|die":"C1_Die_Burgundy_BG-Wash.png",
  "C1|das":"C1_Das_Emerald_BG-Wash.png","C1|verb":"C1_Verbs_Olive-Ochre_BG-Wash.png",
  "C1|adj":"C1_Adjectives_Plum_BG-Wash.png"
};
const typeKey = w => w.pos === "verb" ? "verb" : (w.pos === "adj" ? "adj" : w.art);
const brushOf = w => {
  const f = WASH[w.level + "|" + typeKey(w)] || "";
  return f ? `url('${new URL("worte/" + f, document.baseURI).href}')` : "none";
};

/* ---------- essay sections + their Klischees -------------------------- */
const SECTIONS = [
  {id:"einleitung", num:"01", title:"Einleitung",     sub:"These und Kontext zum Thema",
   ph:"Schreiben Sie Ihre Einleitung auf Deutsch…",
   kli:[
     {de:"In der heutigen Zeit ist <em>…</em> ein wichtiges Thema.", ru:"В наше время … — важная тема."},
     {de:"Immer mehr Menschen beschäftigen sich mit <em>…</em>", ru:"Всё больше людей занимаются …"},
     {de:"Das Thema <em>…</em> gewinnt zunehmend an Bedeutung.", ru:"Тема … приобретает всё большее значение."},
     {de:"Nicht zu bestreiten ist, dass <em>…</em>", ru:"Бесспорно, что …"},
     {de:"In den letzten Jahren hat sich <em>…</em> stark verändert.", ru:"За последние годы … сильно изменилось."},
     {de:"Die Frage, ob <em>…</em>, wird oft diskutiert.", ru:"Вопрос о том, … , часто обсуждается."},
   ]},
  {id:"arg1", num:"02", title:"Argument Eins", sub:"Das stärkste Argument zuerst",
   ph:"Formulieren Sie Ihr erstes Argument…",
   kli:[
     {de:"Ein wichtiges Argument dafür ist, dass <em>…</em>", ru:"Важный аргумент в пользу этого — что …"},
     {de:"Erstens lässt sich feststellen, dass <em>…</em>", ru:"Во-первых, можно констатировать, что …"},
     {de:"Ein klarer Vorteil besteht darin, dass <em>…</em>", ru:"Явное преимущество состоит в том, что …"},
     {de:"Hinzu kommt, dass <em>…</em>", ru:"К тому же …"},
     {de:"Dies zeigt sich besonders daran, dass <em>…</em>", ru:"Это особенно проявляется в том, что …"},
   ]},
  {id:"arg2", num:"03", title:"Argument Zwei", sub:"Gegenargument oder zweite Perspektive",
   ph:"Formulieren Sie Ihr zweites Argument…",
   kli:[
     {de:"Andererseits darf man nicht vergessen, dass <em>…</em>", ru:"С другой стороны, нельзя забывать, что …"},
     {de:"Kritiker behaupten jedoch, dass <em>…</em>", ru:"Однако критики утверждают, что …"},
     {de:"Ein weiterer Aspekt ist, dass <em>…</em>", ru:"Ещё один аспект — что …"},
     {de:"Demgegenüber steht die Tatsache, dass <em>…</em>", ru:"Этому противостоит тот факт, что …"},
     {de:"Trotzdem sollte man bedenken, dass <em>…</em>", ru:"Тем не менее следует учитывать, что …"},
   ]},
  {id:"schluss", num:"04", title:"Schluss", sub:"Fazit und Ausblick",
   ph:"Schreiben Sie Ihr Fazit…",
   kli:[
     {de:"Zusammenfassend lässt sich sagen, dass <em>…</em>", ru:"Подводя итог, можно сказать, что …"},
     {de:"Abschließend bin ich der Meinung, dass <em>…</em>", ru:"В заключение я считаю, что …"},
     {de:"Meiner Ansicht nach <em>…</em>", ru:"На мой взгляд …"},
     {de:"In Zukunft wird <em>…</em> noch wichtiger werden.", ru:"В будущем … станет ещё важнее."},
     {de:"Letztlich kommt es darauf an, dass <em>…</em>", ru:"В конечном счёте всё зависит от того, что …"},
   ]},
];

const TARGET_WORDS = 250;          // goal for the progress bar
const KLI_PER_PAGE = 3;

/* ---------- state ----------------------------------------------------- */
const state = {
  section: 0,
  kliPage: 0,
  text: {},                        // section.id -> innerHTML
  counts: {},                      // section.id -> word count
  favs: new Set(),
};
SECTIONS.forEach(s => { state.text[s.id] = ""; state.counts[s.id] = 0; });

const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));
const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");

function speak(t){
  if(!("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(t); u.lang = "de-DE"; u.rate = .9;
  speechSynthesis.cancel(); speechSynthesis.speak(u);
}
function countWords(html){
  const tmp = document.createElement("div"); tmp.innerHTML = html;
  const txt = (tmp.textContent || "").trim();
  return txt ? txt.split(/\s+/).length : 0;
}

/* =====================================================================
   Generic dropdown wiring (meta strip, niveau, nav)
   ===================================================================== */
function initDropdowns(){
  // the .nav-drop (Lernen) is owned by the shared site-header.js; here we only
  // wire the page-local .dd menus (Niveau, Thema, Form, Vorlage)
  $$(".dd").forEach(dd => {
    const btn = dd.querySelector(":scope > .dd-btn, :scope > button");
    if(!btn) return;
    btn.addEventListener("click", e => {
      e.stopPropagation();
      const wasOpen = dd.classList.contains("open");
      closeAllMenus();
      if(!wasOpen) dd.classList.add("open");
    });
    dd.querySelectorAll(".dd-menu button").forEach(opt => {
      opt.addEventListener("click", () => {
        const label = btn.querySelector(".lbl");
        if(label) label.textContent = opt.dataset.label || opt.textContent;
        dd.querySelectorAll(".dd-menu button").forEach(b => b.classList.remove("sel"));
        opt.classList.add("sel");
        dd.classList.remove("open");
        if(dd.id === "ddNiveau") $("#railNiveau").textContent = opt.textContent;
      });
    });
  });
  document.addEventListener("click", closeAllMenus);
  document.addEventListener("keydown", e => { if(e.key === "Escape") closeAllMenus(); });
}
function closeAllMenus(){ $$(".dd.open").forEach(d => d.classList.remove("open")); }

/* =====================================================================
   Essay map + document header
   ===================================================================== */
function renderMap(){
  const map = $("#essayMap"); map.innerHTML = "";
  SECTIONS.forEach((s, i) => {
    const b = document.createElement("button");
    b.className = "map-item" + (i === state.section ? " active" : "");
    b.innerHTML = `<div class="map-num">${s.num} ${s.title}</div>
                   <div class="map-words">${state.counts[s.id]} Wörter</div>`;
    b.onclick = () => selectSection(i);
    map.appendChild(b);
  });
}
function selectSection(i){
  saveEditor();
  state.section = i; state.kliPage = 0;
  renderMap(); renderDocHead(); loadEditor(); renderKlischees();
}
function renderDocHead(){
  const s = SECTIONS[state.section];
  $("#docEyebrow").textContent = currentThema().toUpperCase();
  $("#docTitle").textContent = s.title;
  $("#docSub").textContent = s.sub;
  $("#editable").setAttribute("data-placeholder", s.ph);
}
function currentThema(){
  const sel = $("#ddThema .dd-menu .sel");
  return sel ? sel.textContent : "Technologie";
}

/* =====================================================================
   Writing surface
   ===================================================================== */
function loadEditor(){
  const ed = $("#editable");
  ed.innerHTML = state.text[SECTIONS[state.section].id] || "";
  updateCounts();
}
function saveEditor(){
  const ed = $("#editable");
  const id = SECTIONS[state.section].id;
  state.text[id] = ed.innerHTML;
  state.counts[id] = countWords(ed.innerHTML);
}
function updateCounts(){
  const ed = $("#editable");
  const id = SECTIONS[state.section].id;
  const n = countWords(ed.innerHTML);
  state.counts[id] = n;
  $("#wordCount").textContent = n + (n === 1 ? " Wort" : " Wörter");
  const total = Object.values(state.counts).reduce((a,b)=>a+b,0);
  $("#progTotal").textContent = total;
  $("#progFill").style.width = Math.min(100, total / TARGET_WORDS * 100) + "%";
  $$("#essayMap .map-item")[state.section].querySelector(".map-words").textContent = n + " Wörter";
}
function initEditor(){
  $("#editable").addEventListener("input", updateCounts);
}

/* =====================================================================
   Pomodoro
   ===================================================================== */
const pomo = { total:25*60, left:25*60, running:false, timer:null, mode:25 };
function fmt(sec){ const m = Math.floor(sec/60), s = sec%60; return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`; }
function renderPomo(){ $("#pomoTime").textContent = fmt(pomo.left); }
function tickPomo(){
  pomo.left--; renderPomo();
  if(pomo.left <= 0){
    clearInterval(pomo.timer); pomo.running = false; setPlayIcon();
    $("#pomoSub").textContent = "Fertig — gut gemacht!";
    if("Notification" in window && Notification.permission === "granted")
      new Notification("Fokuszeit beendet", { body:"Zeit für eine kurze Pause." });
  }
}
function togglePomo(){
  pomo.running = !pomo.running;
  if(pomo.running){ pomo.timer = setInterval(tickPomo, 1000); $("#pomoSub").textContent = "Konzentriert bleiben…"; }
  else clearInterval(pomo.timer);
  setPlayIcon();
}
function resetPomo(){
  clearInterval(pomo.timer); pomo.running = false; pomo.left = pomo.mode*60;
  setPlayIcon(); renderPomo(); $("#pomoSub").textContent = pomo.mode === 25 ? "Fokuszeit" : "Pause";
}
function setMode(min){
  pomo.mode = min; $$(".pomo-mode button").forEach(b => b.classList.toggle("on", +b.dataset.min === min));
  resetPomo();
}
function setPlayIcon(){
  const PLAY = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
  const PAUSE = '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';
  $("#pomoPlay").innerHTML = pomo.running ? PAUSE : PLAY;
}
function initPomo(){
  setPlayIcon(); renderPomo();
  $("#pomoPlay").onclick = togglePomo;
  $("#pomoReset").onclick = resetPomo;
  $$(".pomo-mode button").forEach(b => b.onclick = () => setMode(+b.dataset.min));
  // use the autumn background once it exists; warm gradient is the fallback.
  // NB: absolute URL — a relative url() inside a CSS custom property is resolved
  // against the stylesheet in Safari (→ css/images/…), which 404s.
  const src = new URL("images/autumn.png", document.baseURI).href;
  const img = new Image();
  img.onload = () => {
    const el = $("#pomodoro");
    el.style.setProperty("--pomo-img", `url("${src}")`);
    el.classList.add("has-img");
  };
  img.src = src;
}

/* =====================================================================
   Klischees carousel
   ===================================================================== */
function renderKlischees(){
  const s = SECTIONS[state.section];
  const pages = Math.max(1, Math.ceil(s.kli.length / KLI_PER_PAGE));
  state.kliPage = Math.min(state.kliPage, pages - 1);
  $("#kliTitle").innerHTML = `Klischees <b>· ${s.title}</b>`;
  $("#kliCount").textContent = `${state.kliPage + 1} / ${pages}`;
  $("#kliPrev").disabled = state.kliPage === 0;
  $("#kliNext").disabled = state.kliPage >= pages - 1;
  const start = state.kliPage * KLI_PER_PAGE;
  const list = $("#kliList"); list.innerHTML = "";
  s.kli.slice(start, start + KLI_PER_PAGE).forEach(k => {
    const div = document.createElement("div");
    div.className = "kli";
    div.innerHTML = `<div class="kli-de">${k.de}</div><div class="kli-ru">${k.ru}</div>`;
    div.title = "Zum Einfügen klicken";
    div.onclick = () => insertCliche(k.de);
    list.appendChild(div);
  });
}
function insertCliche(html){
  const ed = $("#editable"); ed.focus();
  const plain = html.replace(/<\/?em>/g, "");
  document.execCommand("insertText", false, (ed.textContent ? " " : "") + plain + " ");
  updateCounts();
}
function initKlischees(){
  $("#kliPrev").onclick = () => { state.kliPage--; renderKlischees(); };
  $("#kliNext").onclick = () => { state.kliPage++; renderKlischees(); };
  // faint per-slot backgrounds, enabled only when the images are present
  const probe = new Image();
  probe.onload = () => $("#kliList").classList.add("has-bg");
  probe.src = "images/kli-1.png";
}

/* =====================================================================
   Wörterbuch panel + word-card popover
   ===================================================================== */
function renderWordList(q=""){
  const list = $("#wbList"); list.innerHTML = "";
  const term = q.trim().toLowerCase();
  const items = WORDS.filter(w =>
    !term || w.de.toLowerCase().includes(term) || w.ru.toLowerCase().includes(term));
  if(!items.length){ list.innerHTML = `<div class="wb-empty">Keine Begriffe gefunden.</div>`; return; }
  items.forEach(w => {
    const row = document.createElement("div");
    row.className = "wb-row";
    row.style.setProperty("--brush", brushOf(w));
    const art = w.art ? `<span class="art">${w.art} </span>` : "";
    row.innerHTML = `
      <span class="wb-wash" aria-hidden="true"></span>
      <span class="wb-de">${art}${w.de}</span>
      <span class="wb-ru">${w.ru}</span>
      <button class="wb-star${state.favs.has(w.de) ? " on" : ""}" aria-label="Merken">
        <svg viewBox="0 0 24 24" fill="${state.favs.has(w.de) ? "currentColor" : "none"}" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 18.3 6.2 21.4l1.1-6.5L2.6 9.8l6.5-.9z"/></svg>
      </button>`;
    row.addEventListener("click", e => {
      if(e.target.closest(".wb-star")) return;
      $$(".wb-row").forEach(r => r.classList.remove("active"));
      row.classList.add("active");
      openCard(w, row);
    });
    row.querySelector(".wb-star").addEventListener("click", e => {
      e.stopPropagation();
      const star = e.currentTarget;
      if(state.favs.has(w.de)){ state.favs.delete(w.de); star.classList.remove("on"); star.querySelector("svg").setAttribute("fill","none"); }
      else { state.favs.add(w.de); star.classList.add("on"); star.querySelector("svg").setAttribute("fill","currentColor"); }
    });
    list.appendChild(row);
  });
}

function cardHTML(w){
  const art = w.art ? `<span class="art">${w.art}</span> ` : "";
  const posLabel = w.pos === "verb" ? "Verb" : w.pos === "adj" ? "Adjektiv" : "Substantiv";
  const params = w.pos === "noun"
    ? `<div class="g-param"><span class="g-k">Genus</span><b>${w.genus}</b></div>
       <div class="g-param"><span class="g-k">Plural</span><b>${w.plural}</b></div>`
    : `<div class="g-param"><span class="g-k">Wortart</span><b>${w.genus}</b></div>`;
  const koll = w.koll || [];
  const useBlock = koll.length ? `
    <div class="g-use"><span class="g-use-lab">Verwendung</span>
      <span class="g-use-rule">${koll[0]}</span>
      ${koll[1] ? `<span class="g-use-ex">${koll[1]}</span>` : ""}</div>` : "";
  const examples = (w.ex || []).map(([de,ru],i) => `
    <div class="ex"><span class="ex-n">${String(i+1).padStart(2,"0")}</span>
      <div class="ex-body"><p class="ex-de">${de}</p>${ru ? `<p class="ex-ru">${ru}</p>` : ""}</div></div>`).join("");
  return `
    <button class="d-close" id="dClose" type="button" aria-label="Schließen">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
    <div class="d-head">
      <div class="d-meta"><span class="d-cat"><span class="hl">${posLabel}</span> · ${w.cat}</span><span class="d-level">${w.level}</span></div>
      <div class="d-word">${art}${w.de}</div>
      <div class="d-tools">
        <span class="d-ipa">${w.ipa || ""}</span>
        <button class="d-hear" id="dHear" type="button">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 9v6h4l5 5V4L9 9H5z"/><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>
          Aussprache
        </button>
      </div>
      <div class="d-ru">${w.ru}</div>
    </div>
    <div class="d-body">
      <section><div class="lab">Bedeutung</div><p class="def">${w.def}</p>
        ${w.pull ? `<blockquote class="pull">${w.pull}</blockquote>` : ""}</section>
      <section><div class="lab">Grammatik</div>
        <div class="g-params">${params}</div>${useBlock}</section>
      ${examples ? `<section><div class="lab">Beispiele</div><div class="ex-list">${examples}</div></section>` : ""}
    </div>`;
}

let activeRow = null;

function openCard(w, rowEl){
  const card = $("#wordCard"), overlay = $("#wcOverlay");
  activeRow = rowEl;
  card.innerHTML = cardHTML(w);
  overlay.classList.add("open");

  // position: to the LEFT of the clicked row, over the essay surface
  const cardW = Math.min(430, window.innerWidth - 32);
  card.style.width = cardW + "px";
  card.style.top = "0px"; card.style.right = "auto"; card.style.visibility = "hidden";
  card.classList.add("open");
  requestAnimationFrame(() => {
    const r = rowEl.getBoundingClientRect();
    let left = r.left - cardW - 26;
    if(left < 16) left = 16;                                  // never run off-screen
    card.style.left = left + "px";
    const h = card.offsetHeight;
    let top = r.top + r.height/2 - h/2;
    top = Math.max(16, Math.min(top, window.innerHeight - h - 16));
    card.style.top = top + "px";
    card.style.visibility = "visible";
    requestAnimationFrame(updateLink);                        // after layout settles
  });

  card.querySelector("#dClose").onclick = closeCard;
  const hear = card.querySelector("#dHear");
  if(hear) hear.onclick = () => speak((w.art ? w.art + " " : "") + w.de);
}
function closeCard(){
  $("#wordCard").classList.remove("open");
  $("#wcOverlay").classList.remove("open");
  $$(".wb-row").forEach(r => r.classList.remove("active"));
  activeRow = null; hideLink();
}
function initWordPanel(){
  renderWordList();
  $("#wbSearch").addEventListener("input", e => renderWordList(e.target.value));
  $("#wcOverlay").addEventListener("click", closeCard);
  document.addEventListener("keydown", e => { if(e.key === "Escape") closeCard(); });
  // keep the connector glued while either side moves
  window.addEventListener("scroll", updateLink, {passive:true});
  $("#wbList").addEventListener("scroll", updateLink, {passive:true});
}

/* ---------- live orange connector — same look & logic as the Wörterbuch */
function hideLink(){ $("#linkLine").setAttribute("hidden",""); }
function updateLink(){
  const line = $("#linkLine");
  if(!$("#wordCard").classList.contains("open") || !activeRow){ hideLink(); return; }
  const wordEl = activeRow.querySelector(".wb-de");
  const titleEl = $("#wordCard .d-word");
  if(!wordEl || !titleEl){ hideLink(); return; }
  // hide if the word scrolled out of the list's visible window
  const listR = $("#wbList").getBoundingClientRect();
  const wR = wordEl.getBoundingClientRect();
  if(wR.bottom < listR.top + 2 || wR.top > listR.bottom - 2){ hideLink(); return; }

  const cR = $("#wordCard").getBoundingClientRect();
  const sx = cR.right - 6,        sy = titleEl.getBoundingClientRect().top + titleEl.getBoundingClientRect().height/2; // card side
  const ex = wR.left - 8,         ey = wR.top + wR.height/2;                                                           // list word
  const dir = Math.sign(ex - sx) || 1;
  const k = Math.max(70, Math.abs(ex - sx) * 0.4);
  const c1x = sx + dir*k, c2x = ex - dir*k;
  $("#linkPath").setAttribute("d",
    `M ${sx.toFixed(1)} ${sy.toFixed(1)} C ${c1x.toFixed(1)} ${sy.toFixed(1)}, ${c2x.toFixed(1)} ${ey.toFixed(1)}, ${ex.toFixed(1)} ${ey.toFixed(1)}`);
  $("#linkAnchor").setAttribute("cx", sx.toFixed(1)); $("#linkAnchor").setAttribute("cy", sy.toFixed(1));
  $("#linkDot").setAttribute("cx", ex.toFixed(1));    $("#linkDot").setAttribute("cy", ey.toFixed(1));
  line.removeAttribute("hidden");
}

/* ---------- analysieren CTA ------------------------------------------- */
function initAnalyze(){
  const btn = $("#btnAnalyze"); if(!btn) return;
  btn.addEventListener("click", () => {
    if(btn.disabled) return;
    const label = btn.querySelector(".lbl"), prev = label.textContent;
    btn.disabled = true; label.textContent = "Analyse folgt…";
    setTimeout(() => { btn.disabled = false; label.textContent = prev; }, 1600);
  });
}

/* =====================================================================
   Boot  (theme toggle + Lernen dropdown live in js/site-header.js)
   ===================================================================== */
function boot(){
  initDropdowns();
  renderMap(); renderDocHead(); loadEditor();
  initEditor();
  initPomo();
  renderKlischees(); initKlischees();
  initWordPanel();
  initAnalyze();
  // re-anchor the open card on resize
  window.addEventListener("resize", () => { if($("#wordCard").classList.contains("open")) closeCard(); });
}
if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();

})();

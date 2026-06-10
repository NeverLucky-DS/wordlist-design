/* =====================================================================
   Deutsch Essay · Editor (Schreiben) — interactions
   Backend-enabled editor with inline annotation UX.
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
  text: {},                        // section.id -> plain text
  counts: {},                      // section.id -> word count
  favs: new Set(),
  essayId: null,
  saveTimer: null,
  apiReady: false,
  backendWords: [],
  backendPhrases: {},
  errorsBySection: { einleitung: [], arg1: [], arg2: [], schluss: [] },
  selectedAnnotation: null,
  reanchorTimer: null,
  annotationRuleOpen: false,
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
  const txt = String(html || "").trim();
  return txt ? txt.split(/\s+/).length : 0;
}

function partToApi(partId){
  if(partId === "einleitung") return "einleitung";
  if(partId === "arg1") return "argument1";
  if(partId === "arg2") return "argument2";
  return "schluss";
}

function apiToPart(partId){
  if(partId === "argument1") return "arg1";
  if(partId === "argument2") return "arg2";
  if(partId === "einleitung") return "einleitung";
  return "schluss";
}

function plainText(html){
  return String(html || "")
    .replace(/\u00a0/g, " ")
    .replace(/\r/g, "");
}

function buildEssayTextForBackend(){
  return [
    `Einleitung:\n${plainText(state.text.einleitung).trim()}`,
    `Argument Eins:\n${plainText(state.text.arg1).trim()}`,
    `Argument Zwei:\n${plainText(state.text.arg2).trim()}`,
    `Schluss:\n${plainText(state.text.schluss).trim()}`,
  ].join("\n\n");
}

/* Russian gloss of the governed case, e.g. "von + Dat." → "дательный падеж" */
function caseGlossRu(rule){
  const m = /\b(Akk|Dat|Gen|Nom)/i.exec(rule || "");
  if(!m) return "";
  return {akk:"винительный падеж",dat:"дательный падеж",gen:"родительный падеж",nom:"именительный падеж"}[m[1].toLowerCase()] || "";
}

/* highlight the headword + its known inflected forms in an example (escaped HTML) */
function highlightForms(html, forms){
  if(/<\/?b>/.test(html)) return html;            // already marked (LLM bold)
  const list = [...new Set(forms
    .map(f => String(f||"").replace(/^(der|die|das)\s+/i,"").trim())
    .filter(f => f.length>=3 && /^\p{L}/u.test(f)))].sort((a,b)=>b.length-a.length);
  if(!list.length) return html;
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");
  let re; try{ re = new RegExp("(?<!\\p{L})("+list.map(esc).join("|")+")(?!\\p{L})","giu"); }
  catch(e){ return html; }
  return html.replace(re, "<b>$1</b>");
}

function toEditorWord(apiWord){
  const w = apiWord || {};
  const posRaw = (w.word_type || "").toLowerCase();
  const pos = posRaw.includes("verb") ? "verb" : (posRaw.includes("adj") ? "adj" : "noun");
  const article = w.article ? String(w.article).toLowerCase() : "";
  const grammar = w.grammar_data || {};
  const decl = grammar.declension || {};
  const base = (w.german || "").replace(/^(der|die|das)\s+/i, "");
  const formStr = v => (v && typeof v === "object")
    ? (v["er/sie/es"] || v.ich || Object.values(v)[0] || "") : (v || "");

  const genus = pos === "verb" ? "Verb"
    : pos === "adj" ? "Adjektiv"
    : article === "die" ? "Femininum"
    : article === "der" ? "Maskulinum"
    : article === "das" ? "Neutrum" : "Substantiv";

  // compact key-forms spec line + the forms we use to highlight examples
  const spec = [];                       // [label, value, wide?]
  const forms = new Set([base]);
  const addForm = s => { s = String(s||"").replace(/^(der|die|das)\s+/i,"").trim(); if(s.length>=3) forms.add(s); };
  let hint = "";

  if(pos === "noun"){
    const plural = (decl.Nominativ && decl.Nominativ.plural) || decl.Plural || decl.plural || "";
    const genitiv = (decl.Genitiv && decl.Genitiv.singular) || decl["Genitiv Singular"] || decl.genitiv_singular || "";
    spec.push(["Genus", genus]);
    if(plural && !["–","—"].includes(plural)){ spec.push(["Plural", plural]); addForm(plural); addForm(plural+"n"); }
    if(genitiv && genitiv!=="–"){ spec.push(["Genitiv", genitiv]); addForm(genitiv); }
    ["s","es","e","en","n","ern","er"].forEach(suf => addForm(base+suf));
    const g = {der:"мужской род",die:"женский род",das:"средний род"}[article]; if(g) hint = g;
  } else if(pos === "verb"){
    const pres = decl.Präsens || decl.praesens || decl.present || {};
    const er = pres["er/sie/es"] || pres.er || "";
    const praet = formStr(decl["Präteritum"] || decl.prateritum || decl.simple_past);
    const part = formStr(decl["Partizip II"] || decl.partizip2 || decl.perfect);
    const hilf = decl.hilfsverb || decl.Hilfsverb || "haben";
    spec.push(["Hilfsverb", hilf]);
    if(er){ spec.push(["Präsens (er)", er]); addForm(er.split(" ")[0]); }
    if(praet){ spec.push(["Präteritum", praet]); addForm(String(praet).split(" ")[0]); }
    if(part){ spec.push(["Perfekt", (hilf==="sein"?"ist ":"hat ")+part]); addForm(part); }
    hint = "вспом. глагол «"+hilf+"»";
  } else { // adjective
    const positiv = decl.positiv || decl.Positiv || base;
    const komp = decl.komparativ || decl.Komparativ || "—";
    const sup  = decl.superlativ || decl.Superlativ || "—";
    spec.push(["Steigerung", `${positiv} → ${komp} → ${sup}`, true]);
    ["","e","er","es","en","em","ere","eren","sten"].forEach(suf => addForm(base+suf));
    [positiv,komp,sup].forEach(addForm);
  }

  const examples = Array.isArray(w.examples) ? w.examples.slice(0, 3) : [];
  const ex = examples.map((e) => {
    const txt = (e && typeof e === "object") ? (e.text_de || "") : String(e || "");
    const ru  = (e && typeof e === "object") ? (e.text_ru || "") : "";
    const html = esc(txt).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
    return [highlightForms(html, [...forms]), esc(ru)];
  });

  return {
    de: w.german || "",
    art: article,
    pos,
    cat: (Array.isArray(w.topics) && w.topics[0]) ? w.topics[0] : "Thema",
    level: w.level || "B1",
    ru: w.translation_ru || "",
    ipa: grammar.ipa || "",
    spec,
    hint,
    rektion: grammar.rektion || "",
    readyPhrase: grammar.ready_phrase || "",
    def: grammar.definition || "",
    ex,
  };
}

function setAnalyzeStatus(text){
  const btn = $("#btnAnalyze");
  if(!btn) return;
  const label = btn.querySelector(".lbl");
  if(label) label.textContent = text;
}

function setSavedStatus(text){
  const el = document.querySelector(".saved");
  if(!el) return;
  const dot = '<span class="dot"></span>';
  el.innerHTML = `${dot} ${text}`;
}

async function persistEssayNow(){
  const text = buildEssayTextForBackend();
  const payload = {
    title: currentThema(),
    text,
    essay_type: ($("#ddForm .dd-menu .sel") || {}).textContent || "argumentativ",
    topic: currentThema().toLowerCase(),
    level: ($("#ddNiveau .dd-menu .sel") || {}).textContent || "B1",
  };
  if(!state.apiReady || !window.EditorApi) return;
  try{
    if(state.essayId){
      await window.EditorApi.updateEssay(state.essayId, payload);
    }else{
      const created = await window.EditorApi.createEssay(payload);
      state.essayId = created.id;
    }
    setSavedStatus("Automatisch gespeichert");
  }catch(err){
    setSavedStatus("Speichern fehlgeschlagen");
    console.error("save essay failed", err);
  }
}

function schedulePersistEssay(){
  if(!state.apiReady || !window.EditorApi) return;
  if(state.saveTimer) clearTimeout(state.saveTimer);
  setSavedStatus("Speichern...");
  state.saveTimer = setTimeout(() => {
    persistEssayNow();
  }, 1200);
}

function applyPartFeedback(event){
  if(!event || !event.part) return;
  const partId = apiToPart(event.part);
  const sectionIdx = SECTIONS.findIndex(s => s.id === partId);
  if(sectionIdx < 0) return;
  const section = SECTIONS[sectionIdx];
  if(event.feedback_ru){
    section.feedback = event.feedback_ru;
    if(state.section === sectionIdx) renderVerdict();
  }
}

/* the tutor's verdict — rendered at the END of the section text */
function renderVerdict(){
  const s = SECTIONS[state.section];
  const box = $("#partVerdict");
  if(!box) return;
  if(s && s.feedback){
    $("#verdictText").textContent = s.feedback;
    box.removeAttribute("hidden");
  }else{
    box.setAttribute("hidden", "");
  }
}

function escapeHtml(text){
  return String(text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function normalizeErrorKey(sectionId, err){
  const base = `${sectionId}:${err.excerpt || ""}:${err.start || 0}:${err.type || ""}`;
  let hash = 0;
  for(let i = 0; i < base.length; i += 1){
    hash = (hash * 31 + base.charCodeAt(i)) | 0;
  }
  return `e${Math.abs(hash).toString(36)}`;
}

function resolveAnnotationKind(err){
  const explicit = String(err.annotation_kind || "").toLowerCase();
  if(["critical", "style", "b2_potential", "good_fragment", "suggestion"].includes(explicit)){
    return explicit;
  }
  const severity = String(err.severity || "").toLowerCase();
  const type = String(err.type || "").toLowerCase();
  if(severity === "suggestion") return "suggestion";
  if(type === "grammar" || severity === "critical") return "critical";
  if(type === "vocabulary" && err.b2_variant_de) return "b2_potential";
  if(type === "good" || type === "strength") return "good_fragment";
  return "style";
}

function findExcerptIndex(text, excerpt, hintStart){
  const needle = String(excerpt || "").trim();
  if(!needle) return -1;
  if(typeof hintStart !== "number") return text.indexOf(needle);
  let best = -1;
  let bestDist = Infinity;
  let idx = text.indexOf(needle);
  while(idx >= 0){
    const dist = Math.abs(idx - hintStart);
    if(dist < bestDist){
      best = idx;
      bestDist = dist;
    }
    idx = text.indexOf(needle, idx + 1);
  }
  return best;
}

function normalizeErrorForSection(err, text){
  const plain = String(text || "");
  if(!plain.trim()) return null;
  const out = { ...err };
  const excerpt = String(out.excerpt || "").trim();
  let start = Number.isFinite(out.start) ? Number(out.start) : 0;
  let end = Number.isFinite(out.end) ? Number(out.end) : start;
  if(excerpt){
    const idx = findExcerptIndex(plain, excerpt, start);
    if(idx >= 0){
      start = idx;
      end = idx + excerpt.length;
    }
  }
  start = Math.max(0, Math.min(start, Math.max(0, plain.length - 1)));
  end = Math.max(start + 1, Math.min(end, plain.length));
  if(end <= start) return null;
  out.start = start;
  out.end = end;
  out.excerpt = excerpt || plain.slice(start, end);
  out.orphaned = false;
  return out;
}

function mergeOverlappingErrors(errors){
  if(!Array.isArray(errors) || errors.length <= 1) return errors || [];
  const sorted = [...errors].sort((a,b) => a.start - b.start);
  const out = [];
  for(const err of sorted){
    const prev = out[out.length - 1];
    if(!prev){
      out.push(err);
      continue;
    }
    const prevExcerpt = String(prev.excerpt || "").trim();
    const thisExcerpt = String(err.excerpt || "").trim();
    const sameExcerpt = prevExcerpt && thisExcerpt && prevExcerpt === thisExcerpt;
    if(sameExcerpt && err.start <= prev.end){
      out[out.length - 1] = { ...prev, end: Math.max(prev.end, err.end) };
      continue;
    }
    out.push(err);
  }
  return out;
}

function mapErrorsToSections(events){
  const mapped = { einleitung: [], arg1: [], arg2: [], schluss: [] };
  const incoming = Array.isArray(events) ? events : [];
  for(const raw of incoming){
    const apiPart = String(raw.part || "").toLowerCase();
    const sectionId = apiToPart(apiPart);
    if(!mapped[sectionId]) continue;
    const sectionText = state.text[sectionId] || "";
    const normalized = normalizeErrorForSection(raw, sectionText);
    if(!normalized) continue;
    mapped[sectionId].push({
      ...normalized,
      annotation_kind: resolveAnnotationKind(normalized),
      error_id: normalizeErrorKey(sectionId, normalized),
    });
  }
  Object.keys(mapped).forEach((k) => {
    mapped[k] = mergeOverlappingErrors(mapped[k]);
  });
  return mapped;
}

function reanchorSectionErrors(sectionId){
  const source = state.errorsBySection[sectionId] || [];
  const text = state.text[sectionId] || "";
  if(!text.trim()){
    state.errorsBySection[sectionId] = source.map((e) => ({ ...e, orphaned: true }));
    return;
  }
  state.errorsBySection[sectionId] = source.map((err) => {
    const excerpt = String(err.excerpt || "").trim();
    if(excerpt){
      const idx = findExcerptIndex(text, excerpt, err.start);
      if(idx < 0) return { ...err, orphaned: true };
      return { ...err, start: idx, end: idx + excerpt.length, orphaned: false };
    }
    const start = Math.max(0, Math.min(Number(err.start) || 0, Math.max(0, text.length - 1)));
    const end = Math.max(start + 1, Math.min(Number(err.end) || start + 1, text.length));
    if(end <= start || !text.slice(start, end).trim()) return { ...err, orphaned: true };
    return { ...err, start, end, orphaned: false };
  });
}

function scheduleReanchor(){
  if(state.reanchorTimer) clearTimeout(state.reanchorTimer);
  state.reanchorTimer = setTimeout(() => {
    const sectionId = SECTIONS[state.section].id;
    reanchorSectionErrors(sectionId);
    renderEditorText();
    if(state.selectedAnnotation){
      const active = (state.errorsBySection[state.selectedAnnotation.sectionId] || []).find(
        (e) => e.error_id === state.selectedAnnotation.error_id && !e.orphaned
      );
      if(!active) closeAnnotationPopover();
      else updateAnnotationConnector();
    }
  }, 180);
}

function renderEditorText(){
  const sectionId = SECTIONS[state.section].id;
  const ed = $("#editable");
  const text = state.text[sectionId] || "";
  const selection = window.getSelection();
  const hadFocus = document.activeElement === ed && selection && selection.rangeCount > 0;
  const caretOffset = hadFocus ? getCaretCharacterOffsetWithin(ed) : null;
  const errors = (state.errorsBySection[sectionId] || [])
    .filter((e) => !e.orphaned)
    .map((e) => {
      const startRaw = Number(e.start);
      const endRaw = Number(e.end);
      const start = Number.isFinite(startRaw) ? Math.max(0, Math.min(startRaw, text.length)) : 0;
      const end = Number.isFinite(endRaw) ? Math.max(start + 1, Math.min(endRaw, text.length)) : start + 1;
      return { ...e, start, end };
    })
    .filter((e) => e.end > e.start)
    .sort((a,b) => a.start - b.start);
  if(!errors.length){
    ed.innerHTML = textToHtml(text);
    if(hadFocus && caretOffset != null){
      setCaretCharacterOffsetWithin(ed, Math.min(caretOffset, text.length));
    }
    return;
  }
  let html = "";
  let cursor = 0;
  for(const err of errors){
    if(err.start < cursor) continue;
    const before = textToHtml(text.slice(cursor, err.start));
    const mid = textToHtml(text.slice(err.start, err.end));
    const kind = resolveAnnotationKind(err);
    html += `${before}<span data-annotation="${kind}" data-error-id="${err.error_id}">${mid}</span>`;
    cursor = err.end;
  }
  html += textToHtml(text.slice(cursor));
  ed.innerHTML = html;
  if(hadFocus && caretOffset != null){
    setCaretCharacterOffsetWithin(ed, Math.min(caretOffset, text.length));
  }
}

function textToHtml(value){
  const escaped = escapeHtml(String(value || ""));
  return escaped
    .replace(/\n/g, "<br>")
    .replace(/ {2}/g, " &nbsp;")
    .replace(/(^ )|( $)/g, "&nbsp;");
}

function readEditorText(element){
  const out = [];
  const walk = (node) => {
    if(node.nodeType === Node.TEXT_NODE){
      out.push(node.nodeValue || "");
      return;
    }
    if(node.nodeType !== Node.ELEMENT_NODE) return;
    const tag = node.tagName;
    if(tag === "BR"){
      out.push("\n");
      return;
    }
    if(tag === "DIV" || tag === "P"){
      const before = out.length;
      node.childNodes.forEach(walk);
      if(out.length > before){
        const last = out[out.length - 1] || "";
        if(!last.endsWith("\n")) out.push("\n");
      }
      return;
    }
    node.childNodes.forEach(walk);
  };
  element.childNodes.forEach(walk);
  return out.join("").replace(/\n+$/,"");
}

function getCaretCharacterOffsetWithin(element){
  const sel = window.getSelection();
  if(!sel || !sel.rangeCount) return 0;
  const range = sel.getRangeAt(0).cloneRange();
  const pre = document.createRange();
  pre.selectNodeContents(element);
  pre.setEnd(range.endContainer, range.endOffset);
  return readEditorTextFromRange(pre);
}

function setCaretCharacterOffsetWithin(element, offset){
  const selection = window.getSelection();
  if(!selection) return;
  const target = Math.max(0, Number(offset) || 0);
  const range = createRangeAtTextOffset(element, target);
  selection.removeAllRanges();
  selection.addRange(range);
}

function readEditorTextFromRange(range){
  const fragment = range.cloneContents();
  const holder = document.createElement("div");
  holder.appendChild(fragment);
  return readEditorText(holder).length;
}

function createRangeAtTextOffset(root, target){
  let remaining = target;
  let found = null;

  const walk = (node) => {
    if(found) return;
    if(node.nodeType === Node.TEXT_NODE){
      const value = node.nodeValue || "";
      if(remaining <= value.length){
        found = { node, offset: remaining };
        return;
      }
      remaining -= value.length;
      return;
    }
    if(node.nodeType !== Node.ELEMENT_NODE) return;
    const tag = node.tagName;
    if(tag === "BR"){
      if(remaining <= 1){
        const parent = node.parentNode;
        const idx = Array.prototype.indexOf.call(parent.childNodes, node);
        found = { node: parent, offset: idx + 1 };
        return;
      }
      remaining -= 1;
      return;
    }
    if(tag === "DIV" || tag === "P"){
      const before = remaining;
      node.childNodes.forEach(walk);
      if(found) return;
      if(before !== remaining){
        if(remaining <= 1){
          const parent = node.parentNode;
          const idx = Array.prototype.indexOf.call(parent.childNodes, node);
          found = { node: parent, offset: idx + 1 };
          return;
        }
        remaining -= 1;
      }
      return;
    }
    node.childNodes.forEach(walk);
  };

  root.childNodes.forEach(walk);
  const range = document.createRange();
  if(found){
    range.setStart(found.node, found.offset);
    range.collapse(true);
    return range;
  }
  range.selectNodeContents(root);
  range.collapse(false);
  return range;
}

function normalizeExplanation(text){
  const lines = String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const rows = lines.map((line) => {
    const idx = line.indexOf(":");
    if(idx < 1) return null;
    return { label: line.slice(0, idx).trim(), value: line.slice(idx + 1).trim() };
  }).filter(Boolean);
  return rows.length ? rows : [{ label: "Объяснение", value: String(text || "").trim() }];
}

function splitStrategies(text){
  return String(text || "")
    .split(/\d\)\s+/g)
    .map((line) => line.trim())
    .filter(Boolean);
}

function annotationCardHTML(err){
  const explanation = normalizeExplanation(err.explanation_ru || "");
  const whatWrong = err.what_wrong_ru || explanation.find((x) => x.label.toLowerCase().includes("что"))?.value || explanation[0]?.value || "Есть неточность в формулировке.";
  const whyBad = err.why_bad_ru || explanation.find((x) => x.label.toLowerCase().includes("почему"))?.value || "";
  const hints = splitStrategies(err.how_to_fix_ru || "");
  const light = ["suggestion", "style"].includes(resolveAnnotationKind(err));
  const phrases = Array.isArray(err.study_phrases_de) ? err.study_phrases_de.slice(0, 4) : [];

  const variants = [];
  if(err.b1_variant_de){
    variants.push(
      `<div class="annotation-variant annotation-variant-b1">
        <span class="annotation-variant-level">B1</span>
        <p>${escapeHtml(err.b1_variant_de)}</p>
        ${err.b1_explain_ru ? `<p class="annotation-variant-explain">${escapeHtml(err.b1_explain_ru)}</p>` : ""}
        <button type="button" class="btn-ghost" data-annotation-action="insert" data-annotation-text="${encodeURIComponent(err.b1_variant_de)}">Einfügen</button>
      </div>`
    );
  }
  if(err.b2_variant_de){
    variants.push(
      `<div class="annotation-variant annotation-variant-b2">
        <span class="annotation-variant-level">B2</span>
        <p>${escapeHtml(err.b2_variant_de)}</p>
        ${err.b2_explain_ru ? `<p class="annotation-variant-explain">${escapeHtml(err.b2_explain_ru)}</p>` : ""}
        <button type="button" class="btn-ghost" data-annotation-action="insert" data-annotation-text="${encodeURIComponent(err.b2_variant_de)}">Einfügen</button>
      </div>`
    );
  }

  const tipsHTML = hints.length ? `
    <section class="annotation-section annotation-section-tips">
      <h4 class="annotation-section-title">Как улучшить</h4>
      <ol class="annotation-tips">
        ${hints.map((x) => `<li>${escapeHtml(x)}</li>`).join("")}
      </ol>
    </section>
  ` : "";

  const variantsHTML = variants.length && !light ? `
    <section class="annotation-section">
      <h4 class="annotation-section-title">Варианты с вашей мыслью</h4>
      <div class="annotation-variants">${variants.join("")}</div>
    </section>
  ` : "";

  const phrasesHTML = phrases.length ? `
    <section class="annotation-section">
      <h4 class="annotation-section-title">Конструкции для обучения</h4>
      <div class="annotation-phrases">
        ${phrases.map((phrase) => `
          <div class="annotation-variant">
            <p>${escapeHtml(phrase)}</p>
            <button type="button" class="btn-ghost" data-annotation-action="insert" data-annotation-text="${encodeURIComponent(phrase)}">Einfügen</button>
            <button type="button" class="btn-ghost" data-annotation-action="train" data-annotation-text="${encodeURIComponent(phrase)}">Training</button>
          </div>
        `).join("")}
      </div>
    </section>
  ` : "";

  const cardClass = light ? "annotation-card annotation-card--compact" : "annotation-card";
  return `
    <div class="${cardClass}">
    <section class="annotation-section annotation-section-problem">
      <h4 class="annotation-section-title">Что не так</h4>
      <p class="annotation-popover-lead">${escapeHtml(whatWrong)}</p>
    </section>
    ${(!light && whyBad) ? `
      <section class="annotation-section">
        <h4 class="annotation-section-title">Почему важно</h4>
        <p class="annotation-popover-sub">${escapeHtml(whyBad)}</p>
      </section>
    ` : ""}
    ${variantsHTML}
    ${tipsHTML}
    ${phrasesHTML}
    </div>
  `;
}

function connectorPath(anchorRect, cardRect, side){
  const x1 = side === "right" ? anchorRect.right - 2 : anchorRect.left + 2;
  const y1 = anchorRect.top + anchorRect.height / 2;
  const x2 = side === "right" ? cardRect.left + 8 : cardRect.right - 8;
  const y2 = cardRect.top + Math.min(48, cardRect.height * 0.2);
  const c1x = x1 + (side === "right" ? 40 : -40);
  const c2x = x2 + (side === "right" ? -30 : 30);
  return `M ${x1} ${y1} C ${c1x} ${y1}, ${c2x} ${y2}, ${x2} ${y2}`;
}

function computePopoverPosition(anchorRect, cardHeight){
  const gap = 28;
  const width = 380;
  const margin = 16;
  const spaceRight = window.innerWidth - anchorRect.right - gap - margin;
  const spaceLeft = anchorRect.left - gap - margin;
  const side = (spaceRight >= width || spaceRight >= spaceLeft) ? "right" : "left";
  let left = side === "right" ? anchorRect.right + gap : anchorRect.left - gap - width;
  left = Math.max(margin, Math.min(left, window.innerWidth - width - margin));
  let top = anchorRect.top + anchorRect.height / 2 - cardHeight / 2;
  top = Math.max(margin, Math.min(top, window.innerHeight - cardHeight - margin));
  return { top, left, side };
}

function closeAnnotationPopover(){
  state.selectedAnnotation = null;
  state.annotationRuleOpen = false;
  $("#annotationPopover").setAttribute("hidden", "");
  $("#annotationBackdrop").setAttribute("hidden", "");
  $("#annotationConnector").setAttribute("hidden", "");
}

function updateAnnotationConnector(){
  const selected = state.selectedAnnotation;
  if(!selected) return closeAnnotationPopover();
  const anchorEl = document.querySelector(`#editable span[data-error-id="${selected.error_id}"]`);
  const pop = $("#annotationPopover");
  if(!anchorEl || pop.hasAttribute("hidden")) return closeAnnotationPopover();
  if(SECTIONS[state.section].id !== selected.sectionId){
    closeAnnotationPopover();
    return;
  }
  const anchorRect = anchorEl.getBoundingClientRect();
  const cardRect = pop.getBoundingClientRect();
  const side = pop.dataset.side || "right";
  const d = connectorPath(anchorRect, cardRect, side);
  $("#annotationConnectorPath").setAttribute("d", d);
  $("#annotationConnector").removeAttribute("hidden");
}

function renderAnnotationPopover(sectionId, err){
  const anchorEl = document.querySelector(`#editable span[data-error-id="${err.error_id}"]`);
  if(!anchorEl) return;
  const anchorRect = anchorEl.getBoundingClientRect();
  const pop = $("#annotationPopover");
  const content = $("#annotationContent");
  content.innerHTML = annotationCardHTML(err);

  const ruleBtn = $("#annotationRuleBtn");
  const ruleEl = $("#annotationRule");
  if(err.rule){
    ruleBtn.removeAttribute("hidden");
    ruleEl.textContent = err.rule;
    if(state.annotationRuleOpen) ruleEl.removeAttribute("hidden");
    else ruleEl.setAttribute("hidden", "");
  }else{
    state.annotationRuleOpen = false;
    ruleBtn.setAttribute("hidden", "");
    ruleEl.setAttribute("hidden", "");
    ruleEl.textContent = "";
  }

  pop.classList.toggle("compact", ["suggestion", "style"].includes(resolveAnnotationKind(err)));
  pop.removeAttribute("hidden");
  $("#annotationBackdrop").removeAttribute("hidden");

  requestAnimationFrame(() => {
    const pos = computePopoverPosition(anchorRect, pop.offsetHeight || 320);
    pop.style.top = `${pos.top}px`;
    pop.style.left = `${pos.left}px`;
    pop.dataset.side = pos.side;
    updateAnnotationConnector();
  });

  state.selectedAnnotation = { sectionId, error_id: err.error_id };
}

function onAnnotationAction(action, text){
  if(action === "insert"){
    insertCliche(text);
    closeAnnotationPopover();
    return;
  }
  if(action === "train"){
    if(!window.EditorApi || !state.apiReady || !text){
      closeAnnotationPopover();
      return;
    }
    const q = String(text).trim();
    window.EditorApi.listWords({ q, level: ($("#ddNiveau .dd-menu .sel") || {}).textContent || "B1" })
      .then((rows) => {
        if(rows && rows[0] && rows[0].id) return window.EditorApi.queueWord(rows[0].id);
        return null;
      })
      .then(() => {
        setAnalyzeStatus("Konstruktion zur Übung hinzugefügt");
      })
      .catch(() => {
        setAnalyzeStatus("Training nicht verfügbar");
      })
      .finally(() => closeAnnotationPopover());
  }
}

function bindAnnotationPopoverEvents(){
  $("#annotationCloseBtn").addEventListener("click", closeAnnotationPopover);
  $("#annotationBackdrop").addEventListener("click", closeAnnotationPopover);
  $("#annotationRuleBtn").addEventListener("click", () => {
    state.annotationRuleOpen = !state.annotationRuleOpen;
    const rule = $("#annotationRule");
    if(state.annotationRuleOpen) rule.removeAttribute("hidden");
    else rule.setAttribute("hidden", "");
    updateAnnotationConnector();
  });
  $("#annotationContent").addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-annotation-action]");
    if(!btn) return;
    const action = btn.getAttribute("data-annotation-action");
    const payload = decodeURIComponent(btn.getAttribute("data-annotation-text") || "");
    onAnnotationAction(action, payload);
  });

  document.addEventListener("click", (e) => {
    const pop = $("#annotationPopover");
    if(pop.hasAttribute("hidden")) return;
    if(e.target.closest("#annotationPopover")) return;
    if(e.target.closest("#editable span[data-error-id]")) return;
    closeAnnotationPopover();
  });

  window.addEventListener("resize", () => {
    if(state.selectedAnnotation) updateAnnotationConnector();
  });
  window.addEventListener("scroll", () => {
    if(state.selectedAnnotation) updateAnnotationConnector();
  }, true);
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
        if(dd.id === "ddNiveau" || dd.id === "ddThema"){
          updateWbTitle();
          $("#docEyebrow").textContent = currentThema().toUpperCase();
          const topic = currentThema().toLowerCase();
          const level = ($("#ddNiveau .dd-menu .sel") || {}).textContent || "B1";
          loadBackendWords(topic, level);
          loadBackendPhrases(topic, level);
          schedulePersistEssay();
        }
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
  closeAnnotationPopover();
  state.section = i; state.kliPage = 0;
  renderMap(); renderDocHead(); loadEditor(); renderKlischees();
}
function renderDocHead(){
  const s = SECTIONS[state.section];
  $("#docEyebrow").textContent = currentThema().toUpperCase();
  $("#docTitle").textContent = s.title;
  $("#docSub").textContent = s.sub;
  $("#editable").setAttribute("data-placeholder", s.ph);
  renderVerdict();
}
function currentThema(){
  const sel = $("#ddThema .dd-menu .sel");
  return sel ? sel.textContent : "Technologie";
}

function updateWbTitle(){
  const title = document.querySelector(".rail-right .tool-title");
  if(title) title.innerHTML = `Wörterbuch <b>· ${escapeHtml(currentThema())}</b>`;
}

function mergeWordLists(staticWords, backendWords){
  const merged = new Map();
  staticWords.forEach((w) => merged.set(w.de.toLowerCase(), w));
  backendWords.forEach((w) => {
    if(w.de) merged.set(w.de.toLowerCase(), { ...merged.get(w.de.toLowerCase()), ...w });
  });
  return Array.from(merged.values());
}

function klischeeSourceForSection(sectionId){
  const staticKli = SECTIONS.find((s) => s.id === sectionId)?.kli || [];
  const backendPart = state.backendPhrases[sectionId];
  if(!Array.isArray(backendPart) || !backendPart.length) return staticKli;
  const seen = new Set();
  const merged = [];
  backendPart.forEach((item) => {
    const key = String(item.de || "").replace(/<\/?em>/g, "").trim();
    if(!key || seen.has(key)) return;
    seen.add(key);
    merged.push(item);
  });
  staticKli.forEach((item) => {
    const key = String(item.de || "").replace(/<\/?em>/g, "").trim();
    if(!key || seen.has(key)) return;
    seen.add(key);
    merged.push(item);
  });
  return merged.length ? merged : staticKli;
}

/* =====================================================================
   Writing surface
   ===================================================================== */
function loadEditor(){
  renderEditorText();
  updateCounts();
}
function saveEditor(){
  const ed = $("#editable");
  const id = SECTIONS[state.section].id;
  state.text[id] = plainText(readEditorText(ed));
  state.counts[id] = countWords(state.text[id]);
}
function updateCounts(){
  const id = SECTIONS[state.section].id;
  const n = countWords(state.text[id] || "");
  state.counts[id] = n;
  $("#wordCount").textContent = n + (n === 1 ? " Wort" : " Wörter");
  const total = Object.values(state.counts).reduce((a,b)=>a+b,0);
  $("#progTotal").textContent = total;
  $("#progFill").style.width = Math.min(100, total / TARGET_WORDS * 100) + "%";
  const mapRow = $$("#essayMap .map-item")[state.section];
  if(mapRow){
    const mapWords = mapRow.querySelector(".map-words");
    if(mapWords) mapWords.textContent = n + " Wörter";
  }
}
function initEditor(){
  let composing = false;
  $("#editable").addEventListener("compositionstart", () => { composing = true; });
  $("#editable").addEventListener("compositionend", () => {
    composing = false;
    updateCounts();
    saveEditor();
    scheduleReanchor();
    schedulePersistEssay();
  });

  $("#editable").addEventListener("click", (e) => {
    const hit = e.target.closest("span[data-error-id]");
    if(!hit) return;
    const sectionId = SECTIONS[state.section].id;
    const errorId = hit.getAttribute("data-error-id");
    const err = (state.errorsBySection[sectionId] || []).find((x) => x.error_id === errorId && !x.orphaned);
    if(err){
      renderAnnotationPopover(sectionId, err);
      e.preventDefault();
      e.stopPropagation();
    }
  });
  $("#editable").addEventListener("input", () => {
    updateCounts();
    saveEditor();
    const sectionId = SECTIONS[state.section].id;
    const hasAnnotations = (state.errorsBySection[sectionId] || []).some((e) => !e.orphaned);
    if(!composing && !hasAnnotations){
      renderEditorText();
    }
    if(!composing){
      scheduleReanchor();
    }
    closeAnnotationPopover();
    schedulePersistEssay();
  });
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
  const source = klischeeSourceForSection(s.id);
  const pages = Math.max(1, Math.ceil(source.length / KLI_PER_PAGE));
  state.kliPage = Math.min(state.kliPage, pages - 1);
  $("#kliTitle").innerHTML = `Klischees <b>· ${s.title}</b>`;
  $("#kliCount").textContent = `${state.kliPage + 1} / ${pages}`;
  $("#kliPrev").disabled = state.kliPage === 0;
  $("#kliNext").disabled = state.kliPage >= pages - 1;
  const start = state.kliPage * KLI_PER_PAGE;
  const list = $("#kliList"); list.innerHTML = "";
  source.slice(start, start + KLI_PER_PAGE).forEach(k => {
    const div = document.createElement("div");
    div.className = "kli";
    div.innerHTML = `<div class="kli-de">${k.de}</div><div class="kli-ru">${escapeHtml(k.ru)}</div><span class="kli-add">Einfügen</span>`;
    div.title = "Zum Einfügen klicken";
    div.onclick = () => insertCliche(k.de);
    list.appendChild(div);
  });
}
function insertCliche(html){
  const ed = $("#editable");
  const plain = String(html || "").replace(/<\/?em>/g, "").trim();
  if(!plain) return;
  const sectionId = SECTIONS[state.section].id;
  const text = state.text[sectionId] || "";
  const focusInEditor = document.activeElement === ed;
  let offset = text.length;
  if(focusInEditor){
    offset = Math.max(0, Math.min(getCaretCharacterOffsetWithin(ed), text.length));
  }
  const left = text.slice(0, offset);
  const right = text.slice(offset);
  const needsLeftSpace = left.length > 0 && !/\s$/.test(left);
  const needsRightSpace = right.length > 0 && !/^\s/.test(right);
  const inserted = `${needsLeftSpace ? " " : ""}${plain}${needsRightSpace ? " " : ""}`;
  state.text[sectionId] = `${left}${inserted}${right}`;
  ed.focus();
  renderEditorText();
  const newOffset = left.length + inserted.length;
  setCaretCharacterOffsetWithin(ed, newOffset);
  updateCounts();
  saveEditor();
  scheduleReanchor();
  schedulePersistEssay();
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
  const topic = currentThema().toLowerCase();
  const staticForTopic = WORDS.filter((w) => String(w.cat || "").toLowerCase() === topic);
  const sourceWords = mergeWordLists(
    staticForTopic.length ? staticForTopic : WORDS,
    state.backendWords,
  );
  const items = sourceWords.filter(w =>
    !term || w.de.toLowerCase().includes(term) || w.ru.toLowerCase().includes(term));
  if(!items.length){ list.innerHTML = `<div class="wb-empty">Keine Begriffe gefunden.</div>`; return; }
  items.forEach(w => {
    const row = document.createElement("div");
    row.className = "wb-row";
    row.style.setProperty("--brush", brushOf(w));
    const de = escapeHtml(w.de);
    const ru = escapeHtml(w.ru);
    const art = w.art ? `<span class="art">${escapeHtml(w.art)} </span>` : "";
    row.innerHTML = `
      <span class="wb-wash" aria-hidden="true"></span>
      <span class="wb-de">${art}${de}</span>
      <span class="wb-ru">${ru}</span>
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
  const safe = {
    art: escapeHtml(w.art || ""),
    de: escapeHtml(w.de || ""),
    cat: escapeHtml(w.cat || ""),
    level: escapeHtml(w.level || ""),
    ipa: escapeHtml(w.ipa || ""),
    ru: escapeHtml(w.ru || ""),
  };
  const art = w.art ? `<span class="art">${safe.art}</span> ` : "";
  const posLabel = w.pos === "verb" ? "Verb" : w.pos === "adj" ? "Adjektiv" : "Substantiv";
  const longCls = ((w.art ? w.art.length+1 : 0) + (w.de||"").length) > 16 ? " long" : "";

  // compact key-forms spec line
  const spec = (w.spec || []).map(([label, value, wide]) => {
    let v = escapeHtml(value);
    if(wide) v = v.replace(/→/g, "<em>→</em>");
    return `<span class="g-s${wide ? " g-s--wide" : ""}"><i>${escapeHtml(label)}</i>${v}</span>`;
  }).join("");
  const specBlock = spec ? `<div class="g-spec">${spec}</div>` : "";
  const hintBlock = w.hint ? `<div class="g-hint">${escapeHtml(w.hint)}</div>` : "";

  // Verwendung — rektion rule + RU case gloss + ready_phrase
  const ruCase = caseGlossRu(w.rektion);
  const useBlock = (w.rektion || w.readyPhrase) ? `
    <div class="g-use"><span class="g-use-lab">Verwendung</span>
      ${w.rektion ? `<span class="g-use-rule">${escapeHtml(w.rektion)}</span>` : ""}
      ${ruCase ? `<span class="g-use-ru">${ruCase}</span>` : ""}
      ${w.readyPhrase ? `<span class="g-use-ex">${escapeHtml(w.readyPhrase)}</span>` : ""}</div>` : "";

  const examples = (w.ex || []).map(([de,ru],i) => `
    <div class="ex"><span class="ex-n">${String(i+1).padStart(2,"0")}</span>
      <div class="ex-body"><p class="ex-de">${de}</p>${ru ? `<p class="ex-ru">${ru}</p>` : ""}</div></div>`).join("");
  return `
    <button class="d-close" id="dClose" type="button" aria-label="Schließen">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
    <div class="d-head">
      <div class="d-meta"><span class="d-cat"><span class="hl">${posLabel}</span> · ${safe.cat}</span><span class="d-level">${safe.level}</span></div>
      <div class="d-word${longCls}">${art}${safe.de}</div>
      <div class="d-tools">
        <span class="d-ipa">${safe.ipa}</span>
        <button class="d-hear" id="dHear" type="button">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 9v6h4l5 5V4L9 9H5z"/><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>
          Aussprache
        </button>
      </div>
      <div class="d-ru">${safe.ru}</div>
    </div>
    <div class="d-body">
      ${w.def ? `<section><div class="lab">Bedeutung</div><p class="def">${w.def}</p></section>` : ""}
      <section><div class="lab">Grammatik</div>${specBlock}${hintBlock}${useBlock}</section>
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
  btn.addEventListener("click", async () => {
    if(btn.disabled) return;
    const label = btn.querySelector(".lbl"), prev = label.textContent;
    btn.disabled = true;
    label.textContent = "Analysiere…";
    try{
      saveEditor();
      await persistEssayNow();
      if(!state.apiReady || !window.EditorApi || !state.essayId){
        label.textContent = "Analyse folgt…";
        setTimeout(() => { btn.disabled = false; label.textContent = prev; }, 1000);
        return;
      }
      await window.EditorApi.streamAnalyze(state.essayId, (event) => {
        if(!event || !event.type) return;
        if(event.type === "part_start"){
          setAnalyzeStatus(`Analysiere ${event.label || event.part}…`);
          return;
        }
        if(event.type === "part_done"){
          applyPartFeedback(event);
          const partialMap = mapErrorsToSections(event.all_errors || []);
          state.errorsBySection = partialMap;
          if(SECTIONS[state.section].id === apiToPart(event.part)){
            renderEditorText();
          }
          setAnalyzeStatus(`Teil ${event.label || event.part} fertig`);
          return;
        }
        if(event.type === "done"){
          const grade = event.grade || "—";
          const score = Number.isFinite(event.overall_score) ? event.overall_score : 0;
          state.errorsBySection = mapErrorsToSections(event.errors || []);
          closeAnnotationPopover();
          renderEditorText();
          setAnalyzeStatus(`Analysiert · ${grade} (${score})`);
        }
      });
      setTimeout(() => { btn.disabled = false; label.textContent = prev; }, 1400);
    }catch(err){
      console.error("analyze failed", err);
      label.textContent = "Analyse fehlgeschlagen";
      setTimeout(() => { btn.disabled = false; label.textContent = prev; }, 1800);
    }
  });
}

async function loadBackendPhrases(topic, level){
  if(!state.apiReady || !window.EditorApi) return;
  const bySection = {};
  const jobs = SECTIONS.map((sec) => {
    const part = partToApi(sec.id);
    return window.EditorApi.listPhrases({ topic, level, part })
      .then((rows) => {
        bySection[sec.id] = (rows || []).map((row) => ({
          de: row.text_de || "",
          ru: row.translation_ru || "",
        }));
      })
      .catch(() => {
        bySection[sec.id] = [];
      });
  });
  await Promise.all(jobs);
  state.backendPhrases = bySection;
  renderKlischees();
}

async function loadBackendWords(topic, level){
  if(!state.apiReady || !window.EditorApi) return;
  try{
    const rows = await window.EditorApi.listWords({ topic, level });
    state.backendWords = (rows || []).map(toEditorWord).filter(w => w.de && w.ru);
    renderWordList($("#wbSearch").value || "");
  }catch(err){
    console.warn("words backend unavailable", err);
  }
}

async function loadDynamicTopics(){
  try {
    const words = await fetch("/api/words?limit=500").then(r => r.json());
    if (!Array.isArray(words)) return;

    const menu  = $("#ddThema .dd-menu");
    const dd    = $("#ddThema");
    const ddBtn = dd ? dd.querySelector(".dd-btn") : null;
    if (!menu || !dd) return;

    // Collect topics already shown in the dropdown
    const existing = new Set(
      Array.from(menu.querySelectorAll("button"))
        .map(b => b.textContent.trim().toLowerCase())
    );

    // Gather new unique topics from API words
    const newTopics = new Map(); // lowercase → display
    words.forEach(w => {
      (w.topics || []).forEach(t => {
        if (t && !existing.has(t.toLowerCase())) {
          const display = t.charAt(0).toUpperCase() + t.slice(1);
          newTopics.set(t.toLowerCase(), display);
        }
      });
    });

    newTopics.forEach((display, topicKey) => {
      const opt = document.createElement("button");
      opt.textContent = display;
      opt.addEventListener("click", () => {
        const lbl = ddBtn ? ddBtn.querySelector(".lbl") : null;
        if (lbl) lbl.textContent = display;
        menu.querySelectorAll("button").forEach(b => b.classList.remove("sel"));
        opt.classList.add("sel");
        dd.classList.remove("open");
        const level = ($("#ddNiveau .dd-menu .sel") || {}).textContent || "B1";
        loadBackendWords(topicKey, level);
        loadBackendPhrases(topicKey, level);
        schedulePersistEssay();
      });
      menu.appendChild(opt);
    });
  } catch(_){}
}

async function initBackendBridge(){
  if(!window.EditorApi){
    return;
  }
  try{
    const healthy = await window.EditorApi.health();
    state.apiReady = !!healthy;
  }catch(err){
    state.apiReady = false;
  }

  // Load dynamic topics regardless of API health (uses nginx proxy directly)
  loadDynamicTopics();

  if(!state.apiReady) return;

  const topic = currentThema().toLowerCase();
  const level = ($("#ddNiveau .dd-menu .sel") || {}).textContent || "B1";
  await Promise.all([
    loadBackendWords(topic, level),
    loadBackendPhrases(topic, level),
  ]);
  await persistEssayNow();
}

/* =====================================================================
   Boot  (theme toggle + Lernen dropdown live in js/site-header.js)
   ===================================================================== */
function boot(){
  initDropdowns();
  updateWbTitle();
  renderMap(); renderDocHead(); loadEditor();
  initEditor();
  bindAnnotationPopoverEvents();
  initPomo();
  renderKlischees(); initKlischees();
  initWordPanel();
  initAnalyze();
  initBackendBridge();
  // re-anchor the open card on resize
  window.addEventListener("resize", () => {
    if($("#wordCard").classList.contains("open")) closeCard();
    if(state.selectedAnnotation) updateAnnotationConnector();
  });
  document.addEventListener("keydown", (e) => {
    if(e.key === "Escape") closeAnnotationPopover();
  });
}
if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();

})();

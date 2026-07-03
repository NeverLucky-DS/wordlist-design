/* =====================================================================
   Deutsch Essay · Wörterbuch — app logic (data + rendering)
   ===================================================================== */

/* ---------- brushes ----------------------------------------------------
   Each word gets its OWN brush by LEVEL + grammatical TYPE
   (der/die/das/Verb/Adjektiv) — so B1/B2/C1 look distinct, and every
   gender/part-of-speech has its own colour. Rendered as the real PNG with
   its own paint; opacity is dialled down in CSS to keep the soft, faded feel
   and keep black text readable. */
const WASH = {
  "B1|der":"B1_Der_Powdery-Blue_Horizontal-Soft.png",
  "B1|die":"B1_Die_Powdery-Pink_BG-Wash.png",
  "B1|das":"B1_Das_Pale-Green_BG-Wash.png",
  "B1|verb":"B1_Verbs_Sandy-Ochre_BG-Wash.png",
  "B1|adj":"B1_Adjectives_Lavender_BG-Wash.png",
  "B2|der":"B2_Der_Deep-Blue_BG-Wash.png",
  "B2|die":"B2_Die_Magenta_BG-Wash.png",
  "B2|das":"B2_Das_Grass-Green_BG-Wash.png",
  "B2|verb":"B2_Verbs_Terracotta_BG-Wash.png",
  "B2|adj":"B2_Adjectives_Amethyst_BG-Wash.png",
  "C1|der":"C1_Der_Indigo_BG-Wash.png",
  "C1|die":"C1_Die_Burgundy_BG-Wash.png",
  "C1|das":"C1_Das_Emerald_BG-Wash.png",
  "C1|verb":"C1_Verbs_Olive-Ochre_BG-Wash.png",
  "C1|adj":"C1_Adjectives_Plum_BG-Wash.png"
};
function typeKey(w){ return w.pos==="verb" ? "verb" : (w.pos==="adj" ? "adj" : w.art); }
/* absolute URL (resolved against the document, not the stylesheet) so the
   brush loads correctly when referenced from a CSS custom property */
function brushOf(w){
  const f = WASH[w.level+"|"+typeKey(w)] || "";
  return `url('${new URL('worte/'+f, document.baseURI).href}')`;
}

/* ---------- data ---------- */
const WORDS = [
  {de:"Abhängigkeit",art:"die",pos:"noun",cat:"Technologie",level:"B1",genus:"Femininum",ru:"зависимость",ipa:"[ˈapˌhɛŋɪçkaɪt]",
   def:"Ein Zustand, in dem jemand oder etwas von etwas anderem bestimmt oder benötigt wird.",
   pull:"Die Abhängigkeit von fossilen Brennstoffen ist eine globale Herausforderung.",
   gram:{type:"noun",plural:"die Abhängigkeiten",rows:[
     ["Nominativ","die Abhängigkeit","die Abhängigkeiten"],
     ["Genitiv","der Abhängigkeit","der Abhängigkeiten"],
     ["Dativ","der Abhängigkeit","den Abhängigkeiten"],
     ["Akkusativ","die Abhängigkeit","die Abhängigkeiten"]]},
   examples:["<b>Die Abhängigkeit</b> von Technologie nimmt in der modernen Gesellschaft ständig zu.",
             "Eine starke <b>Abhängigkeit</b> von einem einzigen Anbieter ist riskant.",
             "Soziale <b>Abhängigkeit</b> kann die persönliche Freiheit einschränken."]},

  {de:"Algorithmus",art:"der",pos:"noun",cat:"Technologie",level:"B2",genus:"Maskulinum",ru:"алгоритм",ipa:"[alɡoˈrɪtmʊs]",
   def:"Eine eindeutige Handlungsvorschrift zur Lösung eines Problems oder einer Klasse von Problemen.",
   pull:"Ein guter Algorithmus spart Zeit und Ressourcen.",
   gram:{type:"noun",plural:"die Algorithmen",rows:[
     ["Nominativ","der Algorithmus","die Algorithmen"],
     ["Genitiv","des Algorithmus","der Algorithmen"],
     ["Dativ","dem Algorithmus","den Algorithmen"],
     ["Akkusativ","den Algorithmus","die Algorithmen"]]},
   examples:["<b>Der Algorithmus</b> entscheidet, welche Beiträge zuerst angezeigt werden.",
             "Ein effizienter <b>Algorithmus</b> verarbeitet Millionen von Daten in Sekunden.",
             "Der <b>Algorithmus</b> wurde so trainiert, dass er Muster erkennt."]},

  {de:"Auswirkung",art:"die",pos:"noun",cat:"Technologie",level:"B1",genus:"Femininum",ru:"последствие, влияние",ipa:"[ˈaʊsˌvɪrkʊŋ]",
   def:"Eine Folge oder ein Effekt, der aus einer Handlung oder einem Ereignis entsteht.",
   pull:"Die Auswirkungen des Klimawandels sind weltweit spürbar.",
   gram:{type:"noun",plural:"die Auswirkungen",rows:[
     ["Nominativ","die Auswirkung","die Auswirkungen"],
     ["Genitiv","der Auswirkung","der Auswirkungen"],
     ["Dativ","der Auswirkung","den Auswirkungen"],
     ["Akkusativ","die Auswirkung","die Auswirkungen"]]},
   examples:["<b>Die Auswirkung</b> neuer Technologien auf den Arbeitsmarkt ist erheblich.",
             "Jede Entscheidung hat eine <b>Auswirkung</b> auf die Zukunft.",
             "Die langfristige <b>Auswirkung</b> ist noch nicht absehbar."]},

  {de:"analysieren",art:"",pos:"verb",cat:"Wissenschaft",level:"B2",genus:"Verb",ru:"анализировать",ipa:"[analyˈziːʁən]",
   def:"Etwas systematisch und gründlich untersuchen, um es zu verstehen oder zu bewerten.",
   pull:"Wer Daten klug analysiert, trifft bessere Entscheidungen.",
   gram:{type:"verb",hilfsverb:"haben",partizip:"analysiert",praeteritum:"analysierte",
     praesens:[["ich","analysiere"],["du","analysierst"],["er/sie/es","analysiert"],
               ["wir","analysieren"],["ihr","analysiert"],["sie/Sie","analysieren"]]},
   examples:["Wir müssen die Ergebnisse genau <b>analysieren</b>.",
             "Der Forscher <b>analysiert</b> die Proben im Labor.",
             "Sie hat den Text Satz für Satz <b>analysiert</b>."]},

  {de:"Fortschritt",art:"der",pos:"noun",cat:"Wissenschaft",level:"B1",genus:"Maskulinum",ru:"прогресс",ipa:"[ˈfɔʁtʃʁɪt]",
   def:"Eine positive Entwicklung hin zu einem besseren oder fortgeschritteneren Zustand.",
   pull:"Wissenschaftlicher Fortschritt verbessert unser Leben.",
   gram:{type:"noun",plural:"die Fortschritte",rows:[
     ["Nominativ","der Fortschritt","die Fortschritte"],
     ["Genitiv","des Fortschritts","der Fortschritte"],
     ["Dativ","dem Fortschritt","den Fortschritten"],
     ["Akkusativ","den Fortschritt","die Fortschritte"]]},
   examples:["<b>Der Fortschritt</b> in der Medizin rettet jeden Tag Leben.",
             "Technischer <b>Fortschritt</b> verändert, wie wir arbeiten.",
             "Jeder kleine <b>Fortschritt</b> zählt beim Lernen."]},

  {de:"nachhaltig",art:"",pos:"adj",cat:"Umwelt",level:"C1",genus:"Adjektiv",ru:"устойчивый, экологичный",ipa:"[ˈnaːxˌhaltɪç]",
   def:"So gestaltet, dass Ressourcen geschont und auch für künftige Generationen erhalten bleiben.",
   pull:"Nachhaltiges Handeln ist eine Investition in die Zukunft.",
   gram:{type:"adj",steigerung:["nachhaltig","nachhaltiger","am nachhaltigsten"],rows:[
     ["Maskulinum","der nachhaltige Wandel"],
     ["Femininum","die nachhaltige Lösung"],
     ["Neutrum","das nachhaltige Handeln"],
     ["Plural","die nachhaltigen Ziele"]]},
   examples:["Wir setzen auf <b>nachhaltige</b> Energiequellen.",
             "Ein <b>nachhaltiger</b> Lebensstil schont die Umwelt.",
             "Das Unternehmen wirtschaftet <b>nachhaltig</b>."]},

  {de:"Gesellschaft",art:"die",pos:"noun",cat:"Gesellschaft",level:"B1",genus:"Femininum",ru:"общество",ipa:"[ɡəˈzɛlʃaft]",
   def:"Die Gesamtheit der Menschen, die zusammenleben und durch gemeinsame Normen verbunden sind.",
   pull:"Eine offene Gesellschaft schätzt Vielfalt.",
   gram:{type:"noun",plural:"die Gesellschaften",rows:[
     ["Nominativ","die Gesellschaft","die Gesellschaften"],
     ["Genitiv","der Gesellschaft","der Gesellschaften"],
     ["Dativ","der Gesellschaft","den Gesellschaften"],
     ["Akkusativ","die Gesellschaft","die Gesellschaften"]]},
   examples:["<b>Die Gesellschaft</b> steht vor großen demografischen Veränderungen.",
             "In einer gerechten <b>Gesellschaft</b> haben alle die gleichen Chancen.",
             "Die digitale <b>Gesellschaft</b> verändert unsere Kommunikation."]},

  {de:"Nachhaltigkeit",art:"die",pos:"noun",cat:"Umwelt",level:"C1",genus:"Femininum",ru:"устойчивость",ipa:"[ˈnaːxˌhaltɪçkaɪt]",
   def:"Ein Prinzip, bei dem Ressourcen so genutzt werden, dass sie auch künftigen Generationen erhalten bleiben.",
   pull:"Nachhaltigkeit ist kein Trend, sondern eine Notwendigkeit.",
   gram:{type:"noun",plural:"— (kein Plural)",rows:[
     ["Nominativ","die Nachhaltigkeit","—"],
     ["Genitiv","der Nachhaltigkeit","—"],
     ["Dativ","der Nachhaltigkeit","—"],
     ["Akkusativ","die Nachhaltigkeit","—"]]},
   examples:["<b>Die Nachhaltigkeit</b> sollte im Zentrum jeder Entscheidung stehen.",
             "Ökologische <b>Nachhaltigkeit</b> betrifft uns alle.",
             "Ohne <b>Nachhaltigkeit</b> gibt es keine lebenswerte Zukunft."]},

  {de:"Forschung",art:"die",pos:"noun",cat:"Wissenschaft",level:"B1",genus:"Femininum",ru:"исследование",ipa:"[ˈfɔʁʃʊŋ]",
   def:"Die systematische Suche nach neuem Wissen mit wissenschaftlichen Methoden.",
   pull:"Forschung ist die Grundlage jeder Innovation.",
   gram:{type:"noun",plural:"die Forschungen",rows:[
     ["Nominativ","die Forschung","die Forschungen"],
     ["Genitiv","der Forschung","der Forschungen"],
     ["Dativ","der Forschung","den Forschungen"],
     ["Akkusativ","die Forschung","die Forschungen"]]},
   examples:["<b>Die Forschung</b> an erneuerbaren Energien macht große Fortschritte.",
             "Grundlegende <b>Forschung</b> braucht Geduld und Geld.",
             "Die <b>Forschung</b> hat neue Erkenntnisse gebracht."]},

  {de:"Entwicklung",art:"die",pos:"noun",cat:"Technologie",level:"B1",genus:"Femininum",ru:"развитие",ipa:"[ɛntˈvɪklʊŋ]",
   def:"Der Vorgang, bei dem etwas allmählich entsteht, wächst oder sich verändert.",
   pull:"Jede Entwicklung beginnt mit einer Idee.",
   gram:{type:"noun",plural:"die Entwicklungen",rows:[
     ["Nominativ","die Entwicklung","die Entwicklungen"],
     ["Genitiv","der Entwicklung","der Entwicklungen"],
     ["Dativ","der Entwicklung","den Entwicklungen"],
     ["Akkusativ","die Entwicklung","die Entwicklungen"]]},
   examples:["<b>Die Entwicklung</b> neuer Technologien schreitet rasant voran.",
             "Die wirtschaftliche <b>Entwicklung</b> des Landes ist beeindruckend.",
             "Wir beobachten die <b>Entwicklung</b> mit großem Interesse."]},

  {de:"Verantwortung",art:"die",pos:"noun",cat:"Gesellschaft",level:"B2",genus:"Femininum",ru:"ответственность",ipa:"[fɛɐ̯ˈʔantvɔʁtʊŋ]",
   def:"Die Pflicht, für die Folgen des eigenen Handelns einzustehen.",
   pull:"Mit Freiheit wächst die Verantwortung.",
   gram:{type:"noun",plural:"die Verantwortungen",rows:[
     ["Nominativ","die Verantwortung","die Verantwortungen"],
     ["Genitiv","der Verantwortung","der Verantwortungen"],
     ["Dativ","der Verantwortung","den Verantwortungen"],
     ["Akkusativ","die Verantwortung","die Verantwortungen"]]},
   examples:["Sie übernimmt die <b>Verantwortung</b> für das gesamte Projekt.",
             "Jeder trägt <b>Verantwortung</b> für die Umwelt.",
             "Die <b>Verantwortung</b> liegt bei der Leitung."]},

  {de:"Herausforderung",art:"die",pos:"noun",cat:"Gesellschaft",level:"B2",genus:"Femininum",ru:"вызов, сложная задача",ipa:"[hɛˈʁaʊsfɔʁdəʁʊŋ]",
   def:"Eine schwierige Aufgabe, die besondere Anstrengung und Einsatz verlangt.",
   pull:"Jede Herausforderung ist eine Chance zu wachsen.",
   gram:{type:"noun",plural:"die Herausforderungen",rows:[
     ["Nominativ","die Herausforderung","die Herausforderungen"],
     ["Genitiv","der Herausforderung","der Herausforderungen"],
     ["Dativ","der Herausforderung","den Herausforderungen"],
     ["Akkusativ","die Herausforderung","die Herausforderungen"]]},
   examples:["Der Klimawandel ist eine globale <b>Herausforderung</b>.",
             "Sie sucht ständig neue <b>Herausforderungen</b>.",
             "Diese <b>Herausforderung</b> meistern wir gemeinsam."]},

  {de:"wesentlich",art:"",pos:"adj",cat:"Wissenschaft",level:"B2",genus:"Adjektiv",ru:"существенный, важный",ipa:"[ˈveːzn̩tlɪç]",
   def:"Von grundlegender Bedeutung; entscheidend für das Ganze.",
   pull:"Das Wesentliche bleibt dem Auge oft verborgen.",
   gram:{type:"adj",steigerung:["wesentlich","wesentlicher","am wesentlichsten"],rows:[
     ["Maskulinum","der wesentliche Unterschied"],
     ["Femininum","die wesentliche Rolle"],
     ["Neutrum","das wesentliche Merkmal"],
     ["Plural","die wesentlichen Punkte"]]},
   examples:["Das ist ein <b>wesentlicher</b> Unterschied.",
             "Der Preis spielt eine <b>wesentliche</b> Rolle.",
             "Sie hat <b>wesentlich</b> zum Erfolg beigetragen."]},

  {de:"erfordern",art:"",pos:"verb",cat:"Wissenschaft",level:"B2",genus:"Verb",ru:"требовать",ipa:"[ɛɐ̯ˈfɔʁdɐn]",
   def:"Etwas notwendig machen; als Voraussetzung verlangen.",
   pull:"Große Ziele erfordern Geduld und Ausdauer.",
   gram:{type:"verb",hilfsverb:"haben",partizip:"erfordert",praeteritum:"erforderte",
     praesens:[["ich","erfordere"],["du","erforderst"],["er/sie/es","erfordert"],
               ["wir","erfordern"],["ihr","erfordert"],["sie/Sie","erfordern"]]},
   examples:["Diese Aufgabe <b>erfordert</b> volle Konzentration.",
             "Der Plan <b>erfordert</b> sorgfältige Vorbereitung.",
             "Solche Projekte <b>erfordern</b> viel Zeit und Geduld."]},

  {de:"Zusammenhang",art:"der",pos:"noun",cat:"Wissenschaft",level:"C1",genus:"Maskulinum",ru:"взаимосвязь, контекст",ipa:"[t͡suˈzamənhaŋ]",
   def:"Die innere Beziehung oder Verbindung zwischen mehreren Dingen oder Ereignissen.",
   pull:"Erst im Zusammenhang ergibt alles einen Sinn.",
   gram:{type:"noun",plural:"die Zusammenhänge",rows:[
     ["Nominativ","der Zusammenhang","die Zusammenhänge"],
     ["Genitiv","des Zusammenhangs","der Zusammenhänge"],
     ["Dativ","dem Zusammenhang","den Zusammenhängen"],
     ["Akkusativ","den Zusammenhang","die Zusammenhänge"]]},
   examples:["Es gibt einen klaren <b>Zusammenhang</b> zwischen beiden Ereignissen.",
             "Sie erklärt die <b>Zusammenhänge</b> sehr verständlich.",
             "In diesem <b>Zusammenhang</b> ist das besonders wichtig."]}
];

/* Rektion / collocation — the practical "how to use it" line */
const GOV = {
  "Abhängigkeit":  {rule:"von + Dativ",      ex:"die Abhängigkeit <em>von</em> der Technik"},
  "Algorithmus":   {rule:"für + Akkusativ",  ex:"ein Algorithmus <em>für</em> die Suche"},
  "Auswirkung":    {rule:"auf + Akkusativ",  ex:"die Auswirkung <em>auf</em> die Umwelt"},
  "analysieren":   {rule:"+ Akkusativ",      ex:"die Daten genau <em>analysieren</em>"},
  "Fortschritt":   {rule:"bei / in + Dativ", ex:"Fortschritte <em>bei</em> der Arbeit"},
  "nachhaltig":    {rule:"mit + Dativ",      ex:"<em>nachhaltig</em> mit Ressourcen umgehen"},
  "Gesellschaft":  {rule:"in + Dativ",       ex:"<em>in</em> der Gesellschaft leben"},
  "Nachhaltigkeit":{rule:"in + Dativ",       ex:"Nachhaltigkeit <em>in</em> der Wirtschaft"},
  "Forschung":     {rule:"an / zu + Dativ",  ex:"die Forschung <em>an</em> Impfstoffen"},
  "Entwicklung":   {rule:"von + Dativ",      ex:"die Entwicklung <em>von</em> Software"},
  "Verantwortung": {rule:"für + Akkusativ",  ex:"die Verantwortung <em>für</em> das Team"},
  "Herausforderung":{rule:"für + Akkusativ", ex:"eine Herausforderung <em>für</em> die Gesellschaft"},
  "wesentlich":    {rule:"für + Akkusativ",  ex:"<em>wesentlich</em> für den Erfolg"},
  "erfordern":     {rule:"+ Akkusativ",      ex:"viel Geduld <em>erfordern</em>"},
  "Zusammenhang":  {rule:"zwischen + Dativ", ex:"der Zusammenhang <em>zwischen</em> Ursache und Wirkung"}
};

/* Russian translations for the example sentences (keyed by plain German) */
const EX_RU = {
  "Die Abhängigkeit von Technologie nimmt in der modernen Gesellschaft ständig zu.":"Зависимость от технологий в современном обществе постоянно растёт.",
  "Eine starke Abhängigkeit von einem einzigen Anbieter ist riskant.":"Сильная зависимость от единственного поставщика рискованна.",
  "Soziale Abhängigkeit kann die persönliche Freiheit einschränken.":"Социальная зависимость может ограничивать личную свободу.",
  "Der Algorithmus entscheidet, welche Beiträge zuerst angezeigt werden.":"Алгоритм решает, какие публикации показываются первыми.",
  "Ein effizienter Algorithmus verarbeitet Millionen von Daten in Sekunden.":"Эффективный алгоритм обрабатывает миллионы данных за секунды.",
  "Der Algorithmus wurde so trainiert, dass er Muster erkennt.":"Алгоритм обучили так, чтобы он распознавал закономерности.",
  "Die Auswirkung neuer Technologien auf den Arbeitsmarkt ist erheblich.":"Влияние новых технологий на рынок труда значительно.",
  "Jede Entscheidung hat eine Auswirkung auf die Zukunft.":"Каждое решение имеет последствия для будущего.",
  "Die langfristige Auswirkung ist noch nicht absehbar.":"Долгосрочные последствия пока невозможно предвидеть.",
  "Wir müssen die Ergebnisse genau analysieren.":"Нам нужно тщательно проанализировать результаты.",
  "Der Forscher analysiert die Proben im Labor.":"Исследователь анализирует пробы в лаборатории.",
  "Sie hat den Text Satz für Satz analysiert.":"Она проанализировала текст предложение за предложением.",
  "Der Fortschritt in der Medizin rettet jeden Tag Leben.":"Прогресс в медицине каждый день спасает жизни.",
  "Technischer Fortschritt verändert, wie wir arbeiten.":"Технический прогресс меняет то, как мы работаем.",
  "Jeder kleine Fortschritt zählt beim Lernen.":"В учёбе важен каждый маленький шаг вперёд.",
  "Wir setzen auf nachhaltige Energiequellen.":"Мы делаем ставку на устойчивые источники энергии.",
  "Ein nachhaltiger Lebensstil schont die Umwelt.":"Экологичный образ жизни бережёт окружающую среду.",
  "Das Unternehmen wirtschaftet nachhaltig.":"Компания ведёт хозяйство экологично.",
  "Die Gesellschaft steht vor großen demografischen Veränderungen.":"Общество стоит перед большими демографическими изменениями.",
  "In einer gerechten Gesellschaft haben alle die gleichen Chancen.":"В справедливом обществе у всех равные возможности.",
  "Die digitale Gesellschaft verändert unsere Kommunikation.":"Цифровое общество меняет нашу коммуникацию.",
  "Die Nachhaltigkeit sollte im Zentrum jeder Entscheidung stehen.":"Устойчивость должна быть в центре каждого решения.",
  "Ökologische Nachhaltigkeit betrifft uns alle.":"Экологическая устойчивость касается всех нас.",
  "Ohne Nachhaltigkeit gibt es keine lebenswerte Zukunft.":"Без устойчивого развития нет достойного будущего.",
  "Die Forschung an erneuerbaren Energien macht große Fortschritte.":"Исследования в области возобновляемой энергии делают большие успехи.",
  "Grundlegende Forschung braucht Geduld und Geld.":"Фундаментальные исследования требуют терпения и денег.",
  "Die Forschung hat neue Erkenntnisse gebracht.":"Исследование принесло новые знания.",
  "Die Entwicklung neuer Technologien schreitet rasant voran.":"Развитие новых технологий стремительно продвигается.",
  "Die wirtschaftliche Entwicklung des Landes ist beeindruckend.":"Экономическое развитие страны впечатляет.",
  "Wir beobachten die Entwicklung mit großem Interesse.":"Мы наблюдаем за развитием с большим интересом.",
  "Sie übernimmt die Verantwortung für das gesamte Projekt.":"Она берёт на себя ответственность за весь проект.",
  "Jeder trägt Verantwortung für die Umwelt.":"Каждый несёт ответственность за окружающую среду.",
  "Die Verantwortung liegt bei der Leitung.":"Ответственность лежит на руководстве.",
  "Der Klimawandel ist eine globale Herausforderung.":"Изменение климата — это глобальный вызов.",
  "Sie sucht ständig neue Herausforderungen.":"Она постоянно ищет новые вызовы.",
  "Diese Herausforderung meistern wir gemeinsam.":"С этим вызовом мы справимся вместе.",
  "Das ist ein wesentlicher Unterschied.":"Это существенное различие.",
  "Der Preis spielt eine wesentliche Rolle.":"Цена играет существенную роль.",
  "Sie hat wesentlich zum Erfolg beigetragen.":"Она существенно способствовала успеху.",
  "Diese Aufgabe erfordert volle Konzentration.":"Эта задача требует полной концентрации.",
  "Der Plan erfordert sorgfältige Vorbereitung.":"План требует тщательной подготовки.",
  "Solche Projekte erfordern viel Zeit und Geduld.":"Такие проекты требуют много времени и терпения.",
  "Es gibt einen klaren Zusammenhang zwischen beiden Ereignissen.":"Между обоими событиями есть чёткая взаимосвязь.",
  "Sie erklärt die Zusammenhänge sehr verständlich.":"Она объясняет взаимосвязи очень понятно.",
  "In diesem Zusammenhang ist das besonders wichtig.":"В этом контексте это особенно важно."
};

const CATS = ["Alle","Technologie","Gesellschaft","Wissenschaft","Umwelt"];
const LEVELS = { B1:{theme:"Technologie",done:128}, B2:{theme:"Wissenschaft",done:64}, C1:{theme:"Philosophie",done:22} };
const LVL_ORDER = ["B1","B2","C1"];
const LVL_COLOR = { B1:"var(--rose)", B2:"var(--blue)", C1:"var(--lav)" };

/* A "page" is revealed in CHUNK-sized blocks as you scroll; once the whole
   page is shown, further words are reached by turning the page (pager). */
const PAGE_SIZE=12, CHUNK=4;
let level="B1", activeCat="Alle", activeIndex=-1, query="", page=0, shown=CHUNK, cardOpen=false, io=null;

const chipsEl=document.getElementById('chips'), listEl=document.getElementById('wordList'),
  detailEl=document.getElementById('detail'), searchEl=document.getElementById('search'),
  pagerEl=document.getElementById('pager'), mainEl=document.getElementById('mainGrid');

function filtered(){
  const q=query.trim().toLowerCase();
  return WORDS.filter(w=>{
    const c=activeCat==="Alle"||w.cat===activeCat;
    const m=!q||w.de.toLowerCase().includes(q)||w.ru.toLowerCase().includes(q)||(w.art+" "+w.de).toLowerCase().includes(q);
    return c&&m;
  });
}
function speak(t){ if('speechSynthesis'in window){const u=new SpeechSynthesisUtterance(t);u.lang='de-DE';u.rate=.9;speechSynthesis.cancel();speechSynthesis.speak(u);} }
function posLabel(w){return w.pos==="verb"?"Verb":(w.pos==="adj"?"Adjektiv":"Substantiv");}

const ARTS=["der","die","das","den","dem","des"];
function hlArt(s){
  const p=s.split(" ");
  if(ARTS.includes(p[0])) return `<em>${p[0]}</em>${p.slice(1).join(" ")?" "+p.slice(1).join(" "):""}`;
  return s;
}

/* ---------- category filters ---------- */
function renderChips(){
  chipsEl.innerHTML="";
  CATS.forEach(c=>{
    const b=document.createElement('button');
    b.className="chip"+(c===activeCat?" active":"");
    b.textContent=c==="Alle"?`Alle · ${WORDS.length}`:c;
    b.onclick=()=>{activeCat=c;page=0;shown=CHUNK;render();};
    chipsEl.appendChild(b);
  });
}

/* ---------- word list (ordered as added to the dictionary) ----------
   Within a page the rows reveal in CHUNK-sized blocks while you scroll down;
   when the whole page is shown, the pager turns to the next page. */
function pageCount(){return Math.max(1,Math.ceil(filtered().length/PAGE_SIZE));}
function renderList(){
  const items=filtered();listEl.innerHTML="";
  if(io){io.disconnect();io=null;}
  if(!items.length){listEl.innerHTML='<div class="empty">Keine Begriffe gefunden.</div>';renderPager(0);return;}
  page=Math.min(page,pageCount()-1);
  const pageItems=items.slice(page*PAGE_SIZE, page*PAGE_SIZE+PAGE_SIZE);
  shown=Math.max(Math.min(CHUNK,pageItems.length), Math.min(shown,pageItems.length));
  pageItems.slice(0,shown).forEach(w=>{
    const real=WORDS.indexOf(w);
    const d=document.createElement('div');
    d.className="word"+(cardOpen&&real===activeIndex?" active":"");
    d.dataset.level=w.level;
    d.dataset.index=real;
    d.style.setProperty('--brush', brushOf(w));
    const artHtml=w.art?`<span class="art">${w.art}</span> `:"";
    d.innerHTML=`
      <span class="wash"></span>
      <div class="w-body"><div class="de">${artHtml}${w.de}</div><div class="ru">${w.ru}</div></div>
      <div class="w-right"><span class="lvl-tag">${w.level}</span></div>`;
    d.onclick=()=>openDetail(real);
    listEl.appendChild(d);
  });
  // lazy reveal: when the last visible row scrolls into view, show one more block
  if(shown<pageItems.length){
    const last=listEl.lastElementChild;
    io=new IntersectionObserver(es=>{
      if(es.some(e=>e.isIntersecting)){
        shown=Math.min(shown+CHUNK, pageItems.length);
        renderList();
        if(cardOpen&&window.__updateSticky)requestAnimationFrame(window.__updateSticky);
      }
    },{rootMargin:'0px 0px 120px 0px'});
    io.observe(last);
  }
  renderPager(pageCount());
}

/* ---------- pagination control ---------- */
function renderPager(total){
  pagerEl.innerHTML="";
  if(total<=1){pagerEl.hidden=true;return;}
  pagerEl.hidden=false;
  const mk=(label,p,{active=false,disabled=false,ell=false}={})=>{
    if(ell){const s=document.createElement('span');s.className="pg-ell";s.textContent="…";pagerEl.appendChild(s);return;}
    const b=document.createElement('button');
    b.className="pg-btn"+(active?" active":"");b.textContent=label;b.disabled=disabled;
    if(!disabled&&!active)b.onclick=()=>{page=p;shown=CHUNK;render();listEl.scrollIntoView({behavior:'smooth',block:'start'});};
    pagerEl.appendChild(b);
  };
  mk("‹",page-1,{disabled:page===0});
  for(let i=0;i<total;i++){
    if(i===0||i===total-1||Math.abs(i-page)<=1){ mk(String(i+1),i,{active:i===page}); }
    else if(Math.abs(i-page)===2){ mk("",0,{ell:true}); }
  }
  mk("›",page+1,{disabled:page===total-1});
}

/* ---------- grammar ---------- */
function useBlock(w){
  // Prefer the curated GOV table for seed words; fall back to the rektion /
  // ready_phrase that the pipeline stores on each enriched word.
  let rule="", ex="";
  const g=GOV[w.de];
  if(g){ rule=g.rule; ex=g.ex; }
  else { rule=w._rektion||""; ex=w._readyPhrase||""; }
  if(!rule && !ex) return "";
  const ru=caseGlossRu(rule);
  return `<div class="g-use">
    <div class="g-use-top"><span class="g-use-lab">Verwendung</span>${rule?`<span class="g-use-rule">${rule}</span>`:""}</div>
    ${ru?`<div class="g-use-ru">${ru}</div>`:""}
    ${ex?`<div class="g-use-ex">${ex}</div>`:""}</div>`;
}

/* Russian gloss of the governed case, e.g. "von + Dat." → "дательный падеж" */
function caseGlossRu(rule){
  const m=/\b(Akk|Dat|Gen|Nom)/i.exec(rule||"");
  if(!m) return "";
  return {akk:"винительный падеж",dat:"дательный падеж",gen:"родительный падеж",nom:"именительный падеж"}[m[1].toLowerCase()]||"";
}
/* collapsible paradigm (verb conjugation / noun & adjective declension) */
function toggleAcc(btn){
  const open=btn.classList.toggle('open');
  btn.querySelector('.g-arrow').style.transform=open?'rotate(180deg)':'';
  btn.nextElementSibling.style.display=open?'block':'none';
  if(window.__updateSticky)requestAnimationFrame(window.__updateSticky);
}
function accBlock(title,inner){
  return `<button class="g-acc-btn" type="button" onclick="toggleAcc(this)">
      <span>${title}</span><span class="g-arrow">▼</span></button>
    <div class="g-acc">${inner}</div>`;
}
function specChip(label,value){
  return `<span class="g-s"><i>${label}</i>${value}</span>`;
}

/* short Russian grammar hints — gender / aux / Rektion, in quiet grey */
function ruGrammarHint(w){
  const bits=[];
  if(w.pos==="noun"){
    const gx={der:"мужской род",die:"женский род",das:"средний род"}[w.art]||"";
    if(gx) bits.push(gx);
  } else if(w.pos==="verb" && w.gram && w.gram.hilfsverb){
    bits.push("вспом. глагол «"+w.gram.hilfsverb+"»");
  }
  return bits.join(" · ");
}

/* highlight the headword + its known inflected forms in an example sentence */
function highlightForms(text,w){
  if(/<\/?b>/.test(text)) return text;            // already marked (LLM bold)
  const base=w.de;
  const forms=new Set();
  const add=s=>{ s=String(s||"").replace(/^(der|die|das)\s+/i,"").trim();
    if(s.length>=3 && /^\p{L}/u.test(s)) forms.add(s); };
  add(base);
  const g=w.gram||{};
  if(w.pos==="noun"){
    add(g.plural); add(g.genitiv);
    if(g.rows) g.rows.forEach(r=>{ add(r[1]); add(r[2]); });
    ["s","es","e","en","n","ern","er"].forEach(suf=>add(base+suf));
    if(g.plural) add(String(g.plural).replace(/^(der|die|das)\s+/i,"")+"n");  // Dativ Plural
  } else if(w.pos==="adj"){
    ["","e","er","es","en","em","ere","eren","sten"].forEach(suf=>add(base+suf));
    if(g.steigerung) g.steigerung.forEach(add);
  } else if(w.pos==="verb"){
    add(g.partizip);
    if(g.praeteritum) add(String(g.praeteritum).split(" ")[0]);
    if(g.praesens) g.praesens.forEach(p=>add(String(p[1]).split(" ")[0]));
  }
  const list=[...forms].filter(Boolean).sort((a,b)=>b.length-a.length);
  if(!list.length) return text;
  const esc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");
  let re;
  try{ re=new RegExp("(?<!\\p{L})("+list.map(esc).join("|")+")(?!\\p{L})","giu"); }
  catch(e){ return text; }
  return text.replace(re,"<b>$1</b>");
}

/* Grammatik — compact "spec line" of key forms; the full paradigm lives behind
   an "alle Formen" toggle. Forms that don't apply are simply omitted. */
function gramBlock(w){
  const g=w.gram;
  if(!g) return `<div class="g-spec">${specChip("Wortart",posLabel(w))}</div>`+useBlock(w);
  let chips=[],title="",table="",extra="",hasTable=false;

  if(g.type==="noun"){
    chips.push(specChip("Genus",w.genus));
    if(g.plural && !["–","—",""].includes(g.plural)) chips.push(specChip("Plural",g.plural));
    let gen=g.genitiv;
    if(!gen && g.rows){ const r=g.rows.find(x=>x[0]==="Genitiv"); if(r) gen=r[1]; }
    if(gen && gen!=="–") chips.push(specChip("Genitiv",gen));
    if(g.rows){
      hasTable=true; title="Alle Formen";
      const order=[0,3,2,1]; // Nominativ · Akkusativ · Dativ · Genitiv
      const rows=order.map(i=>g.rows[i]).map(r=>`<tr><th>${r[0]}</th><td>${hlArt(r[1])}</td><td>${hlArt(r[2])}</td></tr>`).join("");
      table=`<table class="gram"><thead><tr><th></th><th>Singular</th><th>Plural</th></tr></thead><tbody>${rows}</tbody></table>`;
    }
  } else if(g.type==="verb"){
    chips.push(specChip("Hilfsverb",g.hilfsverb));
    const er=(g.praesens.find(p=>p[0]==="er/sie/es")||[])[1];
    if(er && er!=="–") chips.push(specChip("Präsens (er)",er));
    if(g.praeteritum && g.praeteritum!=="–") chips.push(specChip("Präteritum",g.praeteritum));
    if(g.partizip && g.partizip!=="–") chips.push(specChip("Perfekt",(g.hilfsverb==="sein"?"ist ":"hat ")+g.partizip));
    hasTable=true; title="Alle Formen";
    const rows=g.praesens.map(r=>`<tr><th>${r[0]}</th><td>${r[1]}</td></tr>`).join("");
    table=`<table class="gram"><thead><tr><th>Person</th><th>Präsens</th></tr></thead><tbody>${rows}</tbody></table>`;
  } else { // adjective — Steigerung line is enough; no filler table
    const s=g.steigerung;
    chips.push(`<span class="g-s g-s--wide"><i>Steigerung</i>${s[0]} <em>→</em> ${s[1]} <em>→</em> ${s[2]}</span>`);
  }

  const hint=ruGrammarHint(w);
  return `<div class="g-spec">${chips.join("")}</div>`
    + (hint?`<div class="g-hint">${hint}</div>`:"")
    + useBlock(w)
    + (hasTable?accBlock(title,table+extra):"");
}

/* ---------- detail card ---------- */
function renderDetail(){
  const w=WORDS[activeIndex]; if(!w){detailEl.innerHTML="";return;}
  const artHtml=w.art?`<span class="art">${w.art}</span> `:"";
  const longCls=((w.art?w.art.length+1:0)+w.de.length)>16?" long":"";
  const examplesHtml=w.examples.map((e,i)=>{
    const de=(typeof e==="object")?e.de:e;
    const ru=(typeof e==="object" && e.ru)?e.ru:(EX_RU[String(de).replace(/<\/?b>/g,"")]||"");
    return `<div class="ex"><span class="ex-n">${String(i+1).padStart(2,"0")}</span><div class="ex-body"><p class="ex-de">${highlightForms(de,w)}</p>${ru?`<p class="ex-ru">${ru}</p>`:""}</div></div>`;
  }).join("");
  detailEl.innerHTML=`
    <button class="d-close" id="dClose" type="button" aria-label="Schließen">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
    <div class="d-head">
      <div class="d-meta"><span class="d-cat"><span class="hl">${posLabel(w)}</span> · ${w.cat}</span><span class="d-level">${w.level}</span></div>
      <div class="d-word${longCls}">${artHtml}${w.de}</div>
      <div class="d-tools">
        <span class="d-ipa">${w.ipa||""}</span>
        <button class="d-hear" id="hear">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M5 9v6h4l5 5V4L9 9H5z"/><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>
          Aussprache
        </button>
      </div>
      <div class="d-ru">${w.ru}</div>
    </div>
    <div class="d-body">
      ${(w.def||w.pull)?`<section><div class="lab">Bedeutung</div>${w.def?`<p class="def">${w.def}</p>`:""}${w.pull?`<blockquote class="pull">${w.pull}</blockquote>`:""}</section>
      <hr class="d-sep">`:""}
      <section><div class="lab">Grammatik</div>${gramBlock(w)}</section>
      ${examplesHtml?`<hr class="d-sep">
      <section><div class="lab">Beispiele</div><div class="ex-list">${examplesHtml}</div></section>`:""}
    </div>`;
  detailEl.querySelector('#hear').onclick=()=>speak((w.art?w.art+" ":"")+w.de);
  detailEl.querySelector('#dClose').onclick=closeDetail;
}

/* ---------- open / close the right-column card ---------- */
function openDetail(idx){
  const wasOpen=cardOpen;
  activeIndex=idx; cardOpen=true; mainEl.classList.add('open');
  render();
  // on first open the list reflows from multi-column to one column — keep the
  // chosen word in view so the move never feels like chaos.
  const el=listEl.querySelector('.word[data-index="'+activeIndex+'"]');
  if(el && !wasOpen) el.scrollIntoView({behavior:'smooth',block:'center'});
  requestAnimationFrame(()=>{ if(window.__resetSticky)window.__resetSticky(); });
}
function closeDetail(){
  cardOpen=false; mainEl.classList.remove('open'); hideLink();
  renderList();                 // back to multi-column, drop the active highlight
}
document.addEventListener('keydown',e=>{ if(e.key==="Escape"&&cardOpen)closeDetail(); });

/* ---------- right rail: distribution donut ---------- */
function renderRail(){
  const segs=LVL_ORDER.map(lv=>({lv,val:LEVELS[lv].done,color:LVL_COLOR[lv]}));
  const total=segs.reduce((a,s)=>a+s.val,0);
  const r=46,C=2*Math.PI*r,cx=60,cy=60; let off=0,paths="";
  segs.forEach(s=>{
    const len=s.val/total*C;
    paths+=`<circle class="seg" r="${r}" cx="${cx}" cy="${cy}" fill="none" stroke="${s.color}"
      stroke-width="${s.lv===level?17:14}" stroke-dasharray="${len.toFixed(2)} ${(C-len).toFixed(2)}"
      stroke-dashoffset="${(-off).toFixed(2)}" opacity="${s.lv===level?1:.85}"></circle>`;
    off+=len;
  });
  document.getElementById('donut').innerHTML=`<svg viewBox="0 0 120 120"><g transform="rotate(-90 ${cx} ${cy})">${paths}</g></svg>`;
  document.getElementById('donutTotal').textContent=total;
  document.getElementById('totDone').textContent=total;
  const lg=document.getElementById('legend'); lg.innerHTML="";
  segs.forEach(s=>{
    const row=document.createElement('div');
    row.className="lg "+s.lv.toLowerCase()+(s.lv===level?" is-active":"");
    row.innerHTML=`<span class="dot"></span><span class="nm">${s.lv}</span><span class="vl">${s.val} Wörter</span>`;
    row.onclick=()=>{level=s.lv;applyLevel();};
    lg.appendChild(row);
  });
}

function applyLevel(){
  // the level pill moved out of the header into the unified bar; the rail
  // legend is now the level switcher. Guard the optional header elements.
  const pill=document.getElementById('pillText'); if(pill) pill.textContent=`${level} · ${LEVELS[level].theme}`;
  const lr=document.getElementById('lrLevel'); if(lr) lr.textContent=level;
  renderRail();
}
const levelPillEl=document.getElementById('levelPill');
if(levelPillEl) levelPillEl.onclick=()=>{
  level=LVL_ORDER[(LVL_ORDER.indexOf(level)+1)%LVL_ORDER.length];
  applyLevel();
};

function render(){
  renderChips();
  renderList();
  if(cardOpen){ renderDetail(); requestAnimationFrame(window.__updateSticky||updateLink); }
}

searchEl.addEventListener('input',e=>{query=e.target.value;page=0;shown=CHUNK;render();});

applyLevel();
render();

/* ---------------------------------------------------------------------------
   Live connector line: a dynamic, dashed orange stroke from the word in the
   open card's header to the SAME word in the list. It is anchored to the row,
   so it stays attached while the page scrolls. Recomputed every scroll/resize
   and after each render. If the target word isn't on the current page (or was
   filtered out), the line simply hides.
--------------------------------------------------------------------------- */
const lineEl=document.getElementById('linkLine'), linkPath=document.getElementById('linkPath'),
      linkDot=document.getElementById('linkDot'), linkAnchor=document.getElementById('linkAnchor');

// NB: SVGElement has no `hidden` IDL property, so we must toggle the content
// attribute explicitly (setting `.hidden` would silently do nothing on <svg>).
function hideLink(){ lineEl.setAttribute('hidden',''); }

function updateLink(){
  if(!cardOpen){ hideLink(); return; }
  // card end: the word in the header (anchor just LEFT of the article).
  // list end: the SAME word in the list — the line approaches from the right
  // (past the level tag) and lands on the word itself.
  const titleEl = detailEl.querySelector('.d-word');
  const wordEl  = listEl.querySelector('.word[data-index="'+activeIndex+'"] .de');
  if(!titleEl || !wordEl){ hideLink(); return; }

  const tR=titleEl.getBoundingClientRect(), wR=wordEl.getBoundingClientRect();
  const sx=tR.left,            sy=tR.top + tR.height/2;   // header word, left edge
  const ex=wR.right + 9,       ey=wR.top + wR.height/2;   // list word, just past its end

  const dir=Math.sign(sx-ex)||1;                          // +1 when card is right of the word
  const k=Math.max(70, Math.abs(sx-ex)*0.4);
  const c1x=sx-dir*k, c2x=ex+dir*k;                        // handles fan out horizontally
  linkPath.setAttribute('d',
    `M ${sx.toFixed(1)} ${sy.toFixed(1)} C ${c1x.toFixed(1)} ${sy.toFixed(1)}, ${c2x.toFixed(1)} ${ey.toFixed(1)}, ${ex.toFixed(1)} ${ey.toFixed(1)}`);
  linkAnchor.setAttribute('cx',sx.toFixed(1)); linkAnchor.setAttribute('cy',sy.toFixed(1));
  linkDot.setAttribute('cx',ex.toFixed(1));    linkDot.setAttribute('cy',ey.toFixed(1));
  lineEl.removeAttribute('hidden');
}

/* Directional-sticky card (the original scrolling behaviour): the sheet flows
   with the page until its far edge meets the viewport, then pins — so you read
   the whole card by scrolling the page, with a single scrollbar. The same
   handler refreshes the orange connector right after the card is placed. */
(function(){
  const col=document.getElementById('colDetail'), card=detailEl, GAP=20;
  const clamp=(v,a,b)=> a>b ? a : (v<a?a:(v>b?b:v));
  let colTopDoc=0,colH=0,ch=0,curVt=null,lastScroll=window.pageYOffset;

  function measure(){
    const r=col.getBoundingClientRect();
    colTopDoc=r.top+window.pageYOffset; colH=col.offsetHeight; ch=card.offsetHeight;
  }
  function place(){
    const vh=window.innerHeight, scroll=window.pageYOffset;
    const delta=scroll-lastScroll; lastScroll=scroll;
    const colTopVp=colTopDoc-scroll, colBottomVp=colTopVp+colH;
    if(curVt===null) curVt=colTopVp;
    const stickyMin=Math.min(GAP, vh-ch-GAP);
    let vt=clamp(curVt-delta, stickyMin, GAP);
    vt=clamp(vt, colTopVp, colBottomVp-ch);
    curVt=vt;
    card.style.transform='translate3d(0,'+(vt-colTopVp).toFixed(1)+'px,0)';
  }
  function frame(){
    if(mainEl.classList.contains('open')){ place(); updateLink(); }
    else { hideLink(); }
  }
  window.addEventListener('scroll', frame, {passive:true});
  window.addEventListener('resize', function(){ measure(); frame(); });
  window.addEventListener('load',   function(){ measure(); frame(); });
  window.__updateSticky = function(){ measure(); frame(); };            // after re-render / accordion
  window.__resetSticky  = function(){ curVt=null; measure(); frame(); }; // on a fresh open
  measure(); hideLink();
})();

/* =========================================================================
   API word loader — merges pipeline/seed words from the backend into WORDS
   ========================================================================= */

const API_BASE_DICT = "";

function _mapApiWord(w) {
  const art  = (w.article || "").toLowerCase();
  const pos  = w.word_type === "adjective" ? "adj"
             : w.word_type === "verb"      ? "verb"
             : "noun";

  // Build category from first topic (capitalize first letter)
  const topicRaw = (w.topics && w.topics.length) ? w.topics[0] : "";
  const cat = topicRaw
    ? topicRaw.charAt(0).toUpperCase() + topicRaw.slice(1)
    : "Andere";

  // Examples: API stores [{text_de, text_ru, is_ai}] → {de, ru}.
  // Pipeline marks the headword with markdown **bold**; render it as <b>.
  const examples = (w.examples || []).map(e => {
    const de = (typeof e === "object") ? (e.text_de || "") : String(e);
    const ru = (typeof e === "object") ? (e.text_ru || "") : "";
    return { de: de.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>"), ru };
  }).filter(x => x.de).slice(0, 3);

  // Grammar from pipeline grammar_data. Tolerant of BOTH the canonical full
  // schema (declension as full case/tense tables) and the legacy compact shape
  // ({Genus, Plural, "Genitiv Singular"}), so the table is never empty while
  // the DB is being re-processed. Canonical schema is documented in PIPELINE.md.
  const gd = w.grammar_data || {};
  const decl = gd.declension || {};
  const declKeys = Object.keys(decl);
  const base = (w.german || "").replace(/^(der|die|das)\s+/i, "");
  // a verb form may arrive as a string ("regelte") or a per-person object —
  // coerce to a single display string (prefer 3rd person, then 1st).
  const formStr = v => (v && typeof v === "object")
    ? (v["er/sie/es"] || v.ich || Object.values(v)[0] || "–")
    : (v || "–");
  let gram = null;

  if (pos === "noun" && declKeys.length) {
    const cases = ["Nominativ","Genitiv","Dativ","Akkusativ"];
    const hasFullTable = cases.some(c => decl[c] && typeof decl[c] === "object");
    let rows, plural;
    if (hasFullTable) {
      rows = cases.map(c => {
        const row = decl[c] || {};
        return [c, row.singular || "–", row.plural || "–"];
      });
      plural = decl.Nominativ?.plural || decl.Plural || decl.plural || "–";
      gram = { type:"noun", plural, rows };
    } else {
      // legacy compact data — no full case table yet. Show Genus/Plural/Genitiv
      // compactly instead of a wall of "–"; the full table fills in on re-process.
      plural = decl.Plural || decl.plural || "–";
      const genSg = decl["Genitiv Singular"] || decl.genitiv_singular || decl.Genitiv || "";
      gram = { type:"noun", plural, genitiv: genSg };
    }
  } else if (pos === "verb" && declKeys.length) {
    const pres = decl.Präsens || decl.praesens || decl.present || {};
    const praesens = ["ich","du","er/sie/es","wir","ihr","sie/Sie"].map(p => [p, pres[p] || "–"]);
    gram = {
      type:"verb",
      hilfsverb:   decl.hilfsverb || decl.Hilfsverb || decl.auxiliary || "haben",
      partizip:    formStr(decl["Partizip II"] || decl.partizip2 || decl.partizipII || decl.perfect),
      praeteritum: formStr(decl["Präteritum"] || decl.prateritum || decl.simple_past || decl.preterite),
      praesens,
    };
  } else if (pos === "adj" && declKeys.length) {
    const positiv    = decl.positiv    || decl.Positiv    || base;
    const komparativ = decl.komparativ || decl.Komparativ || "—";
    const superlativ = decl.superlativ || decl.Superlativ || "—";
    gram = {
      type: "adj",
      steigerung: [positiv, komparativ, superlativ],
      rows: [
        ["Maskulinum", "der " + positiv + "e …"],
        ["Femininum",  "die " + positiv + "e …"],
        ["Neutrum",    "das " + positiv + "e …"],
        ["Plural",     "die " + positiv + "en …"],
      ],
    };
  }

  return {
    de:       base,
    art:      art || null,
    pos,
    cat,
    level:    w.level || "B2",
    genus:    art === "die" ? "Femininum" : art === "der" ? "Maskulinum" : art === "das" ? "Neutrum" : "",
    ru:       w.translation_ru || "",
    ipa:      gd.ipa || "",
    def:      gd.definition || "",
    // ready_phrase is surfaced in the Verwendung block; keep the pull-quote for
    // a real definition-derived line (filled once words are re-processed).
    pull:     "",
    gram,
    examples,
    _apiId:   w.id,
    _source:  w.source || "api",
    _rektion: gd.rektion || "",
    _readyPhrase: gd.ready_phrase || "",
  };
}

async function loadApiWords() {
  try {
    const res = await fetch(`${API_BASE_DICT}/api/words?limit=500`);
    if (!res.ok) return;
    const apiWords = await res.json();
    if (!Array.isArray(apiWords)) return;

    // IDs already in WORDS (avoid double-adding on refresh)
    const existingIds = new Set(WORDS.map(w => w._apiId).filter(Boolean));
    // Names already in WORDS (avoid duplicating seed words)
    const existingNames = new Set(WORDS.map(w => w.de.toLowerCase()));

    let added = 0;
    apiWords.forEach(w => {
      if (existingIds.has(w.id)) return;
      const mapped = _mapApiWord(w);
      if (existingNames.has(mapped.de.toLowerCase())) return;
      existingNames.add(mapped.de.toLowerCase());
      existingIds.add(w.id);
      WORDS.push(mapped);
      added++;
    });

    if (added > 0) {
      // Add any new categories from API to CATS
      const newCats = [...new Set(WORDS.map(w => w.cat))].filter(c => !CATS.includes(c));
      CATS.push(...newCats);

      // Update level counts from API data
      const lvlCounts = {B1:0, B2:0, C1:0};
      WORDS.forEach(w => { if(lvlCounts[w.level] !== undefined) lvlCounts[w.level]++; });
      Object.keys(lvlCounts).forEach(lv => { if(LEVELS[lv]) LEVELS[lv].done = lvlCounts[lv]; });

      render();
      renderRail();
    }
  } catch(e) {
    console.warn("Could not load API words:", e);
  }
}

// Load on page init
loadApiWords();

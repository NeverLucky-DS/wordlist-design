/* =====================================================================
   Pipeline page — dictionary-ingestion dashboard.
   Talks to /api/vocab/{build,status,stats,words,word}. Transparent by design:
   launch the run, watch every stage, browse the saved words per source.
   ===================================================================== */
'use strict';

const SRC_LABEL = {universal:"Universal", langenscheidt:"Langenscheidt", lein:"Lein",
  allgemein:"Общелексический", advanced:"Advanced", duden_syn:"Duden синонимы",
  collocations:"Коллокации", idioms:"Идиомы"};
const LVL = {b1_core:{n:"B1",v:"--b1"}, b2_core:{n:"B2",v:"--b2"},
  c1_core:{n:"C1",v:"--c1"}, extended:{n:"ext",v:"--ext"}};

let minZipf = 2.3, polling = null, curLevel = "", deb = null;
const $ = id => document.getElementById(id);
const fmt = n => (n==null ? "–" : n.toLocaleString("ru-RU"));
const esc = s => (s||"").replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));

document.querySelectorAll("#presets .preset").forEach(b => b.onclick = () => {
  document.querySelectorAll("#presets .preset").forEach(x => x.classList.remove("on"));
  b.classList.add("on"); minZipf = parseFloat(b.dataset.z);
});
document.querySelectorAll("#lvls button").forEach(b => b.onclick = () => {
  document.querySelectorAll("#lvls button").forEach(x => x.classList.remove("on"));
  b.classList.add("on"); curLevel = b.dataset.l; searchWords();
});
$("runBtn").onclick = startBuild;
$("q").oninput = () => { clearTimeout(deb); deb = setTimeout(searchWords, 220); };

async function startBuild(){
  const btn = $("runBtn");
  if (btn.classList.contains("stop")) return;
  btn.disabled = true;
  const r = await fetch(`/api/vocab/build?min_zipf=${minZipf}`, {method:"POST"});
  if (r.status === 409){ btn.disabled = false; toast("Обработка уже идёт"); return; }
  $("srcs").innerHTML = "";
  poll(); polling = setInterval(poll, 1000);
}

const STAGE_TXT = {
  start: () => "Читаю источники…",
  source: e => `Прочитан ${SRC_LABEL[e.source]||e.source}: ${fmt(e.entries)} записей · агрегат ${fmt(e.agg)}`,
  source_error: e => `⚠ ошибка в ${e.source}: ${e.error}`,
  aggregate_done: e => `Агрегация готова — ${fmt(e.agg)} записей`,
  coverage: e => `Покрытие (реальные леммы): ${fmt(e.count)}`,
  cap: e => `Порог zipf ≥ ${e.min_zipf} → оставлено ${fmt(e.kept)}`,
  writing: e => e.written ? `Запись в БД… ${fmt(e.written)}/${fmt(e.total)}` : `Запись в БД… (${fmt(e.total)})`,
  done: e => `Готово · ${fmt(e.summary.total)} слов за ${e.summary.secs}s`,
};
const STAGE_PCT = {start:5, source:35, aggregate_done:55, coverage:65, cap:72, writing:90, done:100};

async function poll(){
  let j;
  try { j = await (await fetch("/api/vocab/status")).json(); }
  catch { return; }
  const cur = j.current;
  if (cur){
    $("stage").textContent = (STAGE_TXT[cur.stage] || (() => cur.stage))(cur);
    $("barFill").style.width = (STAGE_PCT[cur.stage] || 10) + "%";
    $("elapsed").textContent = cur.t != null ? cur.t + " s" : "";
  }
  const done = {};
  j.events.filter(e => e.stage === "source").forEach(e => done[e.source] = e.entries);
  $("srcs").innerHTML = Object.keys(SRC_LABEL).map(k =>
    done[k] != null ? `<span class="chip done">${SRC_LABEL[k]} <b>${fmt(done[k])}</b></span>`
                    : `<span class="chip">${SRC_LABEL[k]}</span>`).join("");
  $("log").innerHTML = j.events.slice(-12).map(e =>
    `<div>${(STAGE_TXT[e.stage] || (() => e.stage))(e)}</div>`).join("");
  const btn = $("runBtn");
  if (j.running){ btn.classList.add("stop"); btn.textContent = "Идёт обработка…"; btn.disabled = true; }
  else {
    clearInterval(polling); polling = null;
    btn.classList.remove("stop"); btn.textContent = "Запустить обработку"; btn.disabled = false;
    if (j.error) $("stage").textContent = "Ошибка: " + j.error;
    else if (j.summary) toast(`Готово · ${fmt(j.summary.total)} слов`);
    loadStats(); searchWords();
  }
}

async function loadStats(){
  let s;
  try { s = await (await fetch("/api/vocab/stats")).json(); }
  catch { return; }
  if (!s.exists){ $("statsSub").textContent = "База ещё не собрана — запусти обработку."; return; }
  $("statsSub").textContent = `Всего ${fmt(s.total)} лемм · обязательных (B1+B2) ${fmt(s.obligatory)}`;
  $("kpis").innerHTML =
    `<div class="kpi"><b>${fmt(s.total)}</b><span>слов в базе</span></div>
     <div class="kpi"><b>${fmt(s.obligatory)}</b><span>обязательных (B1+B2)</span></div>
     <div class="kpi"><b>${fmt(s.fields.synonyms)}</b><span>с синонимами</span></div>
     <div class="kpi"><b>${fmt(s.fields.examples)}</b><span>с примерами</span></div>`;
  const tot = s.total || 1;
  $("levelbar").innerHTML = Object.keys(LVL).map(k => {
    const n = s.levels[k] || 0, w = 100 * n / tot;
    return `<div style="width:${w}%;background:var(${LVL[k].v})" title="${LVL[k].n}: ${n}">${w>7?LVL[k].n:""}</div>`;
  }).join("");
  $("legend").innerHTML = Object.keys(LVL).map(k =>
    `<span><i style="background:var(${LVL[k].v})"></i>${LVL[k].n} · ${fmt(s.levels[k]||0)}</span>`).join("");
  $("fields").innerHTML = Object.entries(s.sources).map(([k,v]) =>
    `<div>${SRC_LABEL[k]||k}: <b>${fmt(v)}</b></div>`).join("");
}

async function searchWords(){
  const q = $("q").value.trim();
  let r;
  try { r = await (await fetch(`/api/vocab/words?q=${encodeURIComponent(q)}&level=${curLevel}&limit=40`)).json(); }
  catch { return; }
  const el = $("results");
  if (!r.items.length){ el.innerHTML = `<div class="empty">Ничего не найдено.</div>`; return; }
  el.innerHTML = r.items.map(w => {
    const art = w.article ? `<span class="art">${w.article}</span> ` : "";
    const L = LVL[w.level] || {n:w.level, v:"--muted"};
    const tr = (w.translations||[]).slice(0,3).join("; ");
    return `<div class="word">
      <div class="row" data-lemma="${esc(w.lemma)}">
        <span class="lemma">${art}${esc(w.lemma)}</span>
        <span class="tag" style="background:var(${L.v})">${L.n}</span>
        <span class="tr">${esc(tr)}</span>
        <span class="rank">#${w.freq_rank}</span>
      </div><div class="detail"></div></div>`;
  }).join("");
  el.querySelectorAll(".row").forEach(row =>
    row.onclick = () => toggleCard(row, row.dataset.lemma));
}

async function toggleCard(row, lemma){
  const d = row.nextElementSibling;
  if (d.classList.contains("open")){ d.classList.remove("open"); return; }
  let w;
  try { w = await (await fetch(`/api/vocab/word/${encodeURIComponent(lemma)}`)).json(); }
  catch { return; }
  let h = "";
  if ((w.forms&&w.forms.length) || (w.pos&&w.pos.length))
    h += `<div class="k">грамматика</div><div>${esc([(w.pos||[]).join(", "),(w.forms||[]).join(", ")].filter(Boolean).join(" · ")) || "—"}</div>`;
  h += `<div class="k">переводы</div><div>${esc((w.translations||[]).slice(0,8).join("; ")) || "—"}</div>`;
  if (w.synonyms&&w.synonyms.length) h += `<div class="k">синонимы (de)</div><div>${esc(w.synonyms.slice(0,5).join(" | "))}</div>`;
  if (w.idioms&&w.idioms.length) h += `<div class="k">идиомы</div><div>${esc(w.idioms.slice(0,4).join(" | "))}</div>`;
  if (w.collocations&&w.collocations.length) h += `<div class="k">коллокации</div><div>${esc(w.collocations.slice(0,3).join(" | "))}</div>`;
  h += `<div class="k">вклад по источникам</div>`;
  for (const [s, bs] of Object.entries(w.by_source||{})){
    const bits = [];
    if (bs.translations) bits.push("перев: " + bs.translations.slice(0,3).join("; "));
    if (bs.synonyms) bits.push("син: " + bs.synonyms.slice(0,2).join("; "));
    if (bs.examples) bits.push("прим: " + bs.examples[0]);
    if (bs.idioms) bits.push("идиом: " + bs.idioms.slice(0,2).join("; "));
    if (bs.collocations) bits.push("коллок: " + bs.collocations[0]);
    h += `<div class="bysrc"><span class="s">${SRC_LABEL[s]||s}</span>${esc(bits.join("  ·  ") || "грамматика/формы")}</div>`;
  }
  d.innerHTML = h; d.classList.add("open");
}

let toastT = null;
function toast(msg){
  const t = $("toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("show"), 2600);
}

loadStats();
searchWords();

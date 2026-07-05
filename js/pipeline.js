/* =====================================================================
   Pipeline page — talks to /api/pipeline/{overview,queue,runs,run}
   ===================================================================== */
'use strict';

const API = "";

/* mirror of the backend's curated catalog — for the suggestion chips */
const CATALOG = [
  'Klimawandel', 'Digitalisierung', 'Migration', 'Soziale Medien',
  'Künstliche Intelligenz', 'Globalisierung', 'Bildungssystem', 'Arbeitswelt der Zukunft',
  'Umweltschutz', 'Energiewende', 'Massentourismus', 'Datenschutz', 'Homeoffice',
  'Konsumgesellschaft', 'Generationenkonflikt', 'Sprachenlernen',
];

let overview = null, runs = [], queueItems = [];
const openRuns = new Set();
let pollTimer = null;

function api(path, opts) {
  return fetch(API + path, opts).then(r => {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  });
}

async function refresh() {
  try {
    const [ov, rs, q] = await Promise.all([
      api('/api/pipeline/overview'),
      api('/api/pipeline/runs'),
      api('/api/pipeline/queue'),
    ]);
    overview = ov; runs = rs; queueItems = q;
    render();
  } catch (_) { /* backend asleep — keep last view */ }
  schedule();
}

function schedule() {
  clearTimeout(pollTimer);
  const busy = runs.some(r => r.status === 'running') ||
               queueItems.some(i => i.status === 'running');
  pollTimer = setTimeout(refresh, busy ? 3000 : 9000);
}

async function queueTopic() {
  const input = document.getElementById('topicInput');
  const topic = input.value.trim();
  if (!topic) { input.focus(); return; }
  const btn = document.getElementById('queueBtn');
  btn.disabled = true;
  try {
    const res = await api('/api/pipeline/queue', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topics: [topic] }),
    });
    input.value = '';
    toast(res.queued?.length ? `„${topic}“ eingereiht` : `„${topic}“ ist bereits in der Warteschlange`);
    await refresh();
  } catch (e) { toast('Fehler: ' + e.message); }
  btn.disabled = false;
}

async function startNow(topic, btnEl) {
  if (btnEl) btnEl.disabled = true;
  try {
    await api('/api/pipeline/run', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, article_urls: [] }),
    });
    toast(`„${topic}“ gestartet`);
    await refresh();
  } catch (e) { toast('Fehler: ' + e.message); if (btnEl) btnEl.disabled = false; }
}

function render() {
  renderAutopilot();
  renderSuggest();
  renderQueue();
  renderShelf();
  renderLog();
  renderRail();
}

function renderAutopilot() {
  const s = overview?.settings;
  const el = document.getElementById('autopilot');
  if (!s) { el.hidden = true; return; }
  el.hidden = false;
  el.classList.toggle('off', !s.autorun);
  document.getElementById('autopilotText').textContent = s.autorun
    ? `Autopilot aktiv — prüft alle ${s.interval_minutes} Min${s.auto_topics ? ', ergänzt Themen von selbst' : ''}`
    : 'Autopilot pausiert';
}

function renderSuggest() {
  const host = document.getElementById('suggest');
  const known = new Set([
    ...(overview?.topics || []).map(t => t.topic.toLowerCase()),
    ...queueItems.map(i => i.topic.trim().toLowerCase()),
  ]);
  const fresh = CATALOG.filter(t => !known.has(t.toLowerCase())).slice(0, 5);
  host.querySelectorAll('.sg-chip').forEach(c => c.remove());
  host.hidden = fresh.length === 0;
  fresh.forEach(t => {
    const chip = document.createElement('button');
    chip.className = 'sg-chip'; chip.type = 'button'; chip.textContent = t;
    chip.onclick = () => {
      const input = document.getElementById('topicInput');
      input.value = t; input.focus();
    };
    host.appendChild(chip);
  });
}

function renderQueue() {
  const stack = document.getElementById('queueStack');
  const active = queueItems.filter(i => i.status === 'pending' || i.status === 'running');
  document.getElementById('queueCount').textContent = active.length || '';
  stack.innerHTML = '';
  if (!active.length) {
    stack.innerHTML = `<div class="empty"><p>Die Warteschlange ist leer — der Autopilot ergänzt
      bei Bedarf <b>neue Themen von selbst</b>.</p></div>`;
    return;
  }
  active.forEach(item => {
    const running = item.status === 'running';
    const card = document.createElement('div');
    card.className = 'q-card' + (running ? ' is-running' : '');
    const attempts = item.attempts > 1 ? ` · Versuch ${item.attempts}/3` : '';
    card.innerHTML = `
      ${running ? '<span class="spin"></span>' : ''}
      <div class="q-name">${esc(item.topic)}</div>
      <div class="q-meta">${item.target_words ? 'Ziel ' + item.target_words + attempts : (attempts ? attempts.slice(3) : '')}</div>
      <span class="pill ${running ? 'p-run' : 'p-wait'}">${running ? 'Läuft' : 'Wartet'}</span>
    `;
    if (!running) {
      const btn = document.createElement('button');
      btn.className = 'q-start'; btn.type = 'button';
      btn.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Jetzt starten`;
      btn.onclick = () => startNow(item.topic, btn);
      card.appendChild(btn);
    }
    stack.appendChild(card);
  });
}

function renderShelf() {
  const shelf = document.getElementById('shelf');
  const topics = (overview?.topics || []).filter(t => t.words > 0 || t.queue_status);
  document.getElementById('shelfCount').textContent = topics.length || '';
  shelf.innerHTML = '';
  if (!topics.length) {
    shelf.innerHTML = `<div class="empty" style="grid-column:1/-1"><p>Noch keine Themen in der Sammlung.</p></div>`;
    return;
  }
  topics.forEach(t => {
    const target = t.target_words || overview?.settings?.target_words || 60;
    const pct = Math.min(100, Math.round(100 * t.words / target));
    const full = t.words >= target;
    const tile = document.createElement('div');
    tile.className = 'tile' + (full ? ' t-full' : '');
    tile.style.setProperty('--wash', `url('${PIPELINE_WASHES[hashIdx(t.topic, PIPELINE_WASHES.length)]}')`);
    tile.innerHTML = `
      <div class="tile-top">
        <div class="tile-name" title="${esc(t.topic)}">${esc(t.topic)}</div>
        ${tilePill(t, full)}
      </div>
      <div class="tile-frac"><b>${t.words}</b><span class="of">/ ${target} Wörter</span></div>
      <div class="tile-track"><div class="tile-fill" style="width:${pct}%"></div></div>
      <div class="tile-meta">
        <span>${t.phrases} Redemittel</span>
        ${t.failures_open ? `<span class="dot-sep"></span><span class="warn">${t.failures_open} offene Fehler</span>` : ''}
      </div>
    `;
    shelf.appendChild(tile);
  });
}

function tilePill(t, full) {
  if (t.queue_status === 'running') return `<span class="pill p-run">In Arbeit</span>`;
  if (t.queue_status === 'pending') return `<span class="pill p-wait">Wartet</span>`;
  if (t.queue_status === 'failed')  return `<span class="pill p-err">Fehler</span>`;
  if (full)                         return `<span class="pill p-ok">Vollständig</span>`;
  if (t.queue_status === 'done')    return `<span class="pill p-part">Teilweise</span>`;
  return '';
}

function renderLog() {
  const stack = document.getElementById('logStack');
  const list = runs.slice(0, 20);
  document.getElementById('logCount').textContent = runs.length || '';
  stack.innerHTML = '';
  if (!list.length) {
    stack.innerHTML = `<div class="empty"><p>Noch keine abgeschlossenen Läufe.</p></div>`;
    return;
  }
  list.forEach(r => stack.appendChild(buildRun(r)));
}

function buildRun(r) {
  const cls = r.status === 'completed' ? 'r-ok' : r.status === 'failed' ? 'r-err' : 'r-run';
  const glyph = r.status === 'completed' ? '✓' : r.status === 'failed' ? '✗' : `<span class="spin"></span>`;
  const open = openRuns.has(r.run_id);
  const el = document.createElement('div');
  el.className = `run ${cls}` + (open ? ' is-open' : '');

  const bits = [];
  bits.push(`<b>${r.words_added}</b>&nbsp;neu`);
  if (r.words_linked) bits.push(`<b>${r.words_linked}</b>&nbsp;verknüpft`);
  if (r.phrases_added) bits.push(`<b>${r.phrases_added}</b>&nbsp;Redemittel`);
  if (r.errors_count) bits.push(`${r.errors_count}&nbsp;Hinweise`);
  const stats = bits.join('<span style="color:var(--muted-2)">&nbsp;·&nbsp;</span>');

  el.innerHTML = `
    <div class="run-head">
      <div class="run-glyph">${glyph}</div>
      <div class="run-name" title="${esc(r.topic)}">${esc(r.topic)}</div>
      <div class="run-stats">${stats}</div>
      <div class="run-when">${fmtWhen(r)}</div>
      <svg class="run-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
    </div>
  `;
  el.querySelector('.run-head').onclick = () => toggleRun(r, el);
  if (open) loadRunBody(r, el);
  return el;
}

async function toggleRun(r, el) {
  if (openRuns.has(r.run_id)) {
    openRuns.delete(r.run_id);
    el.classList.remove('is-open');
    el.querySelector('.run-body')?.remove();
  } else {
    openRuns.add(r.run_id);
    el.classList.add('is-open');
    loadRunBody(r, el);
  }
}

async function loadRunBody(r, el) {
  el.querySelector('.run-body')?.remove();
  const body = document.createElement('div');
  body.className = 'run-body';
  const dur = fmtDur(r);
  body.innerHTML = `
    <div class="run-strip">
      <div class="rs-cell"><div class="rs-v">${r.words_added}</div><div class="rs-l">Neu</div></div>
      <div class="rs-cell"><div class="rs-v">${r.words_linked}</div><div class="rs-l">Verknüpft</div></div>
      <div class="rs-cell"><div class="rs-v">${r.phrases_added ?? 0}</div><div class="rs-l">Redemittel</div></div>
      <div class="rs-cell"><div class="rs-v">${dur}</div><div class="rs-l">Dauer</div></div>
    </div>`;
  el.appendChild(body);

  if (r.errors_count) {
    try {
      const detail = await api('/api/pipeline/run/' + r.run_id);
      const errs = (detail.errors || []).filter(e => e.error);
      if (errs.length && openRuns.has(r.run_id)) {
        const host = document.createElement('div');
        host.className = 'run-errs';
        errs.slice(0, 12).forEach(e => {
          const n = document.createElement('div');
          n.className = 'err-note';
          n.innerHTML = `<span class="e-stage">${esc(e.stage || '')}</span>${esc(trim(e.item, 38))} — ${esc(trim(e.error, 130))}`;
          host.appendChild(n);
        });
        if (errs.length > 12) {
          const more = document.createElement('div');
          more.className = 'err-more';
          more.textContent = `… und ${errs.length - 12} weitere`;
          host.appendChild(more);
        }
        body.appendChild(host);
      }
    } catch (_) {}
  }
}

function renderRail() {
  if (!overview) return;
  const topics = overview.topics || [];
  const sum = k => topics.reduce((a, t) => a + (t[k] || 0), 0);
  document.getElementById('railWords').textContent = sum('words');
  document.getElementById('railTopics').textContent = topics.filter(t => t.words > 0).length;
  document.getElementById('railPhrases').textContent = sum('phrases');
  document.getElementById('railFails').textContent = sum('failures_open');
  document.getElementById('railTarget').textContent = overview.settings?.target_words ?? '–';
  const auto = document.getElementById('railAuto');
  const s = overview.settings || {};
  auto.classList.toggle('off', !s.autorun);
  document.getElementById('railAutoText').textContent = s.autorun
    ? `prüft alle ${s.interval_minutes} Min${s.auto_topics ? ' · ergänzt Themen' : ''}`
    : 'pausiert';
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function trim(s, n) { s = String(s ?? ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; }
function hashIdx(s, mod) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h % mod;
}
function fmtWhen(r) {
  if (!r.started_at) return '';
  const d = new Date(r.started_at);
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' }) + ' · ' +
         d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
}
function fmtDur(r) {
  if (!r.started_at) return '—';
  const end = r.finished_at ? new Date(r.finished_at) : new Date();
  const s = Math.max(0, Math.round((end - new Date(r.started_at)) / 1000));
  if (s < 60) return s + 's';
  return Math.floor(s / 60) + 'm';
}
let toastTimer = null;
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('queueBtn').addEventListener('click', queueTopic);
  document.getElementById('topicInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') queueTopic();
  });
  refresh();
});

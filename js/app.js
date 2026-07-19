/* =====================================================================
   Wörterbuch — dictionary lookup (left) + the personal word list (right).

   Everything comes from /api/vocab/*:
     • /search  resolves a query against the enriched card base. Latin input is
       read as German, Cyrillic as Russian; the backend decides and says which.
     • /list    is the user's own words. It needs an account — there is no guest
       mode here, unlike essays.
   Cards arrive with `band` (B1/B2/C1) and `type` (der/die/das/verb/adj) already
   resolved server-side, so the brush mapping lives in exactly one place
   (backend app/vocab/norm.py) and cannot drift from what search returns.

   The detail card opens over the column OPPOSITE its word, so the word stays
   on screen with the orange connector running to it.
   ===================================================================== */
'use strict';

const PAGE = 20;              // the list shows the most recent words, then pages
const DEBOUNCE = 200;

const el = {
  search:  document.getElementById('search'),
  lang:    document.getElementById('searchLang'),
  results: document.getElementById('results'),
  mine:    document.getElementById('myList'),
  pager:   document.getElementById('pager'),
  donut:   document.getElementById('donut'),
  donutTot:document.getElementById('donutTotal'),
  legend:  document.getElementById('legend'),
  layer:   document.getElementById('cardLayer'),
  detail:  document.getElementById('detail'),
};

const BANDS = ['B1', 'B2', 'C1'];
const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const BAND_COLOR = { B1: cssVar('--rose'), B2: cssVar('--blue'), C1: cssVar('--lav') };

let results = [];
let mine = [], mineTotal = 0, minePage = 0;
let stats = { total: 0, bands: { B1: 0, B2: 0, C1: 0 } };
let authed = false;
let openCard = null;          // { card, side: 'left' | 'right' }

/* ---------- helpers ---------- */
const esc = s => String(s ?? '').replace(/[&<>"']/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* card text is model output and may contain **bold** — escape first, then
   promote the markers, so nothing in the data can inject markup */
const md = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');

async function api(path, options) {
  const response = await fetch(path, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.status === 204 ? null : response.json();
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'de-DE'; u.rate = 0.9;
  speechSynthesis.cancel(); speechSynthesis.speak(u);
}

const POS_LABEL = { noun: 'Substantiv', verb: 'Verb', adj: 'Adjektiv', adv: 'Adverb' };
const posLabel = pos => POS_LABEL[pos] || 'Wort';

/* ---------- word rows ---------- */
const ICON = {
  add:    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  have:   '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',
  remove: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
};
const ACT_LABEL = {
  add: 'Zur Lernliste hinzufügen',
  have: 'Schon in der Lernliste',
  remove: 'Aus der Lernliste entfernen',
};

/* A card the source dictionary listed as a form rather than a headword. Backend
   demotes these below real words; here they just say what they are, so `gemacht`
   reads as "Form von machen" instead of posing as a word of its own. The base is
   a button because the next thing you want is that word — the move Yandex makes
   when it answers a form with a link to its dictionary entry. */
const FORM_OF_LABEL = {
  inflection:  'Form von',
  capitalised: 'Form von',
  abbrev:      'Kurzform von',
  variant:     'Nebenform von',
};
// A combining form has no base to point at: `Schnell-` is not a form of
// anything, it is only ever the front half of Schnellzug.
const FORM_PLAIN_LABEL = { compound: 'nur in Zusammensetzungen' };

function formNote(card) {
  if (!card.form_kind) return '';
  const plain = FORM_PLAIN_LABEL[card.form_kind];
  if (plain) return `<span class="form-note">${plain}</span>`;
  // Every other kind names a base; without one there is nothing to say that the
  // word does not already say for itself.
  const prefix = FORM_OF_LABEL[card.form_kind];
  if (!prefix || !card.form_of) return '';
  return `<span class="form-note">${prefix} ` +
    `<button class="form-base" type="button" data-base="${esc(card.form_of)}">` +
    `${esc(card.form_of)}</button></span>`;
}

// Goethe publishes word lists for A1/A2/B1 only, so 95.6% of the base carries
// `level: "unlisted"` and the CEFR chip built from it said "C1" on almost every
// row — a placeholder wearing the clothes of a fact. Where a real Goethe level
// exists we show it; everywhere else we show frequency, which we know for every
// single card, and label it as frequency.
//
// ⚠️ These are two different claims and must stay visually distinct. Frequency
// is NOT a computed CEFR level: measured against the 4 023 genuinely labelled
// cards, zipf cannot tell B1 from B2 at all (medians 4.16 vs 4.15). Styling the
// frequency chip like the level chip would re-tell the same lie in a new font.
const FREQ_LABEL = {
  haeufig: 'häufig',
  mittel:  'mittelhäufig',
  selten:  'selten',
};
const FREQ_TITLE = {
  haeufig: 'So häufig wie der B1-Grundwortschatz',
  mittel:  'Weniger häufig als der Grundwortschatz',
  selten:  'Seltenes Wort — im Aufsatz meist vermeidbar',
};

function levelChip(card) {
  if (card.level && card.level !== 'unlisted') {
    return `<span class="lvl-tag is-cefr" title="Goethe-Wortliste ${esc(card.band)}">` +
      `${esc(card.band)}</span>`;
  }
  if (!card.freq) return '';   // no frequency known — say nothing, guess nothing
  return `<span class="lvl-tag is-freq" title="${esc(FREQ_TITLE[card.freq] || '')}">` +
    `${esc(FREQ_LABEL[card.freq] || '')}</span>`;
}

function wordRow(card, act) {
  const row = document.createElement('div');
  row.className = 'word' + (openCard && openCard.card.lemma === card.lemma ? ' active' : '')
    + (card.form_kind ? ' is-form' : '');
  row.dataset.lemma = card.lemma;
  row.style.setProperty('--brush', brushOfCard(card));
  const art = card.article ? `<span class="art">${esc(card.article)}</span> ` : '';
  row.innerHTML = `
    <span class="wash"></span>
    <div class="w-body">
      <div class="de">${art}${esc(card.lemma)}${formNote(card)}</div>
      <div class="ru">${esc(card.ru)}</div>
    </div>
    <div class="w-right">
      ${levelChip(card)}
      <button class="w-act" type="button" data-act="${act}" title="${ACT_LABEL[act]}"
              aria-label="${ACT_LABEL[act]}"${act === 'have' ? ' disabled' : ''}>${ICON[act]}</button>
    </div>`;
  return row;
}

/* ---------- lookup ---------- */
let searchSeq = 0, searchTimer = null;

async function runSearch(query) {
  const seq = ++searchSeq;
  if (!query.trim()) { results = []; el.lang.hidden = true; renderResults(); return; }
  try {
    const data = await api(`/api/vocab/search?q=${encodeURIComponent(query)}&limit=${PAGE}`);
    if (seq !== searchSeq) return;      // a later keystroke already answered
    results = data.items;
    el.lang.textContent = data.lang === 'ru' ? 'RU → DE' : 'DE → RU';
    el.lang.hidden = false;
    renderResults();
  } catch (err) {
    if (seq !== searchSeq) return;
    results = [];
    el.results.innerHTML = '<div class="empty"><b>Suche nicht erreichbar</b>' +
      'Der Server antwortet gerade nicht.</div>';
  }
}

function renderResults() {
  const query = el.search.value.trim();
  el.results.innerHTML = '';
  if (!query) {
    el.results.innerHTML = '<div class="empty">Ein Wort eingeben — auf Deutsch oder Russisch.</div>';
    return;
  }
  if (!results.length) {
    // The base is still being enriched, so "we don't have it" is the honest
    // answer — better than dressing up unrelated near-matches as a result.
    el.results.innerHTML = `<div class="empty"><b>Kein Eintrag gefunden</b>` +
      `„${esc(query)}“ steht noch nicht im Wörterbuch. Der Bestand wächst laufend.</div>`;
    return;
  }
  results.forEach(group => {
    el.results.appendChild(wordRow(group, group.in_list ? 'have' : 'add'));
    if (group.syn && group.syn.length) el.results.appendChild(synRow(group.syn));
  });
}

/* The "seltener" row: cards that answer the query with the SAME meaning as the
   head above them, so search collapses them here instead of as equal rows (the
   shape Yandex nests under `tr`, Linguee prints as "less common"). Compact
   chips, not full rows — a click opens the card, where the collect button lives,
   which keeps the answer from turning back into the wall we just folded. */
function synRow(syns) {
  const wrap = document.createElement('div');
  wrap.className = 'syn-row';
  const openLemma = openCard && openCard.card.lemma;
  wrap.innerHTML = `<span class="syn-lab">seltener</span>` + syns.map(s => {
    const art = s.article ? `${esc(s.article)} ` : '';
    const on = s.lemma === openLemma ? ' is-open' : '';
    return `<button class="syn-chip${on}" type="button" data-lemma="${esc(s.lemma)}">` +
      `${art}${esc(s.lemma)}</button>`;
  }).join('');
  return wrap;
}

// Head cards plus their nested synonyms, flattened — the click and connector
// both address a synonym by lemma, and it lives one level down from `results`.
function flatResults() {
  return results.flatMap(g => [g, ...(g.syn || [])]);
}

/* ---------- personal list ---------- */
async function loadMine() {
  if (!authed) { mine = []; mineTotal = 0; stats = { total: 0, bands: { B1: 0, B2: 0, C1: 0 } };
    renderMine(); renderDonut(); return; }
  const [list, s] = await Promise.all([
    api(`/api/vocab/list?limit=${PAGE}&offset=${minePage * PAGE}`),
    api('/api/vocab/list/stats'),
  ]);
  mine = list.items; mineTotal = list.total; stats = s;
  // deleting the last word of a page would otherwise strand you on an empty one
  const pages = Math.max(1, Math.ceil(mineTotal / PAGE));
  if (minePage > pages - 1) { minePage = pages - 1; return loadMine(); }
  renderMine(); renderDonut();
}

function renderMine() {
  el.mine.innerHTML = '';
  if (!authed) {
    el.mine.innerHTML = `<div class="empty"><b>Eigene Wortliste</b>` +
      `Melden Sie sich an, um Wörter zu sammeln — sie bleiben auf allen Geräten erhalten.` +
      `<button class="empty-cta" type="button" id="loginCta">Anmelden</button></div>`;
    el.mine.querySelector('#loginCta').onclick = () => window.SiteAuth && window.SiteAuth.open();
    renderPager(0);
    return;
  }
  if (!mine.length) {
    el.mine.innerHTML = '<div class="empty"><b>Noch keine Wörter</b>' +
      'Links nachschlagen und mit „+“ zur Lernliste hinzufügen.</div>';
    renderPager(0);
    return;
  }
  mine.forEach(card => el.mine.appendChild(wordRow(card, 'remove')));
  renderPager(Math.ceil(mineTotal / PAGE));
}

function renderPager(total) {
  el.pager.innerHTML = '';
  if (total <= 1) { el.pager.hidden = true; return; }
  el.pager.hidden = false;
  const mk = (label, page, { active = false, disabled = false, ell = false } = {}) => {
    if (ell) {
      const s = document.createElement('span');
      s.className = 'pg-ell'; s.textContent = '…';
      el.pager.appendChild(s); return;
    }
    const b = document.createElement('button');
    b.className = 'pg-btn' + (active ? ' active' : '');
    b.textContent = label; b.disabled = disabled;
    if (!disabled && !active) b.onclick = () => { minePage = page; loadMine(); };
    el.pager.appendChild(b);
  };
  mk('‹', minePage - 1, { disabled: minePage === 0 });
  for (let i = 0; i < total; i++) {
    if (i === 0 || i === total - 1 || Math.abs(i - minePage) <= 1) mk(String(i + 1), i, { active: i === minePage });
    else if (Math.abs(i - minePage) === 2) mk('', 0, { ell: true });
  }
  mk('›', minePage + 1, { disabled: minePage === total - 1 });
}

async function addWord(lemma) {
  if (!authed) { window.SiteAuth && window.SiteAuth.open(); return; }
  await api('/api/vocab/list', { method: 'POST', body: JSON.stringify({ lemma }) });
  const hit = results.find(c => c.lemma === lemma);
  if (hit) hit.in_list = true;
  minePage = 0;
  renderResults();
  await loadMine();
}

async function removeWord(lemma) {
  await api(`/api/vocab/list/${encodeURIComponent(lemma)}`, { method: 'DELETE' });
  const hit = results.find(c => c.lemma === lemma);
  if (hit) hit.in_list = false;
  if (openCard && openCard.card.lemma === lemma && openCard.side === 'right') closeCard();
  renderResults();
  await loadMine();
}

/* ---------- donut: your words, by level ---------- */
function renderDonut() {
  const segs = BANDS.map(b => ({ band: b, val: stats.bands[b] || 0 }));
  const total = stats.total || 0;
  const r = 46, C = 2 * Math.PI * r, cx = 60, cy = 60;
  let off = 0, paths = '';
  if (!total) {
    paths = `<circle r="${r}" cx="${cx}" cy="${cy}" fill="none" stroke="${cssVar('--hair')}" stroke-width="14"></circle>`;
  } else {
    segs.forEach(s => {
      if (!s.val) return;
      const len = s.val / total * C;
      paths += `<circle class="seg" r="${r}" cx="${cx}" cy="${cy}" fill="none" stroke="${BAND_COLOR[s.band]}"
        stroke-width="14" stroke-dasharray="${len.toFixed(2)} ${(C - len).toFixed(2)}"
        stroke-dashoffset="${(-off).toFixed(2)}"></circle>`;
      off += len;
    });
  }
  el.donut.innerHTML = `<svg viewBox="0 0 120 120"><g transform="rotate(-90 ${cx} ${cy})">${paths}</g></svg>`;
  el.donutTot.textContent = total;
  el.legend.innerHTML = '';
  segs.forEach(s => {
    const row = document.createElement('div');
    row.className = 'lg ' + s.band.toLowerCase() + (s.val ? '' : ' is-empty');
    row.innerHTML = `<span class="dot"></span><span class="nm">${s.band}</span><span class="vl">${s.val}</span>`;
    el.legend.appendChild(row);
  });
}

/* ---------- detail card ---------- */
function gramSpec(card) {
  const g = card.grammar || {};
  const chips = [];
  const add = (label, value) => {
    if (value) chips.push(`<span class="g-s"><i>${label}</i>${esc(value)}</span>`);
  };
  add('Genitiv', g.genitiv);
  add('Plural', g.plural);
  add('Präteritum', g.praeteritum);
  add('Partizip II', g.partizip2);
  add('Hilfsverb', g.hilfsverb);
  add('Komparativ', g.komparativ);
  add('Superlativ', g.superlativ);
  return chips.length ? `<div class="g-spec">${chips.join('')}</div>` : '';
}

/* The full paradigm, when Wiktionary had one (about two thirds of cards).
   The chips above stay: they cover the third with no paradigm, and they are what
   the enrichment model itself produced. This adds what the model never gave —
   the six present-tense persons, so `du gibst` and `er gibt` are visible, and
   all four noun cases, so the n-declension stops being a guess. */
const PERSON_LABEL = { ich: 'ich', du: 'du', er: 'er/sie/es', wir: 'wir', ihr: 'ihr', sie: 'sie' };
const CASE_LABEL = { nom: 'Nominativ', gen: 'Genitiv', dat: 'Dativ', akk: 'Akkusativ' };

function paradigmBlock(card) {
  const m = card.morphology;
  if (!m) return '';
  if (m.praesens || m.imperativ_du) return verbParadigm(m);
  if (m.sg || m.pl) return nounParadigm(m);
  return '';
}

function verbParadigm(m) {
  const rows = Object.keys(PERSON_LABEL)
    .filter(k => (m.praesens || {})[k])
    .map(k => `<div class="p-cell"><i>${PERSON_LABEL[k]}</i>${esc(m.praesens[k])}</div>`)
    .join('');
  const extra = [];
  const push = (label, value) => {
    if (value) extra.push(`<div class="p-cell"><i>${label}</i>${esc(value)}</div>`);
  };
  push('du!', m.imperativ_du);
  push('ihr!', m.imperativ_ihr);
  push('Konj. II', m.konjunktiv2);
  if (!rows && !extra.length) return '';
  return `<div class="p-block">
    ${rows ? `<div class="p-lab">Präsens</div><div class="p-grid">${rows}</div>` : ''}
    ${extra.length ? `<div class="p-lab">Imperativ · Konjunktiv</div>
      <div class="p-grid">${extra.join('')}</div>` : ''}
  </div>`;
}

function nounParadigm(m) {
  const cases = Object.keys(CASE_LABEL).filter(c => (m.sg || {})[c] || (m.pl || {})[c]);
  if (!cases.length) return '';
  const head = `<div class="p-row p-head"><span></span><span>Singular</span><span>Plural</span></div>`;
  const body = cases.map(c => `<div class="p-row"><span>${CASE_LABEL[c]}</span>` +
    `<span>${esc((m.sg || {})[c] || '—')}</span>` +
    `<span>${esc((m.pl || {})[c] || '—')}</span></div>`).join('');
  return `<div class="p-block"><div class="p-table">${head}${body}</div></div>`;
}

function useBlock(card) {
  const rule = card.rektion || '';
  const colls = card.collocations || [];
  if (!rule && !colls.length) return '';
  return `<div class="g-use">
    <div class="g-use-top"><span class="g-use-lab">Verwendung</span>
      ${rule ? `<span class="g-use-rule">${esc(rule)}</span>` : ''}</div>
    ${colls.length ? `<span class="g-use-ex">${colls.map(esc).join(' · ')}</span>` : ''}
  </div>`;
}

function renderCardSheet(card) {
  const art = card.article ? `<span class="art">${esc(card.article)}</span> ` : '';
  const longCls = ((card.article ? card.article.length + 1 : 0) + card.lemma.length) > 16 ? ' long' : '';
  const meanings = (card.ru_all && card.ru_all.length) ? card.ru_all : [card.ru];
  const examples = (card.examples || []).map((e, i) => `
    <div class="ex"><span class="ex-n">${String(i + 1).padStart(2, '0')}</span>
      <div class="ex-body"><p class="ex-de">${md(e.de || '')}</p>
      ${e.ru ? `<p class="ex-ru">${esc(e.ru)}</p>` : ''}</div></div>`).join('');
  const grammar = gramSpec(card) + paradigmBlock(card) + useBlock(card);
  const inList = !!card.in_list;

  el.detail.innerHTML = `
    <button class="d-close" id="dClose" type="button" aria-label="Schließen">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
    <div class="d-head">
      <div class="d-meta">
        <span class="d-cat"><span class="hl">${posLabel(card.pos)}</span>${card.topic_de ? ' · ' + esc(card.topic_de) : ''}</span>
        ${card.level && card.level !== 'unlisted'
          ? `<span class="d-level" title="Goethe-Wortliste">${esc(card.band)}</span>`
          : (card.freq
              ? `<span class="d-level is-freq" title="${esc(FREQ_TITLE[card.freq] || '')}">`
                + `${esc(FREQ_LABEL[card.freq] || '')}</span>`
              : '')}
      </div>
      <div class="d-word${longCls}">${art}${esc(card.lemma)}</div>
      ${formNote(card) ? `<div class="d-form">${formNote(card)}</div>` : ''}
      <div class="d-tools">
        <button class="d-hear" id="hear" type="button">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M5 9v6h4l5 5V4L9 9H5z"/><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>
          Aussprache
        </button>
      </div>
      <div class="d-ru">${meanings.map(esc).join(', ')}</div>
      <button class="d-collect${inList ? ' is-in' : ''}" id="dCollect" type="button">
        ${inList ? 'In der Lernliste' : 'Zur Lernliste'}
      </button>
    </div>
    <div class="d-body">
      ${card.definition_de ? `<section><div class="lab">Bedeutung</div>
        <p class="def">${esc(card.definition_de)}</p></section>` : ''}
      ${grammar ? `<section><div class="lab">Grammatik</div>${grammar}</section>` : ''}
      ${(card.synonyms || []).length ? `<section><div class="lab">Synonyme</div>
        <p class="def">${card.synonyms.map(esc).join(' · ')}</p></section>` : ''}
      ${examples ? `<section><div class="lab">Beispiele</div>
        <div class="ex-list">${examples}</div></section>` : ''}
    </div>`;

  el.detail.querySelector('#hear').onclick =
    () => speak((card.article ? card.article + ' ' : '') + card.lemma);
  el.detail.querySelector('#dClose').onclick = closeCard;
  el.detail.querySelector('#dCollect').onclick = async () => {
    if (card.in_list) await removeWord(card.lemma); else await addWord(card.lemma);
    card.in_list = !card.in_list;
    if (openCard) { renderCardSheet(card); updateLink(); }
  };
}

/* The card covers the column the word did NOT come from: look a word up on the
   left and it opens over the list on the right, and vice versa. That keeps the
   word visible so the connector has something to point at. */
function showCard(card, side) {
  openCard = { card, side };
  el.layer.classList.toggle('on-left', side === 'left');
  el.layer.classList.toggle('on-right', side === 'right');
  el.layer.hidden = false;
  renderCardSheet(card);
  renderResults();
  renderMine();
  // Draw straight away rather than on the next frame: getBoundingClientRect
  // forces the pending layout anyway, and a background tab never runs
  // requestAnimationFrame at all — the sheet would sit there unconnected.
  // The card's entrance animation moves it, so redraw when that settles too
  // (see the `animationend` listener further down).
  updateLink();
}

function closeCard() {
  openCard = null;
  el.layer.hidden = true;
  el.detail.innerHTML = '';
  hideLink();
  renderResults();
  renderMine();
}

/* ---------- events ---------- */
el.search.addEventListener('input', event => {
  clearTimeout(searchTimer);
  const value = event.target.value;
  searchTimer = setTimeout(() => runSearch(value), DEBOUNCE);
});

function rowHandler(source, side, snapshotOnly) {
  return async event => {
    // "Form von machen" — the base is the entry the reader actually wanted, so
    // send the search there instead of opening the form's own card.
    const base = event.target.closest('.form-base');
    if (base) {
      event.stopPropagation();
      el.search.value = base.dataset.base;
      closeCard();
      runSearch(base.dataset.base);
      return;
    }
    const chip = event.target.closest('.syn-chip');
    if (chip) {
      const syn = flatResults().find(c => c.lemma === chip.dataset.lemma);
      if (syn) showCard(syn, side);   // already a full card_out — no fetch needed
      return;
    }
    const row = event.target.closest('.word');
    if (!row) return;
    const lemma = row.dataset.lemma;
    const button = event.target.closest('.w-act');
    if (button) {
      event.stopPropagation();
      if (button.dataset.act === 'add') await addWord(lemma);
      else if (button.dataset.act === 'remove') await removeWord(lemma);
      return;
    }
    let card = source().find(c => c.lemma === lemma);
    if (snapshotOnly) {
      // The personal list carries only what a ROW needs (lemma, ru, band, type) —
      // no definition, grammar or examples. Fetch the real entry before opening
      // the sheet, or it renders an all-but-empty card.
      try {
        card = await api(`/api/vocab/entry/${encodeURIComponent(lemma)}`);
      } catch (err) {
        // word no longer in the dictionary (or the server is down): the snapshot
        // is all we have, and it still beats showing nothing
        if (card) card = { ...card, in_list: true };
      }
    }
    if (card) showCard(card, side);
  };
}
// a word in the LEFT results opens its card over the RIGHT column, and vice versa
el.results.addEventListener('click', rowHandler(() => results, 'right', false));
el.mine.addEventListener('click', rowHandler(() => mine, 'left', true));

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && openCard) closeCard();
});
// click anywhere outside the sheet closes it — the layer itself ignores pointers
document.addEventListener('click', event => {
  if (!openCard) return;
  if (el.detail.contains(event.target)) return;
  if (event.target.closest('.word') || event.target.closest('.syn-chip') ||
      event.target.closest('.pg-btn')) return;
  closeCard();
});

window.addEventListener('site-auth-change', event => {
  authed = !!(event.detail && event.detail.authenticated);
  minePage = 0;
  loadMine();
});

/* ---------------------------------------------------------------------------
   Live connector: a dashed orange stroke from the word in the open card's
   header to the same word's row in the opposite column. Anchored to the row, so
   it stays attached while the page (or the card's own body) scrolls. Hides
   itself whenever either end is gone.
--------------------------------------------------------------------------- */
const lineEl = document.getElementById('linkLine'),
      linkPath = document.getElementById('linkPath'),
      linkDot = document.getElementById('linkDot'),
      linkAnchor = document.getElementById('linkAnchor');

// NB: SVGElement has no `hidden` IDL property, so toggle the content attribute.
function hideLink() { lineEl.setAttribute('hidden', ''); }

function updateLink() {
  if (!openCard) { hideLink(); return; }
  const titleEl = el.detail.querySelector('.d-word');
  const container = openCard.side === 'right' ? el.results : el.mine;
  const key = CSS.escape(openCard.card.lemma);
  const wordEl = container.querySelector(`.word[data-lemma="${key}"] .de`)
    || container.querySelector(`.syn-chip[data-lemma="${key}"]`);
  if (!titleEl || !wordEl) { hideLink(); return; }

  const t = titleEl.getBoundingClientRect(), w = wordEl.getBoundingClientRect();
  // leave from the card edge that faces the word, land just past the word
  const fromLeft = t.left > w.left;
  const sx = fromLeft ? t.left : t.right, sy = t.top + t.height / 2;
  const ex = fromLeft ? w.right + 9 : w.left - 9, ey = w.top + w.height / 2;

  const dir = Math.sign(sx - ex) || 1;
  const k = Math.max(70, Math.abs(sx - ex) * 0.4);
  linkPath.setAttribute('d',
    `M ${sx.toFixed(1)} ${sy.toFixed(1)} C ${(sx - dir * k).toFixed(1)} ${sy.toFixed(1)}, ` +
    `${(ex + dir * k).toFixed(1)} ${ey.toFixed(1)}, ${ex.toFixed(1)} ${ey.toFixed(1)}`);
  linkAnchor.setAttribute('cx', sx.toFixed(1)); linkAnchor.setAttribute('cy', sy.toFixed(1));
  linkDot.setAttribute('cx', ex.toFixed(1)); linkDot.setAttribute('cy', ey.toFixed(1));
  lineEl.removeAttribute('hidden');
}

window.addEventListener('scroll', updateLink, { passive: true });
window.addEventListener('resize', updateLink);
el.detail.addEventListener('scroll', updateLink, { passive: true });
// the sheet slides in on open (@keyframes cardIn), which moves the anchor —
// re-attach the line once it has come to rest
el.detail.addEventListener('animationend', updateLink);

/* ---------- boot ---------- */
renderResults();
renderDonut();
renderMine();
hideLink();
// SiteAuth fires `site-auth-change` once it has resolved /api/auth/me; if it is
// already resolved by now (cache), take the state straight away.
if (window.SiteAuth) {
  const state = window.SiteAuth.getState();
  if (state && state.authenticated) { authed = true; loadMine(); }
}

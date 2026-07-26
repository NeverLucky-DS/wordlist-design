/* =====================================================================
   Wörterbuch — the page.

   One layout: a single reading measure that becomes a two-page spread when a
   word opens (the list slides left, the card takes the right-hand page). Nothing
   is reserved, so nothing sits empty — the complaint the old two-column page was
   built around. The personal list is a drawer on the right edge, because it is a
   place you GO, not a thing you watch.

   There is ONE way to run this page: `make up`, which serves it from nginx
   :8753 against a relative /api/vocab and the real account list. The prototype
   that used to load these same files from a :8799 file server was deleted on
   2026-07-25 — it had become a second door to identical code, and two URLs to
   check was the whole problem. Do not add another.

   The config hooks below survive that deletion and are now INERT in every
   supported setup (nothing sets them). Left in place rather than unpicked from
   eight call sites; see the note on CFG.demo. (`window.WB_WORTE` was a third
   hook until 2026-07-26; it went away with the duplicated brush map, and the
   path to worte/ is now resolved in one place, js/words-data.js.)
     window.WB_API    base for the vocab API       (default '/api/vocab')
     window.WB_DEMO   true → fixed in-memory list instead of the account's
   ===================================================================== */
'use strict';

const CFG = {
  api:  window.WB_API || '/api/vocab',
  demo: !!window.WB_DEMO,
};
const API  = CFG.api;
const CRED = CFG.demo ? 'include' : 'same-origin';   // demo was the cross-origin prototype
const PAGE = 20;                                     // account list page size

/* ---------------------------------------------------------------------
   Data — the LIVE backend. `search` returns a COMPLETE card_out per hit, so a
   row carries everything its card needs and opening one costs no request.
   `entry/{lemma}` is used only to reach a word NOT in the current results — a
   form's base, a synonym chip, or a word opened from the account list, whose
   snapshot has no examples/grammar. --------------------------------------- */
const cards = {};                          // lemma -> full card_out, filled as fetched
const byLemma = l => cards[l];

async function fetchJSON(url, options) {
  const r = await fetch(url, { credentials: CRED,
    headers: { 'Content-Type': 'application/json' }, ...options });
  if (!r.ok) { const e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
  return r.status === 204 ? null : r.json();
}

/* The demo list. DEAD since the prototype was deleted (2026-07-25) — nothing
   sets WB_DEMO any more, so every CFG.demo branch below is unreachable in prod. */
const DEMO_LEMMAS = ['Verantwortung', 'berücksichtigen', 'Herz', 'Nachhaltigkeit', 'online', 'durchaus'];

const state = {
  query:  'Wirkung',
  lemma:  null,                            // the open card
  drawer: false,
  authed: false,
  results: { lang: null, groups: [] },     // last search response
  mine:   { items: [], total: 0, bands: { B1: 0, B2: 0, C1: 0 } },
  minePage: 0,
};

const norm = s => s.toLowerCase().replace(/[ẞß]/g, 'ss');

/* Collapse — the one bit of grouping the layout depends on and the flat API does
   not do: a card whose meanings overlap an earlier hit's is the SAME answer in a
   rarer word, so it rides under that head as a "реже говорят" alternative instead
   of standing as an equal row. */
function groupItems(hits) {
  const groups = [], taken = new Set();
  hits.forEach(mergeCard);
  hits.forEach(c => {
    if (taken.has(c.lemma)) return;
    taken.add(c.lemma);
    const mine = new Set((c.ru_all || [c.ru]).map(norm));
    const syn = hits.filter(o => !taken.has(o.lemma) &&
      (o.ru_all || [o.ru]).some(m => mine.has(norm(m))));
    syn.forEach(o => taken.add(o.lemma));
    groups.push({ head: c, syn });
  });
  return groups;
}

// keep `in_list` when a fresh copy of a card arrives (search re-run after collect)
function mergeCard(c) {
  const prev = cards[c.lemma];
  cards[c.lemma] = prev ? { ...c, in_list: c.in_list ?? prev.in_list } : c;
  return cards[c.lemma];
}

async function loadSearch(q) {
  const query = (q || '').trim();
  if (!query) { state.results = { lang: null, groups: [] }; return; }
  try {
    const d = await fetchJSON(`${API}/search?q=${encodeURIComponent(query)}`);
    state.results = {
      lang: d.lang === 'ru' ? 'RU → DE' : 'DE → RU',
      groups: groupItems(d.items || []),
      formOf: (d.form_of || [])[0] || null,
    };
  } catch (e) { state.results = { lang: null, groups: [], error: true }; }
}

// fetch a full card; merge over any snapshot so grammar/examples are present
async function loadCard(lemma) {
  const have = cards[lemma];
  if (have && have.examples !== undefined && have.definition_de !== undefined) return have;
  try {
    const c = await fetchJSON(`${API}/entry/${encodeURIComponent(lemma)}`);
    return mergeCard(c);
  } catch (e) { return have || null; }
}

const search = () => state.results || { lang: null, groups: [] };

/* ---------------------------------------------------------------------
   The personal list. Real via /api/vocab/list (needs an account); demo in
   memory. Both feed the same drawer. --------------------------------------- */
const bandsOf = items => {
  const b = { B1: 0, B2: 0, C1: 0 };
  items.forEach(c => { if (b[c.band] !== undefined) b[c.band]++; });
  return b;
};
const mineCount = () => (CFG.demo || !state.authed ? state.mine.items.length : state.mine.total);

async function loadMine() {
  if (CFG.demo) {
    const items = DEMO_LEMMAS.map(byLemma).filter(Boolean);
    state.mine = { items, total: items.length, bands: bandsOf(items) };
    return;
  }
  if (!state.authed) { state.mine = { items: [], total: 0, bands: { B1: 0, B2: 0, C1: 0 } }; return; }
  try {
    const [list, s] = await Promise.all([
      fetchJSON(`${API}/list?limit=${PAGE}&offset=${state.minePage * PAGE}`),
      fetchJSON(`${API}/list/stats`),
    ]);
    // deleting the last word of a page would otherwise strand you on an empty one
    const pages = Math.max(1, Math.ceil((list.total || 0) / PAGE));
    if (state.minePage > pages - 1) { state.minePage = pages - 1; return loadMine(); }
    state.mine = { items: list.items, total: s.total ?? list.total, bands: s.bands || { B1: 0, B2: 0, C1: 0 } };
  } catch (e) { state.mine = { items: [], total: 0, bands: { B1: 0, B2: 0, C1: 0 } }; }
}

async function collectWord(lemma, wantIn) {
  const card = byLemma(lemma);
  if (CFG.demo) {
    const i = DEMO_LEMMAS.indexOf(lemma);
    if (wantIn && i < 0) DEMO_LEMMAS.push(lemma);
    if (!wantIn && i >= 0) DEMO_LEMMAS.splice(i, 1);
    if (card) card.in_list = wantIn;
    await loadMine(); draw(); return;
  }
  if (!state.authed) { window.SiteAuth && window.SiteAuth.open(); return; }
  try {
    if (wantIn) await fetchJSON(`${API}/list`, { method: 'POST', body: JSON.stringify({ lemma }) });
    else await fetchJSON(`${API}/list/${encodeURIComponent(lemma)}`, { method: 'DELETE' });
    if (card) card.in_list = wantIn;
    state.minePage = 0;
    await loadMine(); draw();
  } catch (e) { if (e.status === 401) window.SiteAuth && window.SiteAuth.open(); }
}

/* ---------------------------------------------------------------------
   Row — shared by the results list and the drawer.
--------------------------------------------------------------------- */
const FREQ_RU_SHORT = { haeufig: 'частое', mittel: 'средней частоты', selten: 'редкое' };

/* Three claims, three dresses, and they must never be confused for each other.
   A published Goethe level is a citation and gets the boxed tag. Our estimated
   level is a judgement — measured at 38% exact but 91% on "core vocabulary or
   beyond" — so it is written in lower case with a tilde, the way a reading is
   marked as a reading. Frequency stays what it always was: a corpus fact, not a
   level at all. */
function tagHTML(card) {
  if (card.level && card.level !== 'unlisted') {
    return `<span class="wb-tag" title="Уровень по спискам Goethe">${esc(card.band)}</span>`;
  }
  if (card.level_est) {
    return `<span class="wb-tag is-est" title="Наша оценка сложности, не опубликованный список. Точный уровень угадывается в 38 % случаев, граница «основной словарь / выше» — в 91 %.">~${esc(card.level_est.toUpperCase())}</span>`;
  }
  if (!card.freq) return '';   // no frequency known: say nothing, guess nothing
  return `<span class="wb-tag is-freq" title="Частотность по корпусу — это не уровень CEFR">
    ${slot('freq-' + card.freq, 44, 11, 'Häufigkeitsskala')}${esc(FREQ_RU_SHORT[card.freq])}</span>`;
}

const ADD_ICON  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>';
const HAVE_ICON = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';
const DEL_ICON  = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';

// action: 'search' → +/✓ ,  'remove' → ×  ,  'none'
function rowHTML(card, { action = 'search' } = {}) {
  const active = state.lemma === card.lemma;
  const inList = !!card.in_list;
  let btn = '';
  if (action === 'search') {
    btn = `<span class="wb-rw-add${inList ? ' is-in' : ''}" data-add="${esc(card.lemma)}"
        title="${inList ? 'Уже в списке слов' : 'В список слов'}" role="button" tabindex="0">
        ${inList ? HAVE_ICON : ADD_ICON}</span>`;
  } else if (action === 'remove') {
    btn = `<span class="wb-rw-add is-del" data-del="${esc(card.lemma)}"
        title="Убрать из списка" role="button" tabindex="0">${DEL_ICON}</span>`;
  }
  return `<button class="wb-row${active ? ' is-active' : ''}${card.form_kind ? ' is-form' : ''}"
      type="button" data-lemma="${esc(card.lemma)}" style="--brush:${brushFor(card)}">
    <span class="wb-rw-body">
      <span class="wb-rw-de"><span class="wb-w">${card.article
        ? `<span class="art">${esc(card.article)}</span> ` : ''}${esc(card.lemma)}</span></span>
      <span class="wb-rw-ru">${esc((card.ru_all || [card.ru]).join(', '))}</span>
      ${card.form_kind && card.form_of
        ? `<span class="wb-rw-form">форма от ${esc(card.form_of)}</span>` : ''}
    </span>
    <span class="wb-rw-right">${tagHTML(card)}${btn}</span>
  </button>`;
}

/* "реже говорят" — the same meaning answered by rarer words. Redesigned to read
   as a HIERARCHY: the alternatives hang under their head on a connector rail, a
   caption says what binds them (the shared sense), and each alternative carries
   its article (coloured by gender) plus an underline hit-affordance — no box,
   the paint and the underline do the work. */
const GENDER_CLS = { der: 'g-der', die: 'g-die', das: 'g-das' };
const synRowHTML = syn => syn.length
  ? `<div class="wb-syns"><span class="wb-syns-lab">то же значение, реже</span>
      <span class="wb-syns-list">${syn.map(s =>
        `<button type="button" class="wb-syn" data-lemma="${esc(s.lemma)}">${
          s.article ? `<span class="wb-syn-art ${GENDER_CLS[s.article] || ''}">${esc(s.article)}</span>` : ''}<span class="wb-syn-w">${esc(s.lemma)}</span></button>`).join('')}</span></div>`
  : '';

const groupsHTML = groups => groups.length
  ? groups.map(g => rowHTML(g.head) + synRowHTML(g.syn)).join('')
  : `<div class="wb-empty"><b>Ничего не нашлось</b>
     «${esc(state.query)}» пока нет в словаре. База пополняется — сейчас в ней 92 090 карточек.</div>`;

/* The list has three non-result states, and each says something different:
   nothing typed (a prompt), the server failed (an error), and a real miss (the
   word is not in the base yet). Collapsing them into one "не найдено" would tell
   the reader the word is missing when they simply have not typed anything. */
/* «ist» is not a word — it is a cell of `sein`, and until 2026-07-26 typing it
   answered `Ist-Wert` "фактическое значение". The base card now heads the list,
   but the list alone cannot say WHY: `sein` and `ist` are not the same string,
   and a reader who typed one and got the other is owed the reason. This line is
   that reason, and it is the grammar lesson too — «прошедшее время (претерит)»
   is what the learner actually needed. Yandex.Dictionary and Linguee both put
   it here, above the results. */
const formOfHTML = () => {
  const f = search().formOf;
  if (!f) return '';
  return `<div class="wb-formof">
    <b>${esc(f.form)}</b> — форма от <button class="wb-formof-base" type="button"
      data-goto="${esc(f.base)}">${esc(f.base)}</button>
    <span class="wb-formof-cell">${esc(f.cell_ru || f.cell_de || '')}</span>
  </div>`;
};

function listHTML(groups) {
  if (!state.query.trim()) return `<div class="wb-empty"><b>Начните поиск</b>
    Введите слово по-немецки или по-русски — язык определится сам.</div>`;
  if (search().error) return `<div class="wb-empty"><b>Поиск недоступен</b>
    Сервер сейчас не отвечает. Попробуйте ещё раз через минуту.</div>`;
  return formOfHTML() + groupsHTML(groups);
}

const searchHTML = () => `<label class="wb-search">
  <span class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
  <input id="q" type="text" value="${esc(state.query)}" autocomplete="off" spellcheck="false"
    aria-label="Слово искать" placeholder="Wirkung · nachhaltig · влияние">
  ${state.query.trim() && search().lang ? `<span class="wb-lang">${search().lang}</span>` : ''}
</label>`;

/* ---------------------------------------------------------------------
   The page.
--------------------------------------------------------------------- */
function pageA() {
  const { groups } = search();
  const open = state.lemma ? byLemma(state.lemma) : null;
  const n = mineCount();
  return `
  <div class="pa" data-card="${open ? 1 : 0}">
    <div class="pa-wrap">
      <main class="pa-main">
        <div class="wb-eyebrow">Nachschlagen</div>
        <h1 class="wb-h1">Wörterbuch</h1>
        <p class="wb-lede">Немецкий или русский — язык запроса определяется сам.
          Выберите слово, чтобы увидеть значение, грамматику и примеры.</p>
        <div class="pa-search">${searchHTML()}</div>
        <div class="pa-bar">
          <span class="wb-count">${groups.length ? `${groups.length} ${plural(groups.length, 'слово', 'слова', 'слов')}` : 'Введите слово'}</span>
          <span class="wb-count">${state.query.trim() ? (search().lang || '') : ''}</span>
        </div>
        <div class="pa-list" id="list">${listHTML(groups)}</div>
      </main>
      <aside class="pa-side">${open ? wortkarte(open) : ''}</aside>
    </div>
    <button class="pa-tab${state.drawer ? ' is-open' : ''}" type="button" id="drawerBtn">
      Мои слова <b>${n}</b></button>
    <div class="pa-scrim${state.drawer ? ' on' : ''}" id="scrim"></div>
    <aside class="pa-drawer${state.drawer ? ' on' : ''}" aria-hidden="${state.drawer ? 'false' : 'true'}">
      <div class="pa-drawer-head">
        <h2>Мои слова</h2>
        <button class="wb-close" type="button" id="drawerClose" style="position:static" aria-label="Закрыть">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
      </div>
      ${drawerBody()}
    </aside>
  </div>`;
}

function drawerBody() {
  const n = mineCount();
  if (!CFG.demo && !state.authed) {
    return `<div class="pa-drawer-body"><div class="wb-empty"><b>Личный словарь</b>
      Войдите, чтобы собирать слова — они сохранятся на всех устройствах.
      <button class="wb-empty-cta" type="button" id="drawerLogin">Войти</button></div></div>`;
  }
  if (!n) {
    return `<div class="pa-drawer-body"><div class="wb-empty"><b>Пока пусто</b>
      Найдите слово слева и добавьте его кнопкой «+».</div></div>`;
  }
  const pages = Math.ceil((state.mine.total || n) / PAGE);
  return `<div class="pa-drawer-stat">${donutHTML(state.mine.bands, state.mine.total || n)}</div>
    <div class="pa-drawer-body" id="mine">${state.mine.items.map(c => rowHTML(c, { action: 'remove' })).join('')}</div>
    ${pagerHTML(pages)}`;
}

function donutHTML(bands, total) {
  const C = 2 * Math.PI * 30, colors = { B1: '#C2868D', B2: '#9DB2C9', C1: '#A99BC0' };
  let off = 0, paths = '';
  if (!total) paths = `<circle r="30" cx="37" cy="37" fill="none" stroke="#ECEAE4" stroke-width="10"/>`;
  else Object.keys(bands).forEach(b => {
    if (!bands[b]) return;
    const len = bands[b] / total * C;
    paths += `<circle r="30" cx="37" cy="37" fill="none" stroke="${colors[b]}" stroke-width="10"
      stroke-dasharray="${len.toFixed(2)} ${(C - len).toFixed(2)}" stroke-dashoffset="${(-off).toFixed(2)}"/>`;
    off += len;
  });
  return `<div class="pb-donut">
    <div class="pb-donut-wrap"><svg viewBox="0 0 74 74"><g transform="rotate(-90 37 37)">${paths}</g></svg>
      <div class="pb-donut-c"><b>${total}</b><span>слов</span></div></div>
    <div class="pb-legend">${Object.keys(bands).map(b =>
      `<div class="pb-lg ${b.toLowerCase()}"><span class="dot"></span><span class="nm">${b}</span><span class="vl">${bands[b]}</span></div>`).join('')}</div>
  </div>`;
}

// windowed pager, drawer only (real account list can run to many pages)
function pagerHTML(total) {
  if (total <= 1) return '';
  const p = state.minePage;
  const btn = (lab, page, { active = false, disabled = false } = {}) =>
    `<button class="wb-pg${active ? ' is-active' : ''}" type="button"
      ${disabled ? 'disabled' : `data-page="${page}"`}>${lab}</button>`;
  let out = btn('‹', p - 1, { disabled: p === 0 });
  for (let i = 0; i < total; i++) {
    if (i === 0 || i === total - 1 || Math.abs(i - p) <= 1) out += btn(String(i + 1), i, { active: i === p });
    else if (Math.abs(i - p) === 2) out += `<span class="wb-pg-ell">…</span>`;
  }
  out += btn('›', p + 1, { disabled: p === total - 1 });
  return `<div class="pa-drawer-pager">${out}</div>`;
}

/* ---------------------------------------------------------------------
   Harness
--------------------------------------------------------------------- */
const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
};

const appEl = () => document.getElementById('app');
const reduceMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

function applyDraw({ keepFocus = false } = {}) {
  const sel = document.activeElement && document.activeElement.id === 'q'
    ? document.activeElement.selectionStart : null;
  WB.art = false;                          // no art assets in production
  appEl().innerHTML = pageA();
  wire();
  updateLink();
  if (keepFocus) {
    const q = document.getElementById('q');
    if (q) { q.focus(); if (sel !== null) q.setSelectionRange(sel, sel); }
  }
}

const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

/* Opening a word is the one redraw meant to be WATCHED: the list slides aside and
   the card arrives from the right, then the orange thread draws itself to the
   word. Every other redraw stays instant, so the animation is opt-in.

   The page is rebuilt from innerHTML, and an innerHTML swap carries no transition
   of its own. The View Transitions API bridges that: it snapshots the page, runs
   the swap, then tweens old→new. `.pa-main` / `.pa-side` carry view-transition
   names (woerterbuch.css), so the column shift and the card entrance are animated
   specifically. The connector is occluded by the transition layer while that
   plays, so it is revealed the instant the transition settles. */
function draw(opts = {}) {
  const animate = opts.animate && document.startViewTransition && !reduceMotion();
  if (!animate) { applyDraw(opts); if (opts.reveal) updateLink(true); return; }
  hideLink();
  const done = () => updateLink(opts.reveal);
  const vt = document.startViewTransition(() => applyDraw(opts));
  vt.finished.then(done).catch(done);
}

/* ---------------------------------------------------------------------
   Word actions — the network is here, never in the render.
--------------------------------------------------------------------- */
function onInput(v) { state.query = v; state.lemma = null; runSearchDebounced(); }
const runSearchDebounced = debounce(async () => {
  await loadSearch(state.query);
  applyDraw({ keepFocus: true });
}, 180);

async function openLemma(lemma) {
  if (state.lemma === lemma) { state.lemma = null; draw({ animate: true }); return; }
  await loadCard(lemma);
  if (!cards[lemma]) return;               // fetch failed — leave the page as it is
  const wasClosed = !state.drawer;
  state.lemma = lemma;
  state.drawer = false;                    // a card opening over the drawer would be hidden
  draw({ animate: wasClosed, reveal: true });
}

// a form's base or a synonym: navigate the search TO that word and open it
async function gotoLemma(base) {
  state.query = base; state.lemma = null;
  await Promise.all([loadSearch(base), loadCard(base)]);
  state.lemma = cards[base] ? base : null;
  draw({ animate: true, reveal: true });
}

function wire() {
  const root = appEl();
  const q = root.querySelector('#q');
  if (q) q.oninput = e => onInput(e.target.value);

  const open = state.lemma ? byLemma(state.lemma) : null;
  if (open) wireCard(root, open, {
    close: () => { state.lemma = null; draw({ animate: true }); },
    goto:  base => gotoLemma(base),
    collect: card => collectWord(card.lemma, !card.in_list),
    resize: () => updateLink(),
  });
}

/* One delegated handler for every way a word can be opened — bound ONCE in boot.
   `#app` survives every redraw (only its innerHTML changes), so re-adding the
   listener on each draw would accumulate them. */
function delegate() {
  const root = appEl();
  root.addEventListener('click', e => {
    const add = e.target.closest('[data-add]');
    if (add) { e.stopPropagation(); collectWord(add.dataset.add, !(byLemma(add.dataset.add) || {}).in_list); return; }
    const del = e.target.closest('[data-del]');
    if (del) { e.stopPropagation(); collectWord(del.dataset.del, false); return; }
    const pg = e.target.closest('[data-page]');
    if (pg) { state.minePage = +pg.dataset.page; loadMine().then(() => draw()); return; }
    // The "форма от sein" link sits ABOVE the result list, outside the card, so
    // it cannot ride `wireCard`'s [data-base] handler.
    const go = e.target.closest('[data-goto]');
    if (go) { e.stopPropagation(); gotoLemma(go.dataset.goto); return; }
    const hit = e.target.closest('[data-lemma]');
    if (hit && !e.target.closest('.wb-card')) { openLemma(hit.dataset.lemma); return; }
    if (e.target.closest('#drawerLogin')) { window.SiteAuth && window.SiteAuth.open(); return; }
    if (e.target.closest('#drawerBtn')) { state.drawer = !state.drawer; draw(); return; }
    if (e.target.closest('#drawerClose') || e.target.closest('#scrim')) { state.drawer = false; draw(); }
  });
}

/* ---------------------------------------------------------------------
   The connector — a dashed orange stroke from the OPEN card's headword to the
   same word's row in the list. Slightly transparent, and on open it draws itself
   in (stroke-dashoffset) rather than popping, so the two ends read as one word.
--------------------------------------------------------------------- */
const wbLink = () => document.getElementById('wbLink');
const wbPath = () => document.getElementById('wbLinkPath');

function hideLink() {
  const svg = wbLink(); if (!svg) return;
  svg.classList.remove('is-shown');
  svg.setAttribute('hidden', '');
}

function updateLink(reveal) {
  const svg = wbLink(); if (!svg) return;
  const card = document.querySelector('.pa .wb-card');
  const title = card && card.querySelector('.wb-lemma');
  const row = document.querySelector('.pa-list .wb-row.is-active .wb-w');
  if (!state.lemma || !title || !row) { hideLink(); return; }

  const t = title.getBoundingClientRect(), w = row.getBoundingClientRect();
  const fromLeft = t.left > w.left;                    // card sits right of the word
  const sx = fromLeft ? t.left : t.right, sy = t.top + t.height / 2;
  const ex = fromLeft ? w.right + 8 : w.left - 8, ey = w.top + w.height / 2;
  const dir = Math.sign(sx - ex) || 1, k = Math.max(60, Math.abs(sx - ex) * 0.4);
  wbPath().setAttribute('d',
    `M ${sx.toFixed(1)} ${sy.toFixed(1)} C ${(sx - dir * k).toFixed(1)} ${sy.toFixed(1)}, ` +
    `${(ex + dir * k).toFixed(1)} ${ey.toFixed(1)}, ${ex.toFixed(1)} ${ey.toFixed(1)}`);
  const a = document.getElementById('wbLinkAnchor'); a.setAttribute('cx', sx.toFixed(1)); a.setAttribute('cy', sy.toFixed(1));
  const d = document.getElementById('wbLinkDot');    d.setAttribute('cx', ex.toFixed(1)); d.setAttribute('cy', ey.toFixed(1));
  svg.removeAttribute('hidden');
  svg.classList.add('is-shown');
  if (reveal && !reduceMotion()) playReveal();
}

function playReveal() {
  const path = wbPath(), dot = document.getElementById('wbLinkDot');
  const len = path.getTotalLength();
  path.style.strokeDasharray = `${len} ${len}`;
  path.style.strokeDashoffset = `${len}`;
  path.style.animation = 'none';                       // suspend marching ants
  if (dot) dot.style.opacity = '0';
  const anim = path.animate(
    [{ strokeDashoffset: len }, { strokeDashoffset: 0 }],
    { duration: 560, easing: 'cubic-bezier(.22,.61,.24,1)' });
  anim.onfinish = anim.oncancel = () => {
    path.style.strokeDasharray = '';
    path.style.strokeDashoffset = '';
    path.style.animation = '';                         // resume marching ants
    if (dot) dot.style.opacity = '';
  };
}

/* ---------------------------------------------------------------------
   Boot
--------------------------------------------------------------------- */
async function boot() {
  delegate();
  addEventListener('resize', () => updateLink());
  addEventListener('scroll', () => updateLink(), { passive: true, capture: true });
  addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (state.drawer) { state.drawer = false; draw(); }
    else if (state.lemma) { state.lemma = null; draw({ animate: true }); }
  });

  if (!CFG.demo) {
    addEventListener('site-auth-change', e => {
      state.authed = !!(e.detail && e.detail.authenticated);
      state.minePage = 0;
      loadMine().then(() => draw());
    });
    const s = window.SiteAuth && window.SiteAuth.getState();
    state.authed = !!(s && s.authenticated);
  }

  applyDraw();                             // first paint, before data lands
  const jobs = [loadSearch(state.query)];
  if (CFG.demo) jobs.push(...DEMO_LEMMAS.map(loadCard));
  await Promise.all(jobs);
  if (CFG.demo) DEMO_LEMMAS.forEach(l => { if (cards[l]) cards[l].in_list = true; });
  await loadMine();
  applyDraw();
}

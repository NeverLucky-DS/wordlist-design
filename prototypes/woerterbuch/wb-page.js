/* =====================================================================
   Three Wörterbuch pages, one card.

   The card component is identical in all three — same file, same width, same
   handlers — so a difference between the variants is a decision about the PAGE
   and never a difference in what the card happens to do there. That is the
   whole point of comparing them side by side.

   What each variant is answering, in one line each:

     A «Разворот»   stop reserving the space that is empty
     B «Верстак»    keep the space, give it a permanent job
     C «Картотека»  make the whole width one grid whose cell IS the card

   The four complaints being designed against, with what was measured:

   1. EMPTY SPACE. At 1440px the grid is minmax(400px,1.05fr) + minmax(340px,
      440px) with 56px gap inside 100px padding, so the lookup column is 744px
      and holds ~360px of content, and the 440px card column is empty until
      something is clicked. Roughly a third of the page is a slot waiting.

   2. THE HIERARCHY IS UNREADABLE. The "seltener" row — rarer words answering
      the same meaning — is a 17px serif chip in --ink-soft with no ground and
      no hit area, under a 10px --muted-2 label at 1.75:1.

   3. THE BRUSHES ARE SMEARS. `.word .wash` is width:108%, height:165% OF THE
      ROW, so a compact watercolour mark is stretched to ~800×105px in a 744px
      column. Fixed footprint in wb.css; new art briefed in ART-PROMPTS.md.

   4. THE TRANSLATION IS UNREADABLE. 18px italic serif, --ink-soft, forced to
      one line with ellipsis, sitting over the densest part of the paint.
   ===================================================================== */
'use strict';

/* ---------------------------------------------------------------------
   Data. The twelve cards are real, pulled from the live enrichment.db by the
   same card_out() the search endpoint uses (../cards-data.js) — the design has
   to be judged on what the base actually holds.

   IPA is joined on here rather than invented: the de.wiktionary dump carries a
   transcription for 59 038 of 59 335 of our cards (99.5%), and importing it is
   item B of info/PLANS.md — a join, not a model call. These twelve are the
   real transcriptions for these twelve words.
--------------------------------------------------------------------- */
const IPA = {
  'Wirkung': 'ˈvɪʁkʊŋ', 'Student': 'ʃtuˈdɛnt', 'entwickeln': 'ɛntˈvɪkl̩n',
  'nachhaltig': 'ˈnaːxhaltɪç', 'durchaus': 'dʊʁçˈaʊ̯s', 'Nachhaltigkeit': 'ˈnaːxhaltɪçkaɪ̯t',
  'Verantwortung': 'fɛɐ̯ˈʔantvɔʁtʊŋ', 'berücksichtigen': 'bəˈʁʏkzɪçtɪɡn̩', 'Herz': 'hɛʁt͡s',
  'gemacht': 'ɡəˈmaxt', 'Auswirkung': 'ˈaʊ̯sˌvɪʁkʊŋ', 'online': 'ˈɔnlaɪ̯n',
};
Object.keys(PROTO_CARDS).forEach(k => { PROTO_CARDS[k].ipa = IPA[k] || ''; });

const ALL = Object.values(PROTO_CARDS);
const byLemma = l => PROTO_CARDS[l];

/* the personal list — six of the twelve, so both lists have real content and
   the "already collected" state is visible in the results at the same time */
const MINE = ['Verantwortung', 'berücksichtigen', 'Herz', 'Nachhaltigkeit', 'online', 'durchaus'];
MINE.forEach(l => { PROTO_CARDS[l].in_list = true; });

const state = {
  variant: 'A',
  query: 'Wirkung',
  lemma: null,          // the open card
  drawer: false,        // A only
  tab: 'search',        // C only
  art: true,
};

/* ---------------------------------------------------------------------
   Search, run locally over the twelve so the page can be driven without a
   backend. It reproduces the two things the real endpoint does that the
   LAYOUT has to survive:
     · the query's script picks the side of the dictionary (Latin → German
       lemma, Cyrillic → the Russian translations)
     · cards that answer with the SAME meaning are collapsed under one head
       instead of standing as equal rows — the "seltener" group
--------------------------------------------------------------------- */
const isCyr = s => /[Ѐ-ӿ]/.test(s);
const norm = s => s.toLowerCase().replace(/[ẞß]/g, 'ss');

function search(q) {
  const query = q.trim();
  if (!query) return { lang: null, groups: [] };
  const ru = isCyr(query), n = norm(query);
  let hits = ALL.filter(c => ru
    ? (c.ru_all || [c.ru]).some(m => norm(m).includes(n))
    : norm(c.lemma).includes(n));

  /* Ranking, in the order the real `_by_relevance` applies it:
       exact match → starts with the query → contains it,
       then forms last, then alphabetical.
     The first rule is not cosmetic. Sorted alphabetically, the query
     "Wirkung" answers with `Auswirkung` and files `Wirkung` under it as a
     rarer synonym — the exact word the reader typed, demoted to a chip. */
  const score = c => {
    const t = ru ? (c.ru_all || [c.ru]).map(norm) : [norm(c.lemma)];
    if (t.some(x => x === n)) return 0;
    if (t.some(x => x.startsWith(n))) return 1;
    return 2;
  };
  // `form_kind` cards are entries the source dictionary listed as a form rather
  // than a headword (1 676 of them). They stay findable but never lead:
  // `gemacht` must not outrank a real word.
  const rank = c => (c.form_kind ? 1 : 0);
  hits.sort((a, b) => score(a) - score(b) || rank(a) - rank(b) ||
    a.lemma.length - b.lemma.length || a.lemma.localeCompare(b.lemma));

  // collapse: a card whose meanings overlap an earlier hit's is the same
  // answer in a rarer word, so it rides under it as a chip
  const groups = [], taken = new Set();
  hits.forEach(c => {
    if (taken.has(c.lemma)) return;
    taken.add(c.lemma);
    const mine = new Set((c.ru_all || [c.ru]).map(norm));
    const syn = hits.filter(o => !taken.has(o.lemma) &&
      (o.ru_all || [o.ru]).some(m => mine.has(norm(m))));
    syn.forEach(o => taken.add(o.lemma));
    groups.push({ head: c, syn });
  });
  return { lang: ru ? 'RU → DE' : 'DE → RU', groups };
}

/* ---------------------------------------------------------------------
   Row and tile — shared markup, so a row is the same object in all three.
--------------------------------------------------------------------- */
const FREQ_RU_SHORT = { haeufig: 'частое', mittel: 'средней частоты', selten: 'редкое' };

function tagHTML(card) {
  if (card.level && card.level !== 'unlisted') {
    return `<span class="wb-tag" title="Уровень по спискам Goethe">${esc(card.band)}</span>`;
  }
  if (!card.freq) return '';   // no frequency known: say nothing, guess nothing
  return `<span class="wb-tag is-freq" title="Частотность по корпусу — это не уровень CEFR">
    ${slot('freq-' + card.freq, 44, 11, 'Häufigkeitsskala')}${esc(FREQ_RU_SHORT[card.freq])}</span>`;
}

function rowHTML(card, { showAdd = true } = {}) {
  const active = state.lemma === card.lemma;
  const inList = !!card.in_list;
  return `<button class="wb-row${active ? ' is-active' : ''}${card.form_kind ? ' is-form' : ''}"
      type="button" data-lemma="${esc(card.lemma)}" style="--brush:${brushFor(card)}">
    <span class="wb-rw-body">
      <span class="wb-rw-de"><span class="wb-w">${card.article
        ? `<span class="art">${esc(card.article)}</span> ` : ''}${esc(card.lemma)}</span></span>
      <span class="wb-rw-ru">${esc((card.ru_all || [card.ru]).join(', '))}</span>
      ${card.form_kind && card.form_of
        ? `<span class="wb-rw-form">форма от ${esc(card.form_of)}</span>` : ''}
    </span>
    <span class="wb-rw-right">
      ${tagHTML(card)}
      ${showAdd ? `<span class="wb-rw-add${inList ? ' is-in' : ''}" data-add="${esc(card.lemma)}"
        title="${inList ? 'Уже в списке слов' : 'В список слов'}" role="button" tabindex="0">
        ${inList
          ? '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>'
          : '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>'}
      </span>` : ''}
    </span>
  </button>`;
}

const synRowHTML = syn => syn.length
  ? `<div class="wb-syns"><span class="wb-syns-lab">реже говорят</span>${syn.map(s =>
      `<button type="button" data-lemma="${esc(s.lemma)}">${s.article ? esc(s.article) + ' ' : ''}${esc(s.lemma)}</button>`).join('')}</div>`
  : '';

const groupsHTML = groups => groups.length
  ? groups.map(g => rowHTML(g.head) + synRowHTML(g.syn)).join('')
  : `<div class="wb-empty"><b>Ничего не нашлось</b>
     «${esc(state.query)}» пока нет в словаре. База пополняется — сейчас в ней 92 090 карточек.</div>`;

const searchHTML = (cls = '') => `<label class="wb-search ${cls}">
  <span class="ico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
  <input id="q" type="text" value="${esc(state.query)}" autocomplete="off" spellcheck="false"
    aria-label="Слово искать" placeholder="Wirkung · nachhaltig · влияние">
  ${state.query.trim() ? `<span class="wb-lang">${search(state.query).lang}</span>` : ''}
</label>`;

const topHTML = () => `<header class="wb-top">
  <span class="wb-brand">Deutsch <i>Essay</i></span>
  <nav class="wb-nav"><a href="#">Essay</a><a href="#">Pipeline</a><a href="#" class="on">Wörterbuch</a></nav>
  <span class="wb-av">D</span></header>`;

/* ---------------------------------------------------------------------
   A «Разворот»
--------------------------------------------------------------------- */
function pageA() {
  const { groups } = search(state.query);
  const open = state.lemma ? byLemma(state.lemma) : null;
  const mine = MINE.map(byLemma);
  return `${topHTML()}
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
          <span class="wb-count">${state.query.trim() ? search(state.query).lang : ''}</span>
        </div>
        <div class="pa-list" id="list">${groupsHTML(groups)}</div>
      </main>
      <aside class="pa-side">${open ? wortkarte(open) : ''}</aside>
    </div>
    <button class="pa-tab" type="button" id="drawerBtn">Мои слова <b>${mine.length}</b></button>
    <div class="pa-scrim${state.drawer ? ' on' : ''}" id="scrim"></div>
    <div class="pa-drawer${state.drawer ? ' on' : ''}">
      <div class="pa-drawer-head">
        <h2>Мои слова</h2>
        <button class="wb-close" type="button" id="drawerClose" style="position:static" aria-label="Закрыть">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
      </div>
      <div class="pa-drawer-body" id="mine">${mine.map(c => rowHTML(c, { showAdd: false })).join('')}</div>
    </div>
  </div>`;
}

/* ---------------------------------------------------------------------
   B «Верстак»
   The card column is never empty: with nothing selected it shows the word of
   the day, which is a real card. A reader who has typed nothing still sees
   what the object is and what collecting a word gets them.
--------------------------------------------------------------------- */
const WORD_OF_DAY = 'Nachhaltigkeit';

function pageB() {
  const { groups } = search(state.query);
  const open = state.lemma ? byLemma(state.lemma) : byLemma(WORD_OF_DAY);
  const mine = MINE.map(byLemma);
  const bands = { B1: 0, B2: 0, C1: 0 };
  mine.forEach(c => bands[c.band]++);
  /* The main column comes FIRST in the DOM and is placed into the middle track
     by CSS. Written in visual order the rail led, and a keyboard user had to
     pass nine controls — three nav links, then the whole "мои слова" rail —
     before reaching the search field, measured. Reading order and tab order
     belong to the reader; only the visual order belongs to the grid. */
  return `${topHTML()}
  <div class="pb"><div class="pb-wrap">
    <main class="pb-main">
      <div class="pb-head">
        <div class="wb-eyebrow">Nachschlagen</div>
        <h1 class="wb-h1">Wörterbuch</h1>
      </div>
      ${searchHTML()}
      <div class="pb-bar">
        <span class="wb-count">${groups.length ? `${groups.length} ${plural(groups.length, 'слово', 'слова', 'слов')}` : 'Введите слово'}</span>
        <span class="wb-count">${state.query.trim() ? search(state.query).lang : ''}</span>
      </div>
      <div class="pb-list" id="list">${groupsHTML(groups)}</div>
    </main>

    <aside class="pb-rail">
      <div class="pb-panel">
        <h3>Мой словарь</h3>
        ${donutHTML(bands, mine.length)}
      </div>
      <div class="pb-panel">
        <h3>Последние</h3>
        <div class="pb-mine" id="mine">${mine.slice(0, 6).map(c =>
          `<button class="pb-mini${state.lemma === c.lemma ? ' is-active' : ''}" type="button" data-lemma="${esc(c.lemma)}">
            <b>${esc(c.lemma)}</b><span>${esc(c.ru)}</span></button>`).join('')}</div>
      </div>
    </aside>

    <aside class="pb-card">
      ${state.lemma ? '' : '<div class="wb-eyebrow" style="margin:6px 0 10px">Wort des Tages</div>'}
      ${/* nothing to close back to: the column's resting state IS this card, so
            a ✕ here would be a control that does nothing */
        wortkarte(open, { noClose: !state.lemma })}
      ${state.lemma ? '' : '<p class="pb-hint">Карточка всегда стоит здесь. Пока ничего не выбрано — слово дня.</p>'}
    </aside>
  </div></div>`;
}

function donutHTML(bands, total) {
  const C = 2 * Math.PI * 34, colors = { B1: '#C2868D', B2: '#9DB2C9', C1: '#A99BC0' };
  let off = 0, paths = '';
  if (!total) paths = `<circle r="34" cx="41" cy="41" fill="none" stroke="#ECEAE4" stroke-width="11"/>`;
  else Object.keys(bands).forEach(b => {
    if (!bands[b]) return;
    const len = bands[b] / total * C;
    paths += `<circle r="34" cx="41" cy="41" fill="none" stroke="${colors[b]}" stroke-width="11"
      stroke-dasharray="${len.toFixed(2)} ${(C - len).toFixed(2)}" stroke-dashoffset="${(-off).toFixed(2)}"/>`;
    off += len;
  });
  return `<div class="pb-donut">
    <div class="pb-donut-wrap"><svg viewBox="0 0 82 82"><g transform="rotate(-90 41 41)">${paths}</g></svg>
      <div class="pb-donut-c"><b>${total}</b><span>слов</span></div></div>
    <div class="pb-legend">${Object.keys(bands).map(b =>
      `<div class="pb-lg ${b.toLowerCase()}"><span class="dot"></span><span class="nm">${b}</span><span class="vl">${bands[b]}</span></div>`).join('')}</div>
  </div>`;
}

/* ---------------------------------------------------------------------
   C «Картотека»
   Every cell is 440px, and the card is a cell. Because tile and card share a
   width, the card cannot render at two sizes — the invariant the other two
   variants keep by rule, this one gets from its geometry.
--------------------------------------------------------------------- */
function pageC() {
  const { groups } = search(state.query);
  const mine = MINE.map(byLemma);
  const showing = state.tab === 'search' ? groups.map(g => g.head) : mine;
  const cells = showing.map(c => state.lemma === c.lemma
    ? `<div class="pc-cell">${wortkarte(c)}</div>`
    : `<div class="pc-cell"><div class="pc-tile">${rowHTML(c)}${firstExample(c)}</div></div>`).join('');
  return `${topHTML()}
  <div class="pc"><div class="pc-wrap">
    <div class="pc-hero">
      <div><div class="wb-eyebrow">Nachschlagen</div><h1 class="wb-h1">Wörterbuch</h1></div>
      <div class="pc-search">${searchHTML()}</div>
    </div>
    <div class="pc-tabs">
      <button class="pc-tab${state.tab === 'search' ? ' on' : ''}" type="button" data-ptab="search">
        Поиск ${groups.length ? `<span class="n">${groups.length}</span>` : ''}</button>
      <button class="pc-tab${state.tab === 'mine' ? ' on' : ''}" type="button" data-ptab="mine">
        Мои слова <span class="n">${mine.length}</span></button>
    </div>
    <div class="pc-grid" id="list">${cells || `<div class="wb-empty"><b>Ничего не нашлось</b>
      «${esc(state.query)}» пока нет в словаре.</div>`}</div>
  </div></div>`;
}

// one line of the first example: enough for a tile to answer "is this the word
// I meant?" without opening anything, which is what the extra width buys
const firstExample = c => {
  const e = (c.examples || [])[0];
  return e ? `<div class="pc-x">${md(e.de)}</div>` : '';
};

/* ---------------------------------------------------------------------
   Harness
--------------------------------------------------------------------- */
const VARIANTS = {
  A: { fn: pageA, name: 'Разворот', sub: 'Не резервировать пустое' },
  B: { fn: pageB, name: 'Верстак',  sub: 'Колонка с постоянной работой' },
  C: { fn: pageC, name: 'Картотека', sub: 'Сетка из ячеек по 440' },
};

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
};

const app = () => document.getElementById('app');

function draw({ keepFocus = false } = {}) {
  const sel = document.activeElement && document.activeElement.id === 'q'
    ? document.activeElement.selectionStart : null;
  WB.art = state.art;
  app().className = 'v-' + state.variant;
  app().innerHTML = VARIANTS[state.variant].fn();
  wire();
  measure();
  if (keepFocus) {
    const q = document.getElementById('q');
    if (q) { q.focus(); if (sel !== null) q.setSelectionRange(sel, sel); }
  }
}

function wire() {
  const root = app();

  const q = root.querySelector('#q');
  if (q) q.oninput = e => { state.query = e.target.value; state.lemma = null; draw({ keepFocus: true }); };

  const open = state.lemma ? byLemma(state.lemma)
    : (state.variant === 'B' ? byLemma(WORD_OF_DAY) : null);
  if (open) wireCard(root, open, {
    close: () => { state.lemma = null; draw(); },
    goto:  base => { state.query = base; state.lemma = null; draw(); },
    collect: card => {
      card.in_list = !card.in_list;
      if (card.in_list) MINE.push(card.lemma);
      else MINE.splice(MINE.indexOf(card.lemma), 1);
      draw();
    },
    resize: measure,
  });
}

/* One delegated handler for every way a word can be opened — a row, a
   "реже говорят" chip, a rail entry. They must not drift apart.

   Bound ONCE, in boot, and never from `wire()`. `#app` survives every redraw
   (only its innerHTML is replaced), so re-adding the listener on each draw
   accumulated them: after N draws one click ran N handlers, each of which drew
   again and added another. Two or three interactions and the page hangs.
   Every other handler here is an `.onXXX` assignment, which overwrites — this
   was the one addEventListener in the redraw path. */
function delegate() {
  const root = app();
  root.addEventListener('click', e => {
    const add = e.target.closest('[data-add]');
    if (add) {
      e.stopPropagation();
      const c = byLemma(add.dataset.add);
      if (c && !c.in_list) { c.in_list = true; MINE.push(c.lemma); draw(); }
      return;
    }
    const hit = e.target.closest('[data-lemma]');
    if (hit && !e.target.closest('.wb-card')) {
      state.lemma = state.lemma === hit.dataset.lemma ? null : hit.dataset.lemma;
      draw();
      return;
    }
    const ptab = e.target.closest('[data-ptab]');
    if (ptab) { state.tab = ptab.dataset.ptab; state.lemma = null; draw(); return; }
    if (e.target.closest('#drawerBtn')) { state.drawer = true; draw(); return; }
    if (e.target.closest('#drawerClose') || e.target.closest('#scrim')) { state.drawer = false; draw(); }
  });
}

/* The size readout. Complaint 2 of the original brief — the card is not the
   same object depending on where it opens — is a LAYOUT fact, not a rendering
   one, so the only way to see the fix hold is to print the number live in
   every variant and every state. */
function measure() {
  const card = document.querySelector('.wb-card');
  const list = document.querySelector('#list');
  const out = document.getElementById('hmeasure');
  const vw = innerWidth, vh = innerHeight;
  const c = card ? card.getBoundingClientRect() : null;
  const l = list ? list.getBoundingClientRect() : null;
  out.textContent =
    `экран  ${vw}×${vh}\n` +
    `карточка ${c ? Math.round(c.width) + '×' + Math.round(c.height) : '—'}` +
    (c ? (c.height > vh - 48 ? '  ⚠ выше экрана' : '  ok') : '') + '\n' +
    `колонка списка ${l ? Math.round(l.width) : '—'}`;
}

function boot() {
  const bar = document.getElementById('hbar');
  bar.innerHTML = Object.entries(VARIANTS).map(([k, v]) =>
    `<button class="hb${k === state.variant ? ' on' : ''}" data-v="${k}">
      <b>Вариант ${k}</b><span>${v.name}</span><i>${v.sub}</i></button>`).join('') +
    `<div class="hb-tools">
      <label><input type="checkbox" id="artChk" ${state.art ? 'checked' : ''}> слоты под графику</label>
      <label><input type="checkbox" id="wideChk"> 1920</label>
    </div>`;
  bar.addEventListener('click', e => {
    const b = e.target.closest('.hb'); if (!b) return;
    state.variant = b.dataset.v; state.lemma = null; state.drawer = false;
    bar.querySelectorAll('.hb').forEach(x => x.classList.toggle('on', x === b));
    draw();
  });
  document.getElementById('artChk').onchange = e => { state.art = e.target.checked; draw(); };
  document.getElementById('wideChk').onchange = e => {
    document.body.style.zoom = e.target.checked ? String(innerWidth / 1920) : '';
    measure();
  };
  delegate();
  addEventListener('resize', measure);
  addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (state.drawer) { state.drawer = false; draw(); }
    else if (state.lemma) { state.lemma = null; draw(); }
  });
  draw();
}

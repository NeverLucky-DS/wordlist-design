/* =====================================================================
   Wortkarte — V9 «Крупно», taken from a sketch to a finished component.

   V9 was chosen for a reason that is measurable and must survive every edit
   below: it was the only variant where nothing on the sheet fell under
   WCAG AA. The three lines that "disappear at bad eyesight" in V4 — the extra
   translations, the Russian line of the example, the Rektion — sat at
   2.79 / 2.79 / 2.96 : 1 against white where AA asks 4.5. V9 answers that with
   size and weight instead of colour, so the card still works for a reader who
   cannot separate the pastels at all.

   The concept is NOT touched. Kept verbatim from V9:
     · the order              word → перевод → пример → употребление → tabs
     · all meanings equal     numbered, one size (77.2% of cards carry >1)
     · Russian chrome         labels explain where you are; German is material
     · closed tabs            nothing secondary on screen until asked for
     · filled label tags      a label has to survive being read by someone who
                              is already struggling with the body text
     · a body that cannot grow past head + three blocks + one open panel

   What changed, and why each change is a defect being fixed rather than a
   redesign — every number below was read off the browser, not estimated:

   1. THE FREQUENCY METER COLLIDED WITH THE CLOSE BUTTON. In V9 the art sat
      absolutely at `top:16px; right:52px` and the ✕ at `top:16px; right:16px`;
      at 440px they touch. The meter is not decoration floating over the head,
      it is a PROPERTY of the word, exactly like the CEFR chip — so it moves
      into the meta line and stands next to it. Nothing can collide with the
      close button any more because nothing else is positioned near it.

   2. THE CARD OVERFLOWED THE VIEWPORT. `entwickeln` with Grammatik open
      measured 850px against 852px of usable height (900 viewport − 48 of
      sticky margin). Two blocks were spending a label, a 2px rule and 16px of
      margin each to say one line. Rektion IS grammar of use and collocations
      ARE how the word is used, so they became ONE block, «Употребление» —
      saves ~62px and stops the card claiming two headings for one idea.

   3. COLLOCATIONS WERE STACKING ONE PER ROW. As 15.5px pills with 11px side
      padding, "eine Theorie entwickeln" needs 214px of a 380px content column,
      so two never fit and three became four rows. They are now an inline run
      separated by · — the shape a printed dictionary uses for exactly this,
      and 2 rows instead of 4.

   4. NO PRONUNCIATION, THOUGH WE HAVE IT. The dump carries IPA for 59 038 of
      59 335 cards (99.5%) — see info/PLANS.md item B. The head prints it and
      the speaker sits beside it, which is also what frees the footer to carry
      exactly one action instead of two competing ones.

   5. THE HEADWORD COULD OVERFLOW. 52px Cormorant × "die Verantwortung" needs
      ~430px of a 384px content column. `headSize()` steps the lemma down by
      measured length instead of letting it clip.

   6. TABS DID NOT SAY HOW MUCH WAS BEHIND THEM. A closed tab is only honest if
      it declares its contents; «Примеры» now carries the count, and the open
      tab is marked with a caret so "closed" reads as a state and not as a
      row of links someone forgot to style.
   ===================================================================== */
'use strict';

const esc = s => String(s ?? '').replace(/[&<>"']/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* `md` on EVERY model-written string, not just the German one. Production runs
   it on `examples[].de` and escapes the rest, so 33 508 of 276 270 examples
   (12.1%) show literal asterisks in the Russian line and 461 cards show them in
   the collocations — 11 260 cards, 12.2% of the base, print raw `**` at a
   reader. Escape first, then promote, so nothing in the data can inject markup.
   This is info/PLANS.md 0e and it must travel with the card into app.js. */
const md = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<em>$1</em>');

const POS_RU = { noun: 'существительное', verb: 'глагол', adj: 'прилагательное',
                 adv: 'наречие', other: 'слово' };
/* Frequency stays frequency in the wording too. It is not a CEFR level and must
   never be readable as one: measured on the 4 023 cards that do carry a Goethe
   level, zipf cannot separate B1 from B2 at all (medians 4.16 vs 4.15). */
const FREQ_RU = { haeufig: 'частое', mittel: 'средней частоты', selten: 'редкое' };

/* ---------------------------------------------------------------------
   The grammar model — one layer above the drawing, carried over unchanged
   from the prototype because it is not a matter of styling.

   The block looked bolted on because one table was drawn for words that have
   nothing in common:
     · 44.2% of nouns with a paradigm (22 226 of 50 311) have the SAME form in
       all four singular cases, so a 4×2 table printed one word eight times.
       What declines is the ARTICLE, and the article was not in the table.
     · adverbs have an empty grammar object in 100% of cases (1 271 of 1 271),
       so the block must be ABSENT, not empty and captioned "Grammatik".
     · adjectives have two forms — a ladder, never a grid.
     · verbs are memorised as three principal parts; the six present persons
       are a lookup, so only one of the two belongs above the fold.
--------------------------------------------------------------------- */
const ARTICLES = {
  der: { nom: 'der', gen: 'des', dat: 'dem', akk: 'den' },
  die: { nom: 'die', gen: 'der', dat: 'der', akk: 'die' },
  das: { nom: 'das', gen: 'des', dat: 'dem', akk: 'das' },
  pl:  { nom: 'die', gen: 'der', dat: 'den', akk: 'die' },
};
const CASE_SHORT = { nom: 'Nom', gen: 'Gen', dat: 'Dat', akk: 'Akk' };
const PERSONS = { ich: 'ich', du: 'du', er: 'er/sie/es', wir: 'wir', ihr: 'ihr', sie: 'sie' };
const AUX = { haben: 'hat', sein: 'ist' };

function grammarModel(card) {
  const g = card.grammar || {}, m = card.morphology || null;
  const pos = card.pos;

  if (pos === 'noun') {
    const art = ARTICLES[card.article] || null;
    const sg = (m && m.sg) || null, pl = (m && m.pl) || null;
    const sgForms = sg ? [...new Set(Object.values(sg).filter(Boolean))] : [];
    const declines = sgForms.length > 1;
    const rows = (sg && art) ? Object.keys(CASE_SHORT).map(c => ({
      case: c,
      sg: sg[c] ? `${art[c]} ${sg[c]}` : null,
      pl: (pl && pl[c]) ? `${ARTICLES.pl[c]} ${pl[c]}` : null,
    })) : null;
    return {
      kind: 'noun',
      key: [
        g.genitiv ? { lab: 'Genitiv', val: g.genitiv } : null,
        g.plural ? { lab: 'Plural', val: g.plural } : null,
      ].filter(Boolean),
      brief: (art && sg) ? {
        one: `${art.nom} ${sg.nom || card.lemma}`,
        many: (pl && pl.nom) ? `${ARTICLES.pl.nom} ${pl.nom}` : null,
      } : null,
      rows,
      informative: declines,
      note: declensionNote(card.article, sg),
    };
  }

  if (pos === 'verb') {
    const praesens = (m && m.praesens) || null;
    return {
      kind: 'verb',
      key: [
        { lab: 'Infinitiv', val: card.lemma },
        g.praeteritum ? { lab: 'Präteritum', val: g.praeteritum } : null,
        // conjugated ("hat entwickelt"), the way a dictionary prints the third
        // principal part. Bare "haben entwickelt" is not a form of German and
        // would be memorised as one.
        g.partizip2 ? { lab: 'Partizip II', val: (AUX[g.hilfsverb] ? AUX[g.hilfsverb] + ' ' : '') + g.partizip2 } : null,
      ].filter(Boolean),
      praesens: praesens ? Object.keys(PERSONS)
        .filter(k => praesens[k])
        .map(k => ({ person: PERSONS[k], form: praesens[k] })) : null,
      stemChange: praesens ? stemChanges(card.lemma, praesens) : false,
      extra: [
        m && m.imperativ_du ? { lab: 'Imperativ', val: m.imperativ_du + '!' } : null,
        m && m.konjunktiv2 ? { lab: 'Konjunktiv II', val: m.konjunktiv2 } : null,
      ].filter(Boolean),
      informative: !!praesens,
      note: null,
    };
  }

  if (pos === 'adj' || pos === 'adv') {
    if (!g.komparativ && !g.superlativ) return null;   // online, durchaus — say nothing
    return {
      kind: 'ladder',
      steps: [
        { lab: 'Positiv', val: card.lemma },
        g.komparativ ? { lab: 'Komparativ', val: g.komparativ } : null,
        g.superlativ ? { lab: 'Superlativ', val: g.superlativ } : null,
      ].filter(Boolean),
      informative: false, key: [], rows: null, note: null,
    };
  }
  return null;
}

/* Naming the pattern is what turns a table the reader copies into a rule they
   can apply to the next word — but the two patterns must NOT share a label:
     n-Deklination  weak masculine, -(e)n everywhere but the nominative
     gemischt       genitive in -ens, the rest in -(e)n
   Calling `Herz` an n-Deklination would teach "des Herzen", which is wrong. */
function declensionNote(article, sg) {
  if (!sg || !sg.nom || !sg.gen) return null;
  const { nom, gen, dat, akk } = sg;
  if (gen.endsWith('ens') && dat && dat !== nom) return 'Gemischte Deklination — Genitiv auf -ens';
  if (article === 'der' && gen === dat && dat === akk && gen !== nom && /n$/.test(gen)) {
    return 'n-Deklination — außer im Nominativ immer auf -(e)n';
  }
  return null;
}

/* geben → du gibst. The one thing in the present tense worth flagging;
   everything else is predictable from the infinitive. */
function stemChanges(lemma, p) {
  const stem = lemma.replace(/e[nl]$/, '').replace(/n$/, '');
  return !!(p.du && !p.du.startsWith(stem)) || !!(p.er && !p.er.startsWith(stem));
}

/* ---------------------------------------------------------------------
   Art slots. Drawn as labelled frames rather than left blank, so the brief
   travels with the layout: what to draw, at what size, and where it lands.
   `WB.art = false` swaps every slot for its CSS fallback, which is how the
   card is checked for "does it still work if the art never arrives".
--------------------------------------------------------------------- */
const WB = { art: true };

function slot(id, w, h, what, cls = '') {
  if (!WB.art) return '';
  const tiny = (w < 70 || h < 34) ? ' is-tiny' : '';
  const mute = (w < 52 || h < 13) ? ' is-mute' : '';
  return `<span class="art-slot${tiny}${mute} ${cls}" style="--sw:${w}px;--sh:${h}px"
    data-id="${id}" title="${esc(what)} — ${w}×${h}"><i>${esc(id)}</i></span>`;
}

/* The head wash. 15 brushes exist, keyed `band|type` — but `band` is a
   PLACEHOLDER on 95.6% of cards (88 067 of 92 090 are `unlisted`, because
   Goethe publishes lists for A1/A2/B1 only). So half of what the row brush
   encodes is a guess, and a NEW asset must not multiply a guess: the card head
   is keyed on `type` alone, which is real for every card. Five files, not
   fifteen. The existing row brushes are untouched. */
const HEAD_ART = card => slot('card-head-' + card.type, 440, 152,
  'Aquarell-Kopfwäsche je Wortart', 'is-head');

const brushFor = card => {
  const WASH = {
    'B1|der': 'B1_Der_Powdery-Blue_Horizontal-Soft.png', 'B1|die': 'B1_Die_Powdery-Pink_BG-Wash.png',
    'B1|das': 'B1_Das_Pale-Green_BG-Wash.png', 'B1|verb': 'B1_Verbs_Sandy-Ochre_BG-Wash.png',
    'B1|adj': 'B1_Adjectives_Lavender_BG-Wash.png',
    'B2|der': 'B2_Der_Deep-Blue_BG-Wash.png', 'B2|die': 'B2_Die_Magenta_BG-Wash.png',
    'B2|das': 'B2_Das_Grass-Green_BG-Wash.png', 'B2|verb': 'B2_Verbs_Terracotta_BG-Wash.png',
    'B2|adj': 'B2_Adjectives_Amethyst_BG-Wash.png',
    'C1|der': 'C1_Der_Indigo_BG-Wash.png', 'C1|die': 'C1_Die_Burgundy_BG-Wash.png',
    'C1|das': 'C1_Das_Emerald_BG-Wash.png', 'C1|verb': 'C1_Verbs_Olive-Ochre_BG-Wash.png',
    'C1|adj': 'C1_Adjectives_Plum_BG-Wash.png',
  };
  const f = WASH[card.band + '|' + card.type];
  return f ? `url('../../worte/${f}')` : 'none';
};

/* ---------------------------------------------------------------------
   Head furniture
--------------------------------------------------------------------- */

/* 52px Cormorant needs ~0.47em per average German character, so "die
   Verantwortung" (17 including the article and its gap) asks for ~430px of a
   384px content column. Stepping by measured length is cheaper and steadier
   than fitting in JS, and it never clips. */
function headSize(card) {
  const n = (card.article ? card.article.length + 1 : 0) + card.lemma.length;
  if (n > 19) return ' is-xs';   // berücksichtigen, Migrationshintergrund
  if (n > 15) return ' is-s';    // die Verantwortung, Nachhaltigkeit
  return '';
}

/* One line, two claims, never dressed alike: a published Goethe level is a
   citation, our frequency band is a reading of a corpus. The chip is boxed
   because it quotes a list; the meter is painted because it is ours. */
function metaLine(card) {
  const bits = [`<span class="wb-pos">${POS_RU[card.pos] || 'слово'}</span>`];
  if (card.level && card.level !== 'unlisted') {
    bits.push(`<span class="wb-cefr" title="Уровень по спискам Goethe — опубликованный список">${esc(card.band)}</span>`);
  } else if (card.freq) {
    bits.push(`<span class="wb-freq" title="Частотность по корпусу. Это НЕ уровень CEFR — по частоте B1 и B2 не различаются.">
      ${slot('freq-' + card.freq, 58, 14, 'Häufigkeitsskala, 3 Zustände')}
      <b>${esc(FREQ_RU[card.freq] || '')}</b></span>`);
  }
  return bits.join('');
}

/* IPA is present on 99.5% of the dump (59 038 of 59 335) and we currently
   answer "Aussprache" with a browser speech synthesiser. Printing the
   transcription costs nothing and is the half a learner can actually use
   silently — in a library, in a lesson, at 2am. */
function pronLine(card) {
  const ipa = card.ipa || '';
  return `<div class="wb-pron">
    ${ipa ? `<span class="wb-ipa">${esc(ipa)}</span>` : ''}
    <button class="wb-say" type="button" data-say aria-label="Aussprache anhören">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M5 9v6h4l5 5V4L9 9H5z"/><path fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" d="M16.4 8.6a4.8 4.8 0 0 1 0 6.8"/></svg>
      <span>Прослушать</span></button></div>`;
}

/* 1 676 cards are entries the source dictionary listed as a form rather than a
   headword. Search already demotes them; the card has to SAY so, or `gemacht`
   reads as a word in its own right. The base is a button because the entry the
   reader actually wanted is that base — the move Yandex makes. */
const FORM_OF_LABEL = { inflection: 'форма от', capitalised: 'форма от',
  abbrev: 'сокращение от', variant: 'вариант написания' };

function formNote(card) {
  if (!card.form_kind) return '';
  if (card.form_kind === 'compound') return `<div class="wb-form">только в составе сложных слов</div>`;
  const prefix = FORM_OF_LABEL[card.form_kind];
  if (!prefix || !card.form_of) return '';
  return `<div class="wb-form">${prefix}
    <button class="wb-base" type="button" data-base="${esc(card.form_of)}">${esc(card.form_of)}</button></div>`;
}

/* ---------------------------------------------------------------------
   Body blocks
--------------------------------------------------------------------- */
const exampleHTML = e => `<p class="wb-x-de">${md(e.de || '')}</p>` +
  (e.ru ? `<p class="wb-x-ru">${md(e.ru)}</p>` : '');

/* The order carries a claim — the model puts the main sense first — so the
   number stays. The SIZE does not carry a claim, so every meaning gets the
   same one. V4 printed `ru` at 26px and the rest at 12.5px grey, which read as
   "one real translation plus footnotes"; for `entwickeln` those footnotes are
   развивать / разрабатывать / проявлять, three different Russian verbs. */
function meaningsHTML(card) {
  const all = (card.ru_all && card.ru_all.length) ? card.ru_all : [card.ru];
  if (all.length === 1) return `<div class="wb-mn is-single"><span class="mn-t">${esc(all[0])}</span></div>`;
  return `<ol class="wb-mn">${all.map(m =>
    `<li><span class="mn-n"></span><span class="mn-t">${esc(m)}</span></li>`).join('')}</ol>`;
}

/* Rektion and collocations are ONE idea — how the word behaves in a sentence —
   and giving each its own label, rule and margin cost 62px to say it twice.
   Rektion exists on 3.2% of the base, collocations on 99.1%, so the block is
   named for the thing that is nearly always there and the rare one rides on
   top of it in mono, where it reads as a formula rather than as prose. */
function usageHTML(card) {
  const rek = card.rektion || '', colls = card.collocations || [];
  if (!rek && !colls.length) return '';
  return `<span class="wb-lab">Употребление</span>` +
    (rek ? `<div class="wb-rek">${md(rek)}</div>` : '') +
    (colls.length ? `<div class="wb-colls">${colls.map(md).join('<span class="wb-dot">·</span>')}</div>` : '');
}

const TABS_RU = { ex: 'Ещё примеры', gram: 'Грамматика', sense: 'Значение' };

function panelsOf(card, gm) {
  const ex = card.examples || [];
  const t = [];
  if (ex.length > 1) t.push(['ex', TABS_RU.ex, ex.length - 1,
    `<div class="wb-x-list">${ex.slice(1).map(e => `<div class="wb-x">${exampleHTML(e)}</div>`).join('')}</div>`]);
  if (gm) t.push(['gram', TABS_RU.gram, 0, gramBody(gm)]);
  t.push(['sense', TABS_RU.sense, 0,
    `<p class="wb-def">${esc(card.definition_de)}</p>` +
    ((card.synonyms || []).length
      ? `<div class="wb-syn"><span class="wb-syn-lab">Синонимы</span>${
          card.synonyms.map(s => `<button class="wb-syn-chip" type="button" data-base="${esc(s)}">${esc(s)}</button>`).join('')}</div>`
      : '')]);
  return t;
}

/* Closed to start with — the one property V9 was chosen for is a body that
   cannot grow, and a panel open by default spends it before the reader has
   asked for anything. The count on «Ещё примеры» is what makes a closed tab
   honest: it declares what is behind it instead of hiding an unknown. */
const tabsHTML = t => `<div class="wb-tabs" role="tablist">${t.map(([id, lab, n]) =>
    `<button class="wb-tab" type="button" role="tab" aria-expanded="false"
       aria-controls="wbp-${id}" data-tab="${id}">${esc(lab)}${
      n ? `<span class="wb-tab-n">${n}</span>` : ''}<span class="wb-caret" aria-hidden="true"></span></button>`).join('')}</div>` +
  t.map(([id, , , body]) => `<div class="wb-panel" id="wbp-${id}" role="region" data-panel="${id}">${body}</div>`).join('');

/* ---------------------------------------------------------------------
   The card
--------------------------------------------------------------------- */
function wortkarte(card, opts = {}) {
  const gm = grammarModel(card);
  const ex = card.examples || [];
  const usage = usageHTML(card);
  const inList = !!card.in_list;

  return `
  <article class="wb-card" data-lemma="${esc(card.lemma)}" data-type="${esc(card.type)}">
    ${opts.noClose ? '' : `<button class="wb-close" type="button" data-close aria-label="Карточку закрыть">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>`}

    <header class="wb-head" style="--brush:${brushFor(card)}">
      ${HEAD_ART(card)}
      <div class="wb-meta"${opts.noClose ? ' style="padding-right:0"' : ''}>${metaLine(card)}</div>
      <h2 class="wb-word${headSize(card)}">${card.article
        ? `<span class="wb-art">${esc(card.article)}</span>` : ''}<span class="wb-lemma">${esc(card.lemma)}</span></h2>
      ${formNote(card)}
      ${pronLine(card)}
    </header>

    <div class="wb-body">
      <section class="wb-blk">
        <span class="wb-lab">Перевод</span>
        ${meaningsHTML(card)}
      </section>
      ${ex.length ? `<section class="wb-blk">
        <span class="wb-lab">Пример</span>
        <div class="wb-ex">${exampleHTML(ex[0])}</div>
      </section>` : ''}
      ${usage ? `<section class="wb-blk">${usage}</section>` : ''}
    </div>

    ${tabsHTML(panelsOf(card, gm))}

    <footer class="wb-foot">
      <button class="wb-collect${inList ? ' is-in' : ''}" type="button" data-collect>
        ${inList ? 'В списке слов' : 'В список слов'}
      </button>
      ${opts.foot || ''}
    </footer>
  </article>`;
}

/* ---------------------------------------------------------------------
   Grammar body — one implementation for every shape the model returns.
--------------------------------------------------------------------- */
function gramBody(gm) {
  if (gm.kind === 'ladder') {
    return `<div class="g-ladder">${gm.steps.map(s =>
      `<div class="g-step"><i>${esc(s.lab)}</i><b>${esc(s.val)}</b></div>`).join('<span class="g-arrow"></span>')}</div>`;
  }

  if (gm.kind === 'verb') {
    const parts = `<div class="g-parts">${gm.key.map(k =>
      `<div class="g-part"><i>${esc(k.lab)}</i><b>${esc(k.val)}</b></div>`).join('')}</div>`;
    const pres = gm.praesens ? `<div class="g-sub">
        <div class="g-sub-lab">Präsens${gm.stemChange ? ' <em>· Stammwechsel</em>' : ''}</div>
        <div class="g-persons">${gm.praesens.map(p =>
          `<div class="g-person"><i>${esc(p.person)}</i>${esc(p.form)}</div>`).join('')}</div></div>` : '';
    const extra = gm.extra.length ? `<div class="g-extra">${gm.extra.map(e =>
      `<span><i>${esc(e.lab)}</i>${esc(e.val)}</span>`).join('')}</div>` : '';
    return parts + pres + extra;
  }

  if (gm.kind === 'noun') {
    // Two lines, not eight cells: which article it takes and how the plural is
    // built answers the question for the 44.2% whose singular never changes.
    // The full paradigm is offered underneath and only opens by itself when the
    // noun actually declines.
    // "Plural" and the plural form are ONE unit and must wrap together: as three
    // loose flex children the label was left stranded at the end of the first
    // line, reading as if `die Verantwortung` were the plural.
    const brief = gm.brief ? `<div class="g-brief">
        <span class="g-brief-one">${esc(gm.brief.one)}</span>
        ${gm.brief.many ? `<span class="g-brief-pl"><span class="g-brief-sep">Plural</span>
          <span class="g-brief-many">${esc(gm.brief.many)}</span></span>` : ''}
      </div>` : `<div class="g-brief">${gm.key.map(k => `<span class="g-brief-one">${esc(k.val)}</span>`).join('')}</div>`;
    if (!gm.rows) return brief;
    const table = `<div class="g-cases-wrap"><table class="g-cases">
      <thead><tr><th></th><th>Singular</th><th>Plural</th></tr></thead><tbody>
      ${gm.rows.map(r => `<tr><th>${CASE_SHORT[r.case]}</th>
        <td>${r.sg ? esc(r.sg) : '—'}</td><td>${r.pl ? esc(r.pl) : '—'}</td></tr>`).join('')}
      </tbody></table></div>`;
    return brief + (gm.note ? `<div class="g-note">${esc(gm.note)}</div>` : '') +
      `<details class="g-more"${gm.informative ? ' open' : ''}>
         <summary>Все четыре падежа</summary>${table}</details>`;
  }
  return '';
}

/* ---------------------------------------------------------------------
   Behaviour. One function, so every page variant wires the card the same way
   and a difference between variants is never a difference in what the card
   can do.
--------------------------------------------------------------------- */
function wireCard(root, card, handlers = {}) {
  const el = root.querySelector('.wb-card');
  if (!el) return;

  el.querySelectorAll('[data-close]').forEach(b => b.onclick = e => {
    e.stopPropagation(); handlers.close && handlers.close();
  });

  el.querySelectorAll('[data-say]').forEach(b => b.onclick = e => {
    e.stopPropagation();
    if (!('speechSynthesis' in window)) return;
    const u = new SpeechSynthesisUtterance((card.article ? card.article + ' ' : '') + card.lemma);
    u.lang = 'de-DE'; u.rate = 0.9;
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  });

  // a form's base and a synonym are both "the entry you actually wanted"
  el.querySelectorAll('[data-base]').forEach(b => b.onclick = e => {
    e.stopPropagation(); handlers.goto && handlers.goto(b.dataset.base);
  });

  el.querySelectorAll('[data-collect]').forEach(b => b.onclick = e => {
    e.stopPropagation(); handlers.collect && handlers.collect(card);
  });

  // Clicking the open tab closes it, so the card can always be returned to its
  // shortest state — a reader who opened Grammatik by accident is not made to
  // scroll past it for the rest of the session.
  el.querySelectorAll('.wb-tab').forEach(b => b.onclick = e => {
    e.stopPropagation();
    const closing = b.classList.contains('on');
    el.querySelectorAll('.wb-tab').forEach(x => {
      const on = !closing && x === b;
      x.classList.toggle('on', on);
      x.setAttribute('aria-expanded', String(on));
    });
    el.querySelectorAll('.wb-panel').forEach(p =>
      p.classList.toggle('on', !closing && p.dataset.panel === b.dataset.tab));
    handlers.resize && handlers.resize();
  });

  el.querySelectorAll('details').forEach(d =>
    d.addEventListener('toggle', () => handlers.resize && handlers.resize()));
}

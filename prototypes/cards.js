/* =====================================================================
   Card prototypes — five directions for the Wörterbuch entry sheet.

   The point of the file is the layer ABOVE the variants: `grammarModel`.
   Every variant draws the same model, so a difference between two variants is
   a design difference and never an accident of which fields one of them
   happened to read.

   Why the model exists at all — the grammar block currently looks bolted on
   because it is drawn the same way for words that have nothing in common:

     • 44.2% of nouns with a paradigm (22 226 of 50 311, measured on the live
       enrichment.db) have the SAME form in all four singular cases. Rendering
       them as a 4×2 table prints one word eight times. What actually declines
       is the ARTICLE, and the article was not in the table at all.
     • adverbs have an empty grammar object in 100% of cases (1 271 of 1 271),
       so for them the block must be absent, not empty.
     • adjectives have two forms, never a grid — a ladder reads them better.
     • verbs memorise as three principal parts; the six present-tense persons
       are a lookup, not a headline. So they are two different things and only
       one of them belongs above the fold.

   `grammarModel` therefore returns a SHAPE per part of speech, plus an honest
   `table: null` whenever the table would carry no information.
   ===================================================================== */
'use strict';

const esc = s => String(s ?? '').replace(/[&<>"']/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* model output may carry **bold** around the keyword — escape first, then
   promote, so nothing in the data can inject markup */
const md = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<em>$1</em>');

const POS_LABEL = { noun: 'Substantiv', verb: 'Verb', adj: 'Adjektiv', adv: 'Adverb', other: 'Wort' };
const FREQ_LABEL = { haeufig: 'häufig', mittel: 'mittelhäufig', selten: 'selten' };

/* The declined article, by gender. Not data — this is closed-class German
   grammar, the same four rows for every noun of a gender, and deriving it here
   is what turns an invariant noun ("die Wirkung" four times) into the thing the
   learner is actually memorising ("der Wirkung" in dative). */
const ARTICLES = {
  der: { nom: 'der', gen: 'des', dat: 'dem', akk: 'den' },
  die: { nom: 'die', gen: 'der', dat: 'der', akk: 'die' },
  das: { nom: 'das', gen: 'des', dat: 'dem', akk: 'das' },
  pl:  { nom: 'die', gen: 'der', dat: 'den', akk: 'die' },
};
const CASE_LABEL = { nom: 'Nominativ', gen: 'Genitiv', dat: 'Dativ', akk: 'Akkusativ' };
const CASE_SHORT = { nom: 'Nom', gen: 'Gen', dat: 'Dat', akk: 'Akk' };
const PERSONS = { ich: 'ich', du: 'du', er: 'er/sie/es', wir: 'wir', ihr: 'ihr', sie: 'sie' };
const AUX = { haben: 'hat', sein: 'ist' };

function grammarModel(card) {
  const g = card.grammar || {}, m = card.morphology || null;
  const pos = card.pos;

  if (pos === 'noun') {
    const art = ARTICLES[card.article] || null;
    const sg = (m && m.sg) || null, pl = (m && m.pl) || null;
    // Does the noun itself decline, or is the article doing all the work?
    const sgForms = sg ? [...new Set(Object.values(sg).filter(Boolean))] : [];
    const declines = sgForms.length > 1;
    const rows = (sg && art) ? Object.keys(CASE_LABEL).map(c => ({
      case: c,
      sg: sg[c] ? `${art[c]} ${sg[c]}` : null,
      pl: (pl && pl[c]) ? `${ARTICLES.pl[c]} ${pl[c]}` : null,
    })) : null;
    return {
      kind: 'noun',
      // the two facts a dictionary prints in its headline, always available
      key: [
        g.genitiv ? { lab: 'Genitiv', val: g.genitiv } : null,
        g.plural ? { lab: 'Plural', val: g.plural } : null,
      ].filter(Boolean),
      // Nominativ singular / plural, the pair that answers "which article, which
      // plural" — enough for the 44% whose singular never changes.
      brief: (art && sg) ? {
        one: `${art.nom} ${sg.nom || card.lemma}`,
        many: (pl && pl.nom) ? `${ARTICLES.pl.nom} ${pl.nom}` : null,
      } : null,
      rows,
      // A table for an invariant noun prints the same word eight times. Offer it
      // anyway (it is still the full paradigm) but never as the default view.
      informative: declines,
      note: declensionNote(card.article, sg),
    };
  }

  if (pos === 'verb') {
    const praesens = (m && m.praesens) || null;
    return {
      kind: 'verb',
      // the three principal parts, in the order they are learned and drilled
      key: [
        { lab: 'Infinitiv', val: card.lemma },
        g.praeteritum ? { lab: 'Präteritum', val: g.praeteritum } : null,
        // The auxiliary is shown CONJUGATED ("hat entwickelt"), the way a
        // dictionary prints the third principal part. Bare "haben entwickelt"
        // is not a form of German and would be memorised as one.
        g.partizip2 ? { lab: 'Partizip II', val: (AUX[g.hilfsverb] ? AUX[g.hilfsverb] + ' ' : '') + g.partizip2 } : null,
      ].filter(Boolean),
      praesens: praesens ? Object.keys(PERSONS)
        .filter(k => praesens[k])
        .map(k => ({ person: PERSONS[k], form: praesens[k] })) : null,
      // stem change is the whole reason to look at the present tense at all
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
      informative: false,
      key: [], rows: null, note: null,
    };
  }
  return null;
}

/* Why the noun declines, when it does. Naming the pattern is the difference
   between a table the reader copies and a rule they can apply to the next word
   — but the two patterns are NOT the same and must not share a label:
     n-Deklination   weak masculine, -(e)n in every case but the nominative
                     (der Student → des/dem/den Studenten)
     gemischt        genitive in -ens, the rest in -(e)n
                     (das Herz → des Herzens, dem Herzen, das Herz)
   Calling Herz an n-Deklination would teach "des Herzen", which is wrong. */
function declensionNote(article, sg) {
  if (!sg || !sg.nom || !sg.gen) return null;
  const { nom, gen, dat, akk } = sg;
  if (gen.endsWith('ens') && dat && dat !== nom) return 'Gemischte Deklination — Genitiv auf -ens';
  if (article === 'der' && gen === dat && dat === akk && gen !== nom && /n$/.test(gen)) {
    return 'n-Deklination — außer im Nominativ immer auf -(e)n';
  }
  return null;
}

/* du/er forms that are not the plain stem + ending: geben → du gibst. This is
   the one thing in the present tense worth flagging; everything else is
   predictable from the infinitive and does not deserve the reader's attention. */
function stemChanges(lemma, p) {
  const stem = lemma.replace(/e[nl]$/, '').replace(/n$/, '');
  return !!(p.du && !p.du.startsWith(stem)) || !!(p.er && !p.er.startsWith(stem));
}

/* ---------- pieces every variant needs ---------- */

// The Rektion is what a verb actually demands of the sentence around it, but
// only 21% of verbs carry one (1 964 of 9 358) and 3.2% of the base overall.
// Collocations are filled for 99.1%, so they — not the Rektion — are the
// dependable "how it is used" signal, and the layout must not assume otherwise.
function usageOf(card) {
  return { rektion: card.rektion || '', colls: card.collocations || [] };
}

/* "Form von machen". 1 676 cards are entries the source dictionary listed as a
   form rather than a headword; search already demotes them, and the card must
   say so or `gemacht` reads as a word in its own right. The base is a button
   because the entry the reader actually wanted is that base. */
const FORM_OF_LABEL = { inflection: 'Form von', capitalised: 'Form von',
  abbrev: 'Kurzform von', variant: 'Nebenform von' };

function formNote(card) {
  if (!card.form_kind) return '';
  if (card.form_kind === 'compound') return `<div class="form-note">nur in Zusammensetzungen</div>`;
  const prefix = FORM_OF_LABEL[card.form_kind];
  if (!prefix || !card.form_of) return '';
  return `<div class="form-note">${prefix} <button class="form-base" type="button"
    data-base="${esc(card.form_of)}">${esc(card.form_of)}</button></div>`;
}

function levelMark(card) {
  if (card.level && card.level !== 'unlisted') {
    return { text: card.band, kind: 'cefr', title: `Goethe-Wortliste ${card.band}` };
  }
  if (!card.freq) return null;
  return { text: FREQ_LABEL[card.freq], kind: 'freq', title: 'Häufigkeit im Korpus — kein Niveau' };
}

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
  return f ? `url('../worte/${f}')` : 'none';
};

/* A slot for art that does not exist yet. Rendered as a labelled frame rather
   than left blank, so the brief travels with the layout: what to draw, at what
   size, and why the card is worse without it. */
function slot(id, w, h, what) {
  // Anything this small cannot carry a caption; it keeps the id and hands the
  // brief to the tooltip instead of spilling text past its own frame.
  const tiny = w < 60 || h < 40 ? ' is-tiny' : '';
  return `<div class="art-slot${tiny}" style="--sw:${w}px;--sh:${h}px" data-id="${id}" title="${esc(what)} — ${w}×${h}">
    <span class="art-slot-id">${esc(id)}</span><span class="art-slot-what">${esc(what)}</span>
    <span class="art-slot-dim">${w}×${h}</span></div>`;
}

/* A collapsible module. Closed by default is the whole idea: the base fills
   definition, three examples, synonyms and collocations for essentially every
   card, and printing all of it at once is what makes today's sheet a wall. */
function mod(id, label, count, body, open = false) {
  return `<details class="m"${open ? ' open' : ''} data-mod="${id}">
    <summary><span class="m-lab">${esc(label)}</span>
      ${count ? `<span class="m-count">${count}</span>` : ''}
      <span class="m-chev" aria-hidden="true"></span></summary>
    <div class="m-body">${body}</div></details>`;
}

/* `md` on BOTH lines. Production runs it only on the German one and escapes the
   Russian, so wherever the model marked the keyword in the translation too, the
   reader is shown literal asterisks: "Я сейчас **онлайн**". Measured on the live
   base — 33 508 of 276 270 examples (12.1%) carry ** in `ru`, affecting 11 260
   cards. It is a one-character fix and it belongs in js/app.js as well. */
const exampleHTML = e => `<p class="x-de">${md(e.de || '')}</p>` +
  (e.ru ? `<p class="x-ru">${md(e.ru)}</p>` : '');

/* =====================================================================
   VARIANT 1 — «Lexikon»
   Typography only. No panel, no frame, no fill: the sheet is a page, and
   structure comes from size, weight and one hairline. The single piece of art
   is the brush the row already uses, laid under the headword as a colour code
   that is doing real work (level × gender), not decoration.
   ===================================================================== */
function v1(card) {
  const gm = grammarModel(card), u = usageOf(card), lv = levelMark(card);
  const ex = card.examples || [];
  const gram = gm ? mod('gram', 'Grammatik', null, gramBody(gm, card)) : '';
  return `
  <div class="v1">
    <div class="v1-head">
      <div class="v1-wash" style="--brush:${brushFor(card)}"></div>
      <div class="v1-word">${card.article ? `<span class="art">${esc(card.article)}</span> ` : ''}${esc(card.lemma)}</div>
      <div class="v1-ru">${esc(card.ru)}</div>
      ${card.ru_all.length > 1 ? `<div class="v1-ru2">${card.ru_all.slice(1).map(esc).join(' · ')}</div>` : ''}
      ${formNote(card)}
    </div>
    <div class="v1-meta">
      <span>${POS_LABEL[card.pos] || 'Wort'}</span>
      ${lv ? `<span class="v1-lv is-${lv.kind}" title="${esc(lv.title)}">${esc(lv.text)}</span>` : ''}
      ${u.rektion ? `<span class="v1-rek">${esc(u.rektion)}</span>` : ''}
    </div>
    <div class="v1-ex">${exampleHTML(ex[0] || {})}</div>
    ${u.colls.length ? `<div class="v1-coll">${u.colls.map(md).join('  ·  ')}</div>` : ''}
    <div class="v1-mods">
      ${ex.length > 1 ? mod('ex', 'Weitere Beispiele', ex.length - 1,
        `<div class="x-list">${ex.slice(1).map(e => `<div class="x">${exampleHTML(e)}</div>`).join('')}</div>`) : ''}
      ${gram}
      ${mod('sense', 'Bedeutung & Synonyme', null,
        `<p class="v1-def">${esc(card.definition_de)}</p>` +
        (card.synonyms.length ? `<p class="v1-syn">${card.synonyms.map(esc).join(' · ')}</p>` : ''))}
    </div>
  </div>`;
}

/* =====================================================================
   VARIANT 2 — «Karteikarte»
   The card as a physical object: a tab that names the part of speech, a ruled
   paper ground, and a real back side. Front holds only word, translation and
   one sentence — everything a flashcard is for. Grammar lives on the BACK, so
   "hide the secondary" is not a toggle but the shape of the object.
   ===================================================================== */
function v2(card) {
  const gm = grammarModel(card), u = usageOf(card), lv = levelMark(card);
  const ex = card.examples || [];
  return `
  <div class="v2" data-face="front">
    <div class="v2-tab">${POS_LABEL[card.pos] || 'Wort'}${lv ? ` · <i class="is-${lv.kind}">${esc(lv.text)}</i>` : ''}</div>
    <div class="v2-face v2-front">
      ${slot('kk-paper', 440, 300, 'Papierstruktur: liniertes Karteikarten-Papier, sehr blass, kachelbar')}
      <div class="v2-word">${card.article ? `<span class="art">${esc(card.article)}</span> ` : ''}${esc(card.lemma)}</div>
      ${formNote(card)}
      <div class="v2-rule"></div>
      <div class="v2-ru">${esc(card.ru)}</div>
      ${card.ru_all.length > 1 ? `<div class="v2-ru2">${card.ru_all.slice(1).map(esc).join(' · ')}</div>` : ''}
      <div class="v2-ex">${exampleHTML(ex[0] || {})}</div>
      ${u.rektion ? `<div class="v2-rek"><i>Rektion</i>${esc(u.rektion)}</div>` : ''}
      <button class="v2-flip" type="button" data-flip>Rückseite — Grammatik &amp; Beispiele →</button>
    </div>
    <div class="v2-face v2-back">
      <div class="v2-back-in">
        ${gm ? `<div class="v2-sec"><div class="v2-sec-lab">Grammatik</div>${gramBody(gm, card)}</div>` : ''}
        <div class="v2-sec"><div class="v2-sec-lab">Beispiele</div>
          <div class="x-list">${ex.slice(1).map(e => `<div class="x">${exampleHTML(e)}</div>`).join('')}</div></div>
        <div class="v2-sec"><div class="v2-sec-lab">Bedeutung</div>
          <p class="v2-def">${esc(card.definition_de)}</p>
          ${card.synonyms.length ? `<p class="v2-syn">${card.synonyms.map(esc).join(' · ')}</p>` : ''}
          ${u.colls.length ? `<p class="v2-coll">${u.colls.map(md).join('  ·  ')}</p>` : ''}</div>
      </div>
      <button class="v2-flip" type="button" data-flip>← Zurück zum Wort</button>
    </div>
  </div>`;
}

/* =====================================================================
   VARIANT 3 — «Datenblatt»
   Rationalist spec sheet. One grid, one typeface, tabular figures, labels in a
   fixed left rail so every row starts on the same vertical. Nothing is
   centred, nothing is decorative; the only ornament is the gender mark, and it
   is an index, not a flourish. This is the pedantic end of the range.
   ===================================================================== */
function v3(card) {
  const gm = grammarModel(card), u = usageOf(card), lv = levelMark(card);
  const ex = card.examples || [];
  const row = (lab, val) => `<div class="v3-row"><span class="v3-lab">${esc(lab)}</span><div class="v3-val">${val}</div></div>`;
  return `
  <div class="v3">
    <div class="v3-top">
      ${slot('mark-' + (card.article || card.pos), 34, 34, 'Genus-/Wortart-Marke, Tuschestrich, 1 Glyphe je Typ (8 Stück)')}
      <div class="v3-topmeta">
        <span>${(POS_LABEL[card.pos] || 'Wort').toUpperCase()}</span>
        ${card.article ? `<span>${esc(card.article).toUpperCase()}</span>` : ''}
        ${lv ? `<span class="is-${lv.kind}" title="${esc(lv.title)}">${esc(lv.text)}</span>` : ''}
      </div>
    </div>
    <div class="v3-word">${esc(card.lemma)}</div>
    <div class="v3-ru">${esc(card.ru)}</div>
    <div class="v3-sheet">
      ${card.form_kind ? row('Status', formNote(card)) : ''}
      ${card.ru_all.length > 1 ? row('weitere', `<span class="v3-plain">${card.ru_all.slice(1).map(esc).join('; ')}</span>`) : ''}
      ${row('Beispiel', `<div class="v3-ex">${exampleHTML(ex[0] || {})}</div>`)}
      ${u.rektion ? row('Rektion', `<span class="v3-mono">${esc(u.rektion)}</span>`) : ''}
      ${u.colls.length ? row('Kollokation', `<span class="v3-plain">${u.colls.map(md).join('; ')}</span>`) : ''}
    </div>
    <div class="v3-mods">
      ${ex.length > 1 ? mod('ex', 'Beispiele', ex.length - 1,
        `<div class="x-list">${ex.slice(1).map(e => `<div class="x">${exampleHTML(e)}</div>`).join('')}</div>`) : ''}
      ${gm ? mod('gram', 'Formen', null, gramBody(gm, card)) : ''}
      ${mod('sense', 'Definition', null,
        `<p class="v3-def">${esc(card.definition_de)}</p>` +
        (card.synonyms.length ? `<p class="v3-syn">${card.synonyms.map(esc).join(' · ')}</p>` : ''))}
    </div>
  </div>`;
}

/* =====================================================================
   VARIANT 4 — «Bühne»
   One thing at a time. The word gets a full-bleed head in its own brush, the
   first sentence gets the stage, and everything else is behind a single row of
   tabs where exactly one panel can be open. Compact by construction: the
   sheet cannot grow past head + sentence + one panel.
   ===================================================================== */
function v4(card) {
  const gm = grammarModel(card), u = usageOf(card), lv = levelMark(card);
  const ex = card.examples || [];
  const tabs = [];
  if (ex.length > 1) tabs.push(['ex', 'Beispiele', `<div class="x-list">${ex.slice(1).map(e => `<div class="x">${exampleHTML(e)}</div>`).join('')}</div>`]);
  if (gm) tabs.push(['gram', 'Grammatik', gramBody(gm, card)]);
  tabs.push(['sense', 'Bedeutung', `<p class="v4-def">${esc(card.definition_de)}</p>` +
    (card.synonyms.length ? `<p class="v4-syn">${card.synonyms.map(esc).join(' · ')}</p>` : '')]);

  return `
  <div class="v4">
    <div class="v4-head" style="--brush:${brushFor(card)}">
      <div class="v4-headmeta">
        <span>${POS_LABEL[card.pos] || 'Wort'}</span>
        ${lv ? `<span class="v4-lv is-${lv.kind}" title="${esc(lv.title)}">${esc(lv.text)}</span>` : ''}
      </div>
      <div class="v4-word">${card.article ? `<span class="art">${esc(card.article)}</span> ` : ''}${esc(card.lemma)}</div>
      <div class="v4-ru">${esc(card.ru)}</div>
      ${formNote(card)}
    </div>
    ${card.ru_all.length > 1 ? `<div class="v4-ru2">${card.ru_all.slice(1).map(esc).join(' · ')}</div>` : ''}
    <div class="v4-stage">
      ${exampleHTML(ex[0] || {})}
      ${u.rektion ? `<div class="v4-rek">${esc(u.rektion)}</div>` : ''}
      ${u.colls.length ? `<div class="v4-coll">${u.colls.map(c => `<span>${md(c)}</span>`).join('')}</div>` : ''}
    </div>
    <div class="v4-tabs" role="tablist">
      ${tabs.map(([id, lab], i) => `<button class="v4-tab${i === 0 ? ' on' : ''}" type="button" data-tab="${id}">${esc(lab)}</button>`).join('')}
    </div>
    ${tabs.map(([id, , body], i) => `<div class="v4-panel${i === 0 ? ' on' : ''}" data-panel="${id}">${body}</div>`).join('')}
  </div>`;
}

/* =====================================================================
   VARIANT 5 — «Buchseite»
   A dictionary page: a narrow margin column carries the apparatus (part of
   speech, level, grammar keys, Rektion) and the wide column carries language.
   The grammar never sits ON the content as a slab — it stands beside it, which
   is exactly how a printed dictionary avoids the bolted-on feeling.
   ===================================================================== */
function v5(card) {
  const gm = grammarModel(card), u = usageOf(card), lv = levelMark(card);
  const ex = card.examples || [];
  const keys = gm && gm.key ? gm.key : [];
  return `
  <div class="v5">
    ${slot('ornament', 168, 46, 'Feiner Tuschestrich / Zierlinie über dem Wort, nur Alpha, 1 Datei')}
    <div class="v5-word">${card.article ? `<span class="art">${esc(card.article)}</span> ` : ''}${esc(card.lemma)}</div>
    <div class="v5-ru">${esc(card.ru)}</div>
    ${card.ru_all.length > 1 ? `<div class="v5-ru2">${card.ru_all.slice(1).map(esc).join(' · ')}</div>` : ''}
    <div class="v5-cols">
      <aside class="v5-margin">
        <div class="v5-m-item"><i>Wortart</i>${POS_LABEL[card.pos] || 'Wort'}</div>
        ${card.form_kind ? `<div class="v5-m-item v5-m-form"><i>Status</i>${formNote(card)}</div>` : ''}
        ${lv ? `<div class="v5-m-item is-${lv.kind}"><i>${lv.kind === 'cefr' ? 'Niveau' : 'Häufigkeit'}</i>${esc(lv.text)}</div>` : ''}
        ${keys.map(k => `<div class="v5-m-item"><i>${esc(k.lab)}</i>${esc(k.val)}</div>`).join('')}
        ${u.rektion ? `<div class="v5-m-item v5-m-rek"><i>Rektion</i>${esc(u.rektion)}</div>` : ''}
      </aside>
      <div class="v5-main">
        <div class="v5-ex">${exampleHTML(ex[0] || {})}</div>
        ${u.colls.length ? `<div class="v5-coll">${u.colls.map(md).join('  ·  ')}</div>` : ''}
      </div>
    </div>
    <!-- The modules sit BELOW the two columns, at full card width, not inside
         the main one. The marginalia layout is for prose; a case paradigm is a
         table, and German gives it long cells — "die Verantwortungen" twice
         over needs 324px, while V5's main column is 224px. Nested, the table
         overflowed the card by 69px on an ordinary B1 noun. -->
    <div class="v5-mods">
      ${ex.length > 1 ? mod('ex', 'Weitere Beispiele', ex.length - 1,
        `<div class="x-list">${ex.slice(1).map(e => `<div class="x">${exampleHTML(e)}</div>`).join('')}</div>`) : ''}
      ${gm ? mod('gram', 'Vollständige Formen', null, gramBody(gm, card)) : ''}
      ${mod('sense', 'Bedeutung & Synonyme', null,
        `<p class="v5-def">${esc(card.definition_de)}</p>` +
        (card.synonyms.length ? `<p class="v5-syn">${card.synonyms.map(esc).join(' · ')}</p>` : ''))}
    </div>
  </div>`;
}

/* ---------------------------------------------------------------------
   The grammar body, drawn from the model — one implementation, all variants.
   Each shape is chosen so the block says something the reader could not have
   guessed; where there is nothing to say, `grammarModel` returned null and no
   block is drawn at all.
--------------------------------------------------------------------- */
function gramBody(gm, card) {
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
    // The default answer for a noun is two lines, not eight cells: which
    // article it takes and how the plural is built. The full case table is
    // offered underneath, and only opened by default when the noun itself
    // declines — otherwise it repeats one word four times.
    const brief = gm.brief ? `<div class="g-brief">
        <span class="g-brief-one">${esc(gm.brief.one)}</span>
        ${gm.brief.many ? `<span class="g-brief-sep">Plural</span><span class="g-brief-many">${esc(gm.brief.many)}</span>` : ''}
      </div>` : `<div class="g-brief">${gm.key.map(k => `<span class="g-brief-one">${esc(k.val)}</span>`).join('')}</div>`;
    if (!gm.rows) return brief;
    const table = `<div class="g-cases-wrap"><table class="g-cases"><thead><tr><th></th><th>Singular</th><th>Plural</th></tr></thead><tbody>
      ${gm.rows.map(r => `<tr><th>${CASE_SHORT[r.case]}</th>
        <td>${r.sg ? esc(r.sg) : '—'}</td><td>${r.pl ? esc(r.pl) : '—'}</td></tr>`).join('')}
      </tbody></table></div>`;
    return brief + (gm.note ? `<div class="g-note">${esc(gm.note)}</div>` : '') +
      `<details class="g-more"${gm.informative ? ' open' : ''}>
         <summary>Alle vier Fälle</summary>${table}</details>`;
  }
  return '';
}

/* =====================================================================
   Prototype harness — page chrome, switchers, and the side test.
   ===================================================================== */
const VARIANTS = {
  v1: { fn: v1, name: 'Lexikon', sub: 'Nur Typografie' },
  v2: { fn: v2, name: 'Karteikarte', sub: 'Vorder- und Rückseite' },
  v3: { fn: v3, name: 'Datenblatt', sub: 'Raster, tabellarisch' },
  v4: { fn: v4, name: 'Bühne', sub: 'Ein Panel zur Zeit' },
  v5: { fn: v5, name: 'Buchseite', sub: 'Marginalspalte' },
};

const state = { variant: 'v1', lemma: 'Wirkung', side: 'right' };
const detail = () => document.getElementById('detail');

function draw() {
  const card = PROTO_CARDS[state.lemma];
  const layer = document.getElementById('cardLayer');
  layer.hidden = false;
  layer.classList.toggle('on-left', state.side === 'left');
  layer.classList.toggle('on-right', state.side === 'right');
  const d = detail();
  d.dataset.variant = state.variant;
  d.innerHTML = `<button class="d-close" type="button" aria-label="Schließen">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button>` +
    VARIANTS[state.variant].fn(card) +
    `<div class="d-foot"><button class="d-collect" type="button">Zur Lernliste</button>
       <button class="d-hear" type="button">Aussprache</button></div>`;
  wire();
  document.querySelectorAll('.word').forEach(w =>
    w.classList.toggle('active', w.dataset.lemma === state.lemma));
  measure();
  requestAnimationFrame(link);
}

function wire() {
  const d = detail();
  d.querySelectorAll('[data-flip]').forEach(b => b.onclick = () => {
    const v = d.querySelector('.v2');
    v.dataset.face = v.dataset.face === 'front' ? 'back' : 'front';
  });
  d.querySelectorAll('.v4-tab').forEach(b => b.onclick = () => {
    d.querySelectorAll('.v4-tab').forEach(x => x.classList.toggle('on', x === b));
    d.querySelectorAll('.v4-panel').forEach(p =>
      p.classList.toggle('on', p.dataset.panel === b.dataset.tab));
    requestAnimationFrame(link);
  });
  d.querySelectorAll('details').forEach(x => x.addEventListener('toggle', () => requestAnimationFrame(link)));
}

/* The size readout. Point 2 of the brief — the card is not the same object on
   the two sides — is a layout fact, not a rendering one: the grid gives the
   lookup column minmax(400px,1.05fr) and the list column minmax(340px,440px),
   so the SAME card is ~1.7× wider when it opens over the lookup. Printing both
   numbers live is the only way to see the fix hold. */
function measure() {
  const r = detail().getBoundingClientRect();
  document.getElementById('measure').textContent =
    `${Math.round(r.width)} × ${Math.round(r.height)} px`;
}

/* the live connector, same idea as production: card headword → its row */
function link() {
  const svg = document.getElementById('linkLine'),
        path = document.getElementById('linkPath'),
        dot = document.getElementById('linkDot'),
        anch = document.getElementById('linkAnchor');
  const head = detail().querySelector('.v1-word,.v2-word,.v3-word,.v4-word,.v5-word');
  const col = state.side === 'right' ? document.getElementById('results') : document.getElementById('myList');
  const row = col.querySelector(`.word[data-lemma="${CSS.escape(state.lemma)}"] .de`);
  if (!head || !row) { svg.setAttribute('hidden', ''); return; }
  const t = head.getBoundingClientRect(), w = row.getBoundingClientRect();
  // The Karteikarte hides its headword when flipped to the back; a hidden
  // element measures 0×0 and the line would shoot to the viewport origin.
  // Nothing to point at means no line, not a line to nowhere.
  if (!t.width || !t.height) { svg.setAttribute('hidden', ''); return; }
  const fromLeft = t.left > w.left;
  const sx = fromLeft ? t.left : t.right, sy = t.top + t.height / 2;
  const ex = fromLeft ? w.right + 9 : w.left - 9, ey = w.top + w.height / 2;
  const dir = Math.sign(sx - ex) || 1, k = Math.max(70, Math.abs(sx - ex) * 0.4);
  path.setAttribute('d', `M ${sx.toFixed(1)} ${sy.toFixed(1)} C ${(sx - dir * k).toFixed(1)} ${sy.toFixed(1)}, ${(ex + dir * k).toFixed(1)} ${ey.toFixed(1)}, ${ex.toFixed(1)} ${ey.toFixed(1)}`);
  anch.setAttribute('cx', sx.toFixed(1)); anch.setAttribute('cy', sy.toFixed(1));
  dot.setAttribute('cx', ex.toFixed(1)); dot.setAttribute('cy', ey.toFixed(1));
  svg.removeAttribute('hidden');
}

/* ---------- the two word columns, so the card is judged in place ---------- */
function rowHTML(card) {
  const lv = levelMark(card);
  return `<div class="word" data-lemma="${esc(card.lemma)}" style="--brush:${brushFor(card)}">
    <span class="wash"></span>
    <div class="w-body">
      <div class="de">${card.article ? `<span class="art">${esc(card.article)}</span> ` : ''}${esc(card.lemma)}</div>
      <div class="ru">${esc(card.ru)}</div>
    </div>
    <div class="w-right">${lv ? `<span class="lvl-tag is-${lv.kind}">${esc(lv.text)}</span>` : ''}
      <button class="w-act" type="button" data-act="add" title="Zur Lernliste">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
      </button></div></div>`;
}

const LEFT = ['Wirkung', 'entwickeln', 'nachhaltig', 'Student', 'durchaus', 'gemacht'];
const RIGHT = ['Verantwortung', 'berücksichtigen', 'Herz', 'Nachhaltigkeit', 'Auswirkung', 'online'];

function boot() {
  document.getElementById('results').innerHTML = LEFT.map(l => rowHTML(PROTO_CARDS[l])).join('');
  document.getElementById('myList').innerHTML = RIGHT.map(l => rowHTML(PROTO_CARDS[l])).join('');

  const bar = document.getElementById('vbar');
  bar.innerHTML = Object.entries(VARIANTS).map(([k, v]) =>
    `<button class="vb${k === state.variant ? ' on' : ''}" data-v="${k}">
       <b>${k.toUpperCase()}</b><span>${v.name}</span><i>${v.sub}</i></button>`).join('');
  bar.onclick = e => {
    const b = e.target.closest('.vb'); if (!b) return;
    state.variant = b.dataset.v;
    bar.querySelectorAll('.vb').forEach(x => x.classList.toggle('on', x === b));
    draw();
  };

  document.getElementById('results').onclick = e => {
    const r = e.target.closest('.word'); if (!r) return;
    state.lemma = r.dataset.lemma; state.side = 'right'; draw();
  };
  document.getElementById('myList').onclick = e => {
    const r = e.target.closest('.word'); if (!r) return;
    state.lemma = r.dataset.lemma; state.side = 'left'; draw();
  };
  detail().addEventListener('click', e => {
    if (e.target.closest('.d-close')) { document.getElementById('cardLayer').hidden = true;
      document.getElementById('linkLine').setAttribute('hidden', ''); }
  });
  addEventListener('scroll', link, { passive: true });
  addEventListener('resize', () => { measure(); link(); });
  draw();
}
document.addEventListener('DOMContentLoaded', boot);

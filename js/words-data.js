/* =====================================================================
   Shared watercolor brush map — level + grammatical type → worte/*.png
   Used by index (app.js), schreiben, pipeline shelf tiles.
   ===================================================================== */
'use strict';

const WASH = {
  'B1|der': 'B1_Der_Powdery-Blue_Horizontal-Soft.png',
  'B1|die': 'B1_Die_Powdery-Pink_BG-Wash.png',
  'B1|das': 'B1_Das_Pale-Green_BG-Wash.png',
  'B1|verb': 'B1_Verbs_Sandy-Ochre_BG-Wash.png',
  'B1|adj': 'B1_Adjectives_Lavender_BG-Wash.png',
  'B2|der': 'B2_Der_Deep-Blue_BG-Wash.png',
  'B2|die': 'B2_Die_Magenta_BG-Wash.png',
  'B2|das': 'B2_Das_Grass-Green_BG-Wash.png',
  'B2|verb': 'B2_Verbs_Terracotta_BG-Wash.png',
  'B2|adj': 'B2_Adjectives_Amethyst_BG-Wash.png',
  'C1|der': 'C1_Der_Indigo_BG-Wash.png',
  'C1|die': 'C1_Die_Burgundy_BG-Wash.png',
  'C1|das': 'C1_Das_Emerald_BG-Wash.png',
  'C1|verb': 'C1_Verbs_Olive-Ochre_BG-Wash.png',
  'C1|adj': 'C1_Adjectives_Plum_BG-Wash.png',
};

/* Stable subset cycled on pipeline topic shelf tiles */
const PIPELINE_WASHES = [
  'worte/B1_Adjectives_Lavender_BG-Wash.png',
  'worte/B1_Der_Powdery-Blue_Horizontal-Soft.png',
  'worte/B1_Die_Powdery-Pink_BG-Wash.png',
  'worte/B1_Das_Pale-Green_BG-Wash.png',
  'worte/B1_Verbs_Sandy-Ochre_BG-Wash.png',
  'worte/B2_Adjectives_Amethyst_BG-Wash.png',
  'worte/B2_Das_Grass-Green_BG-Wash.png',
  'worte/B2_Verbs_Terracotta_BG-Wash.png',
];

function typeKey(w) {
  return w.pos === 'verb' ? 'verb' : (w.pos === 'adj' ? 'adj' : w.art);
}

/* absolute URL — works from CSS custom properties, not stylesheet-relative */
function brushOf(w) {
  const f = WASH[w.level + '|' + typeKey(w)] || '';
  if (!f) return 'none';
  return `url('${new URL('worte/' + f, document.baseURI).href}')`;
}

/* Brush for a card coming from /api/vocab/* — it arrives with `band` and `type`
   already resolved server-side (app/vocab/norm.py), because the mapping is
   shared with search and the word list and must not drift between the two.
   The brush set only covers B1/B2/C1 × der/die/das/verb/adj, so the backend
   clamps every level into that band and every part of speech onto those five. */
function brushOfCard(card) {
  const f = WASH[card.band + '|' + card.type] || '';
  if (!f) return 'none';
  return `url('${new URL('worte/' + f, document.baseURI).href}')`;
}

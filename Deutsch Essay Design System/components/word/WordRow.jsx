import React from 'react';
import { LevelTag } from '../display/LevelTag.jsx';

/**
 * WASH — the signature brush map. Each entry is one real painted PNG, keyed
 * by CEFR level + grammatical type (der/die/das/verb/adj). The filenames are
 * the design-system brush assets.
 */
export const WASH = {
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

function typeKey({ pos, art }) {
  if (pos === 'verb') return 'verb';
  if (pos === 'adj') return 'adj';
  return art || 'die';
}

/**
 * WordRow — the heart of the brand. A dictionary entry painted with its own
 * watercolor brush (by level + word-type). The German word in serif, the
 * gloss italic beneath, a level tag at the right. On hover/active the hidden
 * continuation of the stroke is "drawn in" — the paint never moves, only
 * reveals. Set `brushBase` to the relative path of the brush folder from the
 * mounting page (default "assets/brushes/").
 */
export function WordRow({
  art = '',
  de,
  ru,
  pos = 'noun',
  level = 'B1',
  active = false,
  brushBase = 'assets/brushes/',
  onClick,
  style,
  ...rest
}) {
  const file = WASH[`${level}|${typeKey({ pos, art })}`] || WASH['B1|die'];
  const brush = `url('${brushBase}${file}')`;
  return (
    <div
      className={`de-wordrow${active ? ' is-active' : ''}`}
      onClick={onClick}
      style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '14px',
        padding: '13px 14px 13px 26px',
        cursor: 'pointer',
        borderRadius: 'var(--radius-lg)',
        minHeight: '64px',
        overflow: 'hidden',
        ['--brush']: brush,
        ...style,
      }}
      {...rest}
    >
      <span className="de-wordrow-wash" aria-hidden="true" style={{
        position: 'absolute', left: '-10px', top: '50%', transform: 'translateY(-50%)',
        width: '108%', height: '165%', zIndex: 0, pointerEvents: 'none',
        background: `var(--brush) no-repeat left center`, backgroundSize: '62% 118%',
        opacity: active ? 0.92 : 0.6,
        WebkitMaskImage: `linear-gradient(90deg,#000 0,#000 ${active ? '70%' : '12%'},rgba(0,0,0,.4) ${active ? '82%' : '30%'},transparent ${active ? '92%' : '46%'})`,
        maskImage: `linear-gradient(90deg,#000 0,#000 ${active ? '70%' : '12%'},rgba(0,0,0,.4) ${active ? '82%' : '30%'},transparent ${active ? '92%' : '46%'})`,
        transition: 'opacity var(--dur-slow) ease',
      }} />
      <div style={{ position: 'relative', zIndex: 1, flex: '1 1 auto', minWidth: 0, display: 'flex', flexDirection: 'column', gap: '3px' }}>
        <div style={{
          fontFamily: 'var(--font-serif)', fontSize: '26px', fontWeight: 500, lineHeight: 1.08,
          color: 'var(--ink)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          textShadow: '0 0 4px rgba(255,255,255,.4)',
        }}>
          {art ? <span style={{ fontWeight: 500 }}>{art} </span> : null}{de}
        </div>
        {ru ? (
          <div style={{
            fontFamily: 'var(--font-serif)', fontStyle: 'italic', fontSize: '18px', color: 'var(--ink-soft)',
            lineHeight: 1.25, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            textShadow: '0 0 7px rgba(255,255,255,.7)',
          }}>{ru}</div>
        ) : null}
      </div>
      <div style={{ position: 'relative', zIndex: 1, flex: 'none' }}>
        <LevelTag level={level} />
      </div>
    </div>
  );
}

export default WordRow;

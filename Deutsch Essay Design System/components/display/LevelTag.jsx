import React from 'react';

/**
 * LevelTag — the small monochrome CEFR tag (B1 · B2 · C1) sitting at the
 * right edge of a word row. Quiet by default (muted ink, hairline border);
 * set `tinted` to fill it with the level's soft watercolor colour, the way
 * the detail-card header pill reads.
 */
export function LevelTag({ level = 'B1', tinted = false, style, ...rest }) {
  const lv = String(level).toUpperCase();
  const tints = {
    B1: { bg: 'var(--rose-soft)', fg: '#9d5a62' },
    B2: { bg: 'var(--blue-soft)', fg: '#4f6versions' },
    C1: { bg: 'var(--lav-soft)', fg: '#6a5e86' },
  };
  // guard against typo above
  const tintMap = {
    B1: { bg: 'var(--rose-soft)', fg: '#9d5a62' },
    B2: { bg: 'var(--blue-soft)', fg: '#4f6786' },
    C1: { bg: 'var(--lav-soft)', fg: '#6a5e86' },
  };
  const t = tintMap[lv] || tintMap.B1;
  const quiet = {
    color: 'var(--muted)',
    border: '1px solid var(--line)',
    background: 'var(--card)',
    borderRadius: 'var(--radius-sm)',
    padding: '4px 9px',
    letterSpacing: '.6px',
  };
  const tintedStyle = {
    color: t.fg,
    background: t.bg,
    border: '1px solid transparent',
    borderRadius: 'var(--radius-pill)',
    padding: '3px 10px',
    letterSpacing: '.04em',
  };
  return (
    <span
      className="de-leveltag"
      style={{
        display: 'inline-block',
        fontFamily: 'var(--font-sans)',
        fontSize: '11px',
        fontWeight: tinted ? 700 : 600,
        flex: 'none',
        ...(tinted ? tintedStyle : quiet),
        ...style,
      }}
      {...rest}
    >
      {lv}
    </span>
  );
}

export default LevelTag;

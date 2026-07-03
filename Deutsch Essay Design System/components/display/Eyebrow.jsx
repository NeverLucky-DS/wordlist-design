import React from 'react';

/**
 * Eyebrow — the small uppercase, wide-tracked label that sits above a title
 * or section. Accent-orange by default (the editorial kicker); pass
 * tone="muted" for the quieter rail/label voice.
 */
export function Eyebrow({ children, tone = 'accent', style, ...rest }) {
  const colors = {
    accent: 'var(--accent)',
    muted: 'var(--muted)',
    rose: 'var(--rose)',
    ink: 'var(--ink-soft)',
  };
  return (
    <div
      className="de-eyebrow"
      style={{
        fontFamily: 'var(--font-sans)',
        fontSize: '11px',
        letterSpacing: '.22em',
        textTransform: 'uppercase',
        fontWeight: 700,
        color: colors[tone] || colors.accent,
        ...style,
      }}
      {...rest}
    >
      {children}
    </div>
  );
}

export default Eyebrow;

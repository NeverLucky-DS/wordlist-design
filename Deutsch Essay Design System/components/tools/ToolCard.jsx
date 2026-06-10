import React from 'react';

/**
 * ToolCard — the right-rail tool wrapper from the editor. A titled paper
 * panel: a small uppercase label (with an optional accent fragment via
 * `accent`), an optional action node on the right, then the body. Used for
 * Klischees, the inline Wörterbuch, and any side tool.
 */
export function ToolCard({
  title,
  accent,
  action,
  children,
  style,
  bodyStyle,
  ...rest
}) {
  return (
    <section
      className="de-toolcard"
      style={{
        background: 'var(--card)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-md)',
        overflow: 'hidden',
        ...style,
      }}
      {...rest}
    >
      {(title || action) ? (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 18px 12px',
        }}>
          <div style={{
            fontFamily: 'var(--font-sans)', fontSize: '10.5px', letterSpacing: '.16em',
            textTransform: 'uppercase', color: 'var(--ink-mute)', fontWeight: 700,
          }}>
            {title}{accent ? <span style={{ color: 'var(--accent-dk)' }}> · {accent}</span> : null}
          </div>
          {action || null}
        </div>
      ) : null}
      <div style={{ padding: '0 16px 16px', ...bodyStyle }}>{children}</div>
    </section>
  );
}

export default ToolCard;

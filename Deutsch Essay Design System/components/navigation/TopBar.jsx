import React from 'react';
import { Avatar } from '../display/Avatar.jsx';

const { useState } = React;

const Chevron = ({ size = 11 }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" width={size} height={size} style={{ opacity: 0.65 }}>
    <path d="M6 9l6 6 6-6" />
  </svg>
);

const Sun = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" width="18" height="18">
    <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </svg>
);

/* one editorial nav link — uppercase, tracked, quiet active tick */
function NavLink({ it, i, onNavClick }) {
  const [hover, setHover] = useState(false);
  const active = it.active;
  return (
    <button
      type="button"
      onClick={() => onNavClick && onNavClick(it, i)}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      className={`de-navitem${active ? ' is-active' : ''}`}
      style={{
        position: 'relative',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        color: active || hover ? 'var(--ink)' : 'var(--ink-mute)',
        fontSize: '11.5px',
        fontWeight: 600,
        letterSpacing: '.15em',
        textTransform: 'uppercase',
        fontFamily: 'var(--font-sans)',
        padding: '22px 1px',
        border: 0,
        background: 'none',
        cursor: 'pointer',
        transition: 'color var(--dur-base)',
      }}
    >
      {it.label}
      {it.dropdown ? <Chevron size={10} /> : null}
      <span
        aria-hidden="true"
        style={{
          position: 'absolute', left: 0, right: 0, bottom: 0, height: '2px', borderRadius: '2px',
          background: active ? 'linear-gradient(90deg, var(--accent), var(--accent-2))' : 'var(--muted-2)',
          opacity: active ? 1 : (hover ? 0.55 : 0),
          transform: `scaleX(${active ? 1 : (hover ? 1 : 0.3)})`,
          transformOrigin: 'center',
          transition: 'opacity var(--dur-base), transform var(--dur-base)',
        }}
      />
    </button>
  );
}

/* ghost icon button — no chrome at rest, faint bed on hover */
function GhostIcon({ label, children }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      aria-label={label}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center',
        borderRadius: 'var(--radius-md)', border: 0, cursor: 'pointer',
        background: hover ? 'var(--cream)' : 'transparent',
        color: hover ? 'var(--ink)' : 'var(--ink-mute)',
        transition: 'color var(--dur-base), background var(--dur-base)',
      }}
    >
      {children}
    </button>
  );
}

/* plain-text language toggle (no pill box) */
function LangToggle({ lang }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: '5px', padding: '8px 4px', height: '36px',
        border: 0, background: 'none', cursor: 'pointer',
        color: hover ? 'var(--ink)' : 'var(--ink-soft)',
        fontSize: '11.5px', fontWeight: 700, letterSpacing: '.12em', fontFamily: 'var(--font-sans)',
        transition: 'color var(--dur-base)',
      }}
    >
      {lang}<Chevron size={10} />
    </button>
  );
}

/**
 * TopBar — the shared site header, identical across the Wörterbuch and the
 * Editor. A left-aligned editorial masthead: a two-tone serif wordmark, a
 * hairline rule, then uppercase letter-tracked nav with a quiet active tick.
 * The right cluster (theme · language · avatar) stays minimal and neutral.
 * Sticky, frosted ivory, hairline base.
 */
export function TopBar({
  brand = ['Deutsch', 'Essay'],
  items = [],
  onNavClick,
  right,
  lang = 'DE',
  initial = 'D',
  style,
  ...rest
}) {
  const [w0, ...wRest] = brand;
  const w1 = wRest.join(' ');
  return (
    <header
      className="de-topbar"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        gap: 0,
        padding: '0 38px',
        height: '66px',
        background: 'rgba(250,248,244,.85)',
        WebkitBackdropFilter: 'saturate(150%) blur(16px)',
        backdropFilter: 'saturate(150%) blur(16px)',
        borderBottom: '1px solid var(--line)',
        ...style,
      }}
      {...rest}
    >
      <a
        href="#"
        className="de-brand"
        style={{
          display: 'flex', alignItems: 'baseline', gap: '14px',
          fontFamily: 'var(--font-serif)', lineHeight: 1, textDecoration: 'none', flex: 'none',
        }}
      >
        <span style={{ fontSize: '23px', fontWeight: 600, color: 'var(--ink)', letterSpacing: '.2px' }}>{w0}</span>
        {w1 ? <span style={{ fontSize: '23px', fontWeight: 500, fontStyle: 'italic', color: 'var(--ink-soft)' }}>{w1}</span> : null}
      </a>

      <span aria-hidden="true" style={{ width: '1px', height: '26px', background: 'var(--line)', margin: '0 26px', flex: 'none' }} />

      <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
        {items.map((it, i) => <NavLink key={i} it={it} i={i} onNavClick={onNavClick} />)}
      </nav>

      <div style={{ flex: 1 }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 'none' }}>
        {right !== undefined ? right : (
          <React.Fragment>
            <GhostIcon label="Theme"><Sun /></GhostIcon>
            <LangToggle lang={lang} />
            <span aria-hidden="true" style={{ width: '1px', height: '22px', background: 'var(--line)', margin: '0 8px' }} />
            <Avatar initial={initial} />
          </React.Fragment>
        )}
      </div>
    </header>
  );
}

export default TopBar;

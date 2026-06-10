import React from 'react';

/**
 * Select — the pill dropdown button used across the meta strip and niveau
 * controls. A small tracked key ("THEMA"), the current value in semibold,
 * and a chevron. This renders the trigger; wire your own menu/state.
 */
export function Select({
  label,
  value,
  open = false,
  onClick,
  style,
  ...rest
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="de-select"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        height: '38px',
        padding: '0 13px',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--line)',
        background: 'var(--card)',
        color: 'var(--ink)',
        fontFamily: 'var(--font-sans)',
        fontSize: '13.5px',
        fontWeight: 600,
        cursor: 'pointer',
        transition: 'border-color var(--dur-base), box-shadow var(--dur-base)',
        ...style,
      }}
      {...rest}
    >
      {label ? (
        <span style={{
          fontSize: '9.5px',
          letterSpacing: '.16em',
          textTransform: 'uppercase',
          color: 'var(--muted)',
          fontWeight: 700,
          marginRight: '2px',
        }}>{label}</span>
      ) : null}
      <span>{value}</span>
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
        style={{ opacity: 0.6, transform: open ? 'rotate(180deg)' : 'none', transition: 'transform var(--dur-base)' }}>
        <path d="M6 9l6 6 6-6" />
      </svg>
    </button>
  );
}

export default Select;

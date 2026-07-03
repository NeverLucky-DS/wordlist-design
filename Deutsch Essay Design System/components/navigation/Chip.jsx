import React from 'react';

/**
 * Chip — a category filter. Quiet white pill with a hairline at rest; when
 * `active` it fills graphite, grows a touch and lifts. Use a row of these as
 * a single-select filter (the dictionary categories).
 */
export function Chip({ children, active = false, onClick, style, ...rest }) {
  const base = {
    fontFamily: 'var(--font-sans)',
    fontWeight: 500,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    border: '1px solid var(--line)',
    transition: 'transform var(--dur-base) var(--ease-out), box-shadow var(--dur-base), background var(--dur-base), color var(--dur-base), border-color var(--dur-base)',
  };
  const rest_ = {
    background: 'var(--card)',
    color: 'var(--ink-soft)',
    padding: '9px 16px',
    borderRadius: 'var(--radius-lg)',
    fontSize: '13.5px',
    boxShadow: 'var(--shadow-xs)',
  };
  const on = {
    background: 'var(--graphite)',
    color: '#fff',
    borderColor: 'var(--graphite)',
    padding: '12px 22px',
    borderRadius: 'var(--radius-lg)',
    fontSize: '14.5px',
    boxShadow: '0 12px 26px -12px rgba(51,51,58,.55)',
  };
  return (
    <button
      type="button"
      onClick={onClick}
      className={`de-chip${active ? ' is-active' : ''}`}
      style={{ ...base, ...(active ? on : rest_), ...style }}
      {...rest}
    >
      {children}
    </button>
  );
}

export default Chip;

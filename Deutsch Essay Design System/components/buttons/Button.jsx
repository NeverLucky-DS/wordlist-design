import React from 'react';

/**
 * Button — the brand's primary action control.
 *
 * Three variants:
 *  · primary  — muted plum gradient, white text, accent glow. The one
 *               loud element on a page; use sparingly (one per view).
 *  · secondary— white paper, hairline border that warms to accent on hover.
 *  · ghost    — quiet sunk chip, no border, for tertiary actions.
 * Two sizes (md default, lg for hero CTAs). Optional leading icon node.
 */
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  icon = null,
  disabled = false,
  type = 'button',
  onClick,
  style,
  ...rest
}) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    fontFamily: 'var(--font-sans)',
    fontWeight: 600,
    letterSpacing: '.2px',
    border: '1px solid transparent',
    cursor: disabled ? 'default' : 'pointer',
    whiteSpace: 'nowrap',
    transition: 'transform var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out), border-color var(--dur-base), color var(--dur-base), background var(--dur-base)',
    opacity: disabled ? 0.55 : 1,
  };

  const sizes = {
    md: { height: '46px', padding: '0 22px', fontSize: '14px', borderRadius: 'var(--radius-md)' },
    lg: { height: '50px', padding: '0 30px', fontSize: '15px', borderRadius: 'var(--radius-lg)' },
  };

  const variants = {
    primary: {
      color: 'var(--text-on-accent)',
      background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%)',
      boxShadow: disabled ? 'none' : 'var(--shadow-accent)',
    },
    secondary: {
      color: 'var(--ink)',
      background: 'var(--card)',
      borderColor: 'var(--line)',
      boxShadow: 'var(--shadow-xs)',
    },
    ghost: {
      color: 'var(--ink-soft)',
      background: 'transparent',
    },
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`de-btn de-btn--${variant}`}
      style={{ ...base, ...sizes[size], ...variants[variant], ...style }}
      {...rest}
    >
      {icon ? <span style={{ display: 'inline-flex', width: '18px', height: '18px' }}>{icon}</span> : null}
      {children}
    </button>
  );
}

export default Button;

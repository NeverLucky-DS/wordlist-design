import React from 'react';

/**
 * IconButton — a square, hairline-bordered control holding a single icon.
 * Used for theme toggles, folder, notes, pager arrows. Warms to accent on
 * hover. Pass an SVG (or any node) as children.
 */
export function IconButton({
  children,
  size = 'md',
  label,
  disabled = false,
  onClick,
  style,
  ...rest
}) {
  const dims = { sm: 28, md: 38, lg: 46 }[size] || 38;
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="de-iconbtn"
      style={{
        width: `${dims}px`,
        height: `${dims}px`,
        flex: 'none',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--line)',
        background: 'var(--card)',
        color: 'var(--ink-soft)',
        cursor: disabled ? 'default' : 'pointer',
        opacity: disabled ? 0.4 : 1,
        transition: 'border-color var(--dur-base), color var(--dur-base), box-shadow var(--dur-base)',
        ...style,
      }}
      {...rest}
    >
      {children}
    </button>
  );
}

export default IconButton;

import React from 'react';

/**
 * SearchField — the brand's text input, framed as a search. A leading icon,
 * generous height, soft hairline that lights to accent with a focus ring.
 * Works as a plain text field too (omit the icon).
 */
export function SearchField({
  value,
  onChange,
  placeholder = 'Suche…',
  icon,
  size = 'md',
  style,
  ...rest
}) {
  const heights = { sm: '40px', md: '52px' };
  const radii = { sm: 'var(--radius-md)', md: 'var(--radius-lg)' };
  const defaultIcon = (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
  const showIcon = icon === undefined ? defaultIcon : icon;
  return (
    <label
      className="de-search"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '11px',
        background: 'var(--card)',
        border: '1px solid var(--line)',
        borderRadius: radii[size],
        padding: '0 18px',
        height: heights[size],
        transition: 'border-color var(--dur-base), box-shadow var(--dur-base)',
        ...style,
      }}
    >
      {showIcon ? <span style={{ color: 'var(--muted)', flex: 'none', display: 'inline-flex' }}>{showIcon}</span> : null}
      <input
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        style={{
          flex: 1,
          minWidth: 0,
          border: 0,
          outline: 0,
          background: 'transparent',
          fontFamily: 'var(--font-sans)',
          fontSize: size === 'sm' ? '13.5px' : '14.5px',
          color: 'var(--ink)',
        }}
        {...rest}
      />
    </label>
  );
}

export default SearchField;

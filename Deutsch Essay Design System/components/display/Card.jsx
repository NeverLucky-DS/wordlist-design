import React from 'react';

/**
 * Card — a sheet of raised paper. White surface, hairline border, soft warm
 * shadow, generous rounding. The default container for everything that lifts
 * off the page. `elevation` picks the shadow; `pad` toggles inner padding.
 */
export function Card({
  children,
  elevation = 'md',
  pad = true,
  radius = 'xl',
  style,
  ...rest
}) {
  const shadows = {
    flat: 'none',
    sm: 'var(--shadow-sm)',
    md: 'var(--shadow-md)',
    lg: 'var(--shadow-lg)',
    sheet: 'var(--shadow-sheet)',
  };
  const radii = {
    lg: 'var(--radius-lg)',
    xl: 'var(--radius-xl)',
    '2xl': 'var(--radius-2xl)',
  };
  return (
    <div
      className="de-card"
      style={{
        background: 'var(--card)',
        border: '1px solid var(--line)',
        borderRadius: radii[radius] || radii.xl,
        boxShadow: shadows[elevation],
        padding: pad ? '24px' : 0,
        ...style,
      }}
      {...rest}
    >
      {children}
    </div>
  );
}

export default Card;

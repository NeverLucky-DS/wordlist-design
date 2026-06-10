import React from 'react';

/**
 * ProgressBar — the writing-goal track. A thin rounded rail with the warm
 * accent gradient fill. Optionally renders the serif count cap above it
 * ("83 / 250 Wörter").
 */
export function ProgressBar({
  value = 0,
  max = 100,
  label,
  showCount = false,
  unit = 'Wörter',
  style,
  ...rest
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="de-progress" style={style} {...rest}>
      {(label || showCount) ? (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '10px' }}>
          {label ? (
            <span style={{
              fontFamily: 'var(--font-sans)', fontSize: '10px', letterSpacing: '.2em',
              textTransform: 'uppercase', color: 'var(--muted)', fontWeight: 700,
            }}>{label}</span>
          ) : <span />}
          {showCount ? (
            <span style={{ fontFamily: 'var(--font-serif)', fontSize: '22px', fontWeight: 600, color: 'var(--ink)' }}>
              {value}<span style={{ color: 'var(--muted)', fontSize: '15px' }}> / {max} {unit}</span>
            </span>
          ) : null}
        </div>
      ) : null}
      <div style={{ height: '6px', borderRadius: '6px', background: 'var(--line)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${pct}%`, borderRadius: '6px',
          background: 'linear-gradient(90deg, var(--accent), var(--accent-2))',
          transition: 'width var(--dur-slow) var(--ease-out)',
        }} />
      </div>
    </div>
  );
}

export default ProgressBar;

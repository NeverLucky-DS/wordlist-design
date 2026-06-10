import React from 'react';

/**
 * Avatar — a graphite circle holding a serif initial. The user mark in the
 * top bar. Size is in px; the initial scales with it.
 */
export function Avatar({ initial = 'D', size = 38, style, ...rest }) {
  return (
    <div
      className="de-avatar"
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: 'var(--radius-pill)',
        background: 'var(--graphite)',
        color: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'var(--font-serif)',
        fontSize: `${Math.round(size * 0.45)}px`,
        fontWeight: 600,
        flex: 'none',
        ...style,
      }}
      {...rest}
    >
      {initial}
    </div>
  );
}

export default Avatar;

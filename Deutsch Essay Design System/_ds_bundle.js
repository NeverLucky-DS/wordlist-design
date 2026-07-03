/* @ds-bundle: {"format":3,"namespace":"DeutschEssayDesignSystem_3bc91c","components":[{"name":"Button","sourcePath":"components/buttons/Button.jsx"},{"name":"IconButton","sourcePath":"components/buttons/IconButton.jsx"},{"name":"Avatar","sourcePath":"components/display/Avatar.jsx"},{"name":"Card","sourcePath":"components/display/Card.jsx"},{"name":"Eyebrow","sourcePath":"components/display/Eyebrow.jsx"},{"name":"LevelTag","sourcePath":"components/display/LevelTag.jsx"},{"name":"SearchField","sourcePath":"components/forms/SearchField.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Chip","sourcePath":"components/navigation/Chip.jsx"},{"name":"TopBar","sourcePath":"components/navigation/TopBar.jsx"},{"name":"ProgressBar","sourcePath":"components/tools/ProgressBar.jsx"},{"name":"ToolCard","sourcePath":"components/tools/ToolCard.jsx"},{"name":"WASH","sourcePath":"components/word/WordRow.jsx"},{"name":"WordRow","sourcePath":"components/word/WordRow.jsx"}],"sourceHashes":{"components/buttons/Button.jsx":"d37a2e9238ea","components/buttons/IconButton.jsx":"d568caf2f58a","components/display/Avatar.jsx":"153b205ce0d8","components/display/Card.jsx":"61f4ff4b6e07","components/display/Eyebrow.jsx":"d302e2346ec1","components/display/LevelTag.jsx":"573f8c348d69","components/forms/SearchField.jsx":"3c8cdc23c9c1","components/forms/Select.jsx":"2db92371d545","components/navigation/Chip.jsx":"15ccef06e170","components/navigation/TopBar.jsx":"37e2ca6f47a5","components/tools/ProgressBar.jsx":"076a3fdee3b3","components/tools/ToolCard.jsx":"a19f5b51ce27","components/word/WordRow.jsx":"51372f586ba8","ui_kits/editor/Editor.jsx":"78971c418d9a","ui_kits/woerterbuch/Woerterbuch.jsx":"f73b4e85172f","ui_kits/woerterbuch/tweaks-panel.jsx":"6591467622ed"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.DeutschEssayDesignSystem_3bc91c = window.DeutschEssayDesignSystem_3bc91c || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/buttons/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
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
function Button({
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
    opacity: disabled ? 0.55 : 1
  };
  const sizes = {
    md: {
      height: '46px',
      padding: '0 22px',
      fontSize: '14px',
      borderRadius: 'var(--radius-md)'
    },
    lg: {
      height: '50px',
      padding: '0 30px',
      fontSize: '15px',
      borderRadius: 'var(--radius-lg)'
    }
  };
  const variants = {
    primary: {
      color: 'var(--text-on-accent)',
      background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%)',
      boxShadow: disabled ? 'none' : 'var(--shadow-accent)'
    },
    secondary: {
      color: 'var(--ink)',
      background: 'var(--card)',
      borderColor: 'var(--line)',
      boxShadow: 'var(--shadow-xs)'
    },
    ghost: {
      color: 'var(--ink-soft)',
      background: 'transparent'
    }
  };
  return /*#__PURE__*/React.createElement("button", _extends({
    type: type,
    disabled: disabled,
    onClick: onClick,
    className: `de-btn de-btn--${variant}`,
    style: {
      ...base,
      ...sizes[size],
      ...variants[variant],
      ...style
    }
  }, rest), icon ? /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      width: '18px',
      height: '18px'
    }
  }, icon) : null, children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/buttons/Button.jsx", error: String((e && e.message) || e) }); }

// components/buttons/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * IconButton — a square, hairline-bordered control holding a single icon.
 * Used for theme toggles, folder, notes, pager arrows. Warms to accent on
 * hover. Pass an SVG (or any node) as children.
 */
function IconButton({
  children,
  size = 'md',
  label,
  disabled = false,
  onClick,
  style,
  ...rest
}) {
  const dims = {
    sm: 28,
    md: 38,
    lg: 46
  }[size] || 38;
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    "aria-label": label,
    disabled: disabled,
    onClick: onClick,
    className: "de-iconbtn",
    style: {
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
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/buttons/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/display/Avatar.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Avatar — a graphite circle holding a serif initial. The user mark in the
 * top bar. Size is in px; the initial scales with it.
 */
function Avatar({
  initial = 'D',
  size = 38,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: "de-avatar",
    style: {
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
      ...style
    }
  }, rest), initial);
}
Object.assign(__ds_scope, { Avatar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/display/Avatar.jsx", error: String((e && e.message) || e) }); }

// components/display/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Card — a sheet of raised paper. White surface, hairline border, soft warm
 * shadow, generous rounding. The default container for everything that lifts
 * off the page. `elevation` picks the shadow; `pad` toggles inner padding.
 */
function Card({
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
    sheet: 'var(--shadow-sheet)'
  };
  const radii = {
    lg: 'var(--radius-lg)',
    xl: 'var(--radius-xl)',
    '2xl': 'var(--radius-2xl)'
  };
  return /*#__PURE__*/React.createElement("div", _extends({
    className: "de-card",
    style: {
      background: 'var(--card)',
      border: '1px solid var(--line)',
      borderRadius: radii[radius] || radii.xl,
      boxShadow: shadows[elevation],
      padding: pad ? '24px' : 0,
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/display/Card.jsx", error: String((e && e.message) || e) }); }

// components/display/Eyebrow.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Eyebrow — the small uppercase, wide-tracked label that sits above a title
 * or section. Accent-orange by default (the editorial kicker); pass
 * tone="muted" for the quieter rail/label voice.
 */
function Eyebrow({
  children,
  tone = 'accent',
  style,
  ...rest
}) {
  const colors = {
    accent: 'var(--accent)',
    muted: 'var(--muted)',
    rose: 'var(--rose)',
    ink: 'var(--ink-soft)'
  };
  return /*#__PURE__*/React.createElement("div", _extends({
    className: "de-eyebrow",
    style: {
      fontFamily: 'var(--font-sans)',
      fontSize: '11px',
      letterSpacing: '.22em',
      textTransform: 'uppercase',
      fontWeight: 700,
      color: colors[tone] || colors.accent,
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Eyebrow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/display/Eyebrow.jsx", error: String((e && e.message) || e) }); }

// components/display/LevelTag.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * LevelTag — the small monochrome CEFR tag (B1 · B2 · C1) sitting at the
 * right edge of a word row. Quiet by default (muted ink, hairline border);
 * set `tinted` to fill it with the level's soft watercolor colour, the way
 * the detail-card header pill reads.
 */
function LevelTag({
  level = 'B1',
  tinted = false,
  style,
  ...rest
}) {
  const lv = String(level).toUpperCase();
  const tints = {
    B1: {
      bg: 'var(--rose-soft)',
      fg: '#9d5a62'
    },
    B2: {
      bg: 'var(--blue-soft)',
      fg: '#4f6versions'
    },
    C1: {
      bg: 'var(--lav-soft)',
      fg: '#6a5e86'
    }
  };
  // guard against typo above
  const tintMap = {
    B1: {
      bg: 'var(--rose-soft)',
      fg: '#9d5a62'
    },
    B2: {
      bg: 'var(--blue-soft)',
      fg: '#4f6786'
    },
    C1: {
      bg: 'var(--lav-soft)',
      fg: '#6a5e86'
    }
  };
  const t = tintMap[lv] || tintMap.B1;
  const quiet = {
    color: 'var(--muted)',
    border: '1px solid var(--line)',
    background: 'var(--card)',
    borderRadius: 'var(--radius-sm)',
    padding: '4px 9px',
    letterSpacing: '.6px'
  };
  const tintedStyle = {
    color: t.fg,
    background: t.bg,
    border: '1px solid transparent',
    borderRadius: 'var(--radius-pill)',
    padding: '3px 10px',
    letterSpacing: '.04em'
  };
  return /*#__PURE__*/React.createElement("span", _extends({
    className: "de-leveltag",
    style: {
      display: 'inline-block',
      fontFamily: 'var(--font-sans)',
      fontSize: '11px',
      fontWeight: tinted ? 700 : 600,
      flex: 'none',
      ...(tinted ? tintedStyle : quiet),
      ...style
    }
  }, rest), lv);
}
Object.assign(__ds_scope, { LevelTag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/display/LevelTag.jsx", error: String((e && e.message) || e) }); }

// components/forms/SearchField.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * SearchField — the brand's text input, framed as a search. A leading icon,
 * generous height, soft hairline that lights to accent with a focus ring.
 * Works as a plain text field too (omit the icon).
 */
function SearchField({
  value,
  onChange,
  placeholder = 'Suche…',
  icon,
  size = 'md',
  style,
  ...rest
}) {
  const heights = {
    sm: '40px',
    md: '52px'
  };
  const radii = {
    sm: 'var(--radius-md)',
    md: 'var(--radius-lg)'
  };
  const defaultIcon = /*#__PURE__*/React.createElement("svg", {
    width: "20",
    height: "20",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "11",
    cy: "11",
    r: "7"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "21",
    y1: "21",
    x2: "16.65",
    y2: "16.65"
  }));
  const showIcon = icon === undefined ? defaultIcon : icon;
  return /*#__PURE__*/React.createElement("label", {
    className: "de-search",
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '11px',
      background: 'var(--card)',
      border: '1px solid var(--line)',
      borderRadius: radii[size],
      padding: '0 18px',
      height: heights[size],
      transition: 'border-color var(--dur-base), box-shadow var(--dur-base)',
      ...style
    }
  }, showIcon ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--muted)',
      flex: 'none',
      display: 'inline-flex'
    }
  }, showIcon) : null, /*#__PURE__*/React.createElement("input", _extends({
    type: "text",
    value: value,
    onChange: onChange,
    placeholder: placeholder,
    style: {
      flex: 1,
      minWidth: 0,
      border: 0,
      outline: 0,
      background: 'transparent',
      fontFamily: 'var(--font-sans)',
      fontSize: size === 'sm' ? '13.5px' : '14.5px',
      color: 'var(--ink)'
    }
  }, rest)));
}
Object.assign(__ds_scope, { SearchField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/SearchField.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Select — the pill dropdown button used across the meta strip and niveau
 * controls. A small tracked key ("THEMA"), the current value in semibold,
 * and a chevron. This renders the trigger; wire your own menu/state.
 */
function Select({
  label,
  value,
  open = false,
  onClick,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    onClick: onClick,
    className: "de-select",
    style: {
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
      ...style
    }
  }, rest), label ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: '9.5px',
      letterSpacing: '.16em',
      textTransform: 'uppercase',
      color: 'var(--muted)',
      fontWeight: 700,
      marginRight: '2px'
    }
  }, label) : null, /*#__PURE__*/React.createElement("span", null, value), /*#__PURE__*/React.createElement("svg", {
    width: "13",
    height: "13",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    style: {
      opacity: 0.6,
      transform: open ? 'rotate(180deg)' : 'none',
      transition: 'transform var(--dur-base)'
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M6 9l6 6 6-6"
  })));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Chip.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Chip — a category filter. Quiet white pill with a hairline at rest; when
 * `active` it fills graphite, grows a touch and lifts. Use a row of these as
 * a single-select filter (the dictionary categories).
 */
function Chip({
  children,
  active = false,
  onClick,
  style,
  ...rest
}) {
  const base = {
    fontFamily: 'var(--font-sans)',
    fontWeight: 500,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    border: '1px solid var(--line)',
    transition: 'transform var(--dur-base) var(--ease-out), box-shadow var(--dur-base), background var(--dur-base), color var(--dur-base), border-color var(--dur-base)'
  };
  const rest_ = {
    background: 'var(--card)',
    color: 'var(--ink-soft)',
    padding: '9px 16px',
    borderRadius: 'var(--radius-lg)',
    fontSize: '13.5px',
    boxShadow: 'var(--shadow-xs)'
  };
  const on = {
    background: 'var(--graphite)',
    color: '#fff',
    borderColor: 'var(--graphite)',
    padding: '12px 22px',
    borderRadius: 'var(--radius-lg)',
    fontSize: '14.5px',
    boxShadow: '0 12px 26px -12px rgba(51,51,58,.55)'
  };
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    onClick: onClick,
    className: `de-chip${active ? ' is-active' : ''}`,
    style: {
      ...base,
      ...(active ? on : rest_),
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Chip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Chip.jsx", error: String((e && e.message) || e) }); }

// components/navigation/TopBar.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState
} = React;
const Chevron = ({
  size = 11
}) => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2.2",
  width: size,
  height: size,
  style: {
    opacity: 0.65
  }
}, /*#__PURE__*/React.createElement("path", {
  d: "M6 9l6 6 6-6"
}));
const Sun = () => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "1.9",
  strokeLinecap: "round",
  width: "18",
  height: "18"
}, /*#__PURE__*/React.createElement("circle", {
  cx: "12",
  cy: "12",
  r: "4"
}), /*#__PURE__*/React.createElement("path", {
  d: "M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"
}));

/* one editorial nav link — uppercase, tracked, quiet active tick */
function NavLink({
  it,
  i,
  onNavClick
}) {
  const [hover, setHover] = useState(false);
  const active = it.active;
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => onNavClick && onNavClick(it, i),
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    className: `de-navitem${active ? ' is-active' : ''}`,
    style: {
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
      transition: 'color var(--dur-base)'
    }
  }, it.label, it.dropdown ? /*#__PURE__*/React.createElement(Chevron, {
    size: 10
  }) : null, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      position: 'absolute',
      left: 0,
      right: 0,
      bottom: 0,
      height: '2px',
      borderRadius: '2px',
      background: active ? 'linear-gradient(90deg, var(--accent), var(--accent-2))' : 'var(--muted-2)',
      opacity: active ? 1 : hover ? 0.55 : 0,
      transform: `scaleX(${active ? 1 : hover ? 1 : 0.3})`,
      transformOrigin: 'center',
      transition: 'opacity var(--dur-base), transform var(--dur-base)'
    }
  }));
}

/* ghost icon button — no chrome at rest, faint bed on hover */
function GhostIcon({
  label,
  children
}) {
  const [hover, setHover] = useState(false);
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    "aria-label": label,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      width: '36px',
      height: '36px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 'var(--radius-md)',
      border: 0,
      cursor: 'pointer',
      background: hover ? 'var(--cream)' : 'transparent',
      color: hover ? 'var(--ink)' : 'var(--ink-mute)',
      transition: 'color var(--dur-base), background var(--dur-base)'
    }
  }, children);
}

/* plain-text language toggle (no pill box) */
function LangToggle({
  lang
}) {
  const [hover, setHover] = useState(false);
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '5px',
      padding: '8px 4px',
      height: '36px',
      border: 0,
      background: 'none',
      cursor: 'pointer',
      color: hover ? 'var(--ink)' : 'var(--ink-soft)',
      fontSize: '11.5px',
      fontWeight: 700,
      letterSpacing: '.12em',
      fontFamily: 'var(--font-sans)',
      transition: 'color var(--dur-base)'
    }
  }, lang, /*#__PURE__*/React.createElement(Chevron, {
    size: 10
  }));
}

/**
 * TopBar — the shared site header, identical across the Wörterbuch and the
 * Editor. A left-aligned editorial masthead: a two-tone serif wordmark, a
 * hairline rule, then uppercase letter-tracked nav with a quiet active tick.
 * The right cluster (theme · language · avatar) stays minimal and neutral.
 * Sticky, frosted ivory, hairline base.
 */
function TopBar({
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
  return /*#__PURE__*/React.createElement("header", _extends({
    className: "de-topbar",
    style: {
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
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("a", {
    href: "#",
    className: "de-brand",
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: '14px',
      fontFamily: 'var(--font-serif)',
      lineHeight: 1,
      textDecoration: 'none',
      flex: 'none'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: '23px',
      fontWeight: 600,
      color: 'var(--ink)',
      letterSpacing: '.2px'
    }
  }, w0), w1 ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: '23px',
      fontWeight: 500,
      fontStyle: 'italic',
      color: 'var(--ink-soft)'
    }
  }, w1) : null), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: '1px',
      height: '26px',
      background: 'var(--line)',
      margin: '0 26px',
      flex: 'none'
    }
  }), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '28px'
    }
  }, items.map((it, i) => /*#__PURE__*/React.createElement(NavLink, {
    key: i,
    it: it,
    i: i,
    onNavClick: onNavClick
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      flex: 'none'
    }
  }, right !== undefined ? right : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(GhostIcon, {
    label: "Theme"
  }, /*#__PURE__*/React.createElement(Sun, null)), /*#__PURE__*/React.createElement(LangToggle, {
    lang: lang
  }), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: '1px',
      height: '22px',
      background: 'var(--line)',
      margin: '0 8px'
    }
  }), /*#__PURE__*/React.createElement(__ds_scope.Avatar, {
    initial: initial
  }))));
}
Object.assign(__ds_scope, { TopBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/TopBar.jsx", error: String((e && e.message) || e) }); }

// components/tools/ProgressBar.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * ProgressBar — the writing-goal track. A thin rounded rail with the warm
 * accent gradient fill. Optionally renders the serif count cap above it
 * ("83 / 250 Wörter").
 */
function ProgressBar({
  value = 0,
  max = 100,
  label,
  showCount = false,
  unit = 'Wörter',
  style,
  ...rest
}) {
  const pct = Math.max(0, Math.min(100, value / max * 100));
  return /*#__PURE__*/React.createElement("div", _extends({
    className: "de-progress",
    style: style
  }, rest), label || showCount ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline',
      marginBottom: '10px'
    }
  }, label ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-sans)',
      fontSize: '10px',
      letterSpacing: '.2em',
      textTransform: 'uppercase',
      color: 'var(--muted)',
      fontWeight: 700
    }
  }, label) : /*#__PURE__*/React.createElement("span", null), showCount ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontSize: '22px',
      fontWeight: 600,
      color: 'var(--ink)'
    }
  }, value, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--muted)',
      fontSize: '15px'
    }
  }, " / ", max, " ", unit)) : null) : null, /*#__PURE__*/React.createElement("div", {
    style: {
      height: '6px',
      borderRadius: '6px',
      background: 'var(--line)',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: '100%',
      width: `${pct}%`,
      borderRadius: '6px',
      background: 'linear-gradient(90deg, var(--accent), var(--accent-2))',
      transition: 'width var(--dur-slow) var(--ease-out)'
    }
  })));
}
Object.assign(__ds_scope, { ProgressBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/tools/ProgressBar.jsx", error: String((e && e.message) || e) }); }

// components/tools/ToolCard.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * ToolCard — the right-rail tool wrapper from the editor. A titled paper
 * panel: a small uppercase label (with an optional accent fragment via
 * `accent`), an optional action node on the right, then the body. Used for
 * Klischees, the inline Wörterbuch, and any side tool.
 */
function ToolCard({
  title,
  accent,
  action,
  children,
  style,
  bodyStyle,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("section", _extends({
    className: "de-toolcard",
    style: {
      background: 'var(--card)',
      border: '1px solid var(--line)',
      borderRadius: 'var(--radius-xl)',
      boxShadow: 'var(--shadow-md)',
      overflow: 'hidden',
      ...style
    }
  }, rest), title || action ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 18px 12px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-sans)',
      fontSize: '10.5px',
      letterSpacing: '.16em',
      textTransform: 'uppercase',
      color: 'var(--ink-mute)',
      fontWeight: 700
    }
  }, title, accent ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--accent-dk)'
    }
  }, " \xB7 ", accent) : null), action || null) : null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px 16px',
      ...bodyStyle
    }
  }, children));
}
Object.assign(__ds_scope, { ToolCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/tools/ToolCard.jsx", error: String((e && e.message) || e) }); }

// components/word/WordRow.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * WASH — the signature brush map. Each entry is one real painted PNG, keyed
 * by CEFR level + grammatical type (der/die/das/verb/adj). The filenames are
 * the design-system brush assets.
 */
const WASH = {
  'B1|der': 'B1_Der_Powdery-Blue_Horizontal-Soft.png',
  'B1|die': 'B1_Die_Powdery-Pink_BG-Wash.png',
  'B1|das': 'B1_Das_Pale-Green_BG-Wash.png',
  'B1|verb': 'B1_Verbs_Sandy-Ochre_BG-Wash.png',
  'B1|adj': 'B1_Adjectives_Lavender_BG-Wash.png',
  'B2|der': 'B2_Der_Deep-Blue_BG-Wash.png',
  'B2|die': 'B2_Die_Magenta_BG-Wash.png',
  'B2|das': 'B2_Das_Grass-Green_BG-Wash.png',
  'B2|verb': 'B2_Verbs_Terracotta_BG-Wash.png',
  'B2|adj': 'B2_Adjectives_Amethyst_BG-Wash.png',
  'C1|der': 'C1_Der_Indigo_BG-Wash.png',
  'C1|die': 'C1_Die_Burgundy_BG-Wash.png',
  'C1|das': 'C1_Das_Emerald_BG-Wash.png',
  'C1|verb': 'C1_Verbs_Olive-Ochre_BG-Wash.png',
  'C1|adj': 'C1_Adjectives_Plum_BG-Wash.png'
};
function typeKey({
  pos,
  art
}) {
  if (pos === 'verb') return 'verb';
  if (pos === 'adj') return 'adj';
  return art || 'die';
}

/**
 * WordRow — the heart of the brand. A dictionary entry painted with its own
 * watercolor brush (by level + word-type). The German word in serif, the
 * gloss italic beneath, a level tag at the right. On hover/active the hidden
 * continuation of the stroke is "drawn in" — the paint never moves, only
 * reveals. Set `brushBase` to the relative path of the brush folder from the
 * mounting page (default "assets/brushes/").
 */
function WordRow({
  art = '',
  de,
  ru,
  pos = 'noun',
  level = 'B1',
  active = false,
  brushBase = 'assets/brushes/',
  onClick,
  style,
  ...rest
}) {
  const file = WASH[`${level}|${typeKey({
    pos,
    art
  })}`] || WASH['B1|die'];
  const brush = `url('${brushBase}${file}')`;
  return /*#__PURE__*/React.createElement("div", _extends({
    className: `de-wordrow${active ? ' is-active' : ''}`,
    onClick: onClick,
    style: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '14px',
      padding: '13px 14px 13px 26px',
      cursor: 'pointer',
      borderRadius: 'var(--radius-lg)',
      minHeight: '64px',
      overflow: 'hidden',
      ['--brush']: brush,
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("span", {
    className: "de-wordrow-wash",
    "aria-hidden": "true",
    style: {
      position: 'absolute',
      left: '-10px',
      top: '50%',
      transform: 'translateY(-50%)',
      width: '108%',
      height: '165%',
      zIndex: 0,
      pointerEvents: 'none',
      background: `var(--brush) no-repeat left center`,
      backgroundSize: '62% 118%',
      opacity: active ? 0.92 : 0.6,
      WebkitMaskImage: `linear-gradient(90deg,#000 0,#000 ${active ? '70%' : '12%'},rgba(0,0,0,.4) ${active ? '82%' : '30%'},transparent ${active ? '92%' : '46%'})`,
      maskImage: `linear-gradient(90deg,#000 0,#000 ${active ? '70%' : '12%'},rgba(0,0,0,.4) ${active ? '82%' : '30%'},transparent ${active ? '92%' : '46%'})`,
      transition: 'opacity var(--dur-slow) ease'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1,
      flex: '1 1 auto',
      minWidth: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: '3px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontSize: '26px',
      fontWeight: 500,
      lineHeight: 1.08,
      color: 'var(--ink)',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      textShadow: '0 0 4px rgba(255,255,255,.4)'
    }
  }, art ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 500
    }
  }, art, " ") : null, de), ru ? /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontStyle: 'italic',
      fontSize: '18px',
      color: 'var(--ink-soft)',
      lineHeight: 1.25,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      textShadow: '0 0 7px rgba(255,255,255,.7)'
    }
  }, ru) : null), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1,
      flex: 'none'
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.LevelTag, {
    level: level
  })));
}
Object.assign(__ds_scope, { WASH, WordRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/word/WordRow.jsx", error: String((e && e.message) || e) }); }

// ui_kits/editor/Editor.jsx
try { (() => {
/* global React */
const {
  useState
} = React;
const DS = window.DeutschEssayDesignSystem_3bc91c;
const {
  TopBar,
  Button,
  IconButton,
  Select,
  ProgressBar,
  ToolCard,
  SearchField,
  WASH
} = DS;
const BRUSH_BASE = '../../assets/brushes/';
function brushFor(w) {
  const t = w.pos === 'verb' ? 'verb' : w.pos === 'adj' ? 'adj' : w.art || 'die';
  return `url('${BRUSH_BASE}${WASH[w.level + '|' + t] || WASH['B1|die']}')`;
}

/* compact, horizontal dictionary row for the editor side panel */
function CompactRow({
  w
}) {
  const [on, setOn] = useState(false);
  return /*#__PURE__*/React.createElement("div", {
    className: "wb-row",
    onMouseEnter: () => setOn(true),
    onMouseLeave: () => setOn(false),
    style: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '9px 11px',
      borderRadius: 'var(--radius-lg)',
      cursor: 'pointer',
      minHeight: 42,
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      position: 'absolute',
      left: 0,
      top: '50%',
      transform: 'translateY(-50%)',
      width: '62%',
      height: '122%',
      zIndex: 0,
      pointerEvents: 'none',
      background: `${brushFor(w)} no-repeat left center`,
      backgroundSize: 'auto 116%',
      opacity: on ? .95 : .5,
      WebkitMaskImage: `linear-gradient(90deg, transparent 0, rgba(0,0,0,.5) 6px, #000 16px, #000 ${on ? '77%' : '21%'}, rgba(0,0,0,.4) ${on ? '90%' : '34%'}, transparent ${on ? '100%' : '44%'})`,
      maskImage: `linear-gradient(90deg, transparent 0, rgba(0,0,0,.5) 6px, #000 16px, #000 ${on ? '77%' : '21%'}, rgba(0,0,0,.4) ${on ? '90%' : '34%'}, transparent ${on ? '100%' : '44%'})`,
      transition: 'opacity .45s ease'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      zIndex: 1,
      fontSize: 14,
      color: 'var(--ink)',
      fontWeight: 500,
      flex: 'none',
      textShadow: '0 0 4px rgba(255,255,255,.55)'
    }
  }, w.art ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink-mute)',
      fontWeight: 400
    }
  }, w.art, " ") : null, w.de), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      zIndex: 1,
      fontSize: 13,
      color: 'var(--ink-mute)',
      fontStyle: 'italic',
      marginLeft: 'auto',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    }
  }, w.ru), /*#__PURE__*/React.createElement("button", {
    style: {
      position: 'relative',
      zIndex: 1,
      flex: 'none',
      width: 24,
      height: 24,
      borderRadius: 7,
      border: 0,
      background: 'none',
      color: 'var(--muted-2)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M12 3l2.6 5.6 6.1.7-4.5 4.1 1.2 6L12 16.9 6.6 19.4l1.2-6L3.3 9.3l6.1-.7z"
  }))));
}
const SECTIONS = [{
  n: '01',
  name: 'Einleitung',
  words: 36
}, {
  n: '02',
  name: 'Argument Eins',
  words: 0
}, {
  n: '03',
  name: 'Argument Zwei',
  words: 0
}, {
  n: '04',
  name: 'Schluss',
  words: 0
}];
const KLISCHEES = [['Ein wichtiges Argument dafür ist, dass …', 'Важный аргумент в пользу этого — что …', true], ['Erstens lässt sich feststellen, dass …', 'Во-первых, можно констатировать, что …', false], ['Ein klarer Vorteil besteht darin, dass …', 'Явное преимущество состоит в том, что …', false]];
const PANEL_WORDS = [{
  art: 'die',
  de: 'Technologie',
  ru: 'технология',
  pos: 'noun',
  level: 'B1'
}, {
  art: 'die',
  de: 'Entwicklung',
  ru: 'развитие',
  pos: 'noun',
  level: 'B1'
}, {
  art: 'der',
  de: 'Fortschritt',
  ru: 'прогресс',
  pos: 'noun',
  level: 'B1'
}, {
  art: 'der',
  de: 'Algorithmus',
  ru: 'алгоритм',
  pos: 'noun',
  level: 'B2'
}];
function Pomodoro() {
  const [running, setRunning] = useState(false);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      overflow: 'hidden',
      borderRadius: 'var(--radius-xl)',
      minHeight: 218,
      color: 'var(--ink)',
      border: '1px solid var(--accent-ln)',
      background: `radial-gradient(120% 90% at 12% 0%, var(--lav-soft) 0%, transparent 56%), radial-gradient(120% 100% at 100% 100%, var(--rose-soft) 0%, transparent 60%), var(--accent-bg)`
    }
  }, /*#__PURE__*/React.createElement("div", {
    "aria-hidden": "true",
    style: {
      position: 'absolute',
      inset: 0,
      zIndex: 0,
      pointerEvents: 'none',
      opacity: .45,
      background: `url('../../assets/images/abstract-watercolor-column.png') no-repeat -30px center`,
      backgroundSize: 'auto 160%',
      WebkitMaskImage: 'linear-gradient(180deg, rgba(0,0,0,.55) 0%, transparent 78%)',
      maskImage: 'linear-gradient(180deg, rgba(0,0,0,.55) 0%, transparent 78%)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 18px 0'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10.5,
      letterSpacing: '.16em',
      textTransform: 'uppercase',
      fontWeight: 700,
      color: 'var(--accent-dk)'
    }
  }, "Pomodoro-Timer"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: pomoMode(true)
  }, "Fokus"), /*#__PURE__*/React.createElement("button", {
    style: pomoMode(false)
  }, "Pause"))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1,
      textAlign: 'center',
      padding: '6px 18px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontSize: 64,
      fontWeight: 600,
      lineHeight: 1,
      letterSpacing: '1px',
      color: 'var(--ink)'
    }
  }, "25:00"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      letterSpacing: '.06em',
      color: 'var(--ink-mute)',
      marginTop: 2
    }
  }, "Fokuszeit")), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 16,
      padding: '14px 0 20px'
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setRunning(false),
    style: {
      width: 42,
      height: 42,
      borderRadius: 'var(--radius-pill)',
      border: '1px solid var(--accent-ln)',
      background: 'rgba(255,255,255,.7)',
      color: 'var(--accent-dk)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      backdropFilter: 'blur(4px)'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M3 12a9 9 0 1 0 3-6.7L3 8"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M3 3v5h5"
  }))), /*#__PURE__*/React.createElement("button", {
    onClick: () => setRunning(r => !r),
    style: {
      width: 58,
      height: 58,
      borderRadius: 'var(--radius-pill)',
      border: 0,
      cursor: 'pointer',
      background: 'var(--accent)',
      color: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: 'var(--shadow-accent)'
    }
  }, running ? /*#__PURE__*/React.createElement("svg", {
    width: "24",
    height: "24",
    viewBox: "0 0 24 24",
    fill: "currentColor"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "6",
    y: "5",
    width: "4",
    height: "14",
    rx: "1"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "5",
    width: "4",
    height: "14",
    rx: "1"
  })) : /*#__PURE__*/React.createElement("svg", {
    width: "24",
    height: "24",
    viewBox: "0 0 24 24",
    fill: "currentColor"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M8 5v14l11-7z"
  })))));
}
function pomoMode(on) {
  return {
    fontSize: 11,
    fontWeight: 600,
    color: on ? '#fff' : 'var(--ink-mute)',
    background: on ? 'var(--accent)' : 'rgba(255,255,255,.55)',
    border: '1px solid ' + (on ? 'var(--accent)' : 'var(--accent-ln)'),
    borderRadius: 20,
    padding: '4px 11px',
    cursor: 'pointer',
    backdropFilter: 'blur(4px)'
  };
}
function Editor() {
  const [active, setActive] = useState(1);
  const [text, setText] = useState('Einerseits haben Technologien viele Vorteile. Zum Beispiel können wir Informationen in nur wenigen Sekunden finden. Wenn ich eine Hausaufgabe machen muss, suche ich die Antwort bei Google. Außerdem helfen uns soziale Netzwerke, mit Freunden aus anderen Ländern zu kontaktieren.');
  const [kli, setKli] = useState(0);
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(TopBar, {
    items: [{
      label: 'Dashboard'
    }, {
      label: 'Schreiben',
      active: true
    }, {
      label: 'Lernen',
      dropdown: true
    }, {
      label: 'Verlauf'
    }, {
      label: 'Pipeline'
    }]
  }), /*#__PURE__*/React.createElement("div", {
    className: "bg-column",
    "aria-hidden": "true"
  }), /*#__PURE__*/React.createElement("div", {
    className: "side-label"
  }, "SCHREIBEN"), /*#__PURE__*/React.createElement("div", {
    className: "layout"
  }, /*#__PURE__*/React.createElement("aside", {
    className: "rail-left"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    style: {
      flex: 1
    },
    icon: /*#__PURE__*/React.createElement("svg", {
      viewBox: "0 0 24 24",
      width: "16",
      height: "16",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "2",
      strokeLinecap: "round"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M12 5v14M5 12h14"
    }))
  }, "Neues Essay"), /*#__PURE__*/React.createElement(IconButton, {
    label: "Ordner",
    size: "lg"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "18",
    height: "18",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
  })))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "rail-cap"
  }, "Essay Map"), /*#__PURE__*/React.createElement("div", {
    className: "essay-map"
  }, SECTIONS.map((s, i) => /*#__PURE__*/React.createElement("button", {
    key: i,
    className: `map-item${i === active ? ' active' : ''}`,
    onClick: () => setActive(i)
  }, /*#__PURE__*/React.createElement("div", {
    className: "map-num"
  }, s.n, " ", s.name), /*#__PURE__*/React.createElement("div", {
    className: "map-words"
  }, s.words, " W\xF6rter"))))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ProgressBar, {
    value: words,
    max: 250,
    label: "Fortschritt",
    showCount: true
  })), /*#__PURE__*/React.createElement("div", {
    className: "niveau-box"
  }, /*#__PURE__*/React.createElement(Select, {
    label: "",
    value: "B1"
  }), /*#__PURE__*/React.createElement("span", {
    className: "niveau-lab"
  }, "Niveau \xB7 B1"))), /*#__PURE__*/React.createElement("div", {
    className: "editor-card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "doc-meta"
  }, /*#__PURE__*/React.createElement(Select, {
    label: "THEMA",
    value: "Technologie"
  }), /*#__PURE__*/React.createElement(Select, {
    label: "FORM",
    value: "argumentativ"
  }), /*#__PURE__*/React.createElement(Select, {
    value: "Vorlage"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto'
    }
  }), /*#__PURE__*/React.createElement("button", {
    className: "doc-notes"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "15",
    height: "15",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M4 4h16v12H7l-3 3z"
  })), "Notizen")), /*#__PURE__*/React.createElement("div", {
    className: "doc-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "doc-eyebrow"
  }, "Technologie"), /*#__PURE__*/React.createElement("div", {
    className: "doc-title"
  }, "Argument Eins"), /*#__PURE__*/React.createElement("div", {
    className: "doc-sub"
  }, "Das st\xE4rkste Argument zuerst")), /*#__PURE__*/React.createElement("div", {
    className: "doc-scroll"
  }, /*#__PURE__*/React.createElement("div", {
    className: "editable",
    contentEditable: true,
    suppressContentEditableWarning: true,
    onInput: e => setText(e.currentTarget.textContent)
  }, text)), /*#__PURE__*/React.createElement("div", {
    className: "analyze-row"
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "lg",
    icon: /*#__PURE__*/React.createElement("svg", {
      viewBox: "0 0 24 24",
      width: "18",
      height: "18",
      fill: "currentColor"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"
    }))
  }, "Analysiere ", SECTIONS[active].name, "\u2026")), /*#__PURE__*/React.createElement("div", {
    className: "doc-foot"
  }, /*#__PURE__*/React.createElement("span", null, words, " W\xF6rter"), /*#__PURE__*/React.createElement("span", {
    className: "saved"
  }, /*#__PURE__*/React.createElement("span", {
    className: "dot"
  }), "Automatisch gespeichert"))), /*#__PURE__*/React.createElement("aside", {
    className: "rail-right"
  }, /*#__PURE__*/React.createElement(Pomodoro, null), /*#__PURE__*/React.createElement(ToolCard, {
    title: "Klischees",
    accent: SECTIONS[active].name.toUpperCase(),
    action: /*#__PURE__*/React.createElement("div", {
      className: "kli-pager"
    }, /*#__PURE__*/React.createElement("button", {
      className: "kli-nav",
      onClick: () => setKli(k => Math.max(0, k - 1))
    }, "\u2039"), /*#__PURE__*/React.createElement("span", {
      className: "kli-count"
    }, kli + 1, " / 2"), /*#__PURE__*/React.createElement("button", {
      className: "kli-nav",
      onClick: () => setKli(k => Math.min(1, k + 1))
    }, "\u203A"))
  }, KLISCHEES.map((k, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "kli"
  }, /*#__PURE__*/React.createElement("div", {
    className: "kli-de",
    dangerouslySetInnerHTML: {
      __html: k[2] ? `<em>${k[0]}</em>` : k[0]
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "kli-ru"
  }, k[1])))), /*#__PURE__*/React.createElement(ToolCard, {
    title: "W\xF6rterbuch",
    accent: "TECHNOLOGIE"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement(SearchField, {
    size: "sm",
    placeholder: "Suche nach Wort\u2026"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 2
    }
  }, PANEL_WORDS.map((w, i) => /*#__PURE__*/React.createElement(CompactRow, {
    key: i,
    w: w
  })))))));
}
window.Editor = Editor;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/editor/Editor.jsx", error: String((e && e.message) || e) }); }

// ui_kits/woerterbuch/Woerterbuch.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/* global React */
const {
  useState,
  useRef,
  useLayoutEffect
} = React;

// Pull primitives from the compiled design-system bundle.
const DS = window.DeutschEssayDesignSystem_3bc91c;
const {
  TopBar,
  Chip,
  SearchField,
  WordRow,
  LevelTag
} = DS;
const BRUSH_BASE = '../../assets/brushes/';

/* ---- a small slice of the real dictionary data ---- */
const WORDS = [{
  art: 'die',
  de: 'Abhängigkeit',
  ru: 'зависимость',
  pos: 'noun',
  cat: 'Technologie',
  level: 'B1',
  genus: 'Femininum',
  ipa: '[ˈapˌhɛŋɪçkaɪt]',
  def: 'Ein Zustand, in dem jemand oder etwas von etwas anderem bestimmt oder benötigt wird.',
  pull: 'Die Abhängigkeit von fossilen Brennstoffen ist eine globale Herausforderung.',
  rule: 'von + Dativ',
  ruleEx: 'die Abhängigkeit von der Technik',
  examples: [['Die Abhängigkeit von Technologie nimmt ständig zu.', 'Зависимость от технологий постоянно растёт.'], ['Eine starke Abhängigkeit von einem Anbieter ist riskant.', 'Сильная зависимость от поставщика рискованна.']]
}, {
  art: 'der',
  de: 'Algorithmus',
  ru: 'алгоритм',
  pos: 'noun',
  cat: 'Technologie',
  level: 'B2',
  genus: 'Maskulinum',
  ipa: '[alɡoˈrɪtmʊs]',
  def: 'Eine eindeutige Handlungsvorschrift zur Lösung eines Problems.',
  pull: 'Ein guter Algorithmus spart Zeit und Ressourcen.',
  rule: 'für + Akkusativ',
  ruleEx: 'ein Algorithmus für die Suche',
  examples: [['Der Algorithmus entscheidet, was zuerst angezeigt wird.', 'Алгоритм решает, что показывается первым.'], ['Ein effizienter Algorithmus verarbeitet Millionen Daten.', 'Эффективный алгоритм обрабатывает миллионы данных.']]
}, {
  art: 'die',
  de: 'Auswirkung',
  ru: 'последствие, влияние',
  pos: 'noun',
  cat: 'Technologie',
  level: 'B1',
  genus: 'Femininum',
  ipa: '[ˈaʊsˌvɪrkʊŋ]',
  def: 'Eine Folge oder ein Effekt, der aus einer Handlung entsteht.',
  pull: 'Die Auswirkungen des Klimawandels sind weltweit spürbar.',
  rule: 'auf + Akkusativ',
  ruleEx: 'die Auswirkung auf die Umwelt',
  examples: [['Jede Entscheidung hat eine Auswirkung auf die Zukunft.', 'Каждое решение влияет на будущее.']]
}, {
  de: 'analysieren',
  ru: 'анализировать',
  pos: 'verb',
  cat: 'Wissenschaft',
  level: 'B2',
  genus: 'Verb',
  ipa: '[analyˈziːʁən]',
  def: 'Etwas systematisch und gründlich untersuchen, um es zu verstehen.',
  pull: 'Wer Daten klug analysiert, trifft bessere Entscheidungen.',
  rule: '+ Akkusativ',
  ruleEx: 'die Daten genau analysieren',
  examples: [['Wir müssen die Ergebnisse genau analysieren.', 'Нам нужно тщательно проанализировать результаты.']]
}, {
  art: 'der',
  de: 'Fortschritt',
  ru: 'прогресс',
  pos: 'noun',
  cat: 'Wissenschaft',
  level: 'B1',
  genus: 'Maskulinum',
  ipa: '[ˈfɔʁtʃʁɪt]',
  def: 'Eine positive Entwicklung hin zu einem besseren Zustand.',
  pull: 'Wissenschaftlicher Fortschritt verbessert unser Leben.',
  rule: 'bei / in + Dativ',
  ruleEx: 'Fortschritte bei der Arbeit',
  examples: [['Der Fortschritt in der Medizin rettet Leben.', 'Прогресс в медицине спасает жизни.']]
}, {
  de: 'nachhaltig',
  ru: 'устойчивый, экологичный',
  pos: 'adj',
  cat: 'Umwelt',
  level: 'C1',
  genus: 'Adjektiv',
  ipa: '[ˈnaːxˌhaltɪç]',
  def: 'So gestaltet, dass Ressourcen geschont und für künftige Generationen erhalten bleiben.',
  pull: 'Nachhaltiges Handeln ist eine Investition in die Zukunft.',
  rule: 'mit + Dativ',
  ruleEx: 'nachhaltig mit Ressourcen umgehen',
  examples: [['Wir setzen auf nachhaltige Energiequellen.', 'Мы делаем ставку на устойчивые источники.']]
}, {
  art: 'die',
  de: 'Gesellschaft',
  ru: 'общество',
  pos: 'noun',
  cat: 'Gesellschaft',
  level: 'B1',
  genus: 'Femininum',
  ipa: '[ɡəˈzɛlʃaft]',
  def: 'Die Gesamtheit der Menschen, die zusammenleben und durch Normen verbunden sind.',
  pull: 'Eine offene Gesellschaft schätzt Vielfalt.',
  rule: 'in + Dativ',
  ruleEx: 'in der Gesellschaft leben',
  examples: [['Die Gesellschaft steht vor großen Veränderungen.', 'Общество стоит перед большими изменениями.']]
}, {
  art: 'die',
  de: 'Nachhaltigkeit',
  ru: 'устойчивость',
  pos: 'noun',
  cat: 'Umwelt',
  level: 'C1',
  genus: 'Femininum',
  ipa: '[ˈnaːxˌhaltɪçkaɪt]',
  def: 'Ein Prinzip, bei dem Ressourcen so genutzt werden, dass sie erhalten bleiben.',
  pull: 'Nachhaltigkeit ist kein Trend, sondern eine Notwendigkeit.',
  rule: 'in + Dativ',
  ruleEx: 'Nachhaltigkeit in der Wirtschaft',
  examples: [['Nachhaltigkeit sollte im Zentrum jeder Entscheidung stehen.', 'Устойчивость должна быть в центре решений.']]
}, {
  art: 'die',
  de: 'Verantwortung',
  ru: 'ответственность',
  pos: 'noun',
  cat: 'Gesellschaft',
  level: 'B2',
  genus: 'Femininum',
  ipa: '[fɛɐ̯ˈʔantvɔʁtʊŋ]',
  def: 'Die Pflicht, für die Folgen des eigenen Handelns einzustehen.',
  pull: 'Mit Freiheit wächst die Verantwortung.',
  rule: 'für + Akkusativ',
  ruleEx: 'die Verantwortung für das Team',
  examples: [['Jeder trägt Verantwortung für die Umwelt.', 'Каждый несёт ответственность за среду.']]
}, {
  art: 'die',
  de: 'Herausforderung',
  ru: 'вызов',
  pos: 'noun',
  cat: 'Gesellschaft',
  level: 'B2',
  genus: 'Femininum',
  ipa: '[hɛˈʁaʊsfɔʁdəʁʊŋ]',
  def: 'Eine schwierige Aufgabe, die besondere Anstrengung verlangt.',
  pull: 'Jede Herausforderung ist eine Chance zu wachsen.',
  rule: 'für + Akkusativ',
  ruleEx: 'eine Herausforderung für die Gesellschaft',
  examples: [['Der Klimawandel ist eine globale Herausforderung.', 'Изменение климата — глобальный вызов.']]
}, {
  de: 'wesentlich',
  ru: 'существенный, важный',
  pos: 'adj',
  cat: 'Wissenschaft',
  level: 'B2',
  genus: 'Adjektiv',
  ipa: '[ˈveːzn̩tlɪç]',
  def: 'Von grundlegender Bedeutung; entscheidend für das Ganze.',
  pull: 'Das Wesentliche bleibt dem Auge oft verborgen.',
  rule: 'für + Akkusativ',
  ruleEx: 'wesentlich für den Erfolg',
  examples: [['Das ist ein wesentlicher Unterschied.', 'Это существенное различие.']]
}, {
  art: 'der',
  de: 'Zusammenhang',
  ru: 'взаимосвязь, контекст',
  pos: 'noun',
  cat: 'Wissenschaft',
  level: 'C1',
  genus: 'Maskulinum',
  ipa: '[t͡suˈzamənhaŋ]',
  def: 'Die innere Beziehung zwischen mehreren Dingen oder Ereignissen.',
  pull: 'Erst im Zusammenhang ergibt alles einen Sinn.',
  rule: 'zwischen + Dativ',
  ruleEx: 'der Zusammenhang zwischen Ursache und Wirkung',
  examples: [['Es gibt einen klaren Zusammenhang zwischen beiden.', 'Между обоими есть чёткая взаимосвязь.']]
}];
const CATS = ['Alle', 'Technologie', 'Gesellschaft', 'Wissenschaft', 'Umwelt'];
const LVL = {
  B1: {
    n: 22,
    c: 'var(--rose)'
  },
  B2: {
    n: 47,
    c: 'var(--blue)'
  },
  C1: {
    n: 20,
    c: 'var(--lav)'
  }
};
const TOTAL = 89;
function posLabel(w) {
  return w.pos === 'verb' ? 'Verb' : w.pos === 'adj' ? 'Adjektiv' : 'Substantiv';
}

/* ---------- distribution donut ---------- */
function Donut() {
  const order = ['B1', 'B2', 'C1'];
  const C = 2 * Math.PI * 46;
  let off = 0;
  const segs = order.map(lv => {
    const len = LVL[lv].n / TOTAL * C;
    const el = /*#__PURE__*/React.createElement("circle", {
      key: lv,
      r: "46",
      cx: "60",
      cy: "60",
      fill: "none",
      stroke: LVL[lv].c,
      strokeWidth: "14",
      strokeDasharray: `${len.toFixed(2)} ${(C - len).toFixed(2)}`,
      strokeDashoffset: (-off).toFixed(2)
    });
    off += len;
    return el;
  });
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      width: 150,
      height: 150,
      margin: '6px auto 0'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 120 120",
    style: {
      width: '100%',
      height: '100%'
    }
  }, /*#__PURE__*/React.createElement("g", {
    transform: "rotate(-90 60 60)"
  }, segs)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontSize: 36,
      fontWeight: 600,
      color: 'var(--ink)',
      lineHeight: 1
    }
  }, TOTAL), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 8,
      letterSpacing: '2px',
      textTransform: 'uppercase',
      color: 'var(--muted)',
      marginTop: 3
    }
  }, "W\xF6rter")));
}

/* ---------- detail sheet ---------- */
function DetailSheet({
  w,
  onClose
}) {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      position: 'relative',
      overflow: 'hidden',
      background: 'var(--card)',
      border: '1px solid var(--hair)',
      borderRadius: 'var(--radius-xl)',
      boxShadow: 'var(--shadow-sheet)'
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    "aria-label": "Schlie\xDFen",
    style: {
      position: 'absolute',
      top: 16,
      right: 16,
      zIndex: 5,
      width: 34,
      height: 34,
      borderRadius: 'var(--radius-pill)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--card)',
      border: '1px solid var(--hair)',
      color: 'var(--ink-soft)',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "15",
    height: "15",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2.2",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M6 6l12 12M18 6L6 18"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--card)',
      borderBottom: '1px solid var(--hair)',
      borderRadius: '18px 18px 0 0',
      padding: '34px 50px 30px',
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      gap: 10,
      marginBottom: 18
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11.5,
      letterSpacing: '.2em',
      textTransform: 'uppercase',
      color: 'var(--ink-soft)',
      fontWeight: 600
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink)',
      fontWeight: 700
    }
  }, posLabel(w)), " \xB7 ", w.cat), /*#__PURE__*/React.createElement(LevelTag, {
    level: w.level,
    tinted: true
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontSize: 54,
      fontWeight: 600,
      lineHeight: 1,
      letterSpacing: '-.5px',
      color: 'var(--ink)',
      marginBottom: 12
    }
  }, w.art ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink-soft)'
    }
  }, w.art, " ") : null, w.de), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      gap: 16,
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 14.5,
      color: 'var(--ink-soft)'
    }
  }, w.ipa), /*#__PURE__*/React.createElement("button", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      background: 'none',
      border: 0,
      cursor: 'pointer',
      color: 'var(--rose)',
      fontSize: 13,
      fontWeight: 600
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "currentColor"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M5 9v6h4l5 5V4L9 9H5z"
  }), /*#__PURE__*/React.createElement("path", {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    d: "M16.5 8.5a5 5 0 0 1 0 7"
  })), "Aussprache")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontStyle: 'italic',
      fontSize: 28,
      lineHeight: 1.2,
      color: 'var(--ink-soft)'
    }
  }, w.ru)), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '30px 38px 34px'
    }
  }, /*#__PURE__*/React.createElement(Lab, null, "Bedeutung"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 17,
      lineHeight: 1.7,
      color: 'var(--ink)',
      margin: '0 auto',
      maxWidth: '42ch',
      textAlign: 'center'
    }
  }, w.def), /*#__PURE__*/React.createElement("blockquote", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontStyle: 'italic',
      fontSize: 20,
      lineHeight: 1.5,
      color: 'var(--ink-soft)',
      textAlign: 'center',
      maxWidth: '40ch',
      margin: '18px auto 0'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontSize: 40,
      lineHeight: 0,
      color: 'var(--rose)',
      opacity: .55,
      margin: '0 auto 16px'
    }
  }, "\u201C"), w.pull), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 34
    }
  }, /*#__PURE__*/React.createElement(Lab, null, "Grammatik"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'center',
      flexWrap: 'wrap',
      marginBottom: 28
    }
  }, /*#__PURE__*/React.createElement(Param, {
    k: "Genus",
    v: w.genus
  }), /*#__PURE__*/React.createElement(Param, {
    k: "Wortart",
    v: posLabel(w),
    border: true
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      textAlign: 'center',
      border: '1px solid var(--rose-soft)',
      borderRadius: 'var(--radius-lg)',
      padding: '22px 26px',
      background: `linear-gradient(0deg, rgba(255,255,255,.40), rgba(255,255,255,.40)), url('../../assets/images/Verwendung.png') center/cover no-repeat`
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontSize: 10,
      letterSpacing: '.24em',
      textTransform: 'uppercase',
      color: 'var(--rose)',
      fontWeight: 700,
      marginBottom: 11
    }
  }, "Verwendung"), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontFamily: 'var(--font-serif)',
      fontSize: 31,
      fontWeight: 600,
      color: 'var(--ink)',
      lineHeight: 1.04
    }
  }, w.rule), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontFamily: 'var(--font-serif)',
      fontStyle: 'italic',
      fontSize: 17,
      color: 'var(--ink-soft)',
      marginTop: 9
    }
  }, w.ruleEx))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 34
    }
  }, /*#__PURE__*/React.createElement(Lab, null, "Beispiele"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 26
    }
  }, w.examples.map((ex, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      gap: 18,
      alignItems: 'baseline'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 'none',
      width: 24,
      fontFamily: 'var(--font-serif)',
      fontSize: 18,
      fontWeight: 600,
      color: 'var(--rose)'
    }
  }, String(i + 1).padStart(2, '0')), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: 15.5,
      lineHeight: 1.6,
      color: 'var(--ink)'
    }
  }, ex[0]), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: '7px 0 0',
      fontSize: 14,
      lineHeight: 1.55,
      color: 'var(--ink-soft)',
      fontStyle: 'italic'
    }
  }, ex[1]))))))));
}
function Lab({
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 14,
      fontSize: 11,
      letterSpacing: '.24em',
      textTransform: 'uppercase',
      color: 'var(--ink-soft)',
      fontWeight: 700,
      margin: '0 0 24px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      height: 1,
      width: 40,
      background: 'var(--hair)'
    }
  }), children, /*#__PURE__*/React.createElement("span", {
    style: {
      height: 1,
      width: 40,
      background: 'var(--hair)'
    }
  }));
}
function Param({
  k,
  v,
  border
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 4,
      padding: '2px 24px',
      textAlign: 'center',
      borderLeft: border ? '1px solid var(--hair)' : 'none'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9.5,
      letterSpacing: '.14em',
      textTransform: 'uppercase',
      color: 'var(--ink-soft)',
      fontWeight: 600
    }
  }, k), /*#__PURE__*/React.createElement("b", {
    style: {
      fontSize: 15.5,
      color: 'var(--ink)',
      fontWeight: 600
    }
  }, v));
}

/* ---------- the screen ---------- */
function Woerterbuch() {
  const [cat, setCat] = useState('Alle');
  const [q, setQ] = useState('');
  const [openIdx, setOpenIdx] = useState(-1);
  const open = openIdx >= 0;
  const filtered = WORDS.map((w, i) => ({
    w,
    i
  })).filter(({
    w
  }) => {
    const c = cat === 'Alle' || w.cat === cat;
    const s = !q || w.de.toLowerCase().includes(q.toLowerCase()) || (w.ru || '').toLowerCase().includes(q.toLowerCase());
    return c && s;
  });
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(TopBar, {
    items: [{
      label: 'Dashboard'
    }, {
      label: 'Schreiben'
    }, {
      label: 'Lernen',
      dropdown: true,
      active: true
    }, {
      label: 'Verlauf'
    }, {
      label: 'Pipeline'
    }]
  }), /*#__PURE__*/React.createElement("div", {
    className: "bg-column",
    "aria-hidden": "true"
  }), /*#__PURE__*/React.createElement("div", {
    className: "side-label"
  }, "W\xD6RTERBUCH"), /*#__PURE__*/React.createElement("main", {
    style: {
      position: 'relative',
      zIndex: 2,
      display: open ? 'grid' : 'block',
      gridTemplateColumns: open ? 'minmax(340px,1fr) minmax(420px,560px)' : 'none',
      gap: 48,
      padding: '18px 244px 90px 100px'
    }
  }, /*#__PURE__*/React.createElement("section", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      letterSpacing: '.22em',
      color: 'var(--rose)',
      fontWeight: 600,
      textTransform: 'uppercase',
      marginBottom: 10
    }
  }, "Lernen"), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontSize: 76,
      fontWeight: 600,
      lineHeight: .98,
      letterSpacing: '-.5px',
      margin: '0 0 14px',
      color: 'var(--ink)'
    }
  }, "W\xF6rterbuch"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 14.5,
      color: 'var(--ink-soft)',
      lineHeight: 1.6,
      maxWidth: 460,
      margin: 0
    }
  }, "Ihr thematischer Wortschatz f\xFCr pr\xE4zises Deutsch. W\xE4hlen Sie ein Wort, um Bedeutung, Grammatik und Beispiele zu sehen."), /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '28px 0 20px'
    }
  }, /*#__PURE__*/React.createElement(SearchField, {
    value: q,
    onChange: e => setQ(e.target.value),
    placeholder: "Suche nach Begriff oder \xDCbersetzung (z. B. \u201EFortschritt\u201C)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 9,
      flexWrap: 'wrap',
      marginBottom: 18
    }
  }, CATS.map(c => /*#__PURE__*/React.createElement(Chip, {
    key: c,
    active: cat === c,
    onClick: () => {
      setCat(c);
      setOpenIdx(-1);
    }
  }, c === 'Alle' ? `Alle · ${WORDS.length}` : c))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: open ? '1fr' : 'repeat(2,minmax(0,1fr))',
      gap: '10px 30px'
    }
  }, filtered.map(({
    w,
    i
  }) => /*#__PURE__*/React.createElement(WordRow, _extends({
    key: i
  }, w, {
    active: i === openIdx,
    brushBase: BRUSH_BASE,
    onClick: () => setOpenIdx(i)
  }))))), open ? /*#__PURE__*/React.createElement("section", {
    style: {
      position: 'sticky',
      top: 90,
      alignSelf: 'start'
    }
  }, /*#__PURE__*/React.createElement(DetailSheet, {
    w: WORDS[openIdx],
    onClose: () => setOpenIdx(-1)
  })) : null), /*#__PURE__*/React.createElement("aside", {
    className: "rail"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9.5,
      letterSpacing: '2.5px',
      textTransform: 'uppercase',
      color: 'var(--muted)',
      textAlign: 'center',
      fontWeight: 600
    }
  }, "Verteilung nach Niveau"), /*#__PURE__*/React.createElement(Donut, null), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      marginTop: 14
    }
  }, ['B1', 'B2', 'C1'].map(lv => /*#__PURE__*/React.createElement("div", {
    key: lv,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      fontSize: 12.5,
      padding: '4px 6px',
      borderRadius: 9
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 10,
      height: 10,
      borderRadius: 3,
      background: LVL[lv].c
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      color: 'var(--ink-soft)',
      letterSpacing: '.3px'
    }
  }, lv), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      color: 'var(--muted)'
    }
  }, LVL[lv].n, " W\xF6rter"))))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 1,
      background: 'var(--hair)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontSize: 32,
      fontWeight: 600,
      color: 'var(--ink)'
    }
  }, TOTAL), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontSize: 9,
      letterSpacing: '2px',
      textTransform: 'uppercase',
      color: 'var(--muted)',
      marginTop: 5
    }
  }, "W\xF6rter gelernt")), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 1,
      background: 'var(--hair)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-serif)',
      fontStyle: 'italic',
      fontSize: 14,
      lineHeight: 1.55,
      color: 'var(--ink-soft)',
      textAlign: 'center'
    }
  }, "Die Grenzen meiner Sprache bedeuten die Grenzen meiner Welt.", /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      marginTop: 9,
      fontSize: 8,
      fontStyle: 'normal',
      letterSpacing: '2px',
      color: 'var(--rose)',
      textTransform: 'uppercase',
      fontFamily: 'var(--font-sans)',
      fontWeight: 700
    }
  }, "Wittgenstein"))));
}
window.Woerterbuch = Woerterbuch;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/woerterbuch/Woerterbuch.jsx", error: String((e && e.message) || e) }); }

// ui_kits/woerterbuch/tweaks-panel.jsx
try { (() => {
// @ds-adherence-ignore -- omelette starter scaffold (raw elements/hex/px by design)

/* BEGIN USAGE */
// tweaks-panel.jsx
// Reusable Tweaks shell + form-control helpers.
// Exports (to window): useTweaks, TweaksPanel, TweakSection, TweakRow, TweakSlider,
//   TweakToggle, TweakRadio, TweakSelect, TweakText, TweakNumber, TweakColor, TweakButton.
//
// Owns the host protocol (listens for __activate_edit_mode / __deactivate_edit_mode,
// posts __edit_mode_available / __edit_mode_set_keys / __edit_mode_dismissed) so
// individual prototypes don't re-roll it. Ships a consistent set of controls so you
// don't hand-draw <input type="range">, segmented radios, steppers, etc.
//
// Usage (in an HTML file that loads React + Babel):
//
//   const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
//     "primaryColor": "#D97757",
//     "palette": ["#D97757", "#29261b", "#f6f4ef"],
//     "fontSize": 16,
//     "density": "regular",
//     "dark": false
//   }/*EDITMODE-END*/;
//
//   function App() {
//     const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
//     return (
//       <div style={{ fontSize: t.fontSize, color: t.primaryColor }}>
//         Hello
//         <TweaksPanel>
//           <TweakSection label="Typography" />
//           <TweakSlider label="Font size" value={t.fontSize} min={10} max={32} unit="px"
//                        onChange={(v) => setTweak('fontSize', v)} />
//           <TweakRadio  label="Density" value={t.density}
//                        options={['compact', 'regular', 'comfy']}
//                        onChange={(v) => setTweak('density', v)} />
//           <TweakSection label="Theme" />
//           <TweakColor  label="Primary" value={t.primaryColor}
//                        options={['#D97757', '#2A6FDB', '#1F8A5B', '#7A5AE0']}
//                        onChange={(v) => setTweak('primaryColor', v)} />
//           <TweakColor  label="Palette" value={t.palette}
//                        options={[['#D97757', '#29261b', '#f6f4ef'],
//                                  ['#475569', '#0f172a', '#f1f5f9']]}
//                        onChange={(v) => setTweak('palette', v)} />
//           <TweakToggle label="Dark mode" value={t.dark}
//                        onChange={(v) => setTweak('dark', v)} />
//         </TweaksPanel>
//       </div>
//     );
//   }
//
// TweakRadio is the segmented control for 2–3 short options (auto-falls-back to
// TweakSelect past ~16/~10 chars per label); reach for TweakSelect directly when
// options are many or long. For color tweaks always curate 3-4 options rather than
// a free picker; an option can also be a whole 2–5 color palette (the stored value
// is the array). The Tweak* controls are a floor, not a ceiling — build custom
// controls inside the panel if a tweak calls for UI they don't cover.
/* END USAGE */
// ─────────────────────────────────────────────────────────────────────────────

const __TWEAKS_STYLE = `
  .twk-panel{position:fixed;right:16px;bottom:16px;z-index:2147483646;width:280px;
    max-height:calc(100vh - 32px);display:flex;flex-direction:column;
    transform:scale(var(--dc-inv-zoom,1));transform-origin:bottom right;
    background:rgba(250,249,247,.78);color:#29261b;
    -webkit-backdrop-filter:blur(24px) saturate(160%);backdrop-filter:blur(24px) saturate(160%);
    border:.5px solid rgba(255,255,255,.6);border-radius:14px;
    box-shadow:0 1px 0 rgba(255,255,255,.5) inset,0 12px 40px rgba(0,0,0,.18);
    font:11.5px/1.4 ui-sans-serif,system-ui,-apple-system,sans-serif;overflow:hidden}
  .twk-hd{display:flex;align-items:center;justify-content:space-between;
    padding:10px 8px 10px 14px;cursor:move;user-select:none}
  .twk-hd b{font-size:12px;font-weight:600;letter-spacing:.01em}
  .twk-x{appearance:none;border:0;background:transparent;color:rgba(41,38,27,.55);
    width:22px;height:22px;border-radius:6px;cursor:default;font-size:13px;line-height:1}
  .twk-x:hover{background:rgba(0,0,0,.06);color:#29261b}
  .twk-body{padding:2px 14px 14px;display:flex;flex-direction:column;gap:10px;
    overflow-y:auto;overflow-x:hidden;min-height:0;
    scrollbar-width:thin;scrollbar-color:rgba(0,0,0,.15) transparent}
  .twk-body::-webkit-scrollbar{width:8px}
  .twk-body::-webkit-scrollbar-track{background:transparent;margin:2px}
  .twk-body::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15);border-radius:4px;
    border:2px solid transparent;background-clip:content-box}
  .twk-body::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,.25);
    border:2px solid transparent;background-clip:content-box}
  .twk-row{display:flex;flex-direction:column;gap:5px}
  .twk-row-h{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}
  .twk-lbl{display:flex;justify-content:space-between;align-items:baseline;
    color:rgba(41,38,27,.72)}
  .twk-lbl>span:first-child{font-weight:500}
  .twk-val{color:rgba(41,38,27,.5);font-variant-numeric:tabular-nums}

  .twk-sect{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:rgba(41,38,27,.45);padding:10px 0 0}
  .twk-sect:first-child{padding-top:0}

  .twk-field{appearance:none;box-sizing:border-box;width:100%;min-width:0;height:26px;padding:0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;
    background:rgba(255,255,255,.6);color:inherit;font:inherit;outline:none}
  .twk-field:focus{border-color:rgba(0,0,0,.25);background:rgba(255,255,255,.85)}
  select.twk-field{padding-right:22px;
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path fill='rgba(0,0,0,.5)' d='M0 0h10L5 6z'/></svg>");
    background-repeat:no-repeat;background-position:right 8px center}

  .twk-slider{appearance:none;-webkit-appearance:none;width:100%;height:4px;margin:6px 0;
    border-radius:999px;background:rgba(0,0,0,.12);outline:none}
  .twk-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
    width:14px;height:14px;border-radius:50%;background:#fff;
    border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}
  .twk-slider::-moz-range-thumb{width:14px;height:14px;border-radius:50%;
    background:#fff;border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}

  .twk-seg{position:relative;display:flex;padding:2px;border-radius:8px;
    background:rgba(0,0,0,.06);user-select:none}
  .twk-seg-thumb{position:absolute;top:2px;bottom:2px;border-radius:6px;
    background:rgba(255,255,255,.9);box-shadow:0 1px 2px rgba(0,0,0,.12);
    transition:left .15s cubic-bezier(.3,.7,.4,1),width .15s}
  .twk-seg.dragging .twk-seg-thumb{transition:none}
  .twk-seg button{appearance:none;position:relative;z-index:1;flex:1;border:0;
    background:transparent;color:inherit;font:inherit;font-weight:500;min-height:22px;
    border-radius:6px;cursor:default;padding:4px 6px;line-height:1.2;
    overflow-wrap:anywhere}

  .twk-toggle{position:relative;width:32px;height:18px;border:0;border-radius:999px;
    background:rgba(0,0,0,.15);transition:background .15s;cursor:default;padding:0}
  .twk-toggle[data-on="1"]{background:#34c759}
  .twk-toggle i{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;
    background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.25);transition:transform .15s}
  .twk-toggle[data-on="1"] i{transform:translateX(14px)}

  .twk-num{display:flex;align-items:center;box-sizing:border-box;min-width:0;height:26px;padding:0 0 0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;background:rgba(255,255,255,.6)}
  .twk-num-lbl{font-weight:500;color:rgba(41,38,27,.6);cursor:ew-resize;
    user-select:none;padding-right:8px}
  .twk-num input{flex:1;min-width:0;height:100%;border:0;background:transparent;
    font:inherit;font-variant-numeric:tabular-nums;text-align:right;padding:0 8px 0 0;
    outline:none;color:inherit;-moz-appearance:textfield}
  .twk-num input::-webkit-inner-spin-button,.twk-num input::-webkit-outer-spin-button{
    -webkit-appearance:none;margin:0}
  .twk-num-unit{padding-right:8px;color:rgba(41,38,27,.45)}

  .twk-btn{appearance:none;height:26px;padding:0 12px;border:0;border-radius:7px;
    background:rgba(0,0,0,.78);color:#fff;font:inherit;font-weight:500;cursor:default}
  .twk-btn:hover{background:rgba(0,0,0,.88)}
  .twk-btn.secondary{background:rgba(0,0,0,.06);color:inherit}
  .twk-btn.secondary:hover{background:rgba(0,0,0,.1)}

  .twk-swatch{appearance:none;-webkit-appearance:none;width:56px;height:22px;
    border:.5px solid rgba(0,0,0,.1);border-radius:6px;padding:0;cursor:default;
    background:transparent;flex-shrink:0}
  .twk-swatch::-webkit-color-swatch-wrapper{padding:0}
  .twk-swatch::-webkit-color-swatch{border:0;border-radius:5.5px}
  .twk-swatch::-moz-color-swatch{border:0;border-radius:5.5px}

  .twk-chips{display:flex;gap:6px}
  .twk-chip{position:relative;appearance:none;flex:1;min-width:0;height:46px;
    padding:0;border:0;border-radius:6px;overflow:hidden;cursor:default;
    box-shadow:0 0 0 .5px rgba(0,0,0,.12),0 1px 2px rgba(0,0,0,.06);
    transition:transform .12s cubic-bezier(.3,.7,.4,1),box-shadow .12s}
  .twk-chip:hover{transform:translateY(-1px);
    box-shadow:0 0 0 .5px rgba(0,0,0,.18),0 4px 10px rgba(0,0,0,.12)}
  .twk-chip[data-on="1"]{box-shadow:0 0 0 1.5px rgba(0,0,0,.85),
    0 2px 6px rgba(0,0,0,.15)}
  .twk-chip>span{position:absolute;top:0;bottom:0;right:0;width:34%;
    display:flex;flex-direction:column;box-shadow:-1px 0 0 rgba(0,0,0,.1)}
  .twk-chip>span>i{flex:1;box-shadow:0 -1px 0 rgba(0,0,0,.1)}
  .twk-chip>span>i:first-child{box-shadow:none}
  .twk-chip svg{position:absolute;top:6px;left:6px;width:13px;height:13px;
    filter:drop-shadow(0 1px 1px rgba(0,0,0,.3))}
`;

// ── useTweaks ───────────────────────────────────────────────────────────────
// Single source of truth for tweak values. setTweak persists via the host
// (__edit_mode_set_keys → host rewrites the EDITMODE block on disk).
function useTweaks(defaults) {
  const [values, setValues] = React.useState(defaults);
  // Accepts either setTweak('key', value) or setTweak({ key: value, ... }) so a
  // useState-style call doesn't write a "[object Object]" key into the persisted
  // JSON block.
  const setTweak = React.useCallback((keyOrEdits, val) => {
    const edits = typeof keyOrEdits === 'object' && keyOrEdits !== null ? keyOrEdits : {
      [keyOrEdits]: val
    };
    setValues(prev => ({
      ...prev,
      ...edits
    }));
    window.parent.postMessage({
      type: '__edit_mode_set_keys',
      edits
    }, '*');
    // Same-window signal so in-page listeners (deck-stage rail thumbnails)
    // can react — the parent message only reaches the host, not peers.
    window.dispatchEvent(new CustomEvent('tweakchange', {
      detail: edits
    }));
  }, []);
  return [values, setTweak];
}

// ── TweaksPanel ─────────────────────────────────────────────────────────────
// Floating shell. Registers the protocol listener BEFORE announcing
// availability — if the announce ran first, the host's activate could land
// before our handler exists and the toolbar toggle would silently no-op.
// The close button posts __edit_mode_dismissed so the host's toolbar toggle
// flips off in lockstep; the host echoes __deactivate_edit_mode back which
// is what actually hides the panel.
function TweaksPanel({
  title = 'Tweaks',
  children
}) {
  const [open, setOpen] = React.useState(false);
  const dragRef = React.useRef(null);
  const offsetRef = React.useRef({
    x: 16,
    y: 16
  });
  const PAD = 16;
  const clampToViewport = React.useCallback(() => {
    const panel = dragRef.current;
    if (!panel) return;
    const w = panel.offsetWidth,
      h = panel.offsetHeight;
    const maxRight = Math.max(PAD, window.innerWidth - w - PAD);
    const maxBottom = Math.max(PAD, window.innerHeight - h - PAD);
    offsetRef.current = {
      x: Math.min(maxRight, Math.max(PAD, offsetRef.current.x)),
      y: Math.min(maxBottom, Math.max(PAD, offsetRef.current.y))
    };
    panel.style.right = offsetRef.current.x + 'px';
    panel.style.bottom = offsetRef.current.y + 'px';
  }, []);
  React.useEffect(() => {
    if (!open) return;
    clampToViewport();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', clampToViewport);
      return () => window.removeEventListener('resize', clampToViewport);
    }
    const ro = new ResizeObserver(clampToViewport);
    ro.observe(document.documentElement);
    return () => ro.disconnect();
  }, [open, clampToViewport]);
  React.useEffect(() => {
    const onMsg = e => {
      const t = e?.data?.type;
      if (t === '__activate_edit_mode') setOpen(true);else if (t === '__deactivate_edit_mode') setOpen(false);
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({
      type: '__edit_mode_available'
    }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);
  const dismiss = () => {
    setOpen(false);
    window.parent.postMessage({
      type: '__edit_mode_dismissed'
    }, '*');
  };
  const onDragStart = e => {
    const panel = dragRef.current;
    if (!panel) return;
    const r = panel.getBoundingClientRect();
    const sx = e.clientX,
      sy = e.clientY;
    const startRight = window.innerWidth - r.right;
    const startBottom = window.innerHeight - r.bottom;
    const move = ev => {
      offsetRef.current = {
        x: startRight - (ev.clientX - sx),
        y: startBottom - (ev.clientY - sy)
      };
      clampToViewport();
    };
    const up = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  };
  if (!open) return null;
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("style", null, __TWEAKS_STYLE), /*#__PURE__*/React.createElement("div", {
    ref: dragRef,
    className: "twk-panel",
    "data-omelette-chrome": "",
    style: {
      right: offsetRef.current.x,
      bottom: offsetRef.current.y
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-hd",
    onMouseDown: onDragStart
  }, /*#__PURE__*/React.createElement("b", null, title), /*#__PURE__*/React.createElement("button", {
    className: "twk-x",
    "aria-label": "Close tweaks",
    onMouseDown: e => e.stopPropagation(),
    onClick: dismiss
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    className: "twk-body"
  }, children)));
}

// ── Layout helpers ──────────────────────────────────────────────────────────

function TweakSection({
  label,
  children
}) {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "twk-sect"
  }, label), children);
}
function TweakRow({
  label,
  value,
  children,
  inline = false
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: inline ? 'twk-row twk-row-h' : 'twk-row'
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-lbl"
  }, /*#__PURE__*/React.createElement("span", null, label), value != null && /*#__PURE__*/React.createElement("span", {
    className: "twk-val"
  }, value)), children);
}

// ── Controls ────────────────────────────────────────────────────────────────

function TweakSlider({
  label,
  value,
  min = 0,
  max = 100,
  step = 1,
  unit = '',
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label,
    value: `${value}${unit}`
  }, /*#__PURE__*/React.createElement("input", {
    type: "range",
    className: "twk-slider",
    min: min,
    max: max,
    step: step,
    value: value,
    onChange: e => onChange(Number(e.target.value))
  }));
}
function TweakToggle({
  label,
  value,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "twk-row twk-row-h"
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-lbl"
  }, /*#__PURE__*/React.createElement("span", null, label)), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "twk-toggle",
    "data-on": value ? '1' : '0',
    role: "switch",
    "aria-checked": !!value,
    onClick: () => onChange(!value)
  }, /*#__PURE__*/React.createElement("i", null)));
}
function TweakRadio({
  label,
  value,
  options,
  onChange
}) {
  const trackRef = React.useRef(null);
  const [dragging, setDragging] = React.useState(false);
  // The active value is read by pointer-move handlers attached for the lifetime
  // of a drag — ref it so a stale closure doesn't fire onChange for every move.
  const valueRef = React.useRef(value);
  valueRef.current = value;

  // Segments wrap mid-word once per-segment width runs out. The track is
  // ~248px (280 panel − 28 body pad − 4 seg pad), each button loses 12px
  // to its own padding, and 11.5px system-ui averages ~6.3px/char — so 2
  // options fit ~16 chars each, 3 fit ~10. Past that (or >3 options), fall
  // back to a dropdown rather than wrap.
  const labelLen = o => String(typeof o === 'object' ? o.label : o).length;
  const maxLen = options.reduce((m, o) => Math.max(m, labelLen(o)), 0);
  const fitsAsSegments = maxLen <= ({
    2: 16,
    3: 10
  }[options.length] ?? 0);
  if (!fitsAsSegments) {
    // <select> emits strings — map back to the original option value so the
    // fallback stays type-preserving (numbers, booleans) like the segment path.
    const resolve = s => {
      const m = options.find(o => String(typeof o === 'object' ? o.value : o) === s);
      return m === undefined ? s : typeof m === 'object' ? m.value : m;
    };
    return /*#__PURE__*/React.createElement(TweakSelect, {
      label: label,
      value: value,
      options: options,
      onChange: s => onChange(resolve(s))
    });
  }
  const opts = options.map(o => typeof o === 'object' ? o : {
    value: o,
    label: o
  });
  const idx = Math.max(0, opts.findIndex(o => o.value === value));
  const n = opts.length;
  const segAt = clientX => {
    const r = trackRef.current.getBoundingClientRect();
    const inner = r.width - 4;
    const i = Math.floor((clientX - r.left - 2) / inner * n);
    return opts[Math.max(0, Math.min(n - 1, i))].value;
  };
  const onPointerDown = e => {
    setDragging(true);
    const v0 = segAt(e.clientX);
    if (v0 !== valueRef.current) onChange(v0);
    const move = ev => {
      if (!trackRef.current) return;
      const v = segAt(ev.clientX);
      if (v !== valueRef.current) onChange(v);
    };
    const up = () => {
      setDragging(false);
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("div", {
    ref: trackRef,
    role: "radiogroup",
    onPointerDown: onPointerDown,
    className: dragging ? 'twk-seg dragging' : 'twk-seg'
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-seg-thumb",
    style: {
      left: `calc(2px + ${idx} * (100% - 4px) / ${n})`,
      width: `calc((100% - 4px) / ${n})`
    }
  }), opts.map(o => /*#__PURE__*/React.createElement("button", {
    key: o.value,
    type: "button",
    role: "radio",
    "aria-checked": o.value === value
  }, o.label))));
}
function TweakSelect({
  label,
  value,
  options,
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("select", {
    className: "twk-field",
    value: value,
    onChange: e => onChange(e.target.value)
  }, options.map(o => {
    const v = typeof o === 'object' ? o.value : o;
    const l = typeof o === 'object' ? o.label : o;
    return /*#__PURE__*/React.createElement("option", {
      key: v,
      value: v
    }, l);
  })));
}
function TweakText({
  label,
  value,
  placeholder,
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("input", {
    className: "twk-field",
    type: "text",
    value: value,
    placeholder: placeholder,
    onChange: e => onChange(e.target.value)
  }));
}
function TweakNumber({
  label,
  value,
  min,
  max,
  step = 1,
  unit = '',
  onChange
}) {
  const clamp = n => {
    if (min != null && n < min) return min;
    if (max != null && n > max) return max;
    return n;
  };
  const startRef = React.useRef({
    x: 0,
    val: 0
  });
  const onScrubStart = e => {
    e.preventDefault();
    startRef.current = {
      x: e.clientX,
      val: value
    };
    const decimals = (String(step).split('.')[1] || '').length;
    const move = ev => {
      const dx = ev.clientX - startRef.current.x;
      const raw = startRef.current.val + dx * step;
      const snapped = Math.round(raw / step) * step;
      onChange(clamp(Number(snapped.toFixed(decimals))));
    };
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "twk-num"
  }, /*#__PURE__*/React.createElement("span", {
    className: "twk-num-lbl",
    onPointerDown: onScrubStart
  }, label), /*#__PURE__*/React.createElement("input", {
    type: "number",
    value: value,
    min: min,
    max: max,
    step: step,
    onChange: e => onChange(clamp(Number(e.target.value)))
  }), unit && /*#__PURE__*/React.createElement("span", {
    className: "twk-num-unit"
  }, unit));
}

// Relative-luminance contrast pick — checkmarks drawn over a swatch need to
// read on both #111 and #fafafa without per-option configuration. Hex input
// only (#rgb / #rrggbb); named or rgb()/hsl() colors fall through to "light".
function __twkIsLight(hex) {
  const h = String(hex).replace('#', '');
  const x = h.length === 3 ? h.replace(/./g, c => c + c) : h.padEnd(6, '0');
  const n = parseInt(x.slice(0, 6), 16);
  if (Number.isNaN(n)) return true;
  const r = n >> 16 & 255,
    g = n >> 8 & 255,
    b = n & 255;
  return r * 299 + g * 587 + b * 114 > 148000;
}
const __TwkCheck = ({
  light
}) => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 14 14",
  "aria-hidden": "true"
}, /*#__PURE__*/React.createElement("path", {
  d: "M3 7.2 5.8 10 11 4.2",
  fill: "none",
  strokeWidth: "2.2",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  stroke: light ? 'rgba(0,0,0,.78)' : '#fff'
}));

// TweakColor — curated color/palette picker. Each option is either a single
// hex string or an array of 1-5 hex strings; the card adapts — a lone color
// renders solid, a palette renders colors[0] as the hero (left ~2/3) with the
// rest stacked in a sharp column on the right. onChange emits the
// option in the shape it was passed (string stays string, array stays array).
// Without options it falls back to the native color input for back-compat.
function TweakColor({
  label,
  value,
  options,
  onChange
}) {
  if (!options || !options.length) {
    return /*#__PURE__*/React.createElement("div", {
      className: "twk-row twk-row-h"
    }, /*#__PURE__*/React.createElement("div", {
      className: "twk-lbl"
    }, /*#__PURE__*/React.createElement("span", null, label)), /*#__PURE__*/React.createElement("input", {
      type: "color",
      className: "twk-swatch",
      value: value,
      onChange: e => onChange(e.target.value)
    }));
  }
  // Native <input type=color> emits lowercase hex per the HTML spec, so
  // compare case-insensitively. String() guards JSON.stringify(undefined),
  // which returns the primitive undefined (no .toLowerCase).
  const key = o => String(JSON.stringify(o)).toLowerCase();
  const cur = key(value);
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-chips",
    role: "radiogroup"
  }, options.map((o, i) => {
    const colors = Array.isArray(o) ? o : [o];
    const [hero, ...rest] = colors;
    const sup = rest.slice(0, 4);
    const on = key(o) === cur;
    return /*#__PURE__*/React.createElement("button", {
      key: i,
      type: "button",
      className: "twk-chip",
      role: "radio",
      "aria-checked": on,
      "data-on": on ? '1' : '0',
      "aria-label": colors.join(', '),
      title: colors.join(' · '),
      style: {
        background: hero
      },
      onClick: () => onChange(o)
    }, sup.length > 0 && /*#__PURE__*/React.createElement("span", null, sup.map((c, j) => /*#__PURE__*/React.createElement("i", {
      key: j,
      style: {
        background: c
      }
    }))), on && /*#__PURE__*/React.createElement(__TwkCheck, {
      light: __twkIsLight(hero)
    }));
  })));
}
function TweakButton({
  label,
  onClick,
  secondary = false
}) {
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: secondary ? 'twk-btn secondary' : 'twk-btn',
    onClick: onClick
  }, label);
}
Object.assign(window, {
  useTweaks,
  TweaksPanel,
  TweakSection,
  TweakRow,
  TweakSlider,
  TweakToggle,
  TweakRadio,
  TweakSelect,
  TweakText,
  TweakNumber,
  TweakColor,
  TweakButton
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/woerterbuch/tweaks-panel.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Button = __ds_scope.Button;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Avatar = __ds_scope.Avatar;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Eyebrow = __ds_scope.Eyebrow;

__ds_ns.LevelTag = __ds_scope.LevelTag;

__ds_ns.SearchField = __ds_scope.SearchField;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Chip = __ds_scope.Chip;

__ds_ns.TopBar = __ds_scope.TopBar;

__ds_ns.ProgressBar = __ds_scope.ProgressBar;

__ds_ns.ToolCard = __ds_scope.ToolCard;

__ds_ns.WASH = __ds_scope.WASH;

__ds_ns.WordRow = __ds_scope.WordRow;

})();

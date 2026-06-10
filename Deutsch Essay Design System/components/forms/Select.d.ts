import * as React from 'react';

export interface SelectProps {
  /** Small uppercase key shown before the value, e.g. "THEMA". */
  label?: string;
  /** Current value text. */
  value?: React.ReactNode;
  /** Rotates the chevron when true. @default false */
  open?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  style?: React.CSSProperties;
}

/**
 * Pill dropdown trigger — tracked key + value + chevron. Renders the button
 * only; supply your own menu and open-state.
 */
export function Select(props: SelectProps): React.ReactElement;
export default Select;

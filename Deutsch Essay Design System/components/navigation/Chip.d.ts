import * as React from 'react';

export interface ChipProps {
  children?: React.ReactNode;
  /** Selected state — fills graphite and lifts. @default false */
  active?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  style?: React.CSSProperties;
}

/** A category filter pill — quiet at rest, graphite when active. Use in a single-select row. */
export function Chip(props: ChipProps): React.ReactElement;
export default Chip;

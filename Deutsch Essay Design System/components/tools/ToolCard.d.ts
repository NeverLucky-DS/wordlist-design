import * as React from 'react';

export interface ToolCardProps {
  /** Uppercase tool label, e.g. "KLISCHEES". */
  title?: React.ReactNode;
  /** Accent fragment appended after a "·", e.g. "ARGUMENT EINS". */
  accent?: React.ReactNode;
  /** Right-aligned action node (a pager, button, etc.). */
  action?: React.ReactNode;
  children?: React.ReactNode;
  style?: React.CSSProperties;
  bodyStyle?: React.CSSProperties;
}

/** The right-rail titled paper panel — Klischees, inline Wörterbuch, side tools. */
export function ToolCard(props: ToolCardProps): React.ReactElement;
export default ToolCard;

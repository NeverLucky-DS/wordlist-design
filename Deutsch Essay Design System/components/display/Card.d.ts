import * as React from 'react';

/**
 * Props for the paper-sheet container.
 * @startingPoint section="Surfaces" subtitle="Raised paper sheet container" viewport="700x220"
 */
export interface CardProps {
  children?: React.ReactNode;
  /** Shadow depth. @default "md" */
  elevation?: 'flat' | 'sm' | 'md' | 'lg' | 'sheet';
  /** Inner 24px padding. @default true */
  pad?: boolean;
  /** Corner radius. @default "xl" */
  radius?: 'lg' | 'xl' | '2xl';
  style?: React.CSSProperties;
}

/** A sheet of raised white paper — the default lifted container. */
export function Card(props: CardProps): React.ReactElement;
export default Card;

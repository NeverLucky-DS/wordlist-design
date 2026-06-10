import * as React from 'react';

export interface EyebrowProps {
  children?: React.ReactNode;
  /** Colour voice. @default "accent" */
  tone?: 'accent' | 'muted' | 'rose' | 'ink';
  style?: React.CSSProperties;
}

/** Uppercase, wide-tracked kicker above a title or section. */
export function Eyebrow(props: EyebrowProps): React.ReactElement;
export default Eyebrow;

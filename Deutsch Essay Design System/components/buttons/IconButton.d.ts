import * as React from 'react';

export interface IconButtonProps {
  /** A single icon node (SVG). */
  children?: React.ReactNode;
  /** @default "md" */
  size?: 'sm' | 'md' | 'lg';
  /** Accessible label, applied as aria-label. */
  label?: string;
  /** @default false */
  disabled?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  style?: React.CSSProperties;
}

/**
 * Square, hairline-bordered icon control — theme toggles, pager arrows,
 * folder/notes. Warms to accent on hover.
 */
export function IconButton(props: IconButtonProps): React.ReactElement;
export default IconButton;

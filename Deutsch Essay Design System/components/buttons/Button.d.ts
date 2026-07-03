import * as React from 'react';

/**
 * Props for the brand's primary action control.
 * @startingPoint section="Buttons" subtitle="Primary, secondary & ghost actions" viewport="700x200"
 */
export interface ButtonProps {
  /** Button label / content. */
  children?: React.ReactNode;
  /**
   * Visual variant.
   * @default "primary"
   */
  variant?: 'primary' | 'secondary' | 'ghost';
  /** @default "md" */
  size?: 'md' | 'lg';
  /** Optional leading icon node (an SVG). */
  icon?: React.ReactNode;
  /** @default false */
  disabled?: boolean;
  /** @default "button" */
  type?: 'button' | 'submit' | 'reset';
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  style?: React.CSSProperties;
}

/**
 * The brand's primary action control — muted-plum gradient (primary),
 * paper outline (secondary), or quiet ghost. One loud primary per view.
 * @startingPoint section="Buttons" subtitle="Primary, secondary & ghost actions" viewport="700x200"
 */
export function Button(props: ButtonProps): React.ReactElement;
export default Button;

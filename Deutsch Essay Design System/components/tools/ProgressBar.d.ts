import * as React from 'react';

export interface ProgressBarProps {
  value?: number;
  /** @default 100 */
  max?: number;
  /** Optional uppercase label above the track. */
  label?: string;
  /** Show the serif "value / max unit" cap. @default false */
  showCount?: boolean;
  /** Unit word in the count. @default "Wörter" */
  unit?: string;
  style?: React.CSSProperties;
}

/** The writing-goal track — thin rail with the warm accent gradient fill. */
export function ProgressBar(props: ProgressBarProps): React.ReactElement;
export default ProgressBar;

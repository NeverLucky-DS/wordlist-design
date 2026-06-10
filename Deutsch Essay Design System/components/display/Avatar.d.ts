import * as React from 'react';

export interface AvatarProps {
  /** Single initial. @default "D" */
  initial?: string;
  /** Diameter in px. @default 38 */
  size?: number;
  style?: React.CSSProperties;
}

/** Graphite circle with a serif initial — the user mark. */
export function Avatar(props: AvatarProps): React.ReactElement;
export default Avatar;

import * as React from 'react';

export interface LevelTagProps {
  /** CEFR level. @default "B1" */
  level?: 'B1' | 'B2' | 'C1' | string;
  /** Fill with the level's soft watercolor colour (header pill style). @default false */
  tinted?: boolean;
  style?: React.CSSProperties;
}

/** The small CEFR tag (B1·B2·C1) on a word row — quiet hairline or tinted pill. */
export function LevelTag(props: LevelTagProps): React.ReactElement;
export default LevelTag;

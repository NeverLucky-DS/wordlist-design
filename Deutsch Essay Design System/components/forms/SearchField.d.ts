import * as React from 'react';

/**
 * Props for the brand text/search input.
 * @startingPoint section="Forms" subtitle="Search & text input with focus ring" viewport="700x140"
 */
export interface SearchFieldProps {
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** @default "Suche…" */
  placeholder?: string;
  /** Leading icon node. Pass `null` for a plain text field; omit for the search glyph. */
  icon?: React.ReactNode | null;
  /** @default "md" */
  size?: 'sm' | 'md';
  style?: React.CSSProperties;
}

/**
 * The brand's text input, framed as search — leading icon, soft hairline,
 * accent focus ring. Used for the dictionary search and inline lookups.
 */
export function SearchField(props: SearchFieldProps): React.ReactElement;
export default SearchField;

import * as React from 'react';

export interface NavItem {
  label: string;
  active?: boolean;
  dropdown?: boolean;
}

/**
 * Props for the shared site header.
 * @startingPoint section="Navigation" subtitle="Shared sticky site header" viewport="1280x90"
 */
export interface TopBarProps {
  /** Brand words, stacked. @default ["Deutsch","Essay"] */
  brand?: string[];
  /** Centred nav items; mark one `active`. */
  items?: NavItem[];
  onNavClick?: (item: NavItem, index: number) => void;
  /** Override the entire right cluster. Omit for the default theme·avatar·lang. */
  right?: React.ReactNode;
  /** Language pill text. @default "DE" */
  lang?: string;
  /** Avatar initial. @default "D" */
  initial?: string;
  style?: React.CSSProperties;
}

/** The shared, frosted, sticky site header used across every product surface. */
export function TopBar(props: TopBarProps): React.ReactElement;
export default TopBar;

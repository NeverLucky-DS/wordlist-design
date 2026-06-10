import * as React from 'react';

/**
 * Props for the signature watercolor dictionary row.
 * @startingPoint section="Wörterbuch" subtitle="Watercolor dictionary word row" viewport="700x80"
 */
export interface WordRowProps {
  /** Article for nouns: der/die/das. Omit for verbs/adjectives. */
  art?: 'der' | 'die' | 'das' | '';
  /** The German headword. */
  de: string;
  /** Russian gloss, shown italic beneath. */
  ru?: string;
  /** Part of speech — drives the brush and tag. @default "noun" */
  pos?: 'noun' | 'verb' | 'adj';
  /** CEFR level — drives brush colour + tag. @default "B1" */
  level?: 'B1' | 'B2' | 'C1';
  /** Opened/selected — draws the stroke fully in. @default false */
  active?: boolean;
  /** Relative path from the mounting page to the brush folder. @default "assets/brushes/" */
  brushBase?: string;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
  style?: React.CSSProperties;
}

/**
 * The heart of the brand: a dictionary entry painted with its own watercolor
 * brush (level × word-type), German serif headword, italic gloss, level tag.
 * Hover/active draws the hidden continuation of the stroke in.
 */
export function WordRow(props: WordRowProps): React.ReactElement;
export default WordRow;

/** The brush filename map, keyed `"<level>|<der|die|das|verb|adj>"`. */
export const WASH: Record<string, string>;

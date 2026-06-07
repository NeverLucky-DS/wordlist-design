import { WORD_ALTERNATIVES } from "./constants";

const STOP_WORDS = new Set([
  "und",
  "der",
  "die",
  "das",
  "ein",
  "eine",
  "ist",
  "sind",
  "ich",
  "wir",
  "sie",
  "es",
  "in",
  "im",
  "zu",
  "auf",
  "mit",
  "für",
  "von",
  "den",
  "dem",
  "des",
]);

export type WordFocusResult = {
  word: string;
  count: number;
  alternatives: string[];
};

export function findWordFocus(text: string): WordFocusResult | null {
  const tokens = text
    .toLowerCase()
    .replace(/[^a-zäöüß\s]/gi, " ")
    .split(/\s+/)
    .filter((t) => t.length >= 4 && !STOP_WORDS.has(t));

  if (!tokens.length) return null;

  const counts = new Map<string, number>();
  for (const token of tokens) {
    counts.set(token, (counts.get(token) || 0) + 1);
  }

  let bestWord = "";
  let bestCount = 0;
  for (const [word, count] of counts) {
    if (count > bestCount) {
      bestWord = word;
      bestCount = count;
    }
  }

  if (!bestWord) return null;

  const alternatives = WORD_ALTERNATIVES[bestWord] || [];
  return { word: bestWord, count: bestCount, alternatives };
}

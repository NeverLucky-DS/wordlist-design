import type { Word } from "../api";

export const VOCAB_LEVEL_ORDER = ["A2", "B1", "B2", "C1"] as const;

export function groupWordsByLevel(words: Word[]): Array<{ level: string; words: Word[] }> {
  const buckets = new Map<string, Word[]>();

  for (const word of words) {
    const level = (word.level || "B1").toUpperCase();
    const list = buckets.get(level) || [];
    list.push(word);
    buckets.set(level, list);
  }

  const ordered: Array<{ level: string; words: Word[] }> = [];
  for (const level of VOCAB_LEVEL_ORDER) {
    const list = buckets.get(level);
    if (list && list.length > 0) {
      ordered.push({ level, words: list });
    }
  }

  for (const [level, list] of buckets.entries()) {
    if (!VOCAB_LEVEL_ORDER.includes(level as (typeof VOCAB_LEVEL_ORDER)[number])) {
      ordered.push({ level, words: list });
    }
  }

  return ordered;
}

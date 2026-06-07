import type { Word } from "../api";

const ARTICLES = ["der", "die", "das"] as const;

/** Убирает артикль из german, если он уже записан в поле german. */
export function splitGermanLemma(
  german: string,
  article: string | null,
): { lemma: string; article: string | null } {
  let lemma = german.trim();
  let art = article?.trim() || null;

  for (const a of ARTICLES) {
    const prefix = `${a} `;
    if (lemma.toLowerCase().startsWith(prefix)) {
      if (!art) art = a;
      lemma = lemma.slice(prefix.length).trim();
      break;
    }
  }

  return { lemma, article: art };
}

export function formatGermanHeadline(word: Word): string {
  const { lemma, article } = splitGermanLemma(word.german, word.article);
  return article ? `${article} ${lemma}` : lemma;
}

export function wiktionaryLookupTerm(word: Word): string {
  const { lemma } = splitGermanLemma(word.german, word.article);
  return lemma || word.german.trim();
}

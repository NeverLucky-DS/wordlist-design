import type { Word } from "../api";

const BRUSH_BASE = "/assets/wordlist/brushes";

const WASH: Record<string, string> = {
  "B1|der": "B1_Der_Powdery-Blue_Horizontal-Soft.webp",
  "B1|die": "B1_Die_Powdery-Pink_BG-Wash.webp",
  "B1|das": "B1_Das_Pale-Green_BG-Wash.webp",
  "B1|verb": "B1_Verbs_Sandy-Ochre_BG-Wash.webp",
  "B1|adj": "B1_Adjectives_Lavender_BG-Wash.webp",
  "B2|der": "B2_Der_Deep-Blue_BG-Wash.webp",
  "B2|die": "B2_Die_Magenta_BG-Wash.webp",
  "B2|das": "B2_Das_Grass-Green_BG-Wash.webp",
  "B2|verb": "B2_Verbs_Terracotta_BG-Wash.webp",
  "B2|adj": "B2_Adjectives_Amethyst_BG-Wash.webp",
  "C1|der": "C1_Der_Indigo_BG-Wash.webp",
  "C1|die": "C1_Die_Burgundy_BG-Wash.webp",
  "C1|das": "C1_Das_Emerald_BG-Wash.webp",
  "C1|verb": "C1_Verbs_Olive-Ochre_BG-Wash.webp",
  "C1|adj": "C1_Adjectives_Plum_BG-Wash.webp",
};

export const DECOR = {
  bgColumn: "/assets/wordlist/decor/abstract-watercolor-column.webp",
  decorHead: "/assets/wordlist/decor/decor-head.webp",
  verwendung: "/assets/wordlist/decor/Verwendung.webp",
  deklination: "/assets/wordlist/decor/Deklination.webp",
} as const;

export const LVL_ORDER = ["B1", "B2", "C1"] as const;
export type LevelKey = (typeof LVL_ORDER)[number];

export const LVL_COLOR: Record<LevelKey, string> = {
  B1: "var(--site-rose)",
  B2: "var(--site-blue)",
  C1: "var(--site-lav)",
};

function normalizeLevel(level: string): LevelKey {
  const u = level.toUpperCase();
  if (u === "B2" || u === "C1") return u;
  return "B1";
}

function typeKey(word: Word): string {
  const wt = (word.word_type || "").toLowerCase();
  if (wt.includes("verb") || wt === "verb") return "verb";
  if (wt.includes("adj")) return "adj";
  const art = (word.article || "").toLowerCase();
  if (art === "der" || art === "die" || art === "das") return art;
  const g = word.grammar_data;
  if (g && typeof g.type === "string") {
    const t = g.type.toLowerCase();
    if (t === "verb") return "verb";
    if (t === "adjective" || t === "adj") return "adj";
    if (t === "noun") {
      const a = String(g.article ?? word.article ?? "").toLowerCase();
      if (a === "der" || a === "die" || a === "das") return a;
    }
  }
  return "der";
}

export function brushUrlForWord(word: Word): string {
  const level = normalizeLevel(word.level);
  const key = `${level}|${typeKey(word)}`;
  const file = WASH[key] ?? WASH["B1|der"];
  return `url('${BRUSH_BASE}/${file}')`;
}

export function posLabel(word: Word): string {
  const tk = typeKey(word);
  if (tk === "verb") return "Verb";
  if (tk === "adj") return "Adjektiv";
  return "Substantiv";
}

export function speakGerman(text: string): void {
  if (!("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "de-DE";
  u.rate = 0.9;
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

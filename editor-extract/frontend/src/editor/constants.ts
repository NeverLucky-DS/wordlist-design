import type { BlockKey } from "./types";

export const TARGET_WORD_COUNT = 250;

export const EDITORIAL_ASSETS = {
  sidebarDecor: "/assets/editorial/sidebar-decor.png",
  analyseCta: "/assets/editorial/analyse-cta.png",
  annotationNoteBg: "/assets/editorial/annotation-note-bg.webp",
} as const;

export const TONE_STATS_MOCK: Record<
  string,
  { neutral: number; bars: Array<{ label: string; pct: number }> }
> = {
  argumentativ: {
    neutral: 67,
    bars: [
      { label: "neutral", pct: 67 },
      { label: "akademisch", pct: 45 },
      { label: "überzeugend", pct: 72 },
      { label: "persönlich", pct: 28 },
    ],
  },
  erorterung: { neutral: 72, bars: [{ label: "ausgewogen", pct: 80 }, { label: "sachlich", pct: 65 }] },
  kommentar: { neutral: 55, bars: [{ label: "persönlich", pct: 60 }, { label: "expressiv", pct: 40 }] },
  textanalyse: { neutral: 78, bars: [{ label: "analytisch", pct: 85 }, { label: "neutral", pct: 70 }] },
};

export const SECTION_NUMBERS: Record<BlockKey, string> = {
  einleitung: "01",
  argument1: "02",
  argument2: "03",
  schluss: "04",
};

export const WORD_ALTERNATIVES: Record<string, string[]> = {
  heutzutage: ["derzeit", "gegenwärtig", "in der heutigen Zeit"],
  wichtig: ["bedeutsam", "wesentlich", "von Bedeutung"],
  sehr: ["äußerst", "besonders", "überaus"],
  viele: ["zahlreiche", "vielerlei", "etliche"],
};

export const WRITING_TIP =
  "Nutze präzise Verben statt Adjektivketten. Ein klares Beispiel stärkt jeden Argumentationsblock.";

export const BLOCKS: Array<{ key: BlockKey; label: string; hint: string }> = [
  { key: "einleitung", label: "Einleitung", hint: "These und Kontext zum Thema" },
  { key: "argument1", label: "Argument Eins", hint: "Erster Argumentationsstrang mit Beispiel" },
  { key: "argument2", label: "Argument Zwei", hint: "Zweiter Argumentationsstrang mit Beispiel" },
  { key: "schluss", label: "Schluss", hint: "Klare Schlussfolgerung und Position" },
];

export const DEFAULT_PHRASES: Record<
  BlockKey,
  Array<{ text_de: string; translation_ru: string }>
> = {
  einleitung: [
    {
      text_de: "Heutzutage wird oft darüber diskutiert, ob ...",
      translation_ru: "Сегодня часто обсуждают, ...",
    },
    {
      text_de: "Meiner Meinung nach ist dieses Thema sehr wichtig.",
      translation_ru: "На мой взгляд, эта тема очень важна.",
    },
  ],
  argument1: [
    {
      text_de: "Ein wichtiger Vorteil ist, dass ...",
      translation_ru: "Важное преимущество в том, что ...",
    },
    {
      text_de: "Ein gutes Beispiel dafür ist ...",
      translation_ru: "Хороший пример этому — ...",
    },
  ],
  argument2: [
    {
      text_de: "Außerdem sollte man berücksichtigen, dass ...",
      translation_ru: "Кроме того, нужно учитывать, что ...",
    },
    {
      text_de: "Darüber hinaus kann man sagen, dass ...",
      translation_ru: "Кроме этого можно сказать, что ...",
    },
  ],
  schluss: [
    {
      text_de: "Zusammenfassend lässt sich sagen, dass ...",
      translation_ru: "Подводя итог, можно сказать, что ...",
    },
    {
      text_de: "Abschließend bin ich der Meinung, dass ...",
      translation_ru: "В завершение я считаю, что ...",
    },
  ],
};

export const STAGE_HELPERS: Record<BlockKey, Array<{ de: string; ru: string }>> = {
  einleitung: [
    { de: "zunächst", ru: "сначала" },
    { de: "im Allgemeinen", ru: "в целом" },
    { de: "meiner Meinung nach", ru: "по моему мнению" },
  ],
  argument1: [
    { de: "erstens", ru: "во-первых" },
    { de: "zum Beispiel", ru: "например" },
    { de: "außerdem", ru: "кроме того" },
  ],
  argument2: [
    { de: "zweitens", ru: "во-вторых" },
    { de: "darüber hinaus", ru: "более того" },
    { de: "besonders", ru: "особенно" },
  ],
  schluss: [
    { de: "zusammenfassend", ru: "подводя итог" },
    { de: "abschließend", ru: "в завершение" },
    { de: "insgesamt", ru: "в общем" },
  ],
};

export const TONE_BY_TYPE: Record<string, string> = {
  argumentativ: "Чёткая позиция, связки причинности, без лишней эмоции.",
  erorterung: "Сбалансированный тон: тезис, контраргумент, взвешенный вывод.",
  kommentar: "Личная оценка + аргументы, умеренно экспрессивно.",
  textanalyse: "Аналитический тон, опора на текст и цитаты.",
};

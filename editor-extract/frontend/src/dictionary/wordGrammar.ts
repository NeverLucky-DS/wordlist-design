import type { Word } from "../api";

export type GrammarLine = { label: string; value: string };

export type GrammarSection = {
  kicker: string;
  lines: GrammarLine[];
};

export type WordCardModel = {
  status: "ok" | "partial" | "not_found" | "empty";
  statusHint: string;
  typeLabel: string;
  sections: GrammarSection[];
  sourceUrl: string | null;
};

const TYPE_RU: Record<string, string> = {
  noun: "Существительное",
  verb: "Глагол",
  adjective: "Прилагательное",
  adverb: "Наречие",
  unknown: "Слово",
};

function typeFromWord(word: Word): string {
  const g = word.grammar_data;
  if (g && typeof g.type === "string") return g.type;
  const wt = (word.word_type || "").toLowerCase();
  if (wt.includes("noun") || wt.includes("сущ")) return "noun";
  if (wt.includes("verb") || wt.includes("глагол")) return "verb";
  if (wt.includes("adj")) return "adjective";
  return "unknown";
}

function formatForms(forms: unknown): string[] {
  if (!Array.isArray(forms)) return [];
  const lines: string[] = [];
  for (const item of forms) {
    if (!item || typeof item !== "object") continue;
    const row = item as Record<string, unknown>;
    const bits: string[] = [];
    if (row.case) bits.push(String(row.case));
    if (row.sg) bits.push(String(row.sg));
    if (row.pl) bits.push(String(row.pl));
    if (bits.length > 0) lines.push(bits.join(" · "));
  }
  return lines;
}

function pushLine(lines: GrammarLine[], label: string, value: unknown) {
  if (value === null || value === undefined || value === "") return;
  lines.push({ label, value: String(value) });
}

export function buildWordCardModel(word: Word): WordCardModel {
  const g = word.grammar_data;
  const typeKey = typeFromWord(word);
  const typeLabel = TYPE_RU[typeKey] ?? TYPE_RU.unknown;

  if (!g || typeof g !== "object") {
    return {
      status: "empty",
      statusHint: "Грамматика ещё не загружена. Нажмите «Обновить из Wiktionary».",
      typeLabel,
      sections: [],
      sourceUrl: null,
    };
  }

  const status = (g.status as string) || "ok";
  const sourceUrl = typeof g.source_url === "string" ? g.source_url : null;

  if (status === "not_found") {
    return {
      status: "not_found",
      statusHint: "В Wiktionary нет отдельной статьи — попробуйте обновить позже.",
      typeLabel,
      sections: [],
      sourceUrl,
    };
  }

  const sections: GrammarSection[] = [];

  const core: GrammarLine[] = [];
  pushLine(core, "Часть речи", typeLabel);
  pushLine(core, "Артикль", g.article ?? word.article);
  pushLine(core, "Мн. число", g.plural);
  if (core.length > 0) {
    sections.push({ kicker: "Основное", lines: core });
  }

  const gov: GrammarLine[] = [];
  pushLine(gov, "Падеж", g.governing_case);
  pushLine(gov, "Предлог", g.preposition);
  pushLine(gov, "Пример", g.example_governing);
  if (gov.length > 0) {
    sections.push({ kicker: "Управление", lines: gov });
  }

  const formLines = formatForms(g.forms);
  if (formLines.length > 0) {
    sections.push({
      kicker: "Формы",
      lines: formLines.map((value, i) => ({ label: `${i + 1}`, value })),
    });
  }

  const statusHint =
    status === "partial"
      ? "Данные неполные — в заметке только то, что удалось найти."
      : "Краткая выжимка из Wiktionary для учёбы.";

  return {
    status: status === "partial" ? "partial" : "ok",
    statusHint,
    typeLabel,
    sections,
    sourceUrl,
  };
}

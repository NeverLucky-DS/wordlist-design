import type { EssayError } from "../api";
import { BLOCKS } from "./constants";
import type { AnnotationKind, BlockKey } from "./types";

const BLOCK_KEYS = new Set(BLOCKS.map((b) => b.key));

/** Стабильный id ошибки для привязки марки и карточки. */
export function buildErrorId(part: BlockKey, err: EssayError): string {
  const base = `${part}:${err.excerpt || ""}:${err.start}:${err.type || ""}`;
  let hash = 0;
  for (let i = 0; i < base.length; i += 1) {
    hash = (hash * 31 + base.charCodeAt(i)) | 0;
  }
  return `e${Math.abs(hash).toString(36)}`;
}

/** Ищет excerpt в тексте; при дубликатах — ближайший к hintStart. */
export function findExcerptIndex(text: string, excerpt: string, hintStart?: number): number {
  const needle = excerpt.trim();
  if (!needle) return -1;
  if (hintStart == null) return text.indexOf(needle);

  let best = -1;
  let bestDist = Infinity;
  let idx = 0;
  while ((idx = text.indexOf(needle, idx)) >= 0) {
    const dist = Math.abs(idx - hintStart);
    if (dist < bestDist) {
      bestDist = dist;
      best = idx;
    }
    idx += 1;
  }
  return best;
}

export function resolveAnnotationKind(err: EssayError): AnnotationKind {
  const fromApi = (err.annotation_kind || "").toLowerCase();
  if (
    fromApi === "critical" ||
    fromApi === "style" ||
    fromApi === "b2_potential" ||
    fromApi === "good_fragment" ||
    fromApi === "suggestion"
  ) {
    return fromApi as AnnotationKind;
  }

  const severity = (err.severity || "").toLowerCase();
  const type = (err.type || "").toLowerCase();

  if (severity === "suggestion") return "suggestion";
  if (type === "grammar" || severity === "critical") return "critical";
  if (type === "vocabulary" && err.b2_variant_de) return "b2_potential";
  if (type === "style" || type === "weak") return "style";
  if (type === "good" || type === "strength") return "good_fragment";
  return "style";
}

export function isLightError(err: EssayError): boolean {
  const kind = resolveAnnotationKind(err);
  return kind === "suggestion" || kind === "style";
}

/** Привязывает ошибку к тексту блока (по excerpt или индексам). */
export function normalizeErrorForBlock(
  err: EssayError,
  blockText: string,
): EssayError | null {
  if (!blockText.trim()) return null;

  const excerpt = err.excerpt?.trim();
  let start = err.start;
  let end = err.end;

  if (excerpt) {
    const idx = findExcerptIndex(blockText, excerpt, start);
    if (idx >= 0) {
      start = idx;
      end = idx + excerpt.length;
    }
  }

  start = Math.max(0, Math.min(start, blockText.length - 1));
  end = Math.max(start + 1, Math.min(end, blockText.length));
  if (end <= start) return null;

  return { ...err, start, end, orphaned: false };
}

/** Перепривязывает ошибки к актуальному тексту блока по excerpt. */
export function reanchorErrorsForBlock(blockText: string, errors: EssayError[]): EssayError[] {
  if (!blockText.trim()) {
    return errors.map((err) => ({ ...err, orphaned: true }));
  }

  return errors.map((err) => {
    const excerpt = err.excerpt?.trim();
    if (excerpt) {
      const idx = findExcerptIndex(blockText, excerpt, err.start);
      if (idx < 0) return { ...err, orphaned: true };
      return {
        ...err,
        start: idx,
        end: idx + excerpt.length,
        orphaned: false,
      };
    }

    const start = Math.max(0, Math.min(err.start, blockText.length - 1));
    const end = Math.max(start + 1, Math.min(err.end, blockText.length));
    if (end <= start) return { ...err, orphaned: true };
    const slice = blockText.slice(start, end);
    if (!slice.trim()) return { ...err, orphaned: true };
    return { ...err, start, end, orphaned: false };
  });
}

export function reanchorAllBlocks(
  blocks: Record<BlockKey, string>,
  errorsByBlock: Record<BlockKey, EssayError[]>,
): Record<BlockKey, EssayError[]> {
  const out: Record<BlockKey, EssayError[]> = {
    einleitung: [],
    argument1: [],
    argument2: [],
    schluss: [],
  };
  for (const block of BLOCKS) {
    out[block.key] = reanchorErrorsForBlock(blocks[block.key], errorsByBlock[block.key]);
  }
  return out;
}

export function countOrphanedErrors(errorsByBlock: Record<BlockKey, EssayError[]>): number {
  return Object.values(errorsByBlock).reduce(
    (n, list) => n + list.filter((e) => e.orphaned).length,
    0,
  );
}

export function countTotalErrors(errorsByBlock: Record<BlockKey, EssayError[]>): number {
  return Object.values(errorsByBlock).reduce((n, list) => n + list.length, 0);
}

export function buildFallbackErrorsFromBlocks(
  blocks: Record<BlockKey, string>,
): EssayError[] {
  const out: EssayError[] = [];
  for (const block of BLOCKS) {
    const text = blocks[block.key].trim();
    if (!text) continue;
    const end = Math.min(text.length, Math.max(8, Math.min(40, text.length)));
    const excerpt = text.slice(0, end);
    out.push({
      part: block.key,
      excerpt,
      start: 0,
      end,
      type: "style",
      severity: "suggestion",
      annotation_kind: "suggestion",
      explanation_ru:
        "Что не так: Формулировка пока общая.\nПочему: Мысль звучит абстрактно.\nКак исправить: Добавьте пример и связку.",
      correction: "",
      rule: "",
      what_wrong_ru: "Фрагмент можно уточнить.",
      why_bad_ru: "Читателю сложнее уловить вашу мысль.",
      how_to_fix_ru: "1) Добавьте конкретный пример. 2) Уточните причинно-следственную связь.",
    });
  }
  return out;
}

export function mapErrorsToBlocks(
  errors: EssayError[],
  blocks: Record<BlockKey, string>,
  ranges: Record<BlockKey, { start: number; end: number }>,
): Record<BlockKey, EssayError[]> {
  const mapped: Record<BlockKey, EssayError[]> = {
    einleitung: [],
    argument1: [],
    argument2: [],
    schluss: [],
  };

  for (const err of errors) {
    const part = (err.part || "").toLowerCase() as BlockKey;
    let owner: BlockKey | null = null;
    let local = err;

    if (BLOCK_KEYS.has(part)) {
      owner = part;
    } else {
      for (const block of BLOCKS) {
        const range = ranges[block.key];
        if (err.start >= range.start && err.start < range.end) {
          owner = block.key;
          const text = blocks[owner];
          local = {
            ...err,
            start: Math.max(0, err.start - range.start),
            end: Math.min(text.length, err.end - range.start),
          };
          break;
        }
      }
    }

    if (!owner) continue;
    const normalized = normalizeErrorForBlock(local, blocks[owner]);
    if (normalized) {
      mapped[owner].push({
        ...normalized,
        error_id: buildErrorId(owner, normalized),
      });
    }
  }

  return {
    einleitung: mergeOverlappingErrors(mapped.einleitung),
    argument1: mergeOverlappingErrors(mapped.argument1),
    argument2: mergeOverlappingErrors(mapped.argument2),
    schluss: mergeOverlappingErrors(mapped.schluss),
  };
}

export function mergeOverlappingErrors(errors: EssayError[]): EssayError[] {
  if (errors.length <= 1) return errors;
  const sorted = [...errors].sort((a, b) => a.start - b.start);
  const merged: EssayError[] = [];

  for (const err of sorted) {
    const prev = merged[merged.length - 1];
    if (!prev) {
      merged.push(err);
      continue;
    }
    const prevExcerpt = (prev.excerpt || "").trim();
    const errExcerpt = (err.excerpt || "").trim();
    const sameExcerpt = prevExcerpt.length > 0 && prevExcerpt === errExcerpt;
    if (sameExcerpt && err.start <= prev.end) {
      merged[merged.length - 1] = {
        ...prev,
        end: Math.max(prev.end, err.end),
      };
    } else {
      merged.push(err);
    }
  }

  return merged;
}

export function formatExplanation(text: string): { label: string; value: string }[] {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const items = lines
    .map((line) => {
      const idx = line.indexOf(":");
      if (idx < 1) return null;
      const label = line.slice(0, idx).trim();
      const value = line.slice(idx + 1).trim();
      if (!label || !value) return null;
      return { label, value };
    })
    .filter((v): v is { label: string; value: string } => Boolean(v));

  if (items.length > 0) return items;
  return [{ label: "Объяснение", value: text }];
}

export function splitStrategies(text: string): string[] {
  return text
    .split(/\d\)\s+/g)
    .map((line) => line.trim())
    .filter(Boolean);
}

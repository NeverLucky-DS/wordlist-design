import { BLOCKS } from "./constants";
import type { BlockKey } from "./types";

export function buildEssayText(blocks: Record<BlockKey, string>) {
  const ranges: Record<BlockKey, { start: number; end: number }> = {
    einleitung: { start: 0, end: 0 },
    argument1: { start: 0, end: 0 },
    argument2: { start: 0, end: 0 },
    schluss: { start: 0, end: 0 },
  };
  let cursor = 0;
  const chunks: string[] = [];

  BLOCKS.forEach((block, idx) => {
    const header = `${block.label}:\n`;
    const content = blocks[block.key] || "";
    const start = cursor + header.length;
    const end = start + content.length;
    ranges[block.key] = { start, end };

    const piece = `${header}${content}`;
    chunks.push(piece);
    cursor += piece.length;
    if (idx < BLOCKS.length - 1) {
      chunks.push("\n\n");
      cursor += 2;
    }
  });

  return { text: chunks.join(""), ranges };
}

/** Разбирает сохранённый essay.text обратно на блоки редактора. */
export function parseEssayText(text: string): Record<BlockKey, string> {
  const empty: Record<BlockKey, string> = {
    einleitung: "",
    argument1: "",
    argument2: "",
    schluss: "",
  };
  if (!text.trim()) return empty;

  for (const block of BLOCKS) {
    const header = `${block.label}:\n`;
    const start = text.indexOf(header);
    if (start < 0) continue;

    const contentStart = start + header.length;
    let contentEnd = text.length;

    for (const other of BLOCKS) {
      if (other.key === block.key) continue;
      const otherHeader = `\n\n${other.label}:\n`;
      const otherIdx = text.indexOf(otherHeader, contentStart);
      if (otherIdx >= 0 && otherIdx < contentEnd) {
        contentEnd = otherIdx;
      }
    }

    empty[block.key] = text.slice(contentStart, contentEnd).trimEnd();
  }

  const hasAny = BLOCKS.some((b) => empty[b.key].length > 0);
  if (!hasAny) {
    empty.einleitung = text.trim();
  }

  return empty;
}

export function countWords(blocks: Record<BlockKey, string>): number {
  const text = Object.values(blocks).join(" ");
  if (!text.trim()) return 0;
  return text.trim().split(/\s+/).length;
}

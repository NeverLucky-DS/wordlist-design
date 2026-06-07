import type { BlockKey } from "./types";

export const EDITOR_DRAFT_KEY = "deutsch-editor-draft";

export type EditorDraft = {
  essayId: number | null;
  blocks: Record<BlockKey, string>;
  essayMeta: {
    title: string;
    essay_type: string;
    topic: string;
    level: string;
  };
};

export function saveEditorDraft(draft: EditorDraft) {
  try {
    sessionStorage.setItem(EDITOR_DRAFT_KEY, JSON.stringify(draft));
  } catch {
    /* ignore quota errors */
  }
}

export function loadEditorDraft(): EditorDraft | null {
  try {
    const raw = sessionStorage.getItem(EDITOR_DRAFT_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as EditorDraft;
  } catch {
    return null;
  }
}

export function clearEditorDraft() {
  sessionStorage.removeItem(EDITOR_DRAFT_KEY);
}

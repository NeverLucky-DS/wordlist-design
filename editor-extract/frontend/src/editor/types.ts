export type BlockKey = "einleitung" | "argument1" | "argument2" | "schluss";

export type AnnotationKind =
  | "critical"
  | "style"
  | "b2_potential"
  | "good_fragment"
  | "suggestion";

export type SelectedError = { block: BlockKey; error: import("../api").EssayError };

export type ErrorAnchor = {
  block: BlockKey;
  errorId: string;
};

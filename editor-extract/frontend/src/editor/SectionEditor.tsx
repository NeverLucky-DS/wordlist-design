import { EditorContent } from "@tiptap/react";

import type { EssayError } from "../api";
import { useSectionEditor } from "./tiptap/useSectionEditor";

type Props = {
  text: string;
  placeholder: string;
  errors: EssayError[];
  showAnnotations: boolean;
  onTextChange: (value: string) => void;
  onErrorClick: (err: EssayError, errorId: string) => void;
};

export function SectionEditor({
  text,
  placeholder,
  errors,
  showAnnotations,
  onTextChange,
  onErrorClick,
}: Props) {
  const editor = useSectionEditor({
    text,
    placeholder,
    errors,
    showAnnotations,
    onTextChange,
    onErrorClick,
  });

  if (!editor) return null;
  return (
    <div className="manuscript-editor">
      <EditorContent editor={editor} />
    </div>
  );
}

import { useEditor } from "@tiptap/react";
import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
import { useEffect, useRef } from "react";

import type { EssayError } from "../../api";
import { resolveAnnotationKind } from "../errorUtils";
import { AnnotationMark } from "./annotationMark";

type Options = {
  text: string;
  placeholder: string;
  errors: EssayError[];
  showAnnotations: boolean;
  onTextChange: (value: string) => void;
  onErrorClick: (err: EssayError, errorId: string) => void;
};

function toDocContent(value: string) {
  return {
    type: "doc",
    content: [
      {
        type: "paragraph",
        content: value ? [{ type: "text", text: value }] : [],
      },
    ],
  };
}

function refreshMarks(editor: NonNullable<ReturnType<typeof useEditor>>, errors: EssayError[]) {
  const docText = editor.getText();
  const { from, to } = editor.state.selection;
  const markType = editor.schema.marks.annotation;
  if (!markType) return;

  editor
    .chain()
    .command(({ tr, state, dispatch }) => {
      state.doc.descendants((node, pos) => {
        if (!node.isText) return;
        node.marks.forEach((mark) => {
          if (mark.type === markType) {
            tr.removeMark(pos, pos + node.nodeSize, markType);
          }
        });
      });
      if (dispatch) dispatch(tr);
      return true;
    })
    .run();

  const active = errors.filter((err) => !err.orphaned);
  const sorted = [...active].sort((a, b) => b.start - a.start);

  for (const err of sorted) {
    const start = err.start;
    const end = err.end;
    if (end <= start || start < 0 || end > docText.length) continue;

    const fromPos = 1 + start;
    const toPos = 1 + end;
    const kind = resolveAnnotationKind(err);
    const errorId = err.error_id || `e${start}`;
    editor
      .chain()
      .setTextSelection({ from: fromPos, to: toPos })
      .setMark("annotation", { kind, errorId })
      .run();
  }

  const safeFrom = Math.min(from, editor.state.doc.content.size);
  const safeTo = Math.min(to, editor.state.doc.content.size);
  editor.commands.setTextSelection({ from: safeFrom, to: safeTo });
}

export function useSectionEditor({
  text,
  placeholder,
  errors,
  showAnnotations,
  onTextChange,
  onErrorClick,
}: Options) {
  const skipUpdate = useRef(false);
  const errorsRef = useRef(errors);
  errorsRef.current = errors;

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
        bulletList: false,
        orderedList: false,
        blockquote: false,
        codeBlock: false,
        horizontalRule: false,
      }),
      Placeholder.configure({ placeholder }),
      AnnotationMark,
    ],
    content: toDocContent(text),
    editorProps: {
      attributes: { class: "tiptap" },
      handleClick(_view, _pos, event) {
        const span = (event.target as HTMLElement).closest("span[data-error-id]");
        if (!span) return false;
        const errorId = span.getAttribute("data-error-id");
        if (!errorId) return false;
        const err = errorsRef.current.find((e) => e.error_id === errorId);
        if (err) {
          onErrorClick(err, errorId);
          return true;
        }
        return false;
      },
    },
    onUpdate: ({ editor: ed }) => {
      if (skipUpdate.current) return;
      onTextChange(ed.getText());
    },
  });

  useEffect(() => {
    if (!editor) return;
    if (editor.getText() === text) return;
    skipUpdate.current = true;
    editor.commands.setContent(toDocContent(text));
    skipUpdate.current = false;
    if (showAnnotations && errors.length) {
      requestAnimationFrame(() => refreshMarks(editor, errors));
    }
  }, [editor, text]);

  useEffect(() => {
    if (!editor) return;
    skipUpdate.current = true;
    requestAnimationFrame(() => {
      if (showAnnotations && errors.length) {
        refreshMarks(editor, errors);
      } else {
        refreshMarks(editor, []);
      }
      skipUpdate.current = false;
    });
  }, [editor, errors, showAnnotations]);

  return editor;
}

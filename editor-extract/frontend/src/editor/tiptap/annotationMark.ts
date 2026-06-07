import { Mark, mergeAttributes } from "@tiptap/core";

export const AnnotationMark = Mark.create({
  name: "annotation",

  addAttributes() {
    return {
      kind: {
        default: "critical",
        parseHTML: (el) => el.getAttribute("data-annotation") || "critical",
        renderHTML: (attrs) => ({ "data-annotation": attrs.kind }),
      },
      errorId: {
        default: null,
        parseHTML: (el) => el.getAttribute("data-error-id"),
        renderHTML: (attrs) =>
          attrs.errorId != null ? { "data-error-id": String(attrs.errorId) } : {},
      },
    };
  },

  parseHTML() {
    return [{ tag: "span[data-annotation]" }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes(HTMLAttributes), 0];
  },
});

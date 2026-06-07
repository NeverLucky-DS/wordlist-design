import { useLocation } from "react-router-dom";

import { useEditorMetaOptional } from "./editorMetaContext";

export function EditorHeaderChrome() {
  const location = useLocation();
  const meta = useEditorMetaOptional();

  if (!location.pathname.startsWith("/editor") || !meta) return null;

  return (
    <div className="editor-header-chrome">
      <label className="editor-header-level">
        <span className="visually-hidden">Niveau</span>
        <select value={meta.level} onChange={(e) => meta.setLevel(e.target.value)}>
          <option value="B1">B1</option>
          <option value="B2">B2</option>
          <option value="C1">C1</option>
        </select>
      </label>
      <div className="editor-theme-toggle" role="group" aria-label="Theme">
        <button
          type="button"
          className={meta.theme === "dark" ? "" : "is-active"}
          onClick={() => meta.theme !== "light" && meta.toggleTheme()}
          title="Hell"
        >
          ☀
        </button>
        <button
          type="button"
          className={meta.theme === "dark" ? "is-active" : ""}
          onClick={() => meta.theme !== "dark" && meta.toggleTheme()}
          title="Dunkel"
        >
          ☽
        </button>
      </div>
    </div>
  );
}

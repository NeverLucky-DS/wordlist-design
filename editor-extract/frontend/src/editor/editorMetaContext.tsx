import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type EditorMetaContextValue = {
  level: string;
  setLevel: (level: string) => void;
  theme: "light" | "dark";
  toggleTheme: () => void;
};

const EditorMetaContext = createContext<EditorMetaContextValue | null>(null);

export function EditorMetaProvider({ children }: { children: ReactNode }) {
  const [level, setLevel] = useState("B1");
  const [theme, setTheme] = useState<"light" | "dark">("light");

  const value = useMemo(
    () => ({
      level,
      setLevel,
      theme,
      toggleTheme: () => setTheme((t) => (t === "light" ? "dark" : "light")),
    }),
    [level, theme],
  );

  return <EditorMetaContext.Provider value={value}>{children}</EditorMetaContext.Provider>;
}

export function useEditorMeta() {
  const ctx = useContext(EditorMetaContext);
  if (!ctx) throw new Error("useEditorMeta must be used within EditorMetaProvider");
  return ctx;
}

export function useEditorMetaOptional() {
  return useContext(EditorMetaContext);
}

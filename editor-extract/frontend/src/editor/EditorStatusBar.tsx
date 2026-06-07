import { EDITORIAL_ASSETS } from "./constants";

type Props = {
  embedded?: boolean;
  lastAnalyzedAt: string | null;
  analyzing: boolean;
  level: string;
  grade: string | null;
  staleHint?: string | null;
  analyzeProgress?: string | null;
  onAnalyze: () => void;
};

export function EditorStatusBar({
  embedded = false,
  lastAnalyzedAt,
  analyzing,
  level,
  grade,
  staleHint,
  analyzeProgress,
  onAnalyze,
}: Props) {
  return (
    <div className={`editor-status-bar ${embedded ? "is-embedded" : ""}`}>
      <div className="editor-status-left">
        <p className="editor-status-kicker">Letzte Analyse</p>
        <p className="editor-status-last">
          {analyzing && analyzeProgress ? (
            analyzeProgress
          ) : lastAnalyzedAt ? (
            <time dateTime={lastAnalyzedAt}>{formatRelative(lastAnalyzedAt)}</time>
          ) : (
            "Noch keine Analyse"
          )}
        </p>
        {staleHint && !analyzing && <p className="editor-status-stale">{staleHint}</p>}
      </div>
      <button
        type="button"
        className="editor-status-cta-img"
        onClick={onAnalyze}
        disabled={analyzing}
        aria-label={analyzing ? "Analysiere…" : "Analyse starten"}
      >
        <img
          src={EDITORIAL_ASSETS.analyseCta}
          alt=""
          width={220}
          height={138}
          loading="lazy"
          decoding="async"
        />
      </button>
      <div className="editor-status-score" aria-label="Gesamtbewertung">
        <span>Gesamtbewertung</span>
        <strong>{grade ?? level}</strong>
      </div>
    </div>
  );
}

function formatRelative(iso: string): string {
  try {
    const date = new Date(iso);
    const diffMs = Date.now() - date.getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return "gerade eben";
    if (mins < 60) return `vor ${mins} Min.`;
    return date.toLocaleString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

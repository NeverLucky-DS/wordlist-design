import { useCallback, useId, useState, type KeyboardEvent } from "react";

import type { Phrase, TopicMeta, Word } from "../api";
import { EditorStatusBar } from "./EditorStatusBar";
import { KlischeeCard } from "./KlischeeCard";
import { PomodoroTimer } from "./PomodoroTimer";
import { TopicVocabBlock } from "./TopicVocabBlock";
import { TONE_BY_TYPE, TONE_STATS_MOCK, WRITING_TIP } from "./constants";

type DeskTab = "words" | "analyse";

type Props = {
  topic: string;
  topicMeta: TopicMeta | null;
  essayType: string;
  phrases: Phrase[];
  topicWords: Word[];
  sidebarError: string;
  lastAnalyzedAt: string | null;
  analyzing: boolean;
  level: string;
  grade: string | null;
  staleHint?: string | null;
  analyzeProgress?: string | null;
  onAnalyze: () => void;
  onInsertPhrase: (text: string) => void;
  onToggleKnown: (phrase: Phrase, known: boolean) => void;
  onSelectWord: (word: Word) => void;
  selectedWordId: number | null;
};

export function MaterialsDesk({
  topic,
  topicMeta,
  essayType,
  phrases,
  topicWords,
  sidebarError,
  lastAnalyzedAt,
  analyzing,
  level,
  grade,
  staleHint,
  analyzeProgress,
  onAnalyze,
  onInsertPhrase,
  onToggleKnown,
  onSelectWord,
  selectedWordId,
}: Props) {
  const [deskTab, setDeskTab] = useState<DeskTab>("words");
  const baseId = useId();
  const wordsTabId = `${baseId}-words-tab`;
  const analyseTabId = `${baseId}-analyse-tab`;
  const wordsPanelId = `${baseId}-words-panel`;
  const analysePanelId = `${baseId}-analyse-panel`;

  const tone = TONE_BY_TYPE[essayType] || TONE_BY_TYPE.argumentativ;
  const toneStats = TONE_STATS_MOCK[essayType] || TONE_STATS_MOCK.argumentativ;
  const topicLabel = topicMeta?.title_de || topic.trim() || "Thema";

  const onTabKeyDown = useCallback(
    (e: KeyboardEvent<HTMLButtonElement>) => {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();
      setDeskTab((prev) => (prev === "words" ? "analyse" : "words"));
    },
    [],
  );

  return (
    <aside className="materials-desk" aria-label="Schreibwerkzeuge">
      <div className="materials-desk-header">
        <PomodoroTimer />
        <div className="materials-desk-tabs" role="tablist" aria-label="Werkzeuge">
          <button
            type="button"
            id={wordsTabId}
            className={`materials-desk-tab ${deskTab === "words" ? "is-active" : ""}`}
            role="tab"
            aria-selected={deskTab === "words"}
            aria-controls={wordsPanelId}
            tabIndex={deskTab === "words" ? 0 : -1}
            onClick={() => setDeskTab("words")}
            onKeyDown={onTabKeyDown}
          >
            Wörter & Phrasen
          </button>
          <button
            type="button"
            id={analyseTabId}
            className={`materials-desk-tab ${deskTab === "analyse" ? "is-active" : ""}`}
            role="tab"
            aria-selected={deskTab === "analyse"}
            aria-controls={analysePanelId}
            tabIndex={deskTab === "analyse" ? 0 : -1}
            onClick={() => setDeskTab("analyse")}
            onKeyDown={onTabKeyDown}
          >
            Analyse
          </button>
        </div>
      </div>

      {sidebarError && <p className="materials-error">{sidebarError}</p>}

      <div
        id={wordsPanelId}
        className="materials-desk-panel"
        role="tabpanel"
        aria-labelledby={wordsTabId}
        hidden={deskTab !== "words"}
      >
        <KlischeeCard
          phrases={phrases}
          onInsertPhrase={onInsertPhrase}
          onToggleKnown={onToggleKnown}
        />

        <div className="materials-widget materials-widget--vocab">
          <div className="materials-widget-head">
            <p className="materials-widget-kicker">Wörter</p>
            <span className="materials-widget-icon" aria-hidden="true">
              Aa
            </span>
          </div>
          {topicWords.length > 0 ? (
            <TopicVocabBlock
              words={topicWords}
              selectedWordId={selectedWordId}
              onSelectWord={onSelectWord}
            />
          ) : (
            <p className="materials-empty">
              Keine Wörter für «{topicLabel}» in der Datenbank.
            </p>
          )}
        </div>

        <div className="materials-widget materials-widget--tipp">
          <p className="materials-widget-kicker">
            <span aria-hidden="true">💡</span> Tipp des Tages
          </p>
          <p className="materials-tipp-text">{WRITING_TIP}</p>
          <a className="materials-link" href="#editor-summary">
            Mehr erfahren →
          </a>
        </div>
      </div>

      <div
        id={analysePanelId}
        className="materials-desk-panel"
        role="tabpanel"
        aria-labelledby={analyseTabId}
        hidden={deskTab !== "analyse"}
      >
        <EditorStatusBar
          embedded
          lastAnalyzedAt={lastAnalyzedAt}
          analyzing={analyzing}
          level={level}
          grade={grade}
          staleHint={staleHint}
          analyzeProgress={analyzeProgress}
          onAnalyze={onAnalyze}
        />

        <div className="materials-widget materials-widget--tone">
          <div className="materials-widget-head">
            <p className="materials-widget-kicker">Schreibstil</p>
            <a className="materials-link materials-link-inline" href="#editor-summary">
              Details
            </a>
          </div>
          <div className="schreibstil-slider">
            <div className="schreibstil-slider-labels">
              <span>Neutral</span>
              <span>Akademisch</span>
            </div>
            <div className="schreibstil-slider-track" aria-hidden="true">
              <div
                className="schreibstil-slider-thumb"
                style={{ left: `${Math.min(100, Math.max(0, toneStats.neutral))}%` }}
              />
            </div>
          </div>
          <p className="materials-tone-caption">Dein Text klingt: {tone}</p>
        </div>
      </div>
    </aside>
  );
}

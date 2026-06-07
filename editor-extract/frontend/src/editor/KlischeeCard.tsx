import { useCallback, useEffect, useRef, useState } from "react";

import type { Phrase } from "../api";
import { LevelBadge } from "./LevelBadge";

const ROTATE_MS = 7000;

type Props = {
  phrases: Phrase[];
  onInsertPhrase: (text: string) => void;
  onToggleKnown: (phrase: Phrase, known: boolean) => void;
};

/** Self-contained Klischee rotator — auto-advances with a soft fade so the
 *  phrases "flash" through, isolated from the rest of the desk re-renders. */
export function KlischeeCard({ phrases, onInsertPhrase, onToggleKnown }: Props) {
  const [index, setIndex] = useState(0);
  const [animKey, setAnimKey] = useState(0);
  const pausedRef = useRef(false);

  useEffect(() => {
    setIndex(0);
  }, [phrases]);

  const advance = useCallback(
    (dir: number) => {
      if (phrases.length === 0) return;
      setIndex((prev) => (prev + dir + phrases.length) % phrases.length);
      setAnimKey((k) => k + 1);
    },
    [phrases.length],
  );

  useEffect(() => {
    if (phrases.length <= 1) return;
    const id = window.setInterval(() => {
      if (!pausedRef.current) advance(1);
    }, ROTATE_MS);
    return () => window.clearInterval(id);
  }, [phrases.length, advance]);

  if (phrases.length === 0) {
    return (
      <div className="materials-widget materials-widget--phrases">
        <div className="materials-widget-head">
          <p className="materials-widget-kicker">Klischees</p>
        </div>
        <p className="materials-empty">Keine Phrasen für diesen Abschnitt.</p>
      </div>
    );
  }

  const active = phrases[index % phrases.length];

  return (
    <div
      className="materials-widget materials-widget--phrases"
      onMouseEnter={() => {
        pausedRef.current = true;
      }}
      onMouseLeave={() => {
        pausedRef.current = false;
      }}
    >
      <div className="materials-widget-head">
        <p className="materials-widget-kicker">Klischees</p>
        {phrases.length > 1 && (
          <button
            type="button"
            className="materials-widget-icon-btn"
            onClick={() => advance(1)}
            aria-label="Nächste Phrase"
          >
            ↻
          </button>
        )}
      </div>

      <div key={animKey} className="klischee-card klischee-card--flash">
        <div className="phrase-row-head">
          <LevelBadge level={active.level} />
        </div>
        <button
          type="button"
          className="phrase-text"
          onClick={() => onInsertPhrase(active.text_de)}
        >
          {active.text_de}
        </button>
        <p className="phrase-ru">{active.translation_ru || "—"}</p>
        <div className="phrase-actions">
          <button type="button" className="phrase-link" onClick={() => onToggleKnown(active, true)}>
            Known
          </button>
          <button type="button" className="phrase-link" onClick={() => onToggleKnown(active, false)}>
            Learn
          </button>
        </div>
        {phrases.length > 1 && (
          <div className="klischee-dots" aria-hidden="true">
            {phrases.map((phrase, idx) => (
              <span
                key={phrase.id}
                className={`klischee-dot ${idx === index % phrases.length ? "is-active" : ""}`}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

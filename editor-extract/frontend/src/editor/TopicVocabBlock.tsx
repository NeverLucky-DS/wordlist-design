import { useEffect, useMemo, useRef, useState } from "react";

import type { Word } from "../api";
import { WordWashRow } from "../dictionary/WordWashRow";
import { useWordTremble } from "../dictionary/useWordTremble";
import "../dictionary/dictionary.css";

const LEVEL_TABS = ["Alle", "A2", "B1", "B2", "C1"] as const;
type LevelTab = (typeof LEVEL_TABS)[number];

const PAGE_SIZE = 6;

type Props = {
  words: Word[];
  selectedWordId: number | null;
  onSelectWord: (word: Word) => void;
};

export function TopicVocabBlock({ words, selectedWordId, onSelectWord }: Props) {
  const [level, setLevel] = useState<LevelTab>("Alle");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  useWordTremble(listRef);

  const levelCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const w of words) {
      const lv = (w.level || "B1").toUpperCase();
      counts[lv] = (counts[lv] || 0) + 1;
    }
    return counts;
  }, [words]);

  const availableTabs = useMemo(
    () => LEVEL_TABS.filter((t) => t === "Alle" || (levelCounts[t] ?? 0) > 0),
    [levelCounts],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return words.filter((w) => {
      const lv = (w.level || "B1").toUpperCase();
      const okLevel = level === "Alle" || lv === level;
      const okQuery =
        !q ||
        w.german.toLowerCase().includes(q) ||
        (w.translation_ru || "").toLowerCase().includes(q);
      return okLevel && okQuery;
    });
  }, [words, level, query]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const pageItems = filtered.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);

  useEffect(() => {
    setPage(0);
  }, [level, query]);

  return (
    <div className="topic-vocab">
      <div className="topic-vocab-tabs" role="tablist" aria-label="Niveau">
        {availableTabs.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={level === tab}
            className={`topic-vocab-tab${level === tab ? " is-active" : ""}`}
            onClick={() => setLevel(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <label className="topic-vocab-search">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Wort suchen…"
        />
      </label>

      <div ref={listRef} className="topic-vocab-rows" key={`${level}-${safePage}`}>
        {pageItems.length > 0 ? (
          pageItems.map((word) => (
            <WordWashRow
              key={word.id}
              word={word}
              isActive={selectedWordId === word.id}
              onClick={() => onSelectWord(word)}
            />
          ))
        ) : (
          <p className="materials-empty">Keine Wörter gefunden.</p>
        )}
      </div>

      {pageCount > 1 && (
        <div className="topic-vocab-pager">
          <button
            type="button"
            className="topic-vocab-pg-btn"
            disabled={safePage === 0}
            onClick={() => setPage((p) => p - 1)}
            aria-label="Vorherige Seite"
          >
            ‹
          </button>
          <span className="topic-vocab-pg-count">
            {safePage + 1} / {pageCount}
          </span>
          <button
            type="button"
            className="topic-vocab-pg-btn"
            disabled={safePage >= pageCount - 1}
            onClick={() => setPage((p) => p + 1)}
            aria-label="Nächste Seite"
          >
            ›
          </button>
        </div>
      )}
    </div>
  );
}

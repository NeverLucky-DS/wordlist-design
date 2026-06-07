import { useEffect, useState } from "react";

import { fetchWord, refreshWordGrammar, type Word } from "../api";
import { buildWordCardModel } from "../dictionary/wordGrammar";
import { formatGermanHeadline } from "../dictionary/wordDisplay";
import "../dictionary/dictionary.css";

type Props = {
  word: Word;
  onInsert: (text: string) => void;
  onAddTraining: (wordId: number) => void;
  onClose: () => void;
};

export function TopicWordDetail({ word, onInsert, onAddTraining, onClose }: Props) {
  const [full, setFull] = useState<Word>(word);
  const [loading, setLoading] = useState(true);
  const [grammarLoading, setGrammarLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchWord(word.id)
      .then(async (loaded) => {
        if (cancelled) return;
        setFull(loaded);
        const empty =
          !loaded.grammar_data ||
          (typeof loaded.grammar_data === "object" &&
            (loaded.grammar_data as { status?: string }).status === "empty");
        if (empty) {
          setGrammarLoading(true);
          try {
            const refreshed = await refreshWordGrammar(loaded.id);
            if (!cancelled) setFull(refreshed);
          } catch {
            /* грамматика опциональна */
          } finally {
            if (!cancelled) setGrammarLoading(false);
          }
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Fehler");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [word.id]);

  const card = buildWordCardModel(full);
  const headline = formatGermanHeadline(full);

  async function onRefreshGrammar() {
    setGrammarLoading(true);
    setError("");
    try {
      const updated = await refreshWordGrammar(full.id);
      setFull(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Wiktionary-Fehler");
    } finally {
      setGrammarLoading(false);
    }
  }

  return (
    <div className="topic-word-detail" role="region" aria-label={`Wort: ${headline}`}>
      {loading ? (
        <p className="topic-word-detail-loading">Laden…</p>
      ) : (
        <>
          <div className="topic-word-detail-head">
            <p className="topic-word-detail-de">{headline}</p>
            <p className="topic-word-detail-ru">{full.translation_ru}</p>
            <p className="topic-word-detail-type">{card.typeLabel}</p>
            <p className="topic-word-detail-hint">{card.statusHint}</p>
          </div>

          {full.examples.length > 0 && (
            <div className="topic-word-detail-block">
              <p className="topic-word-detail-kicker">Beispiele</p>
              <ul className="topic-word-detail-examples">
                {full.examples.map((ex, idx) => (
                  <li key={idx}>{ex}</li>
                ))}
              </ul>
            </div>
          )}

          {card.sections.length > 0 && (
            <div className="topic-word-detail-block">
              <p className="topic-word-detail-kicker">Грамматика</p>
              {card.sections.map((section) => (
                <div key={section.kicker} className="topic-word-grammar-section">
                  <h4>{section.kicker}</h4>
                  <dl>
                    {section.lines.map((line) => (
                      <div key={`${section.kicker}-${line.label}`} className="topic-word-grammar-row">
                        <dt>{line.label}</dt>
                        <dd>{line.value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              ))}
            </div>
          )}

          <div className="topic-word-detail-actions">
            <button type="button" className="topic-word-action-primary" onClick={() => onInsert(headline)}>
              Einfügen
            </button>
            <button type="button" className="topic-word-action-ghost" onClick={() => onAddTraining(full.id)}>
              + Übung
            </button>
            <button
              type="button"
              className="topic-word-action-ghost"
              onClick={onRefreshGrammar}
              disabled={grammarLoading}
            >
              {grammarLoading ? "Wiktionary…" : "Wiktionary"}
            </button>
            <button type="button" className="topic-word-action-ghost" onClick={onClose}>
              Schließen
            </button>
          </div>
          {error && <p className="topic-word-detail-error">{error}</p>}
          {card.sourceUrl && (
            <a className="topic-word-detail-link" href={card.sourceUrl} target="_blank" rel="noreferrer">
              Wiktionary →
            </a>
          )}
        </>
      )}
    </div>
  );
}

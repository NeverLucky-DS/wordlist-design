import { forwardRef, useMemo, useState } from "react";

import type { Word } from "../api";
import { DECOR, posLabel, speakGerman } from "./brushAssets";
import { buildWordCardModel } from "./wordGrammar";
import { formatGermanHeadline, splitGermanLemma } from "./wordDisplay";

type Props = {
  word: Word;
  loading: boolean;
  error: string;
  wordTitleRef?: React.RefObject<HTMLHeadingElement | null>;
  onClose: () => void;
  onQueue: () => void;
  onRefreshGrammar: () => void;
  onInsert?: () => void;
};

function highlightWordInExample(example: string, lemma: string): string {
  if (!lemma) return example;
  const re = new RegExp(`(${lemma.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  return example.replace(re, "<b>$1</b>");
}

export const WordDetailCard = forwardRef<HTMLElement, Props>(function WordDetailCard(
  { word, loading, error, wordTitleRef, onClose, onQueue, onRefreshGrammar, onInsert },
  ref,
) {
  const [accOpen, setAccOpen] = useState(false);
  const card = buildWordCardModel(word);
  const headline = formatGermanHeadline(word);
  const { lemma, article } = splitGermanLemma(word.german, word.article);
  const category = word.topics[0] ?? "Allgemein";

  const governing = useMemo(() => {
    const g = word.grammar_data;
    if (!g || typeof g !== "object") return null;
    const preposition = g.preposition ? String(g.preposition) : "";
    const governingCase = g.governing_case ? String(g.governing_case) : "";
    const example = g.example_governing ? String(g.example_governing) : "";
    if (!preposition && !governingCase) return null;
    const rule = [preposition, governingCase].filter(Boolean).join(" · ");
    return { rule, example };
  }, [word.grammar_data]);

  const speakText = article ? `${article} ${lemma}` : lemma;

  return (
    <article ref={ref} className="dict-detail">
      <button type="button" className="dict-d-close" onClick={onClose} aria-label="Schließen">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>

      <header className="dict-d-head">
        <div className="dict-d-meta">
          <span className="dict-d-cat">
            <span className="dict-d-cat-hl">{posLabel(word)}</span> · {category}
          </span>
          <span className="dict-d-level">{word.level}</span>
        </div>
        <h2 className="dict-d-word" ref={wordTitleRef}>
          {article ? (
            <>
              <span className="dict-art">{article}</span> {lemma}
            </>
          ) : (
            headline
          )}
        </h2>
        <div className="dict-d-tools">
          <button type="button" className="dict-d-hear" onClick={() => speakGerman(speakText)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M5 9v6h4l5 5V4L9 9H5z" />
              <path fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" d="M16.5 8.5a5 5 0 0 1 0 7" />
            </svg>
            Aussprache
          </button>
        </div>
        <p className="dict-d-ru">{word.translation_ru}</p>
      </header>

      <div className="dict-d-body">
        {loading ? (
          <p className="dict-d-loading">Karte lädt…</p>
        ) : (
          <>
            <section>
              <div className="dict-lab">Bedeutung</div>
              <p className="dict-def">{word.translation_ru}</p>
              {card.statusHint ? <blockquote className="dict-pull">{card.statusHint}</blockquote> : null}
            </section>

            <section>
              <div className="dict-lab">Grammatik</div>
              {governing ? (
                <div
                  className="dict-g-use"
                  style={{ ["--verw-bg" as string]: `url('${DECOR.verwendung}')` }}
                >
                  <span className="dict-g-use-lab">Verwendung</span>
                  <span className="dict-g-use-rule">{governing.rule}</span>
                  {governing.example ? (
                    <span className="dict-g-use-ex">{governing.example}</span>
                  ) : null}
                </div>
              ) : null}

              {card.sections.length > 0 ? (
                <>
                  <button
                    type="button"
                    className={`dict-g-acc-btn${accOpen ? " is-open" : ""}`}
                    onClick={() => setAccOpen((v) => !v)}
                    aria-expanded={accOpen}
                  >
                    <span>Formen &amp; Details</span>
                    <span className="dict-g-arrow">▼</span>
                  </button>
                  {accOpen ? (
                    <div
                      className="dict-g-acc"
                      style={{ ["--decl-bg" as string]: `url('${DECOR.deklination}')` }}
                    >
                      {card.sections.map((section) => (
                        <div key={section.kicker} className="dict-g-section">
                          <h4 className="dict-g-section-title">{section.kicker}</h4>
                          <dl className="dict-g-dl">
                            {section.lines.map((line) => (
                              <div key={`${section.kicker}-${line.label}`} className="dict-g-row">
                                <dt>{line.label}</dt>
                                <dd>{line.value}</dd>
                              </div>
                            ))}
                          </dl>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </>
              ) : (
                <p className="dict-g-empty">
                  Grammatik noch nicht geladen.{" "}
                  <button type="button" className="dict-inline-btn" onClick={onRefreshGrammar}>
                    Aus Wiktionary laden
                  </button>
                </p>
              )}
            </section>

            <section>
              <div className="dict-lab">Beispiele</div>
              <div className="dict-ex-list">
                {word.examples.length > 0 ? (
                  word.examples.map((ex, i) => (
                    <div key={i} className="dict-ex">
                      <span className="dict-ex-n">{String(i + 1).padStart(2, "0")}</span>
                      <div className="dict-ex-body">
                        <p
                          className="dict-ex-de"
                          dangerouslySetInnerHTML={{ __html: highlightWordInExample(ex, lemma) }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="dict-g-empty">Noch keine Beispiele in der Datenbank.</p>
                )}
              </div>
            </section>

            <div className="dict-d-actions">
              {onInsert ? (
                <button type="button" className="dict-btn-primary" onClick={onInsert}>
                  Einfügen
                </button>
              ) : null}
              <button type="button" className={onInsert ? "dict-btn-ghost" : "dict-btn-primary"} onClick={onQueue}>
                In die Übung
              </button>
              <button type="button" className="dict-btn-ghost" onClick={onRefreshGrammar}>
                Wiktionary aktualisieren
              </button>
            </div>
            {error ? <p className="dict-d-error">{error}</p> : null}
            {card.sourceUrl ? (
              <p className="dict-d-source">
                <a href={card.sourceUrl} target="_blank" rel="noreferrer">
                  Wiktionary →
                </a>
              </p>
            ) : null}
          </>
        )}
      </div>
    </article>
  );
});

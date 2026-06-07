import { useEffect, useLayoutEffect, useRef, useState } from "react";

import type { EssayError } from "../api";
import {
  formatExplanation,
  isLightError,
  splitStrategies,
} from "./errorUtils";

type Props = {
  error: EssayError;
  anchorRect: DOMRect;
  onInsert: (text: string) => void;
  onAddToTraining: (phrase: string) => void;
  onClose: () => void;
};

const CARD_WIDTH = 380;
const GAP = 28;

function connectorPath(anchor: DOMRect, card: DOMRect, side: "left" | "right"): string {
  const x1 = side === "right" ? anchor.right - 2 : anchor.left + 2;
  const y1 = anchor.top + anchor.height / 2;
  const x2 = side === "right" ? card.left + 8 : card.right - 8;
  const y2 = card.top + Math.min(48, card.height * 0.2);
  const c1x = x1 + (side === "right" ? 40 : -40);
  const c1y = y1;
  const c2x = x2 + (side === "right" ? -30 : 30);
  const c2y = y2;
  return `M ${x1} ${y1} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${x2} ${y2}`;
}

function whatWrongText(err: EssayError): string {
  return (
    err.what_wrong_ru ||
    formatExplanation(err.explanation_ru).find((x) =>
      x.label.toLowerCase().includes("что"),
    )?.value ||
    formatExplanation(err.explanation_ru)[0]?.value ||
    "Есть неточность в формулировке."
  );
}

function whyBadText(err: EssayError): string {
  return (
    err.why_bad_ru ||
    formatExplanation(err.explanation_ru).find((x) =>
      x.label.toLowerCase().includes("почему"),
    )?.value ||
    ""
  );
}

function computeCardPosition(anchor: DOMRect, cardHeight: number): {
  top: number;
  left: number;
  side: "left" | "right";
} {
  const margin = 16;
  const spaceRight = window.innerWidth - anchor.right - GAP - margin;
  const spaceLeft = anchor.left - GAP - margin;
  const side: "left" | "right" = spaceRight >= CARD_WIDTH || spaceRight >= spaceLeft ? "right" : "left";

  let left =
    side === "right"
      ? anchor.right + GAP
      : anchor.left - GAP - CARD_WIDTH;
  left = Math.max(margin, Math.min(left, window.innerWidth - CARD_WIDTH - margin));

  let top = anchor.top + anchor.height / 2 - cardHeight / 2;
  top = Math.max(margin, Math.min(top, window.innerHeight - cardHeight - margin));

  return { top, left, side };
}

export function AnnotationPopover({
  error,
  anchorRect,
  onInsert,
  onAddToTraining,
  onClose,
}: Props) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [cardRect, setCardRect] = useState<DOMRect | null>(null);
  const [showRule, setShowRule] = useState(false);
  const [layout, setLayout] = useState<{ top: number; left: number; side: "left" | "right" } | null>(
    null,
  );
  const compact = isLightError(error);
  const hints = splitStrategies(error.how_to_fix_ru || "");
  const whyText = whyBadText(error);

  useLayoutEffect(() => {
    const card = cardRef.current;
    if (!card) return;
    const height = card.offsetHeight || 320;
    setLayout(computeCardPosition(anchorRect, height));
    setCardRect(card.getBoundingClientRect());
  }, [anchorRect, error]);

  useEffect(() => {
    const update = () => {
      const card = cardRef.current;
      if (!card) return;
      const height = card.offsetHeight || 320;
      setLayout(computeCardPosition(anchorRect, height));
      setCardRect(card.getBoundingClientRect());
    };
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [anchorRect, error]);

  const style = layout
    ? { top: `${layout.top}px`, left: `${layout.left}px` }
    : { top: `${anchorRect.top}px`, left: `${anchorRect.right + GAP}px`, visibility: "hidden" as const };

  return (
    <>
      <button
        type="button"
        className="annotation-backdrop"
        aria-label="Schließen"
        onClick={onClose}
      />
      {cardRect && layout && (
        <svg className="annotation-connector" aria-hidden="true">
          <path d={connectorPath(anchorRect, cardRect, layout.side)} />
        </svg>
      )}
      <div
        ref={cardRef}
        className={`annotation-popover ${compact ? "compact" : ""}`}
        style={style}
        role="dialog"
        aria-label="Hinweis"
      >
        <p className="annotation-popover-kicker">Редакторская заметка</p>

        <section className="annotation-section annotation-section-problem">
          <h4 className="annotation-section-title">Что не так</h4>
          <p className="annotation-popover-lead">{whatWrongText(error)}</p>
        </section>

        {!compact && whyText && (
          <section className="annotation-section">
            <h4 className="annotation-section-title">Почему важно</h4>
            <p className="annotation-popover-sub">{whyText}</p>
          </section>
        )}

        {!compact && (error.b1_variant_de || error.b2_variant_de) && (
          <section className="annotation-section">
            <h4 className="annotation-section-title">Варианты с вашей мыслью</h4>
            <div className="annotation-variants">
              {error.b1_variant_de && (
                <div className="annotation-variant annotation-variant-b1">
                  <span className="annotation-variant-level">B1</span>
                  <p>{error.b1_variant_de}</p>
                  {error.b1_explain_ru && (
                    <p className="annotation-variant-explain">{error.b1_explain_ru}</p>
                  )}
                  <button type="button" className="btn-ghost" onClick={() => onInsert(error.b1_variant_de || "")}>
                    Einfügen
                  </button>
                </div>
              )}
              {error.b2_variant_de && (
                <div className="annotation-variant annotation-variant-b2">
                  <span className="annotation-variant-level">B2</span>
                  <p>{error.b2_variant_de}</p>
                  {error.b2_explain_ru && (
                    <p className="annotation-variant-explain">{error.b2_explain_ru}</p>
                  )}
                  <button type="button" className="btn-ghost" onClick={() => onInsert(error.b2_variant_de || "")}>
                    Einfügen
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        {hints.length > 0 && (
          <section className="annotation-section annotation-section-tips">
            <h4 className="annotation-section-title">Как улучшить</h4>
            <ol className="annotation-tips">
              {hints.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>
        )}

        {(error.study_phrases_de || []).length > 0 && (
          <section className="annotation-section">
            <h4 className="annotation-section-title">Конструкции для обучения</h4>
            <div className="annotation-phrases">
              {(error.study_phrases_de || []).map((phrase) => (
                <div key={phrase} className="annotation-variant">
                  <p>{phrase}</p>
                  <button type="button" className="btn-ghost" onClick={() => onInsert(phrase)}>
                    Einfügen
                  </button>
                  <button type="button" className="btn-ghost" onClick={() => onAddToTraining(phrase)}>
                    Training
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="annotation-footer">
          {error.rule && (
            <button type="button" className="annotation-footer-link" onClick={() => setShowRule((v) => !v)}>
              Regel anzeigen
            </button>
          )}
          <button type="button" className="annotation-footer-link" onClick={onClose}>
            Schließen
          </button>
        </div>
        {showRule && error.rule && <p className="annotation-rule">{error.rule}</p>}
      </div>
    </>
  );
}

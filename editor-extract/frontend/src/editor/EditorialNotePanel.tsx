import type { EssayError } from "../api";
import {
  formatExplanation,
  isLightError,
  splitStrategies,
} from "./errorUtils";

type Props = {
  error: EssayError;
  onInsert: (text: string) => void;
  onAddToTraining: (phrase: string) => void;
  onClose: () => void;
};

export function EditorialNotePanel({
  error,
  onInsert,
  onAddToTraining,
  onClose,
}: Props) {
  const compact = isLightError(error);

  return (
    <aside className={`editorial-note ${compact ? "compact" : ""}`}>
      <p className="editorial-note-kicker">Редакторская заметка</p>
      <h3>{compact ? "Лёгкая правка" : "Что не так и почему важно"}</h3>

      <div className="editorial-note-section">
        <p>
          {error.what_wrong_ru ||
            formatExplanation(error.explanation_ru)[0]?.value ||
            "Есть неточность в формулировке."}
        </p>
        {!compact && (
          <p>
            {error.why_bad_ru ||
              formatExplanation(error.explanation_ru).find((x) =>
                x.label.toLowerCase().includes("почему"),
              )?.value ||
              "Такой вариант слабее передаёт вашу мысль."}
          </p>
        )}
      </div>

      <div className="editorial-note-section">
        <h4>Как улучшить</h4>
        {splitStrategies(error.how_to_fix_ru || "").length > 0 ? (
          <ul>
            {splitStrategies(error.how_to_fix_ru || "").map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        ) : (
          <p>
            {formatExplanation(error.explanation_ru).find((x) =>
              x.label.toLowerCase().includes("исправ"),
            )?.value || "Сделайте мысль конкретнее и добавьте логическую связку."}
          </p>
        )}
      </div>

      {!compact && (error.b1_variant_de || error.b2_variant_de) && (
        <div className="editorial-note-section">
          <h4>Варианты с вашей мыслью</h4>
          <div className="rewrite-row">
            {error.b1_variant_de && (
              <div className="rewrite-item">
                <h5>B1</h5>
                <p>{error.b1_variant_de}</p>
                {error.b1_explain_ru && <p>{error.b1_explain_ru}</p>}
                <div className="note-actions">
                  <button type="button" onClick={() => onInsert(error.b1_variant_de || "")}>
                    Вставить
                  </button>
                </div>
              </div>
            )}
            {error.b2_variant_de && (
              <div className="rewrite-item">
                <h5>B2</h5>
                <p>{error.b2_variant_de}</p>
                {error.b2_explain_ru && <p>{error.b2_explain_ru}</p>}
                <div className="note-actions">
                  <button type="button" onClick={() => onInsert(error.b2_variant_de || "")}>
                    Вставить
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {(error.study_phrases_de || []).length > 0 && (
        <div className="editorial-note-section">
          <h4>Конструкции для обучения</h4>
          {(error.study_phrases_de || []).map((phrase) => (
            <div key={phrase} className="rewrite-item">
              <p>{phrase}</p>
              <div className="note-actions">
                <button type="button" onClick={() => onInsert(phrase)}>
                  Вставить
                </button>
                <button type="button" onClick={() => onAddToTraining(phrase)}>
                  В тренировку
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="note-actions">
        <button type="button" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </aside>
  );
}

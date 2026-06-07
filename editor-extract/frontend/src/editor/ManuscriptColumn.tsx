import type { EssayAnalysis, EssayError, Word } from "../api";
import { WordDetailCard } from "../dictionary/WordDetailCard";
import { BLOCKS } from "./constants";
import { LineGutter } from "./LineGutter";
import type { BlockKey } from "./types";
import { SectionEditor } from "./SectionEditor";

type Props = {
  blocks: Record<BlockKey, string>;
  activeBlock: BlockKey;
  topic: string;
  blockWordCount: number;
  errorsByBlock: Record<BlockKey, EssayError[]>;
  analysis: EssayAnalysis | null;
  message: string;
  floatWord: Word | null;
  floatWordLoading: boolean;
  floatWordError: string;
  onBlockChange: (block: BlockKey, value: string) => void;
  onFocusBlock: (block: BlockKey) => void;
  onErrorClick: (block: BlockKey, err: EssayError, errorId: string) => void;
  onCloseFloatWord: () => void;
  onQueueFloatWord: () => void;
  onRefreshFloatWord: () => void;
  onInsertFloatWord: () => void;
};

export function ManuscriptColumn({
  blocks,
  activeBlock,
  topic,
  blockWordCount,
  errorsByBlock,
  analysis,
  message,
  floatWord,
  floatWordLoading,
  floatWordError,
  onBlockChange,
  onFocusBlock,
  onErrorClick,
  onCloseFloatWord,
  onQueueFloatWord,
  onRefreshFloatWord,
  onInsertFloatWord,
}: Props) {
  const block = BLOCKS.find((b) => b.key === activeBlock) ?? BLOCKS[0];
  const text = blocks[activeBlock];

  return (
    <div className="editorial-main">
      <div className="manuscript">
        <section
          className="manuscript-section is-active"
          onFocus={() => onFocusBlock(activeBlock)}
        >
          <div className="manuscript-section-head">
            <div>
              <p className="manuscript-topic">{topic || "Thema"}</p>
              <h2 className="manuscript-section-title">{block.label}</h2>
              <p className="manuscript-section-subtitle">{block.hint}</p>
            </div>
            <button type="button" className="manuscript-notes">
              <span aria-hidden="true">✎</span>
              Notizen
            </button>
          </div>

          <div className="manuscript-editor-area">
            {floatWord && (
              <div className="manuscript-word-float">
                <WordDetailCard
                  word={floatWord}
                  loading={floatWordLoading}
                  error={floatWordError}
                  onClose={onCloseFloatWord}
                  onQueue={onQueueFloatWord}
                  onRefreshGrammar={onRefreshFloatWord}
                  onInsert={onInsertFloatWord}
                />
              </div>
            )}

            <div className="manuscript-line-grid">
              <LineGutter text={text} />
              <SectionEditor
                text={text}
                placeholder={`Schreiben Sie Ihre ${block.label} auf Deutsch…`}
                errors={errorsByBlock[activeBlock]}
                showAnnotations={Boolean(analysis)}
                onTextChange={(value) => onBlockChange(activeBlock, value)}
                onErrorClick={(err, errorId) => onErrorClick(activeBlock, err, errorId)}
              />
            </div>
          </div>

          <div className="manuscript-footer">
            <span className="manuscript-footer-spacer" aria-hidden="true" />
            <span className="manuscript-word-count">{blockWordCount} Wörter</span>
          </div>
        </section>

        {analysis && (
          <div className="underline-legend" aria-label="Legende">
            <span>
              <span className="legend-line" /> kritisch
            </span>
            <span>
              <span className="legend-line style" /> Stil
            </span>
            <span>
              <span className="legend-line b2" /> B2
            </span>
            <span>
              <span className="legend-line good" /> gelungen
            </span>
          </div>
        )}

        {analysis && (
          <p className="manuscript-grade">
            Note {analysis.grade} · {analysis.overall_score} / 100
          </p>
        )}
        {analysis?.final_summary && (
          <div className="manuscript-summary" id="editor-summary">
            <p>{analysis.final_summary.overall_comment_ru}</p>
          </div>
        )}
        {message && <p className="manuscript-message">{message}</p>}
      </div>
    </div>
  );
}

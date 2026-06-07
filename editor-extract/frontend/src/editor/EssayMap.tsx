import { BLOCKS, SECTION_NUMBERS, TARGET_WORD_COUNT } from "./constants";
import type { BlockKey } from "./types";

type Props = {
  activeBlock: BlockKey;
  wordCount: number;
  blockWordCounts: Record<BlockKey, number>;
  onJump: (block: BlockKey) => void;
};

export function EssayMap({ activeBlock, wordCount, blockWordCounts, onJump }: Props) {
  const progressPct = Math.min(100, Math.round((wordCount / TARGET_WORD_COUNT) * 100));

  return (
    <nav className="essay-map" aria-label="Essay map">
      <p className="essay-map-kicker">Essay Map</p>

      <div className="essay-map-timeline">
        <div className="essay-map-list">
          {BLOCKS.map((block) => (
            <button
              key={block.key}
              type="button"
              className={`essay-map-item ${activeBlock === block.key ? "is-active" : ""}`}
              onClick={() => onJump(block.key)}
            >
              <span className="essay-map-dot" aria-hidden="true" />
              <span className="essay-map-label">
                {SECTION_NUMBERS[block.key]} {block.label}
              </span>
              <span className="essay-map-hint">{blockWordCounts[block.key]} Wörter</span>
            </button>
          ))}
        </div>
      </div>

      <div className="essay-map-progress">
        <p className="essay-map-progress-label">Fortschritt</p>
        <p className="essay-map-progress-count">
          <strong>{wordCount}</strong>
          <span> / {TARGET_WORD_COUNT} Wörter</span>
        </p>
        <div className="essay-map-progress-bar">
          <div className="essay-map-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>
    </nav>
  );
}

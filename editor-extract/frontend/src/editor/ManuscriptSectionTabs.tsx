import { BLOCKS } from "./constants";
import type { BlockKey } from "./types";

type Props = {
  activeBlock: BlockKey;
  onSelect: (block: BlockKey) => void;
};

export function ManuscriptSectionTabs({ activeBlock, onSelect }: Props) {
  return (
    <nav className="manuscript-tabs" aria-label="Section tabs">
      {BLOCKS.map((block) => (
        <button
          key={block.key}
          type="button"
          className={`manuscript-tab ${activeBlock === block.key ? "is-active" : ""}`}
          onClick={() => onSelect(block.key)}
        >
          {block.label}
        </button>
      ))}
    </nav>
  );
}

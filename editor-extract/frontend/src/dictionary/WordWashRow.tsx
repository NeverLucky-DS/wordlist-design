import { memo } from "react";

import type { Word } from "../api";
import { brushUrlForWord } from "./brushAssets";
import { splitGermanLemma } from "./wordDisplay";

type Props = {
  word: Word;
  isActive: boolean;
  onClick: () => void;
};

function WordWashRowImpl({ word, isActive, onClick }: Props) {
  const { lemma, article } = splitGermanLemma(word.german, word.article);
  const brush = brushUrlForWord(word);

  return (
    <button
      type="button"
      className={`dict-word${isActive ? " is-active" : ""}`}
      data-word-id={word.id}
      onClick={onClick}
      aria-pressed={isActive}
    >
      <span className="dict-wash" style={{ ["--brush" as string]: brush }} aria-hidden="true" />
      <span className="dict-w-body">
        <span className="dict-de">
          {article ? <span className="dict-art">{article} </span> : null}
          {lemma}
        </span>
        <span className="dict-ru">{word.translation_ru}</span>
      </span>
      <span className="dict-w-right">
        <span className="dict-lvl-tag">{word.level}</span>
      </span>
    </button>
  );
}

export const WordWashRow = memo(WordWashRowImpl);

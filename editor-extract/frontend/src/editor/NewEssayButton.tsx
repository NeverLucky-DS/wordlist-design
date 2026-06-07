type Props = {
  onClick: () => void;
};

/** Три стрелки — символ «начать заново». */
function RecycleIcon() {
  return (
    <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">
      <path
        d="M7.2 4.8 9.6 8H5.4L4 6.2A7 7 0 0 1 12 5c1.8 0 3.4.7 4.6 1.8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16.8 19.2 14.4 16H18.6l1.4 1.8A7 7 0 0 1 12 19a6.9 6.9 0 0 1-4.6-1.8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 10v4.5l2.8-1.6M12 14.5 9.2 12.9"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Ручка под углом — «писать снова». */
function PenIcon() {
  return (
    <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true" style={{ transform: "rotate(-35deg)" }}>
      <path
        d="M15.5 4.5 19.5 8.5 9 19H5V15L15.5 4.5z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path
        d="M13.5 6.5 17.5 10.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function NewEssayButton({ onClick }: Props) {
  return (
    <button
      type="button"
      className="editor-new-essay-btn"
      onClick={onClick}
      aria-label="Neues Essay beginnen"
    >
      <span className="editor-new-essay-icons">
        <RecycleIcon />
        <PenIcon />
      </span>
      <span className="editor-new-essay-label">Neues Essay beginnen</span>
    </button>
  );
}

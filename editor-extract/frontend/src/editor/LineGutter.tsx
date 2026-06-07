type Props = {
  text: string;
  minLines?: number;
};

export function LineGutter({ text, minLines = 4 }: Props) {
  const lineCount = Math.max(text.split("\n").length, minLines);

  return (
    <div className="line-gutter" aria-hidden="true">
      {Array.from({ length: lineCount }, (_, idx) => (
        <span key={idx}>{String(idx + 1).padStart(2, "0")}</span>
      ))}
    </div>
  );
}

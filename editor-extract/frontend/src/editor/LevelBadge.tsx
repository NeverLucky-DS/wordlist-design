type Level = "A2" | "B1" | "B2" | "C1" | string;

type Props = {
  level: Level;
  className?: string;
};

export function LevelBadge({ level, className = "" }: Props) {
  const key = level.toUpperCase();
  const variant =
    key === "B1" ? "b1" : key === "B2" ? "b2" : key === "A2" ? "a2" : key === "C1" ? "c1" : "other";

  return (
    <span className={`level-badge level-badge--${variant} ${className}`.trim()} aria-label={`Niveau ${key}`}>
      {key}
    </span>
  );
}

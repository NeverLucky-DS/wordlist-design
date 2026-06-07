import { useCallback, useEffect, useState } from "react";

const FOCUS_SECONDS = 25 * 60;
const BREAK_SECONDS = 5 * 60;

type Phase = "focus" | "break";

function formatTimer(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

/** Self-contained Pomodoro timer — its per-second tick stays local so the rest
 *  of the Materials desk (and the vocab wash rows) never re-render. */
export function PomodoroTimer() {
  const [phase, setPhase] = useState<Phase>("focus");
  const [secondsLeft, setSecondsLeft] = useState(FOCUS_SECONDS);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running) return;
    const id = window.setInterval(() => {
      setSecondsLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => window.clearInterval(id);
  }, [running]);

  useEffect(() => {
    if (secondsLeft > 0) return;
    setRunning(false);
    setPhase((prev) => (prev === "focus" ? "break" : "focus"));
  }, [secondsLeft]);

  useEffect(() => {
    setSecondsLeft(phase === "focus" ? FOCUS_SECONDS : BREAK_SECONDS);
  }, [phase]);

  const total = phase === "focus" ? FOCUS_SECONDS : BREAK_SECONDS;
  const progress = 1 - secondsLeft / total;
  const toggle = useCallback(() => setRunning((r) => !r), []);
  const reset = useCallback(() => {
    setRunning(false);
    setSecondsLeft(phase === "focus" ? FOCUS_SECONDS : BREAK_SECONDS);
  }, [phase]);

  const R = 34;
  const C = 2 * Math.PI * R;

  return (
    <div className={`pomodoro pomodoro--${phase}`}>
      <div className="pomodoro-ring-wrap">
        <svg className="pomodoro-ring" viewBox="0 0 80 80" aria-hidden="true">
          <circle className="pomodoro-ring-bg" cx="40" cy="40" r={R} />
          <circle
            className="pomodoro-ring-fg"
            cx="40"
            cy="40"
            r={R}
            strokeDasharray={C}
            strokeDashoffset={C * (1 - progress)}
            transform="rotate(-90 40 40)"
          />
        </svg>
        <span className="pomodoro-time" aria-live="polite">
          {formatTimer(secondsLeft)}
        </span>
      </div>

      <div className="pomodoro-meta">
        <span className="pomodoro-phase">
          {phase === "focus" ? "Fokus" : "Pause"}
        </span>
        <div className="pomodoro-controls">
          <button
            type="button"
            className="pomodoro-btn pomodoro-btn--main"
            onClick={toggle}
            aria-label={running ? "Pausieren" : "Starten"}
          >
            {running ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M6 5h4v14H6V5zm8 0h4v14h-4V5z" />
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>
          <button
            type="button"
            className="pomodoro-btn"
            onClick={reset}
            aria-label="Zurücksetzen"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
              <path d="M3 3v5h5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

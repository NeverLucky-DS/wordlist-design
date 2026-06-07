import { useEffect, type RefObject } from "react";

/** Micro-jitter on word hover — ported from old_design/js/animations.js */
export function useWordTremble(containerRef: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const root = containerRef.current;
    if (!root) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    let timer: ReturnType<typeof setInterval> | null = null;
    let target: HTMLElement | null = null;

    function reset() {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
      if (target) {
        target.style.transform = "";
        target = null;
      }
    }

    function onOver(e: Event) {
      const de = (e.target as HTMLElement).closest(".dict-word .dict-de") as HTMLElement | null;
      if (!de || !root?.contains(de)) return;
      reset();
      target = de;
      let ticks = 0;
      timer = setInterval(() => {
        if (!target) return;
        ticks += 1;
        const x = (Math.random() - 0.5) * 1.6;
        const r = (Math.random() - 0.5) * 0.6;
        target.style.transform = `translate(${x.toFixed(1)}px,0) rotate(${r.toFixed(2)}deg)`;
        if (ticks > 9) reset();
      }, 100);
    }

    function onOut(e: Event) {
      const de = (e.target as HTMLElement).closest(".dict-word .dict-de");
      if (de === target) reset();
    }

    root.addEventListener("mouseover", onOver);
    root.addEventListener("mouseout", onOut);
    return () => {
      root.removeEventListener("mouseover", onOver);
      root.removeEventListener("mouseout", onOut);
      reset();
    };
  }, [containerRef]);
}

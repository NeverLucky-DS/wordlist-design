import { useEffect, useState } from "react";

import type { ErrorAnchor } from "./types";

/** Живой rect span[data-error-id] — обновляется при scroll/resize. */
export function useLiveAnchorRect(anchor: ErrorAnchor | null): DOMRect | null {
  const [rect, setRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    if (!anchor) {
      setRect(null);
      return;
    }

    const selector = `span[data-error-id="${anchor.errorId}"]`;

    const update = () => {
      const el = document.querySelector(selector);
      setRect(el ? el.getBoundingClientRect() : null);
    };

    update();

    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);

    const manuscript = document.querySelector(".manuscript");
    const observer = manuscript ? new ResizeObserver(update) : null;
    if (manuscript && observer) observer.observe(manuscript);

    const interval = window.setInterval(update, 200);

    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
      observer?.disconnect();
      window.clearInterval(interval);
    };
  }, [anchor?.block, anchor?.errorId]);

  return rect;
}

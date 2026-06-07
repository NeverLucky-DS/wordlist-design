/* =====================================================================
   Deutsch Essay · Editor API bridge (vanilla JS)
   ===================================================================== */

(function () {
  "use strict";

  const API_BASE = window.EDITOR_API_BASE || "";

  const HEADERS_JSON = { "Content-Type": "application/json" };

  function parseMaybeJson(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json();
    }
    return response.text();
  }

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) {
      const payload = await parseMaybeJson(response).catch(() => "");
      const detail =
        payload && typeof payload === "object" && payload.detail
          ? payload.detail
          : typeof payload === "string" && payload
            ? payload
            : `HTTP ${response.status}`;
      throw new Error(detail);
    }
    return parseMaybeJson(response);
  }

  async function createEssay(payload) {
    return request("/api/essays", {
      method: "POST",
      headers: HEADERS_JSON,
      body: JSON.stringify(payload),
    });
  }

  async function updateEssay(essayId, payload) {
    return request(`/api/essays/${essayId}`, {
      method: "PATCH",
      headers: HEADERS_JSON,
      body: JSON.stringify(payload),
    });
  }

  async function listWords(params) {
    const query = new URLSearchParams();
    if (params && params.topic) query.set("topic", params.topic);
    if (params && params.level) query.set("level", params.level);
    if (params && params.q) query.set("q", params.q);
    const qs = query.toString();
    return request(`/api/words${qs ? `?${qs}` : ""}`);
  }

  async function listPhrases(params) {
    const query = new URLSearchParams();
    if (params && params.topic) query.set("topic", params.topic);
    if (params && params.level) query.set("level", params.level);
    if (params && params.part) query.set("part", params.part);
    const qs = query.toString();
    return request(`/api/phrases${qs ? `?${qs}` : ""}`);
  }

  async function queueWord(wordId) {
    return request(`/api/words/${wordId}/queue`, {
      method: "POST",
    });
  }

  async function streamAnalyze(essayId, onEvent) {
    const response = await fetch(`${API_BASE}/api/essays/${essayId}/analyze/stream`, {
      method: "POST",
    });
    if (!response.ok) {
      throw new Error(`Analysefehler (${response.status})`);
    }

    const reader = response.body && response.body.getReader ? response.body.getReader() : null;
    if (!reader) {
      throw new Error("SSE stream not available");
    }

    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() || "";
        frames.forEach((frame) => {
          const line = frame.trim();
          if (!line.startsWith("data: ")) return;
          try {
            onEvent(JSON.parse(line.slice(6)));
          } catch (_) {
            /* ignore malformed partial frame */
          }
        });
      }
    } finally {
      reader.releaseLock();
    }
  }

  async function health() {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  }

  window.EditorApi = {
    baseUrl: API_BASE,
    createEssay,
    updateEssay,
    listWords,
    listPhrases,
    queueWord,
    streamAnalyze,
    health,
  };
})();

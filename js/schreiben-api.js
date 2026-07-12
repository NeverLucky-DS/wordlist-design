/* =====================================================================
   Schreiben · API bridge (essays + streaming Mistral analysis)
   ===================================================================== */
(function () {
  'use strict';

  const API_BASE = '';

  const HEADERS_JSON = { 'Content-Type': 'application/json' };

  const LOG = '[schreiben:api]';
  function log(...args) { try { console.info(LOG, ...args); } catch (_) {} }
  function logErr(...args) { try { console.error(LOG, ...args); } catch (_) {} }

  async function parseMaybeJson(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) return response.json();
    return response.text();
  }

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
      credentials: 'same-origin',
      ...options,
    });
    if (!response.ok) {
      const payload = await parseMaybeJson(response).catch(() => '');
      const detail =
        payload && typeof payload === 'object' && payload.detail
          ? payload.detail
          : typeof payload === 'string' && payload
            ? payload
            : `HTTP ${response.status}`;
      const error = new Error(typeof detail === 'string' ? detail : (detail.message || `HTTP ${response.status}`));
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return parseMaybeJson(response);
  }

  async function createEssay(payload) {
    return request('/api/essays', {
      method: 'POST',
      headers: HEADERS_JSON,
      body: JSON.stringify(payload),
    });
  }

  async function updateEssay(essayId, payload) {
    return request(`/api/essays/${essayId}`, {
      method: 'PATCH',
      headers: HEADERS_JSON,
      body: JSON.stringify(payload),
    });
  }

  async function listEssays() {
    return request('/api/essays');
  }

  async function getEssay(essayId) {
    return request(`/api/essays/${essayId}`);
  }

  async function deleteEssay(essayId) {
    return request(`/api/essays/${essayId}`, { method: 'DELETE' });
  }

  async function createVersion(essayId, reason = 'manual') {
    return request(`/api/essays/${essayId}/versions`, {
      method: 'POST',
      headers: HEADERS_JSON,
      body: JSON.stringify({ reason }),
    });
  }

  async function listVersions(essayId) {
    return request(`/api/essays/${essayId}/versions`);
  }

  async function restoreVersion(essayId, versionId) {
    return request(`/api/essays/${essayId}/versions/${versionId}/restore`, {
      method: 'POST',
    });
  }

  async function startAnalysis(essayId, part = null) {
    return request(`/api/essays/${essayId}/analyses`, {
      method: 'POST',
      headers: HEADERS_JSON,
      body: JSON.stringify({ part }),
    });
  }

  async function listAnalyses(essayId) {
    return request(`/api/essays/${essayId}/analyses`);
  }

  async function getAnalysis(essayId, analysisId) {
    return request(`/api/essays/${essayId}/analyses/${analysisId}`);
  }

  async function getActiveAnalysis(essayId) {
    return request(`/api/essays/${essayId}/analyses/active`);
  }

  async function cancelAnalysis(essayId, analysisId) {
    return request(`/api/essays/${essayId}/analyses/${analysisId}/cancel`, {
      method: 'POST',
    });
  }

  function dispatchSseBuffer(buffer, onEvent) {
    const frames = buffer.split('\n\n');
    const rest = frames.pop() || '';
    frames.forEach((frame) => {
      const line = frame.split('\n').map(l => l.trim()).find(l => l.startsWith('data: '));
      if (!line) return;
      try {
        onEvent(JSON.parse(line.slice(6)));
      } catch (_) { /* malformed frame */ }
    });
    return rest;
  }

  async function streamAnalyze(essayId, onEvent, part) {
    const qs = part ? `?part=${encodeURIComponent(part)}` : '';
    const url = `${API_BASE}/api/essays/${essayId}/analyze/stream${qs}`;
    log('streamAnalyze → POST', url);
    const startedAt = Date.now();
    let response;
    try {
      response = await fetch(url, { method: 'POST' });
    } catch (err) {
      logErr('streamAnalyze fetch failed (network/CORS?)', err);
      throw err;
    }
    log('streamAnalyze response', response.status, response.statusText);
    if (!response.ok) {
      logErr('streamAnalyze HTTP error', response.status);
      throw new Error(`Analysefehler (${response.status})`);
    }

    const reader = response.body && response.body.getReader ? response.body.getReader() : null;
    if (!reader) {
      logErr('streamAnalyze: SSE stream not available (no readable body)');
      throw new Error('SSE stream not available');
    }

    const counts = {};
    const decoder = new TextDecoder();
    let buffer = '';
    const wrapped = (event) => {
      if (event && event.type) counts[event.type] = (counts[event.type] || 0) + 1;
      onEvent(event);
    };
    try {
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });
        buffer = dispatchSseBuffer(buffer, wrapped);
      }
      buffer += decoder.decode();
      dispatchSseBuffer(buffer + '\n\n', wrapped);
    } finally {
      reader.releaseLock();
    }
    log('streamAnalyze done in', Date.now() - startedAt, 'ms · events', counts);
    if (!counts.done) logErr('streamAnalyze: stream ended without a "done" event', counts);
  }

  async function health() {
    try {
      const response = await fetch(`${API_BASE}/health`);
      log('health', response.status, '→', response.ok);
      return response.ok;
    } catch (err) {
      logErr('health check failed (backend unreachable?)', err);
      return false;
    }
  }

  window.SchreibenApi = {
    createEssay,
    updateEssay,
    listEssays,
    getEssay,
    deleteEssay,
    createVersion,
    listVersions,
    restoreVersion,
    startAnalysis,
    listAnalyses,
    getAnalysis,
    getActiveAnalysis,
    cancelAnalysis,
    streamAnalyze,
    health,
  };
})();

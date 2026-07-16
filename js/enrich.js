/* =====================================================================
   Server-side enrichment — the CONTROL panel.
   The key is attached to the logged-in ACCOUNT (encrypted server-side via
   /api/auth/mistral-key) and the SERVER calls Mistral with it. This page only
   saves the key, starts/stops the account's worker, and polls progress.
   The Mistral key never lives in the browser.
   ===================================================================== */
'use strict';

(function () {
  const $ = id => document.getElementById(id);
  const fmt = n => (n == null ? "–" : n.toLocaleString("ru-RU"));
  const esc = s => (s || "").replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const toast = window.toast || (m => { const t = $("toast"); if (!t) return; t.textContent = m; t.classList.add("on"); setTimeout(() => t.classList.remove("on"), 2600); });

  let auth = { authenticated: false, has_mistral_key: false, key_storage_enabled: false };
  let running = false, pollT = null;

  const jget = async p => (await fetch(p, { credentials: "same-origin" })).json();
  async function jsend(method, path, body) {
    const r = await fetch(path, {
      method, credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: body == null ? undefined : JSON.stringify(body),
    });
    return r;
  }

  // ── auth + key state ──
  async function loadAuth() {
    try { auth = await jget("/api/auth/me"); } catch { auth = {}; }
    paint();
  }

  function paint() {
    const enabled = auth.key_storage_enabled;
    const authed = auth.authenticated;
    const hasKey = auth.has_mistral_key;

    if (!enabled) {
      $("keyState").innerHTML = `<span class="warn">Хранение ключей выключено на сервере (нет MISTRAL_KEY_SECRET).</span>`;
      $("mkey").disabled = $("saveKey").disabled = true;
      $("enrBtn").disabled = true;
      if (!running) setStage("Обогащение недоступно: сервер без секрета шифрования.");
      return;
    }
    if (!authed) {
      $("keyState").innerHTML = `<a href="schreiben.html">Войди в аккаунт</a>, чтобы привязать ключ Mistral.`;
      $("mkey").disabled = $("saveKey").disabled = true;
      $("clearKey").hidden = true;
      $("enrBtn").disabled = true;
      if (!running) setStage("Войди в аккаунт и добавь ключ Mistral, чтобы начать.");
      return;
    }
    $("mkey").disabled = $("saveKey").disabled = false;
    $("keyState").innerHTML = hasKey
      ? `<span class="ok">✓ ключ привязан к аккаунту <code>${esc(auth.user && auth.user.email || "")}</code> (зашифрован)</span>`
      : `ключ не привязан к аккаунту <code>${esc(auth.user && auth.user.email || "")}</code>`;
    $("clearKey").hidden = !hasKey;
    $("mkey").placeholder = hasKey ? "ключ привязан — введи новый, чтобы заменить" : "Ключ Mistral (шифруется в БД)…";
    if (!running) {
      $("enrBtn").disabled = !hasKey;
      setStage(hasKey ? "Готов к запуску." : "Добавь ключ Mistral, чтобы начать.");
    }
  }

  $("saveKey").onclick = async () => {
    const v = $("mkey").value.trim();
    if (!v) { toast("Вставь ключ Mistral"); return; }
    $("saveKey").disabled = true;
    const r = await jsend("PUT", "/api/auth/mistral-key", { key: v });
    $("saveKey").disabled = false;
    if (r.status === 204) { $("mkey").value = ""; toast("Ключ сохранён"); await loadAuth(); }
    else if (r.status === 400) { toast("Mistral отклонил этот ключ"); }
    else if (r.status === 401) { toast("Сначала войди в аккаунт"); }
    else if (r.status === 503) { toast("Хранение ключей выключено на сервере"); }
    else { toast("Не удалось сохранить ключ"); }
  };
  $("clearKey").onclick = async () => {
    if (running) await stop();
    const r = await jsend("DELETE", "/api/auth/mistral-key");
    if (r.status === 204) { toast("Ключ удалён"); await loadAuth(); }
    else toast("Не удалось удалить ключ");
  };
  $("mkey").addEventListener("keydown", e => { if (e.key === "Enter") $("saveKey").click(); });

  // ── start / stop the server worker ──
  async function start() {
    setStage("Планирую починку…");     // the first Start scans the base first
    const r = await jsend("POST", "/api/vocab/enrich/start", {});
    if (r.status === 400) { toast("Сначала привяжи ключ Mistral"); return; }
    if (r.status === 401) { toast("Сначала войди в аккаунт"); return; }
    if (!r.ok) { toast("Не удалось запустить"); return; }
    running = true; paintBtn(); setStage("Сервер обогащает словарь…");
    // The plan comes back only for whoever started first; the rest just join in.
    const plan = ((await r.json().catch(() => ({}))) || {}).plan || {};
    const queued = (plan.repair_case || 0) + (plan.repair_ortho || 0);
    if (queued) toast(`В починку: ${fmt(queued)} слов.`);
    startPoll(); refreshProgress();
  }
  async function stop() {
    await jsend("POST", "/api/vocab/enrich/stop", {});
    running = false; paintBtn(); setStage("Остановлено (сервер завершит текущий батч).");
  }
  function paintBtn() {
    const b = $("enrBtn");
    b.classList.toggle("stop", running);
    b.textContent = running ? "Остановить" : "Запустить обогащение";
    b.disabled = false;
  }
  $("enrBtn").onclick = () => (running ? stop() : start());

  // ── progress ──
  function setStage(t) { $("enrStage").textContent = t; }

  // One button runs several kinds of work in order (fix the homograph
  // duplicates, then the pre-1996 spellings, then the backfill). The server
  // picks the phase from the DB — this only reports what it chose.
  function paintPhases(p) {
    const el = $("enrPhases");
    if (!el) return;
    const phases = p.phases || [];
    if (!phases.length) { el.innerHTML = ""; return; }
    const active = phases.findIndex(x => x.remaining > 0);
    el.innerHTML = phases.map((ph, i) => {
      const done = ph.remaining === 0;
      const on = i === active;
      // A repair phase has a planned size, so it can show "осталось 12 из 1274".
      // The backfill has none — its progress is the big bar above.
      const left = done ? "готово"
        : ph.total ? `осталось ${fmt(ph.remaining)} из ${fmt(ph.total)}`
        : `осталось ${fmt(ph.remaining)}`;
      return `<li class="phase ${done ? "done" : ""} ${on ? "on" : ""}">
        <b>${esc(ph.title)}</b><span>${left}</span></li>`;
    }).join("");
  }

  function stageText(p) {
    if (!p.phase) return "Всё обогащено — очередь пуста.";
    const n = (p.phases || []).findIndex(x => x.name === p.phase) + 1;
    const total = (p.phases || []).length;
    return `Этап ${n}/${total}: ${p.phase_title}`;
  }

  async function refreshMine() {
    if (!auth.authenticated) { running = false; return; }
    try {
      const s = await jget("/api/vocab/enrich/status");
      const wasRunning = running;
      running = !!s.running;
      if (wasRunning !== running) paintBtn();
      if (s.reason && !running) setStage("Готово: " + s.reason);
      $("enrRate").textContent = running && s.rate
        ? `${s.rate} слов/с · этот аккаунт ${fmt(s.done)}` : "";
    } catch {}
  }

  async function refreshProgress() {
    let p;
    try { p = await jget("/api/vocab/enrich/progress"); } catch { return; }
    if (!p.exists) { $("enrKpis").innerHTML = `<div class="empty">База ещё не собрана.</div>`; return; }
    $("enrFill").style.width = p.pct + "%";
    paintPhases(p);
    if (running) setStage(stageText(p));
    const workers = (p.workers || []).length;
    $("enrKpis").innerHTML =
      `<div class="kpi"><b>${fmt(p.enriched)}</b><span>обогащено · ${p.pct}%</span></div>
       <div class="kpi"><b>${fmt(p.remaining)}</b><span>осталось</span></div>
       <div class="kpi"><b>${fmt(p.in_flight)}</b><span>в работе</span></div>
       <div class="kpi"><b>${fmt(workers)}</b><span>активных аккаунтов</span></div>
       ${p.skipped ? `<div class="kpi"><b>${fmt(p.skipped)}</b><span>отсеяно (не слова)</span></div>` : ""}
       ${p.failed ? `<div class="kpi"><b>${fmt(p.failed)}</b><span>не удалось</span></div>` : ""}
       ${p.low_confidence ? `<div class="kpi"><b>${fmt(p.low_confidence)}</b><span>низкая уверенность</span></div>` : ""}`;
    const feed = (p.recent || []).map(w =>
      `<span class="ew ${w.confidence === 'low' ? 'low' : ''}"><b>${esc(w.lemma)}</b> ${esc(w.ru || '')}${w.topic ? ` <i>#${esc(w.topic)}</i>` : ''}</span>`
    ).join("");
    $("enrFeed").innerHTML = feed || `<div class="empty">Пока ничего не обогащено — нажми «Запустить».</div>`;
    paintRequeue(p.low_confidence || 0);
    await refreshMine();
  }
  function startPoll() { if (!pollT) pollT = setInterval(refreshProgress, 2500); }

  // ── requeue low-confidence ──
  function paintRequeue(lowCount) {
    const row = $("reqRow"), btn = $("requeueLow"), note = $("reqNote");
    if (!row) return;
    if (lowCount > 0) {
      row.hidden = false;
      note.textContent = `${fmt(lowCount)} карточек с низкой уверенностью.`;
      btn.hidden = !auth.authenticated;
      btn.textContent = `Переобогатить низкую уверенность (${fmt(lowCount)})`;
    } else {
      row.hidden = true;
    }
  }
  const requeueBtn = $("requeueLow");
  if (requeueBtn) requeueBtn.onclick = async () => {
    requeueBtn.disabled = true;
    const r = await jsend("POST", "/api/vocab/enrich/requeue", { scope: "low_confidence" });
    requeueBtn.disabled = false;
    if (r.status === 401) { toast("Сначала войди в аккаунт"); return; }
    if (!r.ok) { toast("Не удалось переобогатить"); return; }
    const j = await r.json();
    toast(`В очередь на переобогащение: ${fmt(j.requeued)}. Запусти обогащение.`);
    refreshProgress(); loadCards(true);
  };

  // ── enriched-card browser ──
  const GRAM = { genitiv: "Gen.", plural: "мн.", praeteritum: "Prät.",
    partizip2: "Part. II", hilfsverb: "всп.", komparativ: "сравн.", superlativ: "превосх." };
  const POS_RU = { noun: "сущ.", verb: "глаг.", adj: "прил.", adv: "нареч.", other: "—" };
  const LVL_CLR = { a1: "--a1", a2: "--a2", b1: "--b1", b2: "--b2", c1: "--c1", c2: "--c2", unlisted: "--ext" };

  let cq = "", cconf = "", cOffset = 0, cTotal = 0, cDeb = null;

  function bold(s) { return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>"); }

  function cardRow(c) {
    const art = c.article ? `<span class="art">${esc(c.article)}</span> ` : "";
    const L = LVL_CLR[c.level] || "--muted";
    const lvl = (c.level || "?").toUpperCase();
    const rus = (c.ru_all && c.ru_all.length ? c.ru_all : [c.ru]).filter(Boolean);
    const tr = rus.slice(0, 3).join("; ") + (rus.length > 3 ? "…" : "");
    return `<div class="word ${c.confidence === 'low' ? 'lowc' : ''}">
      <div class="row" data-lemma="${esc(c.lemma)}">
        <span class="lemma">${art}${esc(c.lemma)}</span>
        <span class="tag" style="background:var(${L})">${esc(lvl)}</span>
        <span class="tr">${esc(tr)}</span>
        ${c.confidence === 'low' ? '<span class="cflag">низкая</span>' : ''}
      </div><div class="detail"></div></div>`;
  }

  function cardDetail(c) {
    const rus = (c.ru_all && c.ru_all.length ? c.ru_all : [c.ru]).filter(Boolean);
    let h = `<div class="k">переводы (${rus.length})</div>
      <div class="chips">${rus.map(r => `<span class="tchip">${esc(r)}</span>`).join("")}</div>`;
    if (c.definition_de) h += `<div class="k">определение (de)</div><div>${esc(c.definition_de)}</div>`;
    const gk = Object.keys(c.grammar || {}).filter(k => c.grammar[k]);
    if (gk.length) h += `<div class="k">грамматика</div><div class="gram">${
      gk.map(k => `<span><i>${GRAM[k] || k}</i> ${esc(c.grammar[k])}</span>`).join("")}</div>`;
    if (c.rektion) h += `<div class="k">управление</div><div>${esc(c.rektion)}</div>`;
    if (c.synonyms && c.synonyms.length)
      h += `<div class="k">синонимы (de)</div><div>${esc(c.synonyms.join(" · "))}</div>`;
    if (c.collocations && c.collocations.length)
      h += `<div class="k">коллокации</div><div>${esc(c.collocations.join(" · "))}</div>`;
    if (c.examples && c.examples.length) {
      h += `<div class="k">примеры</div>`;
      h += c.examples.map(e => `<div class="ex"><span class="de">${bold(e.de)}</span><span class="ru">${esc(e.ru)}</span></div>`).join("");
    }
    const meta = [POS_RU[c.pos] || c.pos, c.topic ? "#" + c.topic : "", c.register, c.model]
      .filter(Boolean).map(esc).join("  ·  ");
    h += `<div class="cmeta">${meta}</div>`;
    return h;
  }

  const cardCache = {};
  async function toggleCardDetail(row, lemma) {
    const d = row.nextElementSibling;
    if (d.classList.contains("open")) { d.classList.remove("open"); return; }
    let c = cardCache[lemma];
    if (!c) {
      try { c = await jget(`/api/vocab/enrich/card/${encodeURIComponent(lemma)}`); }
      catch { return; }
      cardCache[lemma] = c;
    }
    d.innerHTML = cardDetail(c); d.classList.add("open");
  }

  async function loadCards(reset) {
    if (reset) cOffset = 0;
    let r;
    const url = `/api/vocab/enrich/cards?q=${encodeURIComponent(cq)}&confidence=${cconf}&limit=30&offset=${cOffset}`;
    try { r = await jget(url); } catch { return; }
    cTotal = r.total || 0;
    const el = $("cardResults");
    const rows = (r.items || []).map(cardRow).join("");
    if (reset) el.innerHTML = rows || `<div class="empty">Пока нет обогащённых карточек.</div>`;
    else el.insertAdjacentHTML("beforeend", rows);
    el.querySelectorAll(".row").forEach(row => {
      if (row.dataset.bound) return;
      row.dataset.bound = "1";
      row.onclick = () => toggleCardDetail(row, row.dataset.lemma);
    });
    cOffset += (r.items || []).length;
    $("cardCount").textContent = cTotal ? `${fmt(cTotal)} карточек` : "";
    $("cardMore").hidden = cOffset >= cTotal;
  }

  const cqInput = $("cq");
  if (cqInput) cqInput.oninput = () => { clearTimeout(cDeb); cDeb = setTimeout(() => { cq = cqInput.value.trim(); loadCards(true); }, 220); };
  document.querySelectorAll("#cconf button").forEach(b => b.onclick = () => {
    document.querySelectorAll("#cconf button").forEach(x => x.classList.remove("on"));
    b.classList.add("on"); cconf = b.dataset.c; loadCards(true);
  });
  const moreBtn = $("cardMore");
  if (moreBtn) moreBtn.onclick = () => loadCards(false);

  // init
  loadAuth();
  refreshProgress();
  loadCards(true);
  startPoll();
})();

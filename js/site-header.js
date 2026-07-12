/* Shared site-header behaviour for Essay, Pipeline and Wörterbuch. */
(function () {
  const theme = document.getElementById("themeBtn");
  if (theme) {
    theme.setAttribute("aria-pressed", "false");
    theme.addEventListener("click", () => {
      const dimmed = document.body.classList.toggle("theme-dim");
      theme.setAttribute("aria-pressed", String(dimmed));
    });
  }

  const avatar = document.querySelector(".topbar .avatar");
  if (!avatar) return;

  let authState = { authenticated: false, user: null };
  avatar.setAttribute("role", "button");
  avatar.setAttribute("tabindex", "0");
  avatar.setAttribute("aria-label", "Konto öffnen");

  const shell = document.createElement("div");
  shell.className = "auth-shell";
  shell.hidden = true;
  shell.innerHTML = `
    <button class="auth-backdrop" type="button" aria-label="Schließen"></button>
    <section class="auth-dialog" role="dialog" aria-modal="true" aria-labelledby="authTitle">
      <button class="auth-close" type="button" aria-label="Schließen">×</button>
      <div class="auth-guest">
        <p class="auth-kicker">Dein Schreibraum</p>
        <h2 id="authTitle">Konto</h2>
        <div class="auth-tabs" role="tablist">
          <button type="button" data-mode="login" class="active">Anmelden</button>
          <button type="button" data-mode="register">Registrieren</button>
        </div>
        <form class="auth-form">
          <label>E-Mail<input name="email" type="email" autocomplete="email" required></label>
          <label>Passwort<input name="password" type="password" minlength="8" maxlength="128" autocomplete="current-password" required></label>
          <p class="auth-error" role="alert"></p>
          <button class="auth-submit" type="submit">Anmelden</button>
        </form>
        <p class="auth-note">Als Gast bleiben Essays 30 Tage erhalten.</p>
      </div>
      <div class="auth-account" hidden>
        <p class="auth-kicker">Angemeldet als</p>
        <h2 class="auth-email"></h2>
        <button class="auth-logout" type="button">Abmelden</button>
        <details>
          <summary>Konto löschen</summary>
          <form class="auth-delete-form">
            <label>Passwort bestätigen<input name="password" type="password" required></label>
            <p class="auth-error" role="alert"></p>
            <button class="auth-danger" type="submit">Alle Daten endgültig löschen</button>
          </form>
        </details>
      </div>
    </section>`;
  document.body.appendChild(shell);

  const guestView = shell.querySelector(".auth-guest");
  const accountView = shell.querySelector(".auth-account");
  const form = shell.querySelector(".auth-form");
  const submit = shell.querySelector(".auth-submit");
  let mode = "login";

  function emit() {
    window.dispatchEvent(new CustomEvent("site-auth-change", { detail: authState }));
  }
  function render() {
    guestView.hidden = authState.authenticated;
    accountView.hidden = !authState.authenticated;
    if (authState.authenticated) {
      const email = authState.user.email || "";
      shell.querySelector(".auth-email").textContent = email;
      avatar.textContent = email.slice(0, 1).toUpperCase() || "D";
      avatar.title = email;
    } else {
      avatar.textContent = "D";
      avatar.title = "Gastkonto";
    }
  }
  function open() {
    shell.hidden = false;
    render();
    setTimeout(() => shell.querySelector("input:not([hidden])")?.focus(), 0);
  }
  function close() { shell.hidden = true; }
  async function api(path, options) {
    const response = await fetch(path, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    if (response.status === 204) return null;
    return response.json();
  }
  async function refresh() {
    try {
      authState = await api("/api/auth/me");
      render();
      emit();
    } catch (_) {
      authState = { authenticated: false, user: null };
      render();
    }
  }

  shell.querySelectorAll(".auth-tabs button").forEach(btn => {
    btn.addEventListener("click", () => {
      mode = btn.dataset.mode;
      shell.querySelectorAll(".auth-tabs button").forEach(x => x.classList.toggle("active", x === btn));
      submit.textContent = mode === "login" ? "Anmelden" : "Konto erstellen";
      form.password.autocomplete = mode === "login" ? "current-password" : "new-password";
      form.querySelector(".auth-error").textContent = "";
    });
  });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const error = form.querySelector(".auth-error");
    error.textContent = "";
    submit.disabled = true;
    try {
      if (mode === "register" && window.SchreibenBeforeRegister) {
        await window.SchreibenBeforeRegister();
      }
      await api(`/api/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify({ email: form.email.value, password: form.password.value }),
      });
      form.reset();
      await refresh();
      close();
    } catch (err) {
      error.textContent = err.message;
    } finally {
      submit.disabled = false;
    }
  });
  shell.querySelector(".auth-logout").addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST" });
    await refresh();
    close();
  });
  shell.querySelector(".auth-delete-form").addEventListener("submit", async event => {
    event.preventDefault();
    const deleteForm = event.currentTarget;
    const error = deleteForm.querySelector(".auth-error");
    if (!window.confirm("Konto und alle Essays endgültig löschen?")) return;
    try {
      await api("/api/auth/account", {
        method: "DELETE",
        body: JSON.stringify({ password: deleteForm.password.value }),
      });
      localStorage.removeItem("deutschEssay.schreiben.v1");
      await refresh();
      close();
      window.location.reload();
    } catch (err) {
      error.textContent = err.message;
    }
  });

  avatar.addEventListener("click", open);
  avatar.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") open();
  });
  shell.querySelector(".auth-backdrop").addEventListener("click", close);
  shell.querySelector(".auth-close").addEventListener("click", close);
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !shell.hidden) close();
  });

  window.SiteAuth = { refresh, open, getState: () => authState };
  refresh();
})();

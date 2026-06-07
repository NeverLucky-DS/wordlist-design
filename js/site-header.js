/* Shared site-header behaviour — runs on every page that includes the
   unified .topbar (Editor, Wörterbuch, …). Owns the "Lernen" dropdown and
   the theme toggle so the bar behaves identically site-wide. */
(function () {
  const closeDrops = () =>
    document.querySelectorAll(".topbar .nav-drop.open").forEach(d => d.classList.remove("open"));

  document.querySelectorAll(".topbar .nav-drop").forEach(dd => {
    const btn = dd.querySelector(":scope > button");
    if (!btn) return;
    btn.addEventListener("click", e => {
      e.stopPropagation();
      const open = dd.classList.contains("open");
      closeDrops();
      if (!open) dd.classList.add("open");
    });
  });

  document.addEventListener("click", closeDrops);
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeDrops(); });

  const theme = document.getElementById("themeBtn");
  if (theme) theme.addEventListener("click", () => document.body.classList.toggle("theme-dim"));
})();

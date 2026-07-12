/* Shared site-header behaviour for Essay, Pipeline and Wörterbuch. */
(function () {
  const theme = document.getElementById("themeBtn");
  if (!theme) return;

  theme.setAttribute("aria-pressed", "false");
  theme.addEventListener("click", () => {
    const dimmed = document.body.classList.toggle("theme-dim");
    theme.setAttribute("aria-pressed", String(dimmed));
  });
})();

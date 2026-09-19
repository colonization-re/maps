(() => {
  const root = document.documentElement;
  const themeButtons = [...document.querySelectorAll("[data-theme-choice]")];

  function storedTheme() {
    try {
      const value = localStorage.getItem("colonization-map-theme");
      return ["light", "dark", "auto"].includes(value) ? value : "auto";
    } catch {
      return "auto";
    }
  }

  function applyTheme(theme, persist = true) {
    if (theme === "auto") delete root.dataset.theme;
    else root.dataset.theme = theme;

    for (const button of themeButtons) {
      const active = button.dataset.themeChoice === theme;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    }

    if (persist) {
      try {
        localStorage.setItem("colonization-map-theme", theme);
      } catch {
        // The theme still works when storage is unavailable.
      }
    }
  }

  for (const button of themeButtons) {
    button.addEventListener("click", () => applyTheme(button.dataset.themeChoice));
  }
  applyTheme(storedTheme(), false);

  const search = document.querySelector("[data-map-search]");
  if (!search) return;

  const cards = [...document.querySelectorAll("[data-map-card]")];
  const clear = document.querySelector("[data-clear-search]");
  const status = document.querySelector("[data-search-status]");
  const noResults = document.querySelector("[data-no-results]");
  const normalize = (value) => value.toLowerCase().normalize("NFKD").replace(/\p{M}/gu, "");

  function updateResults() {
    const query = normalize(search.value.trim());
    let visible = 0;

    for (const card of cards) {
      const matches = !query || normalize(card.dataset.search || "").includes(query);
      card.hidden = !matches;
      if (matches) visible += 1;
    }

    status.textContent = `${visible} of ${cards.length} ${cards.length === 1 ? "map" : "maps"} shown`;
    noResults.hidden = visible !== 0;
    clear.disabled = query.length === 0;
  }

  search.addEventListener("input", updateResults);
  clear.addEventListener("click", () => {
    search.value = "";
    search.focus();
    updateResults();
  });
  updateResults();
})();

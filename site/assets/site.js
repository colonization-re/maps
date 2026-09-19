(() => {
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

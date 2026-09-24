(() => {
  const cards = [...document.querySelectorAll("[data-map-card]")];
  if (!cards.length) return;

  const grid = document.querySelector("[data-map-grid]");
  const sort = document.querySelector("[data-map-sort]");
  const search = document.querySelector("[data-map-search]");
  const filter = document.querySelector("[data-map-filter]");
  const clear = document.querySelector("[data-clear-filters]");
  const status = document.querySelector("[data-filter-status]");
  const noResults = document.querySelector("[data-no-results]");
  const normalize = (value) => value.toLowerCase().normalize("NFKD").replace(/\p{M}/gu, "");
  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

  function compareCards(first, second) {
    const mode = sort?.value || "name-asc";
    const nameCompare = collator.compare(first.dataset.sortName || "", second.dataset.sortName || "");

    if (mode === "name-desc") {
      return -nameCompare;
    }

    if (mode === "date-desc") {
      const firstDate = first.dataset.sortDate || "";
      const secondDate = second.dataset.sortDate || "";
      if (!firstDate && secondDate) return 1;
      if (firstDate && !secondDate) return -1;
      return collator.compare(secondDate, firstDate) || nameCompare;
    }

    if (mode === "size-desc") {
      const firstSize = Number(first.dataset.sortSize || 0);
      const secondSize = Number(second.dataset.sortSize || 0);
      return secondSize - firstSize || nameCompare;
    }

    return nameCompare;
  }

  function updateSort() {
    if (!grid) return;
    for (const card of [...cards].sort(compareCards)) {
      grid.append(card);
    }
  }

  function updateResults() {
    const query = normalize(search?.value.trim() || "");
    const selected = [...(filter?.selectedOptions || [])].map((option) => option.value);
    let visible = 0;

    for (const card of cards) {
      const tags = (card.dataset.tags || "").split(/\s+/).filter(Boolean);
      const tagMatches = selected.length === 0 || selected.some((tag) => tags.includes(tag));
      const searchMatches = !query || normalize(card.dataset.search || "").includes(query);
      const matches = tagMatches && searchMatches;
      card.hidden = !matches;
      if (matches) visible += 1;
    }

    status.textContent = `${visible} of ${cards.length} ${cards.length === 1 ? "map" : "maps"} shown`;
    noResults.hidden = visible !== 0;
    clear.disabled = selected.length === 0 && query.length === 0;
  }

  search?.addEventListener("input", updateResults);
  filter?.addEventListener("change", updateResults);
  sort?.addEventListener("change", updateSort);
  clear?.addEventListener("click", () => {
    if (search) {
      search.value = "";
    }
    for (const option of filter?.options || []) {
      option.selected = false;
    }
    search?.focus();
    updateResults();
  });
  updateSort();
  updateResults();
})();

const search = document.getElementById("tool-search");

const filters = [ ...document.querySelectorAll(".filter") ];

const cards = [ ...document.querySelectorAll(".tool-card") ];

let category = "all";

// Filter existing tool cards without sending searches or saving them.
function filterTools() {
  const query = search.value.toLocaleLowerCase().trim();
  let visible = 0;
  for (const card of cards) {
    card.hidden = !(card.dataset.search.toLocaleLowerCase().includes(query) && (category === "all" || card.dataset.category === category));
    if (!card.hidden) {
      visible += 1;
    }
  }
  document.getElementById("empty-search").hidden = visible !== 0;
}

// Set one category while preserving the current search.
function chooseCategory(event) {
  category = event.currentTarget.dataset.category;
  for (const filter of filters) {
    const active = filter.dataset.category === category;
    filter.classList.toggle("active", active);
    filter.setAttribute("aria-pressed", String(active));
  }
  filterTools();
}

// Focus search from the keyboard without stealing input from a field.
function focusSearch(event) {
  if (event.key === "/" && ![ "INPUT", "TEXTAREA", "SELECT" ].includes(document.activeElement.tagName)) {
    event.preventDefault();
    search.focus();
  }
}

search.addEventListener("input", filterTools);

for (const button of filters) {
  button.addEventListener("click", chooseCategory);
}

document.addEventListener("keydown", focusSearch);

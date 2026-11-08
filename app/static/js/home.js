const search = document.getElementById("tool-search");
const filters = [...document.querySelectorAll(".filter")];
const cards = [...document.querySelectorAll(".tool-card")];
const categoryLinks = [...document.querySelectorAll(".category-link")];
let category = "all";

// Filter existing service cards locally and announce the visible result count.
function filterTools() {
  const query = search.value.toLocaleLowerCase().trim();
  let visible = 0;
  for (const card of cards) {
    const matches = card.dataset.search.toLocaleLowerCase().includes(query);
    card.hidden = !(matches && (category === "all" || card.dataset.category === category));
    if (!card.hidden) visible += 1;
  }
  document.getElementById("empty-search").hidden = visible !== 0;
  document.getElementById("visible-count").textContent = String(visible);
}

// Select only a known static category without transmitting searches or saving input.
function setCategory(candidate) {
  category = filters.some(filter => filter.dataset.category === candidate) ? candidate : "all";
  for (const filter of filters) {
    const active = filter.dataset.category === category;
    filter.classList.toggle("active", active);
    filter.setAttribute("aria-pressed", String(active));
  }
  for (const link of categoryLinks) {
    if (link.dataset.category === category) link.setAttribute("aria-current", "true");
    else link.removeAttribute("aria-current");
  }
  filterTools();
}

// Apply a category button while retaining the current local search.
function chooseCategory(event) { setCategory(event.currentTarget.dataset.category); }

// Reuse the current catalog when a sidebar category is chosen from the home page.
function chooseSidebarCategory(event) {
  event.preventDefault();
  setCategory(event.currentTarget.dataset.category);
  document.getElementById("catalog").scrollIntoView();
}

// Focus search from the keyboard without taking keystrokes from editable controls.
function focusSearch(event) {
  const target = document.activeElement;
  if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey &&
      !["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) && !target.isContentEditable) {
    event.preventDefault();
    search.focus();
  }
}

search.addEventListener("input", filterTools);
for (const button of filters) button.addEventListener("click", chooseCategory);
for (const link of categoryLinks) link.addEventListener("click", chooseSidebarCategory);
document.addEventListener("keydown", focusSearch);
setCategory(new URLSearchParams(window.location.search).get("category") ?? "all");

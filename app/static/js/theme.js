// Apply the single persisted preference before the page paints.
function applyInitialTheme() {
  let theme = "dark";
  try {
    if (localStorage.getItem("utility-hub-theme") === "light") {
      theme = "light";
    }
  } catch {/* Storage may be disabled. */}
  document.documentElement.dataset.theme = theme;
}

// Keep theme choice and the accessible toggle label in sync.
function connectThemeToggle() {
  const button = document.getElementById("theme-toggle");
  // Describe the action the theme button will perform.
  function updateLabel() {
    button.setAttribute("aria-label", `Switch to ${document.documentElement.dataset.theme === "dark" ? "light" : "dark"} mode`);
  }
  // Persist only a UI preference, never tool contents.
  function toggleTheme() {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("utility-hub-theme", theme);
    } catch {/* Theme still works without storage. */}
    updateLabel();
  }
  button.addEventListener("click", toggleTheme);
  updateLabel();
}

applyInitialTheme();

document.addEventListener("DOMContentLoaded", connectThemeToggle);

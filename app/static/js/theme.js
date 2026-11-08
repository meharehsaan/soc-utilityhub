// Apply both the guide's class and the existing theme attribute before the first paint.
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.classList.toggle("dark", theme === "dark");
  const color = document.getElementById("theme-color");
  if (color) color.content = theme === "dark" ? "#0b0d10" : "#eef2f6";
}

// Read the only persisted UI preference without storing tool contents.
function applyInitialTheme() {
  let theme = "dark";
  try {
    if (localStorage.getItem("utility-hub-theme") === "light") theme = "light";
  } catch { /* The default theme also works when storage is disabled. */ }
  applyTheme(theme);
}

// Keep the theme button's accessible label and icon state synchronized.
function connectThemeToggle() {
  const button = document.getElementById("theme-toggle");
  if (!button) return;

  // Describe the next theme action to keyboard and assistive-technology users.
  function updateLabel() {
    const label = "Switch to " + (document.documentElement.dataset.theme === "dark" ? "light" : "dark") + " mode";
    button.setAttribute("aria-label", label);
    button.title = label;
  }

  // Switch visual tokens while leaving all service inputs and results intact.
  function toggleTheme() {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(theme);
    try { localStorage.setItem("utility-hub-theme", theme); }
    catch { /* Theme switching does not depend on persistence. */ }
    updateLabel();
  }

  button.addEventListener("click", toggleTheme);
  updateLabel();
}

applyInitialTheme();
document.addEventListener("DOMContentLoaded", connectThemeToggle);

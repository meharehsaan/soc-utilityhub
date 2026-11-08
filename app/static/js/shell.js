const sidebar = document.getElementById("app-sidebar");
const column = document.getElementById("app-column");
const backdrop = document.getElementById("nav-backdrop");
const menu = document.getElementById("menu-toggle");
const close = document.getElementById("nav-close");
const collapse = document.getElementById("sidebar-toggle");
const mobile = window.matchMedia("(max-width: 1023px)");
let navigationOpen = false;
let returnFocus = null;

// Keep off-canvas navigation accessible without changing or persisting tool data.
function setNavigationOpen(open, restoreFocus = true) {
  const wasOpen = navigationOpen;
  navigationOpen = mobile.matches && open;
  if (navigationOpen && !wasOpen) returnFocus = document.activeElement;
  sidebar.classList.toggle("open", navigationOpen);
  document.body.classList.toggle("nav-open", navigationOpen);
  menu.setAttribute("aria-expanded", String(navigationOpen));
  menu.setAttribute("aria-label", navigationOpen ? "Close navigation" : "Open navigation");
  backdrop.hidden = !navigationOpen;
  column.inert = navigationOpen;
  sidebar.inert = mobile.matches && !navigationOpen;
  if (sidebar.inert) sidebar.setAttribute("aria-hidden", "true");
  else sidebar.removeAttribute("aria-hidden");
  if (navigationOpen) close.focus();
  else if (wasOpen && restoreFocus && mobile.matches) {
    (returnFocus?.isConnected ? returnFocus : menu).focus();
  }
}

// Open the mobile drawer after an explicit navigation-button action.
function openNavigation() { setNavigationOpen(true); }

// Close the mobile drawer and restore the user's previous focus.
function closeNavigation() { setNavigationOpen(false); }

// Change only desktop navigation density without retaining layout preferences.
function toggleSidebar() {
  const collapsed = document.body.classList.toggle("sidebar-collapsed");
  const label = collapsed ? "Expand sidebar" : "Collapse sidebar";
  collapse.setAttribute("aria-label", label);
  collapse.setAttribute("aria-expanded", String(!collapsed));
  collapse.title = label;
}

// Trap mobile drawer focus and support Escape without consuming form shortcuts.
function handleNavigationKeys(event) {
  if (!navigationOpen) return;
  if (event.key === "Escape") {
    event.preventDefault();
    closeNavigation();
    return;
  }
  if (event.key !== "Tab") return;
  const targets = [...sidebar.querySelectorAll('a[href], button:not(:disabled)')];
  const first = targets[0];
  const last = targets[targets.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

// Release inert states whenever navigation changes between mobile and desktop.
function syncViewport() { setNavigationOpen(false, false); }

menu.addEventListener("click", openNavigation);
close.addEventListener("click", closeNavigation);
backdrop.addEventListener("click", closeNavigation);
collapse.addEventListener("click", toggleSidebar);
for (const link of sidebar.querySelectorAll("a[href]")) link.addEventListener("click", closeNavigation);
document.addEventListener("keydown", handleNavigationKeys);
mobile.addEventListener("change", syncViewport);
syncViewport();

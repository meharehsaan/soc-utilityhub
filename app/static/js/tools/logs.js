import { checked, connectForm, makeTable, readSource, renderResult, requestTool, value } from "../common.js";

let current = null;

let view = "table";

let page = 0;

const PAGE_SIZE = 50;

// Submit explicit parsing, column, filter, and export settings for one document.
async function runLogs(signal) {
  return requestTool("logs", {
    text: await readSource(),
    format: value("format"),
    export: value("export"),
    renames: value("renames").trim() ? JSON.parse(value("renames")) : {},
    network_preset: value("network_preset"),
    source_field: value("source_field"),
    destination_field: value("destination_field"),
    port_field: value("port_field"),
    bytes_field: value("bytes_field"),
    columns: value("columns").split(/\r?\n/).filter(nonempty),
    filter_field: value("filter_field"),
    filter_value: value("filter_value"),
    spreadsheet_safe: checked("spreadsheet_safe")
  }, signal);
}

// Keep exact nonempty column names without guessing which fields were intended.
function nonempty(text) {
  return text !== "";
}

// Preserve the current export while displaying only a bounded table page.
function renderLogs(result) {
  renderResult(result);
  current = result;
  page = 0;
  showView();
}

// Render the selected view using inert nodes and independent export contents.
function showView() {
  if (!current) {
    return;
  }
  const detail = document.getElementById("result-detail");
  detail.replaceChildren();
  document.getElementById("result-output").hidden = view !== "export";
  detail.hidden = view === "export";
  if (view === "table") {
    const rows = current.data.rows;
    const total = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
    page = Math.max(0, Math.min(page, total - 1));
    detail.append(makeTable(current.data.columns, rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)));
    const controls = document.createElement("div");
    controls.className = "pagination";
    const previous = document.createElement("button");
    previous.type = "button";
    previous.className = "small-button";
    previous.textContent = "← Previous";
    previous.disabled = page === 0;
    const next = document.createElement("button");
    next.type = "button";
    next.className = "small-button";
    next.textContent = "Next →";
    next.disabled = page === total - 1;
    const label = document.createElement("span");
    label.textContent = `Page ${page + 1} / ${total} · ${rows.length} records`;
    previous.addEventListener("click", previousPage);
    next.addEventListener("click", nextPage);
    controls.append(previous, label, next);
    detail.append(controls);
  } else if (view === "summary") {
    const rows = [];
    for (const [field, summary] of Object.entries(current.data.summary)) {
      rows.push([ field, summary.missing, summary.top.map(topValue).join("; ") ]);
    }
    detail.append(makeTable([ "Field", "Missing in matching records", "Top values (count)" ], rows));
  } else if (view === "network") {
    const summary = current.data.network;
    if (!Object.keys(summary).length) {
      detail.textContent = "Choose an explicit network mapping, then run again.";
      return;
    }
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(summary, null, 2);
    detail.append(pre);
  } else if (view === "errors") {
    const rows = [];
    for (const record of current.data.errors.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)) {
      rows.push([ record.line, record.error, record.raw ]);
    }
    if (rows.length) {
      detail.append(makeTable([ "Source line", "Reason", "Original record" ], rows));
      const navigation = document.createElement("div");
      navigation.className = "pagination";
      const previous = document.createElement("button");
      previous.type = "button";
      previous.className = "small-button";
      previous.textContent = "Previous";
      previous.disabled = page === 0;
      const next = document.createElement("button");
      next.type = "button";
      next.className = "small-button";
      next.textContent = "Next";
      next.disabled = (page + 1) * PAGE_SIZE >= current.data.errors.length;
      previous.addEventListener("click", previousPage);
      next.addEventListener("click", nextPage);
      const label = document.createElement("span");
      label.textContent = "Malformed records " + (page * PAGE_SIZE + 1) + "–" + Math.min((page + 1) * PAGE_SIZE, current.data.errors.length);
      navigation.append(previous, label, next);
      detail.append(navigation);
    } else {
      detail.textContent = "No malformed records.";
    }
  }
}

// Format a safe scalar frequency label.
function topValue(entry) {
  return `${entry[0]} (${entry[1]})`;
}

// Move to the preceding preview page without rerunning or changing the export.
function previousPage() {
  page -= 1;
  showView();
}

// Move to the following preview page without changing filters or records.
function nextPage() {
  page += 1;
  showView();
}

// Select an inspection view without implicitly transforming content.
function chooseView(event) {
  view = event.currentTarget.dataset.logView;
  page = 0;
  showView();
}

// Clear client result references when the operation is reset.
function resetView() {
  current = null;
  view = "table";
  page = 0;
}

// Load two valid synthetic records and one malformed line for visible error handling.
function example() {
  document.getElementById("source").value = "{\"time\":\"2026-01-12T08:30:00Z\",\"host\":\"web-01\",\"status\":200}\n{\"time\":\"2026-01-12T08:31:00Z\",\"host\":\"web-02\",\"status\":403}\nnot a JSON record";
}

for (const button of document.querySelectorAll("[data-log-view]")) {
  button.addEventListener("click", chooseView);
}

document.addEventListener("tool:reset", resetView);

connectForm(runLogs, example, renderLogs);

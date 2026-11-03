import { connectForm, readSource, renderResult, requestTool, value } from "../common.js";
let current = null;
let view = "tree";
let expandedDepth = 1;
const PAGE_SIZE = 100;

// Request exact-value parsing or an explicitly selected field projection.
async function runJSON(signal) {
  return requestTool("json", {text: await readSource(), action: value("action"), format: value("format"), record: Number(value("record")), query: value("query")}, signal);
}
// Serialize a typed subtree without converting numeric labels through JavaScript Number.
function subtreeText(node) {
  if (node.kind === "object") {
    const pairs = [];
    for (const child of node.children) pairs.push(`${JSON.stringify(child.key)}:${subtreeText(child)}`);
    return `{${pairs.join(",")}}`;
  }
  if (node.kind === "array") return `[${node.children.map(subtreeText).join(",")}]`;
  return node.kind === "string" ? JSON.stringify(node.value) : node.value;
}
// Copy a path or subtree without interpreting it as a DOM fragment.
async function copyTreeValue(text) {
  try { await navigator.clipboard.writeText(text); document.getElementById("result-status").textContent = "Copied tree value."; }
  catch { document.getElementById("result-status").textContent = "Clipboard unavailable. Use the text result view or download."; }
}
// Add exact-value and pointer-copy controls to one visible tree row.
function copyControls(parent, node) {
  const path = document.createElement("button"); path.type = "button"; path.className = "tree-copy"; path.textContent = "path";
  path.setAttribute("aria-label", `Copy JSON Pointer for ${node.key}`);
  const copy = document.createElement("button"); copy.type = "button"; copy.className = "tree-copy"; copy.textContent = "copy";
  copy.setAttribute("aria-label", `Copy value for ${node.key}`);
  // Copy this node's exact JSON Pointer without toggling its surrounding branch.
  function copyPath(event) { event.preventDefault(); event.stopPropagation(); copyTreeValue(node.path); }
  // Serialize this subtree losslessly before sending it to the clipboard.
  function copyValue(event) { event.preventDefault(); event.stopPropagation(); copyTreeValue(subtreeText(node)); }
  path.addEventListener("click", copyPath); copy.addEventListener("click", copyValue); parent.append(path, copy);
}
// Render only the first bounded child page and expand deeper nodes on demand.
function renderNode(node, depth, included = null) {
  if (!node.children) {
    const row = document.createElement("div"); row.className = "json-leaf";
    const key = document.createElement("span"); key.className = "json-key"; key.textContent = `${node.key}: `;
    const label = document.createElement("span"); label.className = "json-value";
    label.textContent = node.kind === "string" ? JSON.stringify(node.value) : node.value;
    row.append(key, label); copyControls(row, node); return row;
  }
  const details = document.createElement("details");
  const summary = document.createElement("summary"); summary.textContent = `${node.key} ${node.kind === "array" ? "[" : "{"}${node.count}${node.kind === "array" ? "]" : "}"}`;
  copyControls(summary, node); details.append(summary);
  const children = [];
  for (const child of node.children) if (!included || included.has(child)) children.push(child);
  const content = document.createElement("div"); details.append(content);
  let offset = 0; let loaded = false;
  const more = document.createElement("button"); more.type = "button"; more.className = "small-button";
  // Append a bounded page rather than constructing thousands of DOM nodes at once.
  function loadMore() {
    const end = Math.min(offset + PAGE_SIZE, children.length);
    for (; offset < end; offset += 1) content.append(renderNode(children[offset], depth + 1, included));
    more.textContent = `Show ${Math.min(PAGE_SIZE, children.length - offset)} more`;
    if (offset < children.length) content.append(more); else more.remove();
  }
  // Materialize child rows only when the user or a depth control opens this branch.
  function onToggle() { if (details.open && !loaded) { loaded = true; loadMore(); } }
  details.addEventListener("toggle", onToggle); more.addEventListener("click", loadMore);
  if (depth < expandedDepth || included) { details.open = true; onToggle(); }
  return details;
}
// Find up to 100 matches while retaining their ancestors for a focused tree preview.
function matchingBranches(root, needle) {
  const included = new Set(); let count = 0;
  // Traverse source nodes, not DOM rows, so searches include collapsed branches.
  function visit(node, parents) {
    if (count >= 100) return;
    if (`${node.key} ${node.value ?? ""}`.toLocaleLowerCase().includes(needle)) {
      count += 1; included.add(node);
      for (const parent of parents) included.add(parent);
    }
    for (const child of node.children ?? []) visit(child, [...parents, node]);
  }
  visit(root, []); return {included, count};
}
// Keep views separate from the full result used by copy and download.
function showView() {
  if (!current) return;
  const tree = document.getElementById("json-tree"); tree.replaceChildren();
  const output = document.getElementById("result-output");
  const hasTree = Boolean(current.data?.tree);
  tree.hidden = view !== "tree" || !hasTree;
  output.hidden = view === "tree" && hasTree;
  output.textContent = view === "raw" ? current.data?.compact ?? current.output : current.output;
  for (const button of document.querySelectorAll("[data-view]")) button.setAttribute("aria-pressed", String(button.dataset.view === view));
  if (!tree.hidden) {
    const query = document.getElementById("tree-search").value.trim().toLocaleLowerCase();
    if (query) {
      const match = matchingBranches(current.data.tree, query);
      if (match.count) tree.append(renderNode(current.data.tree, 0, match.included));
      else tree.textContent = "No matching keys or values.";
      document.getElementById("result-status").textContent = `${match.count}${match.count === 100 ? "+" : ""} tree matches; export remains complete.`;
    } else tree.append(renderNode(current.data.tree, 0));
  }
}
// Initialize a new exact-value result without retaining the previous document.
function renderJSON(result) { renderResult(result); current = result; expandedDepth = 1; showView(); }
// Select an inspection view without removing hidden branches from the export.
function chooseView(event) { view = event.currentTarget.dataset.view; showView(); }
// Close all branches while preserving the complete in-memory result.
function collapseTree() { expandedDepth = 0; document.getElementById("tree-search").value = ""; showView(); }
// Open a bounded default depth without constructing every descendant.
function expandTree() { expandedDepth = 3; document.getElementById("tree-search").value = ""; showView(); }
// Reveal a typed field projection input only when extraction is deliberately selected.
function updateAction() { document.getElementById("query-option").hidden = value("action") !== "query"; }
// Release tree references and reset control state with the form.
function resetTree() { current = null; view = "tree"; document.getElementById("json-tree").replaceChildren(); document.getElementById("json-tree").hidden = true; updateAction(); }
// Load nested synthetic data including a numeric ID that exceeds JavaScript's safe integer.
function example() { document.getElementById("source").value = '{"event_id":9007199254740993,"source":{"ip":"192.0.2.10","host":"web-01"},"events":[{"action":"login","success":true},{"action":"read","success":false}]}'; updateAction(); }
for (const button of document.querySelectorAll("[data-view]")) button.addEventListener("click", chooseView);
document.getElementById("collapse-tree").addEventListener("click", collapseTree);
document.getElementById("expand-tree").addEventListener("click", expandTree);
document.getElementById("tree-search").addEventListener("input", showView);
document.getElementById("json-action").addEventListener("change", updateAction);
document.addEventListener("tool:reset", resetTree);
connectForm(runJSON, example, renderJSON);

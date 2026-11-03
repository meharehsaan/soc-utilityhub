import { checked, connectForm, makeTable, readSource, renderResult, requestTool, value } from "../common.js";
const categories = ["email", "username", "company", "domain", "hostname", "ip"];

// Build literal mappings without trimming or silently broadening the supplied strings.
function suppliedMappings() {
  const mappings = [];
  for (const category of categories) {
    for (const source of value(category).split(/\r?\n/)) if (source !== "") mappings.push({category, source});
  }
  for (const row of document.querySelectorAll(".custom-mapping")) {
    const source = row.querySelector(".custom-source").value;
    const replacement = row.querySelector(".custom-target").value;
    if (source !== "") mappings.push({category: "custom", source, replacement: replacement === "" ? null : replacement});
  }
  return mappings;
}
// Submit one explicit masking mode with only its relevant options.
async function runSanitizer(signal) {
  const mode = value("mode");
  const payload = {text: await readSource(), mode};
  if (mode === "literal") Object.assign(payload, {replacements: suppliedMappings(), case_sensitive: !checked("ignore_case"), whole_token: checked("whole_token")});
  if (mode === "patterns") payload.patterns = ["email", "ip"].filter(isSelectedPattern);
  if (mode === "json_fields") payload.fields = value("fields").split(/\r?\n/).filter(nonempty);
  return requestTool("sanitize", payload, signal);
}
// Keep only deliberately selected built-in pattern types.
function isSelectedPattern(kind) { return checked(`pattern_${kind}`); }
// Retain exact nonempty values while discarding empty input rows.
function nonempty(text) { return text !== ""; }
// Highlight replacements by Unicode code-point offsets without interpreting HTML.
function renderSanitized(result) {
  renderResult(result);
  const target = document.getElementById("result-output");
  const spans = result.data?.spans ?? [];
  if (spans.length) {
    const characters = Array.from(result.output);
    target.replaceChildren(); let position = 0;
    for (const [start, end] of spans) {
      target.append(document.createTextNode(characters.slice(position, start).join("")));
      const mark = document.createElement("mark"); mark.textContent = characters.slice(start, end).join("");
      target.append(mark); position = end;
    }
    target.append(document.createTextNode(characters.slice(position).join("")));
  }
  if (result.data?.matches?.length) {
    const detail = document.getElementById("result-detail");
    const rows = [];
    for (const match of result.data.matches) rows.push([match.source, match.replacement, match.count]);
    detail.append(makeTable(["Supplied string", "Replacement", "Matches"], rows)); detail.hidden = false;
  }
}
// Show only the controls belonging to the selected sanitizer mode.
function updateMode() {
  const mode = value("mode");
  document.getElementById("literal-options").hidden = mode !== "literal";
  document.getElementById("pattern-options").hidden = mode !== "patterns";
  document.getElementById("field-options").hidden = mode !== "json_fields";
}
// Add a bounded, empty custom mapping row without copying entered values.
function addMapping() {
  const parent = document.getElementById("custom-mappings");
  if (parent.children.length >= 20) return;
  const row = parent.firstElementChild.cloneNode(true);
  for (const input of row.querySelectorAll("input")) input.value = "";
  parent.append(row);
}
// Return mode visibility to the reset form without persisting any mapping.
function resetMode() { updateMode(); }
// Load a synthetic example with overlapping email, user, and company values.
function example() {
  document.getElementById("source").value = "Acme Ltd: alice (alice@acme.test) signed into workstation-01.\nContact alice@acme.test for follow-up.";
  document.querySelector('[name="email"]').value = "alice@acme.test";
  document.querySelector('[name="username"]').value = "alice";
  document.querySelector('[name="company"]').value = "Acme Ltd";
  updateMode();
}
document.getElementById("mode").addEventListener("change", updateMode);
document.getElementById("add-mapping").addEventListener("click", addMapping);
document.addEventListener("tool:reset", resetMode);
connectForm(runSanitizer, example, renderSanitized);

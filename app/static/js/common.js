const form = document.getElementById("tool-form");
let output = "";
let downloadBytes = null;
let controller = null;
let busy = false;
const MAX_TEXT = 1_000_000;
export const OUTPUT_LIMIT = 10 * 1024 * 1024;

// Read a named control without interpreting its contents as code or markup.
export function value(name) { return form.elements.namedItem(name)?.value ?? ""; }
// Read an explicit checkbox as a boolean.
export function checked(name) { return form.elements.namedItem(name)?.checked ?? false; }
// Return the currently selected local file without uploading it.
export function selectedFile(id = "source-file") { return document.getElementById(id)?.files[0] ?? null; }
// Convert bytes using only the user-selected supported encoding.
export function decodeBytes(bytes, encoding = "utf-8") {
  if (encoding === "latin-1") {
    let text = "";
    for (let start = 0; start < bytes.length; start += 8192) text += String.fromCharCode(...bytes.subarray(start, start + 8192));
    return text;
  }
  if (!["utf-8", "windows-1252"].includes(encoding)) throw new Error("Unsupported text encoding.");
  try { return new TextDecoder(encoding, { fatal: true }).decode(bytes); }
  catch { throw new Error("The file is not valid in the selected encoding."); }
}
// Read one text source with limits checked before allocating the file buffer.
export async function readSource(id = "source", fileId = "source-file") {
  const area = document.getElementById(id);
  const file = selectedFile(fileId);
  if (file && area.value !== "") throw new Error("Use pasted text or a file for each input, not both.");
  let text = area.value;
  if (file) {
    if (file.size > 5 * 1024 * 1024) throw new Error("Text files must be 5 MiB or smaller.");
    text = decodeBytes(new Uint8Array(await file.arrayBuffer()), value("encoding") || "utf-8");
  }
  if (text.length > MAX_TEXT) throw new Error("Text is limited to one million characters.");
  return text;
}
// Send a same-origin JSON operation without placing input in URLs or storage.
export async function requestTool(slug, payload, signal) {
  const response = await fetch(`/api/v1/${slug}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    cache: "no-store", credentials: "same-origin", signal,
  });
  const result = await response.json();
  if (!response.ok) {
    const fields = result.error?.fields?.slice(0, 4).map(describeField).join("; ");
    throw new Error(fields || result.error?.message || "The request could not be completed.");
  }
  return result;
}
// Describe a validation failure without including submitted field contents.
function describeField(field) { return `${field.field}: ${field.message}`; }
// Upload a hash file to the explicitly selected server operation.
export async function requestHashFile(file, algorithms, expected, signal) {
  const data = new FormData();
  data.append("file", file); data.append("algorithms", JSON.stringify(algorithms)); data.append("expected", expected);
  const response = await fetch("/api/v1/hash/file", { method: "POST", body: data, cache: "no-store", credentials: "same-origin", signal });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error?.message || "File processing failed.");
  return result;
}
// Update result text and metadata through inert DOM nodes only.
export function renderResult(result) {
  output = result.output ?? "";
  downloadBytes = result.binary instanceof Uint8Array ? result.binary : null;
  if (new TextEncoder().encode(output).length > OUTPUT_LIMIT) throw new Error("Result exceeds 10 MiB; reduce the input.");
  document.getElementById("result-empty").hidden = true;
  const target = document.getElementById("result-output");
  target.textContent = output;
  target.hidden = false;
  const details = document.getElementById("result-detail");
  details.replaceChildren(); details.hidden = true;
  const meta = document.getElementById("result-meta");
  meta.replaceChildren();
  for (const [name, amount] of Object.entries(result.meta ?? {})) {
    const span = document.createElement("span"); span.className = "meta-item";
    span.textContent = `${name.replaceAll("_", " ")}: ${amount}`; meta.append(span);
  }
  meta.hidden = meta.childElementCount === 0;
  const warnings = document.getElementById("result-warnings");
  warnings.textContent = (result.warnings ?? []).join(" "); warnings.hidden = !warnings.textContent;
  document.getElementById("copy-result").disabled = Boolean(downloadBytes);
  document.getElementById("download-result").disabled = false;
  document.getElementById("result-status").textContent = "Ready. Review the result before using it.";
}
// Build small tables safely while leaving pagination to each tool's controller.
export function makeTable(headers, rows) {
  const table = document.createElement("table");
  const head = document.createElement("thead"); const headRow = document.createElement("tr");
  for (const label of headers) { const cell = document.createElement("th"); cell.scope = "col"; cell.textContent = label; headRow.append(cell); }
  head.append(headRow); table.append(head);
  const body = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const value of row) { const cell = document.createElement("td"); cell.textContent = String(value ?? ""); tr.append(cell); }
    body.append(tr);
  }
  table.append(body); return table;
}
// Clear operation state without writing content or mappings to persistent storage.
function resetResult() {
  controller?.abort(); controller = null;
  output = ""; downloadBytes = null;
  document.getElementById("result-empty").hidden = false;
  for (const id of ["result-output", "result-meta", "result-warnings", "result-detail", "tool-error"]) {
    const target = document.getElementById(id); target.replaceChildren(); target.hidden = true;
  }
  document.getElementById("result-status").textContent = "";
  document.getElementById("copy-result").disabled = true;
  document.getElementById("download-result").disabled = true;
  document.dispatchEvent(new Event("tool:reset"));
  updateInputCount();
  updateFileLabels();
}
// Show a compact input count without storing or transmitting keystrokes.
function updateInputCount() {
  const count = document.getElementById("input-count");
  const area = document.getElementById("source");
  if (count && area) count.textContent = `${area.value.length.toLocaleString()} characters`;
}
// Display selected local filenames without uploading them or inserting markup.
function updateFileLabels() {
  for (const input of form.querySelectorAll('input[type="file"]')) {
    let label = input.parentElement.querySelector(".selected-file");
    if (!label) { label = document.createElement("span"); label.className = "selected-file"; input.after(label); }
    label.textContent = input.files[0] ? ` · ${input.files[0].name}` : "";
  }
}
// Copy only the current output, with an accessible selection fallback.
async function copyResult() {
  try { await navigator.clipboard.writeText(output); document.getElementById("result-status").textContent = "Copied result."; }
  catch {
    const selection = window.getSelection(); const range = document.createRange();
    const target = document.getElementById("result-output"); target.hidden = false;
    range.selectNodeContents(target); selection.removeAllRanges(); selection.addRange(range);
    document.getElementById("result-status").textContent = "Clipboard unavailable. Result selected; press Ctrl/Cmd+C, or download it.";
  }
}
// Download a current result without server retention or user-controlled filesystem paths.
function downloadResult() {
  const url = URL.createObjectURL(new Blob([downloadBytes ?? output], { type: downloadBytes ? "application/octet-stream" : "text/plain;charset=utf-8" }));
  const anchor = document.createElement("a"); anchor.href = url;
  anchor.download = `${document.querySelector(".workspace").dataset.tool}-result.${downloadBytes ? "bin" : "txt"}`;
  anchor.click();
  // Release only the in-memory blob after the browser begins its download.
  function releaseBlob() { URL.revokeObjectURL(url); }
  setTimeout(releaseBlob, 1000);
}
// Wire common form controls while each service owns its transformation and rendering.
export function connectForm(run, example, render = renderResult) {
  // Run one operation with cancellation and safe, readable error handling.
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    controller = new AbortController(); busy = true;
    const active = controller;
    const error = document.getElementById("tool-error"); error.hidden = true;
    form.classList.add("busy"); form.setAttribute("aria-busy", "true");
    document.getElementById("run-tool").disabled = true;
    try { const result = await run(active.signal); if (!active.signal.aborted) render(result); }
    catch (failure) { if (!active.signal.aborted) { error.textContent = failure.message || "Processing failed."; error.hidden = false; } }
    finally { busy = false; form.classList.remove("busy"); form.removeAttribute("aria-busy"); document.getElementById("run-tool").disabled = false; }
  }
  // Return the form to documented defaults and clear all operation output.
  function resetTool() { form.reset(); resetResult(); }
  // Insert a synthetic example only after a deliberate user action.
  function loadExample() { form.reset(); resetResult(); example(); updateInputCount(); }
  // Submit from a text field with the documented keyboard shortcut.
  function shortcut(event) { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); form.requestSubmit(); } }
  form.addEventListener("submit", submit);
  form.addEventListener("input", updateInputCount);
  form.addEventListener("change", updateFileLabels);
  form.addEventListener("keydown", shortcut);
  document.getElementById("reset-tool").addEventListener("click", resetTool);
  document.getElementById("load-example").addEventListener("click", loadExample);
  document.getElementById("copy-result").addEventListener("click", copyResult);
  document.getElementById("download-result").addEventListener("click", downloadResult);
}

// Upload one explicitly selected inert file without putting its name into a request URL.
export async function requestUploadedTool(slug, file, options, signal) {
  if (file.size > 5 * 1024 * 1024) throw new Error("Files must be 5 MiB or smaller.");
  const data = new FormData(); data.append("file", file); data.append("options", JSON.stringify(options));
  const response = await fetch(`/api/v1/${slug}/file`, {method:"POST",body:data,cache:"no-store",credentials:"same-origin",signal});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error?.message || "File inspection failed.");
  return result;
}

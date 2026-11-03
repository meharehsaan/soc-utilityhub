import { connectForm, makeTable, readSource, renderResult, selectedFile, value } from "../common.js";
import { runWorker } from "../worker.js";
// Keep pasted content and uploaded bytes entirely inside a bounded local worker.
async function runEncoder(signal) {
  const file = selectedFile();
  let input;
  if (file && document.getElementById("source").value !== "") throw new Error("Use text or a file, not both.");
  if (file) { if (file.size > 5 * 1024 * 1024) throw new Error("Browser files must be 5 MiB or smaller."); input = new Uint8Array(await file.arrayBuffer()); }
  else input = await readSource();
  return runWorker("/static/js/workers/encoder.js", {input, options: {mode: value("mode"), action: value("action"), format: value("format"), depth: Number(value("depth"))}}, signal);
}
// Display bounded intermediate previews without executing or rendering payload markup.
function renderEncoding(result) {
  renderResult(result);
  if (result.data?.layers?.length) {
    const rows = [];
    for (const layer of result.data.layers) rows.push([layer.layer, layer.bytes, layer.preview]);
    const detail = document.getElementById("result-detail"); detail.append(makeTable(["Layer", "Bytes", "Preview (first 500 characters)"], rows)); detail.hidden = false;
  }
}
// Load harmless Base64 for a short text example.
function example() { document.getElementById("source").value = "SGVsbG8sIGFuYWx5c3Qu"; }
connectForm(runEncoder, example, renderEncoding);

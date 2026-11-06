import { connectForm, makeTable, readSource, renderResult, requestHashFile, requestTool, selectedFile, value } from "../common.js";

import { runWorker } from "../worker.js";

// Apply the explicitly selected browser or server path without silently uploading local work.
async function runHash(signal) {
  const file = selectedFile();
  const text = document.getElementById("source").value;
  const algorithms = [];
  for (const input of document.querySelectorAll("[name=\"algorithms\"]:checked")) {
    algorithms.push(input.value);
  }
  const options = {
    action: value("action"),
    algorithms: algorithms,
    expected: value("expected")
  };
  if (file && text !== "") {
    throw new Error("Use exact text or one file, not both.");
  }
  if (file && options.action === "identify") {
    throw new Error("Paste a hexadecimal candidate to identify its format.");
  }
  if (value("processing") === "server") {
    if (file) {
      if (file.size > 50 * 1024 * 1024) {
        throw new Error("Server hash files must be 50 MiB or smaller.");
      }
      return requestHashFile(file, algorithms, options.expected, signal);
    }
    return requestTool("hash", {
      text: await readSource(),
      ...options
    }, signal);
  }
  let input = text;
  if (file) {
    if (file.size > 5 * 1024 * 1024) {
      throw new Error("Browser files must be 5 MiB or smaller.");
    }
    input = new Uint8Array(await file.arrayBuffer());
    options.filename = file.name;
  }
  return runWorker("/static/js/workers/hash.js", {
    input: input,
    options: options
  }, signal);
}

// Expose per-value clipboard actions alongside the complete downloadable result.
function renderHashes(result) {
  renderResult(result);
  if (!result.data?.digests) {
    return;
  }
  const rows = [];
  for (const [name, digest] of Object.entries(result.data.digests)) {
    rows.push([ name.toUpperCase(), digest ]);
  }
  const table = makeTable([ "Algorithm", "Digest" ], rows);
  for (const row of table.querySelectorAll("tbody tr")) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "small-button";
    button.textContent = "Copy";
    const digest = row.children[1].textContent;
    // Copy only this digest while leaving the full-result export untouched.
    async function copyDigest() {
      try {
        await navigator.clipboard.writeText(digest);
        document.getElementById("result-status").textContent = "Copied digest.";
      } catch {
        document.getElementById("result-status").textContent = "Clipboard unavailable; copy the digest from the result or download it.";
      }
    }
    button.addEventListener("click", copyDigest);
    row.children[1].append(document.createElement("br"), button);
  }
  const detail = document.getElementById("result-detail");
  detail.append(table);
  detail.hidden = false;
}

// Label processing support without changing input or silently selecting other algorithms.
function updateMode() {
  const browser = value("processing") === "browser";
  document.getElementById("hash-mode-note").textContent = browser ? "Browser mode never uploads inputs. Select MD5, SHA-1, SHA-256, or SHA-512 only." : "This operation sends content to this Python server. Uploaded files are streamed and not retained.";
}

// Load exact synthetic text whose known hashes make cross-checks straightforward.
function example() {
  document.getElementById("source").value = "abc";
  updateMode();
}

document.getElementById("hash-processing").addEventListener("change", updateMode);

document.addEventListener("tool:reset", updateMode);

connectForm(runHash, example, renderHashes);

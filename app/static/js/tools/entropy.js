import { checked, connectForm, readSource, selectedFile, value } from "../common.js";

import { runWorker } from "../worker.js";

// Run this tool in its bounded local worker without uploading content.
async function runTool(signal) {
  const file = selectedFile();
  if (file) {
    if (document.getElementById("source").value !== "") {
      throw new Error("Use text or a file, not both.");
    }
    if (file.size > 5 * 1024 * 1024) {
      throw new Error("Files are limited to 5 MiB.");
    }
    return runWorker("/static/js/workers/entropy.js", {
      bytes: await file.arrayBuffer()
    }, signal);
  }
  return runWorker("/static/js/workers/entropy.js", {
    text: await readSource()
  }, signal, 1e4);
}

// Insert synthetic sample data only after a deliberate user action.
function example() {
  document.getElementById("source").value = "AAAAABBBBBCCCCCDDDDDEEEEE";
}

connectForm(runTool, example);

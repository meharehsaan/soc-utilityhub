import { checked, connectForm, readSource, selectedFile, value } from "../common.js";

import { runWorker } from "../worker.js";

// Run this tool in its bounded local worker without uploading content.
async function runTool(signal) {
  return runWorker("/static/js/workers/user-sid.js", {
    text: await readSource()
  }, signal, 1e4);
}

// Insert synthetic sample data only after a deliberate user action.
function example() {
  document.getElementById("source").value = "S-1-5-18\nS-1-5-21-111-222-333-500\nS-1-5-32-544";
}

connectForm(runTool, example);

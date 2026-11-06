import { checked, connectForm, readSource, selectedFile, value } from "../common.js";

import { runWorker } from "../worker.js";

// Run this tool in its bounded local worker without uploading content.
async function runTool(signal) {
  return runWorker("/static/js/workers/mac.js", {
    text: await readSource()
  }, signal, 1e4);
}

// Insert synthetic sample data only after a deliberate user action.
function example() {
  document.getElementById("source").value = "00:15:5D:00:00:01\n02:11:22:33:44:55";
}

connectForm(runTool, example);

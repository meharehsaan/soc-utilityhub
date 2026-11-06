import { checked, connectForm, readSource, selectedFile, value } from "../common.js";

import { runWorker } from "../worker.js";

// Run this tool in its bounded local worker without uploading content.
async function runTool(signal) {
  return runWorker("/static/js/workers/http-status.js", {
    text: await readSource(),
    code: value("code")
  }, signal, 1e4);
}

// Insert synthetic sample data only after a deliberate user action.
function example() {
  document.getElementById("source").value = "HTTP/1.1 403 Forbidden\nContent-Security-Policy: default-src 'self'\nX-Frame-Options: DENY";
}

connectForm(runTool, example);

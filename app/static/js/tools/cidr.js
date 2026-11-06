import { checked, connectForm, readSource, selectedFile, value } from "../common.js";

import { runWorker } from "../worker.js";

// Run this tool in its bounded local worker without uploading content.
async function runTool(signal) {
  return runWorker("/static/js/workers/cidr.js", {
    text: await readSource(),
    comparison: value("comparison"),
    corporate: value("corporate"),
    context: checked("context")
  }, signal, 1e4);
}

// Insert synthetic sample data only after a deliberate user action.
function example() {
  document.getElementById("source").value = "10.10.1.42/24\n2001:db8::1/64\n1.1.1.1";
}

connectForm(runTool, example);

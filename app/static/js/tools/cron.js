import { checked, connectForm, readSource, selectedFile, value } from "../common.js";

import { runWorker } from "../worker.js";

// Run this tool in its bounded local worker without uploading content.
async function runTool(signal) {
  return runWorker("/static/js/workers/cron.js", {
    text: await readSource(),
    dialect: value("dialect"),
    zone: value("zone"),
    reference: value("reference"),
    horizon_days: Number(value("horizon_days"))
  }, signal, 12e3);
}

// Insert synthetic sample data only after a deliberate user action.
function example() {
  document.getElementById("source").value = "*/15 0-4 * * *\n0 * * * *";
  document.querySelector("[name=\"reference\"]").value = "2026-01-01T00:00:00Z";
}

connectForm(runTool, example);

document.querySelector("[name=\"reference\"]").value = (new Date).toISOString();

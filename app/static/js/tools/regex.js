import {checked,connectForm,readSource,selectedFile,value} from "../common.js";
import {runWorker} from "../worker.js";

// Run this tool in its bounded local worker without uploading content.
async function runTool(signal) {
  return runWorker("/static/js/workers/regex.js",{text:await readSource(),pattern:value("pattern"),flags:value("flags"),template:value("template"),literal:value("literal")},signal,3000);
}
// Insert synthetic sample data only after a deliberate user action.
function example() { document.getElementById("source").value="Sample CVE-2026-12345 and CVE-2025-6789"; }
connectForm(runTool,example);

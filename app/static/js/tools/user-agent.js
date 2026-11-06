import {checked,connectForm,readSource,selectedFile,value} from "../common.js";
import {runWorker} from "../worker.js";

// Run this tool in its bounded local worker without uploading content.
async function runTool(signal) {
  return runWorker("/static/js/workers/user-agent.js",{text:await readSource(),baseline:value("baseline")},signal,10000);
}
// Insert synthetic sample data only after a deliberate user action.
function example() { document.getElementById("source").value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"; }
connectForm(runTool,example);

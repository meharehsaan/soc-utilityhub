import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured sigma operation without saving the input.
async function runTool(signal) {
  const options = {};
  return requestTool("sigma",{text:await readSource(),...options},signal);
}
// Load synthetic example input only after a deliberate user action.
function example() { document.getElementById("source").value = "title: Synthetic process event\nlogsource:\n    product: windows\n    category: process_creation\ndetection:\n    selection:\n        Image|endswith: '\\\\sample.exe'\n    condition: selection\nlevel: low\n"; }
connectForm(runTool,example);

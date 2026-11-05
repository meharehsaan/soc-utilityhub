import { checked, connectForm, readSource, requestTool, value, selectedFile, requestUploadedTool } from "../common.js";

// Run the explicitly configured certificate operation without saving the input.
async function runTool(signal) {
  const options = {};
  const file = selectedFile();
  if (file) {
    if (document.getElementById("source").value !== "") throw new Error("Use pasted text or a file, not both.");
    return requestUploadedTool("certificate",file,options,signal);
  }
  return requestTool("certificate",{text:await readSource(),...options},signal);
}
// Load synthetic example input only after a deliberate user action.
function example() { document.getElementById("source").value = ""; }
connectForm(runTool,example);

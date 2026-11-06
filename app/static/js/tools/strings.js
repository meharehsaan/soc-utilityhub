import { checked, connectForm, readSource, requestTool, value, selectedFile, requestUploadedTool } from "../common.js";

// Run the explicitly configured strings operation without saving the input.
async function runTool(signal) {
  const options = {
    encoding: value("encoding"),
    minimum: Number(value("minimum"))
  };
  const file = selectedFile();
  if (file) {
    if (document.getElementById("source").value !== "") {
      throw new Error("Use pasted text or a file, not both.");
    }
    return requestUploadedTool("strings", file, options, signal);
  }
  return requestTool("strings", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "header\0https://example.test\0payload";
}

connectForm(runTool, example);

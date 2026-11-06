import { checked, connectForm, readSource, requestTool, value, selectedFile, requestUploadedTool } from "../common.js";

// Run the explicitly configured email operation without saving the input.
async function runTool(signal) {
  const options = {};
  const file = selectedFile();
  if (file) {
    if (document.getElementById("source").value !== "") {
      throw new Error("Use pasted text or a file, not both.");
    }
    return requestUploadedTool("email", file, options, signal);
  }
  return requestTool("email", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "From: Analyst <analyst@example.test>\nReply-To: help@example.test\nTo: soc@example.test\nSubject: Synthetic sample\nMIME-Version: 1.0\nContent-Type: text/plain; charset=utf-8\n\nReview https://example.test without visiting it.";
}

connectForm(runTool, example);

import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured url operation without saving the input.
async function runTool(signal) {
  const options = {
    decode_layers: Number(value("decode_layers"))
  };
  return requestTool("url", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "https://example.test:8443/a?tag=one&tag=two#details";
}

connectForm(runTool, example);

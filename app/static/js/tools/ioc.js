import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured ioc operation without saving the input.
async function runTool(signal) {
  const options = {
    mode: value("mode")
  };
  return requestTool("ioc", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "Observed https://example.test/path and 192.0.2.10. Contact analyst@example.test.";
}

connectForm(runTool, example);

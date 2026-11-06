import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured stix operation without saving the input.
async function runTool(signal) {
  const options = {
    mode: value("mode"),
    observable: value("observable")
  };
  return requestTool("stix", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "{\"type\":\"bundle\",\"id\":\"bundle--12ba8300-7d8b-4d16-93fa-d31335a6c9ec\",\"objects\":[]}";
}

connectForm(runTool, example);

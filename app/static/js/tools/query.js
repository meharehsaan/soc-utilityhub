import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured query operation without saving the input.
async function runTool(signal) {
  const options = {
    table: value("table"),
    field: value("field"),
    operator: value("operator")
  };
  return requestTool("query", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "web-01\nweb-02";
}

connectForm(runTool, example);

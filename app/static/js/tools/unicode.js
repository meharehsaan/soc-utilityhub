import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured unicode operation without saving the input.
async function runTool(signal) {
  const options = {
    action: value("action"),
    form: value("form"),
    include_whitespace: checked("include_whitespace")
  };
  return requestTool("unicode", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "user​name\nCafé";
}

connectForm(runTool, example);

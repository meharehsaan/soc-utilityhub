import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured jwt operation without saving the input.
async function runTool(signal) {
  const options = {};
  return requestTool("jwt", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "eyJhbGciOiJub25lIn0.eyJzdWIiOiJleGFtcGxlIiwiaWF0IjoxNzAwMDAwMDAwfQ.";
}

connectForm(runTool, example);

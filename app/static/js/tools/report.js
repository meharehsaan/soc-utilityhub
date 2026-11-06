import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured report operation without saving the input.
async function runTool(signal) {
  const options = {
    title: value("title"),
    timeline: value("timeline"),
    indicators: value("indicators"),
    actions: value("actions"),
    gaps: value("gaps"),
    next_steps: value("next_steps")
  };
  return requestTool("report", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "Analyst reviewed the supplied alert. Evidence and conclusions should be documented explicitly.";
}

connectForm(runTool, example);

import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured timestamp operation without saving the input.
async function runTool(signal) {
  const options = {format:value("format"),input_zone:value("input_zone"),output_zone:value("output_zone"),ambiguity:value("ambiguity")};
  return requestTool("timestamp",{text:await readSource(),...options},signal);
}
// Load synthetic example input only after a deliberate user action.
function example() { document.getElementById("source").value = "2026-01-01T12:00:00Z\n2026-01-01T12:30:00+05:00"; }
connectForm(runTool,example);

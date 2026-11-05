import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured events operation without saving the input.
async function runTool(signal) {
  const options = {mode:value("mode"),format:value("format"),provider:value("provider"),event_id:Number(value("event_id"))};
  return requestTool("events",{text:await readSource(),...options},signal);
}
// Load synthetic example input only after a deliberate user action.
function example() { document.getElementById("source").value = "<Event xmlns=\"http://schemas.microsoft.com/win/2004/08/events/event\"><System><Provider Name=\"Microsoft-Windows-Security-Auditing\"/><EventID>4624</EventID><Channel>Security</Channel></System><EventData><Data Name=\"TargetUserName\">analyst</Data></EventData></Event>"; }
connectForm(runTool,example);

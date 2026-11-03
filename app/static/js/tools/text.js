import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Apply only the selected text action and explicit comparison options.
async function runText(signal) {
  return requestTool("text", {text: await readSource(), action: value("action"), unit: value("unit"),
    descending: checked("descending"), natural: checked("natural"), case_sensitive: !checked("ignore_case"),
    trim: checked("trim"), remove_blank: checked("remove_blank"), keep: value("keep")}, signal);
}
// Load a synthetic list that demonstrates natural ordering and repeated lines.
function example() { document.getElementById("source").value = "host-10\nhost-2\nhost-1\nhost-2\n"; }
connectForm(runText, example);

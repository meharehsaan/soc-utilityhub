import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Read each explicit source independently before requesting the selected comparison.
async function runCompare(signal) {
  return requestTool("compare", {
    a: await readSource(),
    b: await readSource("source-b", "source-file-b"),
    mode: value("mode"),
    operation: value("operation"),
    trim: checked("trim"),
    case_sensitive: !checked("ignore_case"),
    ignore_key_order: checked("ignore_key_order")
  }, signal);
}

// Load two small synthetic host lists with one common member.
function example() {
  document.getElementById("source").value = "host-01\nhost-02\nhost-03";
  document.getElementById("source-b").value = "host-02\nhost-04";
}

connectForm(runCompare, example);

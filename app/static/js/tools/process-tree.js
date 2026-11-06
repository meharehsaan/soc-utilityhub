import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured process-tree operation without saving the input.
async function runTool(signal) {
  const options = {
    format: value("format"),
    export: value("export"),
    guid_field: value("guid_field"),
    parent_field: value("parent_field"),
    host_field: value("host_field"),
    image_field: value("image_field"),
    command_field: value("command_field"),
    pid_field: value("pid_field")
  };
  return requestTool("process-tree", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "{\"Computer\":\"host-01\",\"ProcessGuid\":\"parent\",\"Image\":\"shell.exe\",\"ProcessId\":100}\n{\"Computer\":\"host-01\",\"ProcessGuid\":\"child\",\"ParentProcessGuid\":\"parent\",\"Image\":\"worker.exe\",\"ProcessId\":101}";
}

connectForm(runTool, example);

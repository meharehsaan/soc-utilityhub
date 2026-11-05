import { checked, connectForm, readSource, requestTool, value } from "../common.js";

// Run the explicitly configured timeline operation without saving the input.
async function runTool(signal) {
  const options = {format:value("format"),time_field:value("time_field"),timestamp_format:value("timestamp_format"),input_zone:value("input_zone"),ambiguity:value("ambiguity"),host_field:value("host_field"),user_field:value("user_field"),action_field:value("action_field")};
  const files = [...document.getElementById("source-file").files];
  if (files.length) {
    if (document.getElementById("source").value !== "") throw new Error("Use pasted records or files, not both.");
    if (files.length > 4 || files.reduce(totalBytes,0) > 5*1024*1024) throw new Error("Use up to four files totaling 5 MiB.");
    const documents = [];
    for (const file of files) documents.push({label:file.name,text:new TextDecoder("utf-8",{fatal:true}).decode(await file.arrayBuffer())});
    return requestTool("timeline",{text:"",documents,...options},signal);
  }
  return requestTool("timeline",{text:await readSource(),...options},signal);
}
// Count only declared file sizes before allocating batch buffers.
function totalBytes(total,file) { return total + file.size; }
// Load synthetic example input only after a deliberate user action.
function example() { document.getElementById("source").value = "{\"timestamp\":\"2026-01-01T10:01:00Z\",\"host\":\"web-01\",\"user\":\"analyst\",\"action\":\"read\"}\n{\"timestamp\":\"2026-01-01T10:00:00Z\",\"host\":\"web-01\",\"user\":\"analyst\",\"action\":\"login\"}"; }
connectForm(runTool,example);

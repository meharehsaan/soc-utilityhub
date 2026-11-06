import { checked, connectForm, readSource, requestTool, value, renderResult, makeTable } from "../common.js";

const chosen = new Map;

// Keep only nonempty exact ignore terms.
function nonempty(text) {
  return text !== "";
}

// Run the explicitly configured spell operation without saving the input.
async function runTool(signal) {
  const options = {
    apply_best: checked("apply_best"),
    ignore_uppercase: checked("ignore_uppercase"),
    ignore: value("ignore").split(/\r?\n/).filter(nonempty),
    corrections: Object.fromEntries(chosen)
  };
  return requestTool("spell", {
    text: await readSource(),
    ...options
  }, signal);
}

// Load synthetic example input only after a deliberate user action.
function example() {
  document.getElementById("source").value = "Please check this speling and recieve the report.";
}

// Present candidate actions without changing the original text until the next explicit run.
function renderSpelling(result) {
  renderResult(result);
  const detail = document.getElementById("result-detail");
  for (const entry of result.data?.suggestions ?? []) {
    const row = document.createElement("p");
    row.append(document.createTextNode(entry.word + ": "));
    for (const candidate of entry.candidates) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "small-button";
      button.textContent = candidate;
      // Choose one replacement for the next explicit spelling operation.
      function choose() {
        chosen.set(entry.word, candidate);
        document.getElementById("result-status").textContent = "Replacement selected; run again to apply it.";
      }
      button.addEventListener("click", choose);
      row.append(button);
    }
    if (!entry.candidates.length) {
      row.append(document.createTextNode("No local suggestion"));
    }
    detail.append(row);
  }
  detail.hidden = false;
}

// Drop chosen replacements when the source text or operation changes.
function clearChoices() {
  chosen.clear();
}

document.getElementById("source").maxLength = 2e4;

document.getElementById("source").addEventListener("input", clearChoices);

document.getElementById("source-file").addEventListener("change", clearChoices);

document.addEventListener("tool:reset", clearChoices);

connectForm(runTool, example, renderSpelling);

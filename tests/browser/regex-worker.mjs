import { parentPort } from "node:worker_threads";

import { operate } from "../../app/static/js/tools/regex-engine.js";

// Exercise the same browser engine in an independently terminable test worker.
function run(payload) {
  try {
    parentPort.postMessage(operate(payload));
  } catch (error) {
    parentPort.postMessage({
      error: error.message
    });
  }
}

parentPort.on("message", run);

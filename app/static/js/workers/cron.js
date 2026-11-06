import { operate } from "../tools/cron-engine.js";
// Return only inert results from this fixed local engine.
async function processTool(event) {
  try { postMessage({result:await operate(event.data)}); }
  catch(error) { postMessage({error:error.message || "Processing failed."}); }
}
self.addEventListener("message",processTool);

import { hashBytes } from "../tools/hash-engine.js";

// Hash only local bytes and return fingerprint observations without network requests.
async function processHash(event) {
  try {
    postMessage({
      result: await hashBytes(event.data.input, event.data.options)
    });
  } catch (error) {
    postMessage({
      error: error.message || "Hashing failed."
    });
  }
}

self.addEventListener("message", processHash);

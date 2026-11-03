// Run a fixed local worker with bounded lifetime and explicit cancellation.
export function runWorker(path, payload, signal, timeout = 10000) {
  return new Promise(execute);
  // Own worker cleanup for success, failure, timeout, and form reset.
  function execute(resolve, reject) {
    if (signal?.aborted) { reject(new DOMException("Cancelled", "AbortError")); return; }
    const worker = new Worker(path, {type: "module"});
    let timer;
    // Release the worker and all associated event handlers once an outcome is known.
    function cleanup() { clearTimeout(timer); worker.terminate(); signal?.removeEventListener("abort", abort); }
    // Return only a structured result or a safe public worker error.
    function message(event) { cleanup(); if (event.data.error) reject(new Error(event.data.error)); else resolve(event.data.result); }
    // Hide internal worker stack traces from the product's error surface.
    function failure() { cleanup(); reject(new Error("Browser processing failed. Check browser support and the selected options.")); }
    // Stop bounded local work when the user resets or leaves the operation.
    function abort() { cleanup(); reject(new DOMException("Cancelled", "AbortError")); }
    // Terminate computationally expensive input before it can monopolize the tab.
    function expired() { cleanup(); reject(new Error("Processing exceeded its time limit. Reduce the input.")); }
    worker.addEventListener("message", message, {once: true}); worker.addEventListener("error", failure, {once: true});
    signal?.addEventListener("abort", abort, {once: true}); timer = setTimeout(expired, timeout);
    worker.postMessage(payload);
  }
}

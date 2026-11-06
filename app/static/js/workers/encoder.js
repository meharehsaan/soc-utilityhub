import { transformEncoding } from "../tools/encoder-engine.js";

// Load only local reference assets and return inert transformed data.
async function processEncoding(event) {
  try {
    const {input: input, options: options} = event.data;
    let entities = {};
    if (options.format === "html") {
      const response = await fetch("/static/data/html-entities.json", {
        cache: "force-cache"
      });
      if (!response.ok) {
        throw new Error("The local HTML entity reference is unavailable.");
      }
      entities = await response.json();
    }
    postMessage({
      result: transformEncoding(input, options, entities)
    });
  } catch (error) {
    postMessage({
      error: error.message || "Decoding failed."
    });
  }
}

self.addEventListener("message", processEncoding);

import { connectForm, renderResult, value } from "../common.js";

import { normalizedPoint, paintStrokes } from "./signature-engine.js";

const pad = document.getElementById("signature-pad"), strokes = [];

let active = null, pointer = null, previewUrl = null;

// Convert a pointer position into bounded operation-local coordinates.
function point(event) {
  const rect = pad.getBoundingClientRect();
  return normalizedPoint(event.clientX - rect.left, event.clientY - rect.top, rect.width, rect.height);
}

// Redraw vector strokes on a high-DPI surface without altering their coordinates.
function redraw() {
  const rect = pad.getBoundingClientRect();
  if (!rect.width) {
    return;
  }
  const ratio = Math.min(window.devicePixelRatio || 1, 3);
  pad.width = Math.round(rect.width * ratio);
  pad.height = Math.round(rect.width / 3 * ratio);
  pad.classList.toggle("light-ink", value("pen") === "#ffffff");
  const context = pad.getContext("2d");
  context.clearRect(0, 0, pad.width, pad.height);
  paintStrokes(context, strokes, pad.width, pad.height, value("pen"));
  document.getElementById("stroke-count").textContent = strokes.length + " strokes · 50 maximum";
}

// Begin a bounded stroke only in the selected drawing mode.
function startStroke(event) {
  if (value("mode") !== "drawn" || active || strokes.length >= 50 || event.button !== 0) {
    return;
  }
  event.preventDefault();
  pointer = event.pointerId;
  active = [ point(event) ];
  strokes.push(active);
  pad.setPointerCapture(pointer);
  redraw();
}

// Retain a bounded number of samples for the active pointer.
function moveStroke(event) {
  if (!active || event.pointerId !== pointer) {
    return;
  }
  event.preventDefault();
  if (active.length < 2e3) {
    active.push(point(event));
    redraw();
  }
}

// Finish the current stroke when the pointer or capture is released.
function finishStroke(event) {
  if (event.pointerId === pointer) {
    active = null;
    pointer = null;
  }
}

// Undo one stroke after a deliberate UI action.
function undoStroke() {
  active = null;
  pointer = null;
  strokes.pop();
  redraw();
}

// Clear only the in-memory drawing state.
function clearStrokes() {
  active = null;
  pointer = null;
  strokes.length = 0;
  redraw();
}

// Switch local controls without submitting either input mode.
function switchMode() {
  document.getElementById("typed-controls").hidden = value("mode") !== "typed";
  document.getElementById("drawn-controls").hidden = value("mode") !== "drawn";
  redraw();
}

// Resolve an inert PNG blob from the locally rendered canvas.
function pngBlob(canvas) {
  return new Promise(resolveBlob);
  // Return a browser-generated PNG or a safe export failure.
  function resolveBlob(resolve, reject) {
    canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error("PNG export failed.")), "image/png");
  }
}

// Render the selected signature mode into a fixed-size PNG.
async function runTool() {
  if (value("background") === value("pen")) { throw new Error("Choose different pen and background colors."); }
  const canvas = document.createElement("canvas");
  canvas.width = 1800;
  canvas.height = 600;
  const context = canvas.getContext("2d");
  if (value("background") !== "transparent") {
    context.fillStyle = value("background");
    context.fillRect(0, 0, canvas.width, canvas.height);
  }
  if (value("mode") === "drawn") {
    if (!strokes.length) {
      throw new Error("Draw at least one stroke.");
    }
    paintStrokes(context, strokes, canvas.width, canvas.height, value("pen"));
  } else {
    const text = value("text").trim();
    if (!text || Array.from(text).length > 100 || /[\r\n]/.test(text)) {
      throw new Error("Use one line of 1–100 characters.");
    }
    const family = value("font") === "serif" ? "\"Utility Signature Serif\"" : "sans-serif";
    if (value("font") === "serif") {
      await document.fonts.load("italic 200px \"Utility Signature Serif\"");
    }
    context.fillStyle = value("pen");
    context.font = "italic 200px " + family;
    const fit = Math.min(200, 1600 * 200 / Math.max(1, context.measureText(text).width));
    context.font = "italic " + fit + "px " + family;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(text, 900, 300, 1600);
  }
  const blob = await pngBlob(canvas);
  return {
    output: "PNG signature · 1800 × 600 pixels",
    binary: new Uint8Array(await blob.arrayBuffer()),
    mime: "image/png",
    extension: "png",
    meta: {
      mode: value("mode"),
      background: value("background")
    },
    warnings: [ "Visual signature only; no identity or cryptographic verification." ]
  };
}

// Display the PNG using a revocable local preview URL.
function renderSignature(result) {
  renderResult(result);
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
  }
  previewUrl = URL.createObjectURL(new Blob([ result.binary ], {
    type: "image/png"
  }));
  const img = document.createElement("img");
  img.src = previewUrl;
  img.alt = "Generated signature preview";
  img.className = "signature-preview";
  img.classList.toggle("light-ink", value("pen") === "#ffffff");
  const detail = document.getElementById("result-detail");
  detail.replaceChildren(img);
  detail.hidden = false;
}

// Load a synthetic typed signature after a deliberate user action.
function example() {
  document.getElementById("source").value = "Alex Analyst";
  switchMode();
}

// Release preview state and restore mode visibility on reset.
function resetSignature() {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
  }
  previewUrl = null;
  clearStrokes();
  switchMode();
}

pad.addEventListener("pointerdown", startStroke);

pad.addEventListener("pointermove", moveStroke);

for (const name of [ "pointerup", "pointercancel", "lostpointercapture" ]) {
  pad.addEventListener(name, finishStroke);
}

document.getElementById("undo-stroke").addEventListener("click", undoStroke);

document.getElementById("clear-strokes").addEventListener("click", clearStrokes);

document.getElementById("signature-mode").addEventListener("change", switchMode);

document.querySelector("[name=\"pen\"]").addEventListener("change", redraw);

window.addEventListener("resize", redraw);

document.addEventListener("tool:reset", resetSignature);

connectForm(runTool, example, renderSignature);

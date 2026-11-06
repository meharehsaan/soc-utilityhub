const LIMIT = 10 * 1024 * 1024;

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

// Reject unpaired surrogates rather than silently changing bytes during UTF-8 encoding.
export function wellFormed(text) {
  for (const character of text) {
    const code = character.codePointAt(0);
    if (code >= 55296 && code <= 57343) {
      throw new Error("Text contains an unpaired Unicode surrogate.");
    }
  }
  return text;
}

// Bound every generated representation before displaying or decoding it further.
function bounded(text) {
  if (text.length > LIMIT || (new TextEncoder).encode(text).length > LIMIT) {
    throw new Error("Output exceeds 10 MiB.");
  }
  return text;
}

// Decode valid UTF-8 bytes while retaining invalid binary data for an exact download.
function asText(bytes) {
  return new TextDecoder("utf-8", {
    fatal: true,
    ignoreBOM: true
  }).decode(bytes);
}

// Encode byte chunks without overflowing the JavaScript function argument stack.
export function toBase64(bytes) {
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 8192) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
  }
  return btoa(binary);
}

// Decode canonical Base64 with explicit Base64URL alphabet and padding handling.
export function fromBase64(text, url = false) {
  const clean = text.replace(/[\t\n\r ]/g, "");
  const pattern = url ? /^[A-Za-z0-9_-]*={0,2}$/ : /^[A-Za-z0-9+/]*={0,2}$/;
  if (!pattern.test(clean) || clean.length % 4 === 1 || !url && clean.length % 4 !== 0) {
    throw new Error("Invalid Base64 alphabet, length, or padding.");
  }
  const unpadded = clean.replace(/=+$/, "");
  if (clean.includes("=") && clean.length % 4 !== 0) {
    throw new Error("Invalid Base64 padding.");
  }
  const normalized = unpadded.replaceAll("-", "+").replaceAll("_", "/");
  let binary;
  try {
    binary = atob(normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "="));
  } catch {
    throw new Error("Invalid Base64.");
  }
  const bytes = Uint8Array.from(binary, byteCode);
  const canonical = toBase64(bytes).replace(/=+$/, "");
  if (canonical !== normalized) {
    throw new Error("Non-canonical Base64 padding bits.");
  }
  return bytes;
}

// Convert one Latin-1 binary character to its original byte.
function byteCode(character) {
  return character.charCodeAt(0);
}

// Encode RFC 4648 Base32 with canonical padding.
export function toBase32(bytes) {
  let output = "", buffer = 0, bits = 0;
  for (const byte of bytes) {
    buffer = buffer << 8 | byte;
    bits += 8;
    while (bits >= 5) {
      bits -= 5;
      output += ALPHABET[buffer >>> bits & 31];
    }
  }
  if (bits) {
    output += ALPHABET[buffer << 5 - bits & 31];
  }
  return output.padEnd(Math.ceil(output.length / 8) * 8, "=");
}

// Decode canonical Base32 and reject nonzero unused bits or invalid padding.
export function fromBase32(text) {
  const clean = text.replace(/[\t\n\r ]/g, "").toUpperCase();
  if (!/^[A-Z2-7]*={0,6}$/.test(clean) || clean.length % 8 !== 0) {
    throw new Error("Invalid padded Base32.");
  }
  const raw = clean.replace(/=+$/, "");
  const bytes = [];
  let buffer = 0, bits = 0;
  for (const character of raw) {
    buffer = buffer << 5 | ALPHABET.indexOf(character);
    bits += 5;
    if (bits >= 8) {
      bits -= 8;
      bytes.push(buffer >>> bits & 255);
    }
  }
  const output = Uint8Array.from(bytes);
  if (toBase32(output) !== clean) {
    throw new Error("Non-canonical Base32 padding.");
  }
  return output;
}

// Encode raw bytes as fixed-width hexadecimal values.
function toHex(bytes) {
  return Array.from(bytes, hexByte).join("");
}

// Format one byte without dropping a leading zero.
function hexByte(byte) {
  return byte.toString(16).padStart(2, "0");
}

// Decode HTML character references using a local HTML5 entity map and numeric rules.
function fromHTML(text, entities) {
  return text.replace(/&(#x[0-9a-f]+|#[0-9]+|[A-Za-z][A-Za-z0-9]+);/gi, replaceEntity);
  // Decode a single reference as inert text, never as an HTML fragment.
  function replaceEntity(source, name) {
    if (name.startsWith("#")) {
      const code = name[1]?.toLowerCase() === "x" ? Number.parseInt(name.slice(2), 16) : Number.parseInt(name.slice(1), 10);
      if (code === 0 || code > 1114111 || code >= 55296 && code <= 57343) {
        return "�";
      }
      if (code >= 128 && code <= 159) {
        return new TextDecoder("windows-1252").decode(Uint8Array.of(code));
      }
      return String.fromCodePoint(code);
    }
    if (!Object.hasOwn(entities, name)) {
      throw new Error(`Unknown HTML entity: ${name}`);
    }
    return entities[name];
  }
}

// Encode text or raw file bytes using one explicitly selected representation.
export function encode(bytes, format) {
  if (format === "base64") {
    return bounded(toBase64(bytes));
  }
  if (format === "base64url") {
    return bounded(toBase64(bytes).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, ""));
  }
  if (format === "base32") {
    return bounded(toBase32(bytes));
  }
  if (format === "hex") {
    return bounded(toHex(bytes));
  }
  const text = wellFormed(asText(bytes));
  if (format === "url") {
    return bounded(encodeURIComponent(text));
  }
  if (format === "json") {
    return bounded(JSON.stringify(text));
  }
  if (format === "html") {
    return bounded(text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll("\"", "&quot;").replaceAll("'", "&apos;"));
  }
  if (format === "unicode") {
    let output = "";
    for (let i = 0; i < text.length; i += 1) {
      output += `\\u${text.charCodeAt(i).toString(16).padStart(4, "0")}`;
    }
    return bounded(output);
  }
  if (format === "octal") {
    let output = "";
    for (const byte of bytes) {
      output += `\\${byte.toString(8).padStart(3, "0")}`;
    }
    return bounded(output);
  }
  throw new Error("Unsupported format.");
}

// Decode one representation without invoking a script evaluator or DOM parser.
export function decode(text, format, entities = {}) {
  if (format === "base64" || format === "base64url") {
    return fromBase64(text, format === "base64url");
  }
  if (format === "base32") {
    return fromBase32(text);
  }
  if (format === "hex") {
    const clean = text.replace(/[\t\n\r ]/g, "");
    if (!/^[0-9a-f]*$/i.test(clean) || clean.length % 2) {
      throw new Error("Hex input needs complete byte pairs.");
    }
    const bytes = new Uint8Array(clean.length / 2);
    for (let i = 0; i < clean.length; i += 2) {
      bytes[i / 2] = Number.parseInt(clean.slice(i, i + 2), 16);
    }
    return bytes;
  }
  let result;
  if (format === "url") {
    try {
      result = decodeURIComponent(text);
    } catch {
      throw new Error("Invalid percent-encoding or UTF-8.");
    }
  } else if (format === "html") {
    result = fromHTML(text, entities);
  } else if (format === "json") {
    try {
      result = JSON.parse(text);
    } catch {
      throw new Error("Input must be a valid quoted JSON string.");
    }
    if (typeof result !== "string") {
      throw new Error("Expected a JSON string, not an object or number.");
    }
  } else if (format === "unicode") {
    if (/\\u(?![0-9a-f]{4}|\{[0-9a-f]{1,6}\})/i.test(text)) {
      throw new Error("Malformed Unicode escape.");
    }
    result = text.replace(/\\u\{([0-9a-f]{1,6})\}|\\u([0-9a-f]{4})/gi, unicodeEscape);
  } else if (format === "octal") {
    if (/\\(?![0-7]{1,3})/.test(text)) {
      throw new Error("Use octal escapes such as \\141.");
    }
    const bytes = [];
    for (let position = 0; position < text.length; ) {
      const match = /^\\([0-7]{1,3})/.exec(text.slice(position));
      if (!match || Number.parseInt(match[1], 8) > 255) {
        throw new Error("Octal mode expects escaped bytes only (000–377).");
      }
      bytes.push(Number.parseInt(match[1], 8));
      position += match[0].length;
    }
    return Uint8Array.from(bytes);
  } else {
    throw new Error("Unsupported format.");
  }
  return (new TextEncoder).encode(bounded(wellFormed(result)));
}

// Convert a supported Unicode escape while rejecting out-of-range scalar values.
function unicodeEscape(source, braced, fixed) {
  const value = Number.parseInt(braced ?? fixed, 16);
  if (value > 1114111) {
    throw new Error("Unicode escape exceeds the maximum code point.");
  }
  return braced ? String.fromCodePoint(value) : String.fromCharCode(value);
}

// Execute a bounded browser operation and retain binary output as exact download bytes.
export function transformEncoding(input, options, entities = {}) {
  const bytes = input instanceof Uint8Array ? input : (new TextEncoder).encode(wellFormed(input));
  if (bytes.length > 5 * 1024 * 1024) {
    throw new Error("Browser input must be 5 MiB or smaller.");
  }
  const layers = [];
  let outputBytes = bytes;
  if (options.mode === "powershell") {
    outputBytes = fromBase64(asText(bytes));
    if (outputBytes.length % 2) {
      throw new Error("UTF-16LE needs complete two-byte code units.");
    }
    let text;
    try {
      text = new TextDecoder("utf-16le", {
        fatal: true
      }).decode(outputBytes);
    } catch {
      throw new Error("Invalid UTF-16LE command bytes.");
    }
    return {
      output: bounded(wellFormed(text)),
      meta: {
        decoded_bytes: outputBytes.length
      },
      warnings: [ "Decoded as inert UTF-16LE text. No command was executed." ]
    };
  }
  if (options.mode === "standard" && options.action === "encode") {
    return {
      output: encode(bytes, options.format),
      meta: {
        input_bytes: bytes.length
      }
    };
  }
  const depth = options.mode === "layers" ? options.depth : 1;
  if (!Number.isInteger(depth) || depth < 1 || depth > 5) {
    throw new Error("Choose 1–5 decoding layers.");
  }
  const warnings = [];
  for (let index = 0; index < depth; index += 1) {
    let text;
    try {
      text = asText(outputBytes);
    } catch {
      if (index === 0) {
        throw new Error("Encoded input is not valid UTF-8 text.");
      }
      warnings.push("Stopped at binary output.");
      break;
    }
    let decoded;
    try {
      decoded = decode(text, options.format, entities);
    } catch (error) {
      if (index === 0) {
        throw error;
      }
      warnings.push(`Stopped after ${index} valid layers: ${error.message}`);
      break;
    }
    if (decoded.length > LIMIT) {
      throw new Error("Decoded output exceeds 10 MiB.");
    }
    outputBytes = decoded;
    let preview;
    try {
      preview = asText(decoded);
    } catch {
      preview = "[binary output]";
    }
    layers.push({
      layer: index + 1,
      preview: preview.slice(0, 500),
      bytes: decoded.length
    });
    if (preview === text) {
      break;
    }
  }
  let output;
  try {
    output = bounded(wellFormed(asText(outputBytes)));
  } catch {
    return {
      output: `Binary output · ${outputBytes.length} bytes\nPreview: ${toHex(outputBytes.subarray(0, 64))}\nDownload to save the exact bytes.`,
      binary: outputBytes,
      meta: {
        bytes: outputBytes.length
      },
      warnings: warnings,
      data: {
        layers: layers
      }
    };
  }
  return {
    output: output,
    meta: {
      output_bytes: outputBytes.length,
      layers: layers.length
    },
    warnings: warnings,
    data: {
      layers: layers
    }
  };
}

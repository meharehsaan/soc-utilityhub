import md5 from "../../vendor/md5.js";
import { wellFormed } from "./encoder-engine.js";
const SUPPORTED = {md5: null, sha1: "SHA-1", sha256: "SHA-256", sha512: "SHA-512"};
const SIGNATURES = [
  [[0x25,0x50,0x44,0x46,0x2d], "PDF", ["pdf"]],
  [[0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a], "PNG", ["png"]],
  [[0xff,0xd8,0xff], "JPEG", ["jpg","jpeg"]],
  [[0x47,0x49,0x46,0x38], "GIF", ["gif"]],
  [[0x50,0x4b,0x03,0x04], "ZIP container", ["zip","docx","xlsx","pptx","jar"]],
  [[0x7f,0x45,0x4c,0x46], "ELF header", ["elf","so",""]],
  [[0x4d,0x5a], "DOS/PE header", ["exe","dll","sys","scr"]],
  [[0x1f,0x8b], "GZIP", ["gz","tgz"]],
];
// Format a digest byte as two hexadecimal characters.
function hexByte(byte) { return byte.toString(16).padStart(2, "0"); }
// Identify a representation without mistaking length for definitive algorithm attribution.
export function identifyHash(text) {
  const candidate = text.trim();
  if (!candidate || !/^[0-9a-f]+$/i.test(candidate)) throw new Error("A candidate hash must contain hexadecimal characters only.");
  const candidates = {32:"MD5 or another 128-bit format (including NTLM)",40:"SHA-1 or another 160-bit format",56:"SHA-224 / SHA3-224",64:"SHA-256 / SHA3-256 / BLAKE2s",96:"SHA-384 / SHA3-384",128:"SHA-512 / SHA3-512 / BLAKE2b"};
  return {output: candidates[candidate.length] ?? "Unrecognized digest length", meta: {hex_characters:candidate.length,bits:candidate.length*4}, warnings:["Syntax and length identify candidates only, not a definitive algorithm or benignness."]};
}
// Inspect only bounded header bytes without parsing or executing the selected file.
export function metadata(bytes, filename = "") {
  const basename = filename.replaceAll("\\", "/").split("/").pop();
  const extension = basename.includes(".") ? basename.split(".").pop().toLowerCase() : "";
  for (const [signature, kind, expected] of SIGNATURES) {
    let matches = bytes.length >= signature.length;
    for (let index = 0; index < signature.length && matches; index += 1) if (bytes[index] !== signature[index]) matches = false;
    if (matches) return {signature:kind,extension_mismatch:Boolean(filename && !expected.includes(extension))};
  }
  return {signature:"Unknown / no supported signature",extension_mismatch:false};
}
// Calculate exact basic fingerprints with vetted local MD5 and native SHA primitives.
export async function hashBytes(input, options) {
  if (options.action === "identify") return identifyHash(typeof input === "string" ? input : new TextDecoder("utf-8",{fatal:true}).decode(input));
  const bytes = input instanceof Uint8Array ? input : new TextEncoder().encode(wellFormed(input));
  if (bytes.length > 5 * 1024 * 1024) throw new Error("Browser hashing is limited to 5 MiB.");
  if (!Array.isArray(options.algorithms) || !options.algorithms.length || options.algorithms.length > 4) throw new Error("Choose one or more basic browser algorithms.");
  const names = [...new Set(options.algorithms)];
  const expected = options.expected ?? "";
  if (expected && !/^[0-9a-f]{1,128}$/i.test(expected)) throw new Error("Expected digest must be hexadecimal without spaces.");
  const digests = {};
  for (const name of names) {
    if (!Object.hasOwn(SUPPORTED, name)) throw new Error("This algorithm requires explicit server mode.");
    if (name === "md5") digests[name] = md5(bytes).map(hexByte).join("");
    else {
      if (!globalThis.crypto?.subtle) throw new Error("SHA hashing requires HTTPS or localhost in a supported browser.");
      const digest = await crypto.subtle.digest(SUPPORTED[name], bytes);
      digests[name] = Array.from(new Uint8Array(digest), hexByte).join("");
    }
  }
  const meta = {bytes:bytes.length, ...metadata(bytes.subarray(0,32), options.filename)};
  if (expected) meta.expected_match = Object.values(digests).includes(expected.toLowerCase());
  const lines = [];
  for (const [name, value] of Object.entries(digests)) lines.push(`${name.toUpperCase()}: ${value}`);
  return {output:lines.join("\n"),meta,data:{digests},warnings:["MD5/SHA-1 are legacy fingerprints. Matching hashes and header signatures are not safety verdicts."]};
}

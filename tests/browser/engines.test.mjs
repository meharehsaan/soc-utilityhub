import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { encode, decode, transformEncoding, fromBase64 } from "../../app/static/js/tools/encoder-engine.js";
import { hashBytes, identifyHash } from "../../app/static/js/tools/hash-engine.js";
const entities = JSON.parse(readFileSync(new URL("../../app/static/data/html-entities.json", import.meta.url)));
const utf8 = new TextEncoder();
const decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });

for (const format of ["base64", "base64url", "base32", "hex", "url", "html", "json", "unicode", "octal"]) {
  for (const source of ["", "Hello <analyst> & \"friend\"", "café 😀\n"]) {
    // Every declared text format must round-trip actual UTF-8 input.
    test(format + " round-trip " + JSON.stringify(source), function roundTrip() {
      const encoded = encode(utf8.encode(source), format);
      assert.equal(decoder.decode(decode(encoded, format, entities)), source);
    });
  }
}

// Canonical Base64 rejects invalid alphabets and nonzero unused padding bits.
test("strict Base64", function strictBase64() {
  for (const invalid of ["AB==", "a===", "a", "%%%%", "SGVsbG8"]) assert.throws(function reject() { fromBase64(invalid); });
  assert.equal(decoder.decode(fromBase64("SGVsbG8", true)), "Hello");
});

// Repeated decoding retains intermediate layers without interpreting payload markup.
test("layered HTML is inert", function layeredHTML() {
  const result = transformEncoding("&amp;lt;script&amp;gt;", {mode:"layers", format:"html", depth:3}, entities);
  assert.equal(result.output, "<script>");
  assert.equal(result.data.layers.length, 3);
});

// PowerShell decoding reads UTF-16LE bytes without executing their contents.
test("PowerShell UTF-16LE", function powershell() {
  const bytes = new Uint8Array([87,0,114,0,105,0,116,0,101,0,45,0,72,0,111,0,115,0,116,0]);
  assert.equal(transformEncoding(encode(bytes,"base64"), {mode:"powershell"}).output, "Write-Host");
});

// Binary decoding preserves exact bytes for download.
test("binary output", function binaryOutput() {
  const result = transformEncoding("/wAB", {mode:"standard", action:"decode", format:"base64"});
  assert.deepEqual(result.binary, Uint8Array.of(255,0,1));
});

// Malformed escape sequences fail instead of being evaluated or repaired.
test("strict escapes", function malformedEscapes() {
  for (const [source, format] of [["%", "url"], ["0", "hex"], ["\\uD800", "unicode"], ["\\400", "octal"], ["{}", "json"]]) {
    assert.throws(function rejectEscape() { decode(source, format, entities); });
  }
});

// Known vectors verify vendored MD5 and browser-native SHA together.
test("hash abc vector", async function hashVector() {
  const result = await hashBytes("abc", {action:"hash", algorithms:["md5","sha1","sha256","sha512"]});
  assert.equal(result.data.digests.md5, "900150983cd24fb0d6963f7d28e17f72");
  assert.equal(result.data.digests.sha1, "a9993e364706816aba3e25717850c26c9cd0d89d");
  assert.equal(result.data.digests.sha256, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  assert.equal(result.data.digests.sha512.length, 128);
});

// Exact whitespace changes fingerprints, while format identification stays ambiguous.
test("hash exact input and identification", async function exactHash() {
  const a = await hashBytes("abc", {action:"hash",algorithms:["md5"]});
  const b = await hashBytes("abc\n", {action:"hash",algorithms:["md5"]});
  assert.notEqual(a.output,b.output);
  assert.match(identifyHash("a".repeat(32)).output,/another/);
});

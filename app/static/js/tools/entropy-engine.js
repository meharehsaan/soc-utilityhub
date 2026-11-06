// Measure empirical uncertainty without assigning a security verdict.
export function shannon(counts, total) {
  if (!total) {
    return null;
  }
  let entropy = 0;
  for (const count of counts.values()) {
    const p = count / total;
    entropy -= p * Math.log2(p);
  }
  return entropy;
}

// Separate byte entropy from Unicode code-point entropy.
export function operate({text: text = "", bytes: bytes = null}) {
  const source = bytes ? new Uint8Array(bytes) : (new TextEncoder).encode(text);
  if (source.length > 5 * 1024 * 1024) {
    throw new Error("Input is limited to 5 MiB.");
  }
  const counts = new Map;
  for (const byte of source) {
    counts.set(byte, (counts.get(byte) ?? 0) + 1);
  }
  let characters = null;
  if (!bytes) {
    const chars = new Map;
    let size = 0;
    for (const char of text) {
      size++;
      chars.set(char, (chars.get(char) ?? 0) + 1);
    }
    characters = {
      codepoints: size,
      bits_per_codepoint: shannon(chars, size)
    };
  }
  const histogram = Array.from({
    length: 256
  }, (_, byte) => ({
    hex: byte.toString(16).padStart(2, "0"),
    count: counts.get(byte) ?? 0
  }));
  return {
    output: JSON.stringify({
      bits_per_byte: shannon(counts, source.length),
      byte_range: "0–8; empty input is undefined",
      characters: characters,
      histogram: histogram
    }, null, 2),
    meta: {
      bytes: source.length,
      distinct_bytes: counts.size
    },
    warnings: [ "Entropy depends on sample length and representation. High entropy alone does not prove packing, encryption, or maliciousness." ]
  };
}

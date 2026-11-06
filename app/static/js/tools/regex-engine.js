const SNIPPETS = {
  cve: "CVE-\\d{4}-\\d{4,}",
  timestamp: "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})",
  ipv4: "(?:25[0-5]|2[0-4]\\d|1\\d{2}|[1-9]?\\d)(?:\\.(?:25[0-5]|2[0-4]\\d|1\\d{2}|[1-9]?\\d)){3}",
  base64: "(?:[A-Za-z0-9+/]{4}){4,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?",
  windows: "[A-Za-z]:\\\\[^\\r\\n<>:\"|?*]+"
};

// Escape literal builder values for JavaScript RegExp.
export function escapeRegex(value) {
  return value.replace(/[.*+?^$()|[\]{}\\]/g, "\\$&");
}

// Run bounded matching inside a terminable worker.
export function operate({text: text, pattern: pattern = "", flags: flags = "g", template: template = "custom", literal: literal = ""}) {
  if (text.length > 2e5 || pattern.length > 2048 || literal.length > 512) {
    throw new Error("Use samples under 200,000 characters and patterns under 2,048.");
  }
  if (!/^[gimsu]*$/.test(flags) || new Set(flags).size !== flags.length) {
    throw new Error("Allowed unique flags: g, i, m, s, u.");
  }
  if (template !== "custom") {
    if (template === "literal") {
      pattern = escapeRegex(literal);
    } else if (Object.hasOwn(SNIPPETS, template)) {
      pattern = SNIPPETS[template];
    } else {
      throw new Error("Unknown template.");
    }
  }
  if (!pattern) {
    throw new Error("Enter a pattern or choose a template.");
  }
  let regex;
  try {
    regex = new RegExp(pattern, flags.includes("g") ? flags : flags + "g");
  } catch {
    throw new Error("Invalid or unsupported JavaScript regular expression.");
  }
  const matches = [];
  let match, retained = 0;
  while ((match = regex.exec(text)) !== null) {
    if (matches.length >= 5e3) {
      throw new Error("More than 5,000 matches; narrow the pattern.");
    }
    if (match.length > 129) {
      throw new Error("Use at most 128 capture groups.");
    }
    retained += match.reduce((size, item) => size + (item?.length ?? 0), 0) + Object.entries(match.groups ?? {}).reduce((size, [key, item]) => size + key.length + (item?.length ?? 0), 0) + 256;
    if (retained > 25e4) {
      throw new Error("Match and capture output exceeds its budget; narrow the input.");
    }
    matches.push({
      match: match[0],
      start_utf16: match.index,
      end_utf16: match.index + match[0].length,
      groups: match.slice(1).map(item => item ?? null),
      named_groups: match.groups ?? null
    });
    if (!flags.includes("g")) {
      break;
    }
    if (match[0] === "") {
      regex.lastIndex += flags.includes("u") && text.codePointAt(regex.lastIndex) > 65535 ? 2 : 1;
    }
  }
  return {
    output: JSON.stringify({
      pattern: pattern,
      flags: flags,
      dialect: "JavaScript RegExp",
      matches: matches
    }, null, 2),
    meta: {
      matches: matches.length
    },
    warnings: [ "Offsets are UTF-16 code units. Templates detect syntax, not semantic IP/CIDR validity. JavaScript differs from Python/SIEM dialects." ]
  };
}

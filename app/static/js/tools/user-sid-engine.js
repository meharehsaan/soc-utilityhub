const KNOWN = {
  "S-1-0-0": "Nobody",
  "S-1-1-0": "Everyone",
  "S-1-2-0": "Local",
  "S-1-3-0": "Creator owner",
  "S-1-5-2": "Network",
  "S-1-5-4": "Interactive",
  "S-1-5-7": "Anonymous logon",
  "S-1-5-11": "Authenticated users",
  "S-1-5-14": "Remote interactive logon",
  "S-1-5-18": "Local System",
  "S-1-5-19": "Local Service",
  "S-1-5-20": "Network Service",
  "S-1-5-32-544": "Builtin Administrators group",
  "S-1-5-32-545": "Builtin Users group",
  "S-1-5-32-546": "Builtin Guests group",
  "S-1-16-4096": "Low integrity",
  "S-1-16-8192": "Medium integrity",
  "S-1-16-12288": "High integrity",
  "S-1-16-16384": "System integrity"
};

const RIDS = {
  500: "Administrator account",
  501: "Guest account",
  502: "KRBTGT account (domain context)",
  512: "Domain Admins group",
  513: "Domain Users group",
  514: "Domain Guests group",
  515: "Domain Computers group",
  516: "Domain Controllers group",
  518: "Schema Admins group (forest root context)",
  519: "Enterprise Admins group (forest root context)"
};

// Validate full SID structure before applying contextual account labels.
export function parseSid(source) {
  if (source.length > 200 || !/^S-\d+-\d+(?:-\d+){0,15}$/i.test(source)) {
    throw new Error("Use a decimal SID with at most 15 subauthorities.");
  }
  const fields = source.slice(2).split("-").map(BigInt);
  if (fields[0] !== 1n || fields[1] > 281474976710655n || fields.slice(2).some(item => item > 4294967295n)) {
    throw new Error("Unsupported revision or out-of-range component.");
  }
  const canonical = "S-" + fields.join("-");
  const domain = fields[1] === 5n && fields[2] === 21n && fields.length === 7;
  return {
    source: source,
    canonical: canonical,
    revision: String(fields[0]),
    authority: String(fields[1]),
    subauthorities: fields.slice(2).map(String),
    meaning: KNOWN[canonical] ?? (domain ? RIDS[String(fields.at(-1))] ?? "Unknown account RID" : "Unknown SID"),
    context: domain ? "Domain or machine context; account existence is not resolved" : "Full SID mapping only"
  };
}

// Decode independent SID lines without account lookup.
export function operate({text: text}) {
  const lines = text.split(/\r?\n/).map(item => item.trim()).filter(Boolean);
  if (lines.length > 1e3) {
    throw new Error("Use at most 1,000 SIDs.");
  }
  const rows = lines.map(source => {
    try {
      return parseSid(source);
    } catch (error) {
      return {
        source: source,
        error: error.message
      };
    }
  });
  return {
    output: JSON.stringify(rows, null, 2),
    meta: {
      values: rows.length
    },
    warnings: [ "A trailing RID alone never identifies an account. Labels describe known structures, not account resolution." ]
  };
}

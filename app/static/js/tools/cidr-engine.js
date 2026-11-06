// Parse strict dotted IPv4 without ambiguous octal or short address notation.
export function ipv4(source) {
  const parts = source.split(".");
  if (parts.length !== 4 || parts.some(part => !/^(?:0|[1-9]\d{0,2})$/.test(part) || Number(part) > 255)) {
    throw new Error("Invalid IPv4 address.");
  }
  return parts.reduce((value, part) => value << 8n | BigInt(part), 0n);
}

// Parse complete or compressed IPv6 and embedded dotted IPv4 into an exact integer.
export function ip(source) {
  if (source.includes("%") || source.length > 64) {
    throw new Error("Zone IDs and overlong IP values are unsupported.");
  }
  if (!source.includes(":")) {
    return {
      bits: 32,
      value: ipv4(source)
    };
  }
  let value = source;
  if (value.includes(".")) {
    const at = value.lastIndexOf(":");
    const tail = ipv4(value.slice(at + 1));
    value = value.slice(0, at + 1) + (tail >> 16n).toString(16) + ":" + (tail & 65535n).toString(16);
  }
  const halves = value.split("::");
  if (halves.length > 2) {
    throw new Error("Invalid IPv6 compression.");
  }
  const left = halves[0] ? halves[0].split(":") : [], right = halves.length === 2 && halves[1] ? halves[1].split(":") : [];
  if ([ ...left, ...right ].some(part => !/^[0-9a-f]{1,4}$/i.test(part))) {
    throw new Error("Invalid IPv6 group.");
  }
  const missing = 8 - left.length - right.length;
  if (halves.length === 1 && missing !== 0 || halves.length === 2 && missing < 1) {
    throw new Error("IPv6 must contain eight groups with at most one compression.");
  }
  const groups = [ ...left, ...Array(missing).fill("0"), ...right ];
  return {
    bits: 128,
    value: groups.reduce((result, part) => result << 16n | BigInt("0x" + part), 0n)
  };
}

// Render an IP integer with longest-leftmost IPv6 zero compression.
export function formatIp(value, bits) {
  if (bits === 32) {
    return [ 24n, 16n, 8n, 0n ].map(shift => String(value >> shift & 255n)).join(".");
  }
  const parts = Array.from({
    length: 8
  }, (_, index) => Number(value >> BigInt((7 - index) * 16) & 65535n).toString(16));
  let best = -1, size = 1;
  for (let i = 0; i < 8; i++) {
    if (parts[i] !== "0") {
      continue;
    }
    let end = i;
    while (end < 8 && parts[end] === "0") {
      end++;
    }
    if (end - i > size) {
      best = i;
      size = end - i;
    }
    i = end - 1;
  }
  if (best < 0) {
    return parts.join(":");
  }
  return parts.slice(0, best).join(":") + "::" + parts.slice(best + size).join(":");
}

// Derive inclusive exact network ranges without enumerating addresses.
export function network(source) {
  const parts = source.trim().split("/");
  if (parts.length > 2) {
    throw new Error("Use one optional CIDR prefix.");
  }
  const parsed = ip(parts[0]);
  if (parts.length === 2 && !/^(?:0|[1-9]\d{0,2})$/.test(parts[1])) {
    throw new Error("Invalid CIDR prefix.");
  }
  const prefix = parts.length === 2 ? Number(parts[1]) : parsed.bits;
  if (prefix > parsed.bits) {
    throw new Error("CIDR prefix exceeds address width.");
  }
  const hostBits = BigInt(parsed.bits - prefix), start = parsed.value >> hostBits << hostBits, end = start + (1n << hostBits) - 1n;
  return {
    ...parsed,
    prefix: prefix,
    start: start,
    end: end,
    count: 1n << hostBits,
    canonical: formatIp(start, parsed.bits) + "/" + prefix
  };
}

// Compare only ranges in the same IP family.
export function overlaps(a, b) {
  return a.bits === b.bits && a.start <= b.end && b.start <= a.end;
}

// Classify special address ranges conservatively without claiming public routability.
export function classification(parsed) {
  const rules = parsed.bits === 32 ? [ [ "0.0.0.0/8", "Current-network / unspecified" ], [ "10.0.0.0/8", "Private" ], [ "100.64.0.0/10", "Shared carrier space" ], [ "127.0.0.0/8", "Loopback" ], [ "169.254.0.0/16", "Link-local" ], [ "172.16.0.0/12", "Private" ], [ "192.168.0.0/16", "Private" ], [ "192.0.2.0/24", "Documentation" ], [ "198.18.0.0/15", "Benchmark" ], [ "198.51.100.0/24", "Documentation" ], [ "203.0.113.0/24", "Documentation" ], [ "224.0.0.0/4", "Multicast" ], [ "240.0.0.0/4", "Reserved" ] ] : [ [ "::/128", "Unspecified" ], [ "::1/128", "Loopback" ], [ "::ffff:0:0/96", "IPv4-mapped; inspect embedded IPv4" ], [ "fc00::/7", "Unique local" ], [ "fe80::/10", "Link-local" ], [ "ff00::/8", "Multicast" ], [ "2001:db8::/32", "Documentation" ] ];
  return rules.filter(([cidr]) => {
    const item = network(cidr);
    return parsed.start >= item.start && parsed.end <= item.end;
  }).map(([, name]) => name).join(", ") || "Other or mixed space; no routability claim";
}

// Match attributed ranges while distinguishing full coverage from partial intersections.
export function contextMatches(parsed, data) {
  return data.entries.map(entry => ({
    ...entry,
    range: network(entry.cidr)
  })).filter(entry => overlaps(parsed, entry.range)).sort((a, b) => b.range.prefix - a.range.prefix).map(({range: range, ...entry}) => ({
    ...entry,
    prefix_length: range.prefix,
    coverage: parsed.start >= range.start && parsed.end <= range.end ? "entire input covered" : "partial input overlap"
  }));
}

// Calculate ranges and optional separate ASN/cloud context without DNS or WHOIS.
export async function operate({text: text, comparison: comparison = "", corporate: corporate = "", context: context = false, datasets: datasets = null}) {
  const lines = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
  if (lines.length > 100 || comparison.length > 128 || corporate.length > 2e4) {
    throw new Error("Use at most 100 input ranges and a small corporate range list.");
  }
  const target = comparison.trim() ? network(comparison) : null;
  const corporateLines = corporate.split(/\r?\n/).filter(line => line.trim());
  if (corporateLines.length > 200) {
    throw new Error("Use at most 200 corporate ranges.");
  }
  const custom = {
    entries: corporateLines.map(line => {
      const [cidr, ...label] = line.trim().split(/\s+/);
      network(cidr);
      return {
        cidr: cidr,
        label: label.join(" ") || "Corporate range"
      };
    })
  };
  let data = null;
  if (context) {
    data = datasets ?? await Promise.all([ "asn-prefixes", "cloud-prefixes" ].map(async name => {
      const response = await fetch("/static/data/" + name + ".json");
      if (!response.ok) {
        throw new Error("Offline prefix data unavailable.");
      }
      return response.json();
    }));
  }
  const rows = lines.map(source => {
    try {
      const parsed = network(source), matches = data ? {
        asn_origins: contextMatches(parsed, data[0]),
        cloud_labels: contextMatches(parsed, data[1])
      } : null;
      return {
        source: source,
        family: "IPv" + (parsed.bits === 32 ? 4 : 6),
        address: formatIp(parsed.value, parsed.bits),
        network: parsed.canonical,
        range_start: formatIp(parsed.start, parsed.bits),
        range_end: formatIp(parsed.end, parsed.bits),
        addresses: String(parsed.count),
        classification: classification(parsed),
        ipv4_broadcast: parsed.bits === 32 && parsed.prefix <= 30 ? formatIp(parsed.end, 32) : null,
        comparison: target ? {
          overlap: overlaps(parsed, target),
          input_contains_comparison: parsed.bits === target.bits && parsed.start <= target.start && parsed.end >= target.end,
          comparison_contains_input: parsed.bits === target.bits && target.start <= parsed.start && target.end >= parsed.end
        } : null,
        corporate_matches: contextMatches(parsed, custom),
        offline_context: matches
      };
    } catch (error) {
      return {
        source: source,
        error: error.message
      };
    }
  });
  const references = data?.map(item => ({
    dataset: item.dataset,
    version: item.version,
    retrieved_on: item.retrieved_on,
    partial: item.partial,
    coverage: item.coverage,
    sources: item.sources
  })) ?? [];
  return {
    output: JSON.stringify({
      results: rows,
      references: references
    }, null, 2),
    meta: {
      ranges: rows.length
    },
    warnings: [ "No addresses enumerated. ASN origins and cloud labels are separate, partial dated snapshots. Unknown means absent from this snapshot; matches do not imply trust. Corporate ranges exist only for this operation." ]
  };
}

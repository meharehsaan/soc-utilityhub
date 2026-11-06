const MONTHS = {
  JAN: 1,
  FEB: 2,
  MAR: 3,
  APR: 4,
  MAY: 5,
  JUN: 6,
  JUL: 7,
  AUG: 8,
  SEP: 9,
  OCT: 10,
  NOV: 11,
  DEC: 12
};

const DAYS = {
  SUN: 0,
  MON: 1,
  TUE: 2,
  WED: 3,
  THU: 4,
  FRI: 5,
  SAT: 6
};

// Expand a bounded cron field using explicit numeric ranges, lists, steps, and names.
export function parseField(source, min, max, names = {}) {
  if (source.length > 128) {
    throw new Error("Cron fields are limited to 128 characters.");
  }
  const expanded = source.toUpperCase().replace(/[A-Z]+/g, name => {
    if (!Object.hasOwn(names, name)) {
      throw new Error("Unknown cron name.");
    }
    return String(names[name]);
  });
  const values = new Set;
  for (const part of expanded.split(",")) {
    const match = /^(\*|\d+(?:-\d+)?)(?:\/(\d+))?$/.exec(part);
    if (!match) {
      throw new Error("Supported syntax: *, numbers, lists, ranges, and steps. No ?, L, W, #, or macros.");
    }
    const step = match[2] ? Number(match[2]) : 1;
    if (!Number.isInteger(step) || step < 1 || step > max - min + 1) {
      throw new Error("Cron step is outside its field range.");
    }
    let start = min, end = max;
    if (match[1] !== "*") {
      const range = match[1].split("-").map(Number);
      start = range[0];
      end = range.length === 2 ? range[1] : match[2] ? max : start;
    }
    if (start < min || end > max || start > end) {
      throw new Error("Cron field is outside its allowed range.");
    }
    for (let n = start; n <= end; n += step) {
      values.add(n);
    }
  }
  return {
    source: source,
    values: values,
    wildcard: source === "*",
    star: source.startsWith("*")
  };
}

// Keep five-field Unix and six-field seconds-first dialects explicit.
export function parseCron(expression, dialect = "unix") {
  const parts = expression.trim().split(/\s+/), six = dialect === "seconds";
  if (![ "unix", "seconds" ].includes(dialect) || parts.length !== (six ? 6 : 5)) {
    throw new Error("Select five-field Unix or six-field seconds-first syntax explicitly.");
  }
  const specs = six ? [ [ 0, 59, {} ], [ 0, 59, {} ], [ 0, 23, {} ], [ 1, 31, {} ], [ 1, 12, MONTHS ], [ 0, 7, DAYS ] ] : [ [ 0, 59, {} ], [ 0, 23, {} ], [ 1, 31, {} ], [ 1, 12, MONTHS ], [ 0, 7, DAYS ] ];
  const fields = parts.map((part, index) => parseField(part, ...specs[index]));
  if (!six) {
    fields.unshift(parseField("0", 0, 59));
  }
  const dow = fields[5].values;
  if (dow.has(7)) {
    dow.delete(7);
    dow.add(0);
  }
  return {
    expression: expression,
    fields: fields
  };
}

// Apply Cronie day matching with explicit leading-star behavior.
export function matchesMinute(schedule, parts) {
  const [, minute, hour, dom, month, dow] = schedule.fields;
  if (!minute.values.has(parts.minute) || !hour.values.has(parts.hour) || !month.values.has(parts.month)) {
    return false;
  }
  const a = dom.values.has(parts.day), b = dow.values.has(parts.dow);
  return dom.star || dow.star ? a && b : a || b;
}

// Describe the selected fields without implying a scheduler will run any task.
export function describe(schedule, zone) {
  const labels = [ "seconds", "minutes", "hours", "days of month", "months", "days of week (Sunday=0)" ];
  return schedule.fields.map((field, index) => field.wildcard ? "Every " + labels[index] : labels[index] + ": " + field.source).join("; ") + ". Zone: " + zone + ".";
}

// Reject impossible calendar dates that JavaScript Date.parse would silently normalize.
export function validReference(source) {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,3})?(Z|[+-]\d{2}:\d{2})$/.exec(source);
  if (!match) {
    return false;
  }
  const [, year, month, day, hour, minute, second, offset] = match;
  const maximumDay = new Date(Date.UTC(Number(year), Number(month), 0)).getUTCDate();
  return Number(month) >= 1 && Number(month) <= 12 && Number(day) >= 1 && Number(day) <= maximumDay && Number(hour) < 24 && Number(minute) < 60 && Number(second) < 60 && (offset === "Z" || Number(offset.slice(1, 3)) < 24 && Number(offset.slice(4)) < 60);
}

// Preview real UTC instants so DST gaps skip and folds can yield both wall-time occurrences.
export function operate({text: text, dialect: dialect = "unix", zone: zone = "UTC", reference: reference = "", horizon_days: horizon_days = 366}) {
  if (text.length > 4096) {
    throw new Error("Cron input is limited to 4,096 characters.");
  }
  const expressions = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
  if (!expressions.length || expressions.length > 8) {
    throw new Error("Use one to eight cron expressions.");
  }
  if (!validReference(reference)) {
    throw new Error("Supply an ISO reference instant with Z or an explicit UTC offset.");
  }
  const start = Date.parse(reference);
  if (!Number.isFinite(start) || start < 0 || start > 2533707648e5) {
    throw new Error("Use a reference instant between 1970 and 9998.");
  }
  if (!Number.isInteger(horizon_days) || horizon_days < 1 || horizon_days > 366) {
    throw new Error("Choose a horizon of 1–366 days.");
  }
  let formatter;
  try {
    formatter = new Intl.DateTimeFormat("en-US", {
      timeZone: zone,
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
      weekday: "short",
      hourCycle: "h23"
    });
    formatter.format(start);
  } catch {
    throw new Error("Choose a supported IANA timezone.");
  }
  const schedules = expressions.map(expression => ({
    ...parseCron(expression, dialect),
    next: []
  }));
  const end = start + horizon_days * 864e5, deadline = performance.now() + 8e3;
  let scanned = 0, limited = false;
  for (let minute = Math.floor(start / 6e4) * 6e4; minute <= end; minute += 6e4) {
    if (++scanned % 1e3 === 0 && performance.now() > deadline) {
      limited = true;
      break;
    }
    const tokens = Object.fromEntries(formatter.formatToParts(minute).map(part => [ part.type, part.value ]));
    const parts = {
      minute: Number(tokens.minute),
      hour: Number(tokens.hour),
      day: Number(tokens.day),
      month: Number(tokens.month),
      dow: DAYS[tokens.weekday.toUpperCase()]
    };
    for (const schedule of schedules) {
      if (schedule.next.length >= 5 || !matchesMinute(schedule, parts)) {
        continue;
      }
      for (const second of [ ...schedule.fields[0].values ].sort((a, b) => a - b)) {
        const instant = minute + second * 1e3;
        if (instant <= start || instant > end) {
          continue;
        }
        schedule.next.push({
          utc: new Date(instant).toISOString(),
          local: formatter.format(instant) + ":" + String(second).padStart(2, "0"),
          zone: zone
        });
        if (schedule.next.length === 5) {
          break;
        }
      }
    }
    if (schedules.every(schedule => schedule.next.length === 5)) {
      break;
    }
  }
  const overlap = [];
  for (let a = 0; a < schedules.length; a++) {
    for (let b = a + 1; b < schedules.length; b++) {
      const times = new Set(schedules[b].next.map(item => item.utc));
      const common = schedules[a].next.filter(item => times.has(item.utc)).map(item => item.utc);
      if (common.length) {
        overlap.push({
          schedules: [ a + 1, b + 1 ],
          utc: common
        });
      }
    }
  }
  return {
    output: JSON.stringify({
      schedules: schedules.map(schedule => ({
        expression: schedule.expression,
        description: describe(schedule, zone),
        next: schedule.next
      })),
      overlaps_among_previewed_executions: overlap,
      scan_limited: limited,
      minutes_scanned: scanned
    }, null, 2),
    meta: {
      schedules: schedules.length
    },
    warnings: [ "Preview only. Cronie day rules: OR when neither day field starts with *; otherwise both fields must match. DST gaps skip and folds may repeat. Overlap compares only shown executions. Sparse schedules may have fewer than five results within the selected horizon or execution budget." ]
  };
}

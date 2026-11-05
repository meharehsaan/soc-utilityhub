import ipaddress
from urllib.parse import urlsplit, urlunsplit

import idna
import regex

from app.core.errors import ToolError
from app.schemas.ioc import IocOptions
from app.utils import json_result

PATTERNS = {
    "url": r"\b(?:https?|hxxps?)://[^\s<>\"']+",
    "email": r"(?<![\w.+-])[A-Za-z0-9.!#$%&'*+/=?^{}|~-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?\.[A-Za-z]{2,63}(?![\w.-])",
    "ip": r"(?<![\w:.])(?:[0-9]{1,3}(?:\.|\[\.\])){3}[0-9]{1,3}(?![0-9])|(?<![\w:])[0-9A-Fa-f:]{2,64}(?![\w:])",
    "domain": r"(?<![\w@.-])(?:[A-Za-z0-9\u0080-\uffff](?:[A-Za-z0-9\u0080-\uffff-]{0,61}[A-Za-z0-9\u0080-\uffff])?(?:\.|\[\.\]))+[A-Za-z\u0080-\uffff][A-Za-z0-9\u0080-\uffff-]{1,62}(?![\w-])",
    "hash": r"(?<![A-Fa-f0-9])(?:[A-Fa-f0-9]{128}|[A-Fa-f0-9]{96}|[A-Fa-f0-9]{64}|[A-Fa-f0-9]{56}|[A-Fa-f0-9]{40}|[A-Fa-f0-9]{32})(?![A-Fa-f0-9])",
}


# Restore only documented indicator defanging conventions.
def refang_value(value: str) -> str:
    match = regex.match(r"^(https?|hxxps?)(?::|\[:\])//([^/?#]*)(.*)$", value, regex.IGNORECASE)
    if match:
        scheme = "https" if match[1].lower().endswith("s") else "http"
        prefix, separator, host = match[2].rpartition("@")
        authority = (prefix + "@" if separator else "") + (host if separator else match[2]).replace(
            "[.]", "."
        ).replace("[:]", ":")
        return scheme + "://" + authority + match[3]
    if "@" in value:
        local, domain = value.rsplit("@", 1)
        return local + "@" + domain.replace("[.]", ".")
    return value.replace("[.]", ".").replace("[:]", ":")


# Validate one complete domain rather than accepting arbitrary dotted text.
def domain_ascii(value: str) -> str:
    if len(value) > 253:
        raise ValueError("domain length")
    result = idna.encode(value.rstrip("."), uts46=True).decode("ascii").lower()
    if "." not in result:
        raise ValueError("not a qualified domain")
    return result


# Trim only unmatched report punctuation without damaging IPv6 brackets.
def clean_url(value: str) -> str:
    value = value.rstrip(".,;")
    for closing, opening in ((")", "("), ("]", "[")):
        while value.endswith(closing) and value.count(closing) > value.count(opening):
            value = value[:-1]
    return value


# Validate observations and preserve original source coordinates before normalization.
def normalize_candidate(kind: str, raw: str) -> tuple[str, str]:
    if len(raw) > 4096:
        raise ValueError("indicator length")
    if kind == "url":
        raw = clean_url(raw)
    elif kind == "ip":
        raw = raw.rstrip(".")
    value = refang_value(raw)
    if kind == "ip":
        value = str(ipaddress.ip_address(value))
    elif kind == "domain":
        value = domain_ascii(value)
    elif kind == "url":
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise ValueError("URL authority")
        _ = parts.port
        if ":" not in parts.hostname:
            domain_ascii(parts.hostname)
    elif kind == "email":
        local, domain = value.rsplit("@", 1)
        value = local + "@" + domain_ascii(domain)
    else:
        value = value.lower()
    return raw, value


# Transform a validated indicator's host delimiters without rewriting path or query text.
def defang_value(value: str) -> str:
    value = refang_value(value)
    try:
        address = ipaddress.ip_address(value)
        return (
            str(address).replace(".", "[.]")
            if address.version == 4
            else str(address).replace(":", "[:]")
        )
    except ValueError:
        pass
    if "://" in value:
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("URL")
        _ = parts.port
        if ":" not in parts.hostname:
            domain_ascii(parts.hostname)
        userinfo, separator, authority = parts.netloc.rpartition("@")
        authority = authority if separator else parts.netloc
        if authority.startswith("["):
            end = authority.index("]")
            authority = authority[: end + 1].replace(":", "[:]") + authority[end + 1 :]
        else:
            authority = authority.replace(".", "[.]")
        netloc = userinfo + "@" + authority if separator else authority
        return urlunsplit(
            (
                "hxxps" if parts.scheme == "https" else "hxxp",
                netloc,
                parts.path,
                parts.query,
                parts.fragment,
            )
        )
    if "@" in value:
        local, domain = value.rsplit("@", 1)
        return local + "@" + domain_ascii(domain).replace(".", "[.]")
    return domain_ascii(value).replace(".", "[.]")


# Extract bounded candidate observations or apply an explicitly selected direct sharing transform.
def inspect_iocs(options: IocOptions) -> dict:
    if options.mode != "extract":
        lines = [line.strip() for line in options.text.splitlines() if line.strip()]
        if len(lines) > 1000 or any(len(line) > 4096 for line in lines):
            raise ToolError(
                "Use at most 1,000 indicators of 4,096 characters each.", "work_limit", 413
            )
        output, errors = [], []
        for index, line in enumerate(lines, 1):
            try:
                transformed = defang_value(line)
                output.append(
                    refang_value(transformed) if options.mode == "refang" else transformed
                )
            except (ValueError, idna.IDNAError):
                output.append(line)
                errors.append(f"Line {index}: not a supported complete indicator; unchanged.")
        return {
            "output": "\n".join(output),
            "meta": {"indicators": len(lines), "unchanged_errors": len(errors)},
            "warnings": errors
            + ["Output is inert text. Defanging does not anonymize user information."],
        }
    if not options.types:
        raise ToolError("Select at least one observation type.")
    rows, seen, observations = [], {}, 0
    try:
        for kind in dict.fromkeys(options.types):
            for match in regex.finditer(PATTERNS[kind], options.text, regex.IGNORECASE, timeout=1):
                try:
                    raw, value = normalize_candidate(kind, match.group())
                except (ValueError, idna.IDNAError):
                    continue
                observations += 1
                if observations > 10000:
                    raise ToolError(
                        "More than 10,000 observations; narrow the input.", "work_limit", 413
                    )
                identity = (kind, value)
                if identity not in seen:
                    seen[identity] = len(rows)
                    rows.append(
                        {"type": kind, "value": value, "first_source": raw, "occurrences": []}
                    )
                rows[seen[identity]]["occurrences"].append(
                    {"start": match.start(), "end": match.start() + len(raw)}
                )
    except TimeoutError as exc:
        raise ToolError("Observation matching exceeded its time limit.", "work_limit", 413) from exc
    return json_result(
        rows,
        {"unique_values": len(rows), "observations": observations},
        [
            "Candidate observations only, not threat verdicts. Offsets are Unicode code points. Pattern matching is not complete anonymization."
        ],
    )

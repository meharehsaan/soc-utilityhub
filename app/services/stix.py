import ipaddress
import json
import re
import uuid
from urllib.parse import urlsplit

from app.core.documents import DuplicateKey, load_document
from app.core.errors import ToolError
from app.schemas.stix import StixOptions
from app.services.ioc import domain_ascii
from app.utils import json_result

SCO_NAMESPACE = uuid.UUID("00abedb4-aa42-466c-9c01-fed23315a9b7")
SUPPORTED = {
    "ipv4-addr",
    "ipv6-addr",
    "domain-name",
    "url",
    "email-addr",
    "file",
    "network-traffic",
}


# Create a standard deterministic ID from this tool's string-only contributing-property subset.
def observable_id(kind: str, properties: dict) -> str:
    canonical = json.dumps(properties, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{kind}--{uuid.uuid5(SCO_NAMESPACE, canonical)}"


# Build supported cyber-observable objects without asserting threat intelligence.
def create_observable(kind: str, source: str) -> dict:
    if not isinstance(source, str) or len(source) > 4096:
        raise ToolError("Observable values must be bounded strings.")
    try:
        if kind in {"ipv4-addr", "ipv6-addr"}:
            address = ipaddress.ip_address(source)
            if address.version != (4 if kind == "ipv4-addr" else 6):
                raise ValueError
            properties = {"value": str(address)}
        elif kind == "domain-name":
            properties = {"value": domain_ascii(source)}
        elif kind == "url":
            parsed = urlsplit(source)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError
            _ = parsed.port
            properties = {"value": source}
        elif kind == "email-addr":
            local, domain = source.rsplit("@", 1)
            if not local or len(local) > 64 or any(char.isspace() for char in local):
                raise ValueError
            properties = {"value": local + "@" + domain_ascii(domain)}
        else:
            if not re.fullmatch("[0-9a-fA-F]{64}", source):
                raise ValueError
            properties = {"hashes": {"SHA-256": source.lower()}}
            kind = "file"
    except (ValueError, UnicodeError) as exc:
        raise ToolError("A value is invalid for the selected cyber-observable type.") from exc
    return {
        "type": kind,
        "spec_version": "2.1",
        "id": observable_id(kind, properties),
        **properties,
    }


# Validate identifier syntax and type correspondence without resolving any remote reference.
def valid_id(value: object, kind: str | None = None) -> bool:
    if not isinstance(value, str) or "--" not in value:
        return False
    prefix, suffix = value.split("--", 1)
    try:
        parsed = uuid.UUID(suffix)
    except ValueError:
        return False
    return bool(
        re.fullmatch(r"[a-z][a-z0-9-]*", prefix)
        and (kind is None or kind == prefix)
        and str(parsed) == suffix
        and parsed.variant == uuid.RFC_4122
    )


# Inspect bundle identifiers/references or export a bounded supported observable subset.
def inspect_stix(options: StixOptions) -> dict:
    if options.mode == "export":
        lines = list(
            dict.fromkeys(line.strip() for line in options.text.splitlines() if line.strip())
        )
        if len(lines) > 1000 or any(len(line) > 4096 for line in lines):
            raise ToolError(
                "Use at most 1,000 observables of 4,096 characters each.", "work_limit", 413
            )
        objects = [create_observable(options.observable, line) for line in lines]
        return json_result(
            {"type": "bundle", "id": f"bundle--{uuid.uuid4()}", "objects": objects},
            {"observables": len(objects)},
            ["Cyber-observables only; no maliciousness or indicator assertion is made."],
        )
    try:
        bundle = load_document(options.text)
    except DuplicateKey as exc:
        raise ToolError("Resolve duplicate keys before STIX inspection.") from exc
    if (
        not isinstance(bundle, dict)
        or bundle.get("type") != "bundle"
        or not isinstance(bundle.get("objects"), list)
    ):
        raise ToolError("Supply a STIX bundle object with an objects array.")
    objects = bundle["objects"]
    if len(objects) > 1000:
        raise ToolError("STIX inspection is limited to 1,000 objects.", "work_limit", 413)
    errors, warnings, ids = [], [], set()
    if not valid_id(bundle.get("id"), "bundle"):
        errors.append("Invalid bundle identifier.")
    for index, item in enumerate(objects):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("type"), str)
            or not valid_id(item.get("id"), item.get("type"))
        ):
            errors.append(f"Object {index + 1}: invalid type-qualified identifier.")
            continue
        if item["id"] in ids:
            errors.append(f"Object {index + 1}: duplicate identifier.")
        ids.add(item["id"])
        if item["type"] not in SUPPORTED:
            warnings.append(f"Object {index + 1}: type is outside the supported observable subset.")
        elif item["type"] in {"ipv4-addr", "ipv6-addr", "domain-name", "url", "email-addr"}:
            try:
                create_observable(item["type"], item.get("value", ""))
            except (ToolError, TypeError):
                errors.append(f"Object {index + 1}: invalid observable value.")
        elif item["type"] == "file":
            hashes = item.get("hashes", {})
            if not item.get("name") and not hashes:
                errors.append(f"Object {index + 1}: file needs a name or hashes.")
            if not isinstance(hashes, dict):
                errors.append(f"Object {index + 1}: hashes must be an object.")
            else:
                lengths = {"MD5": 32, "SHA-1": 40, "SHA-256": 64, "SHA-512": 128}
                for algorithm, digest in hashes.items():
                    if algorithm in lengths and (
                        not isinstance(digest, str)
                        or not re.fullmatch(r"[0-9a-fA-F]{" + str(lengths[algorithm]) + "}", digest)
                    ):
                        errors.append(f"Object {index + 1}: malformed file digest.")
        elif item["type"] == "network-traffic":
            protocols = item.get("protocols")
            if (
                not isinstance(protocols, list)
                or not protocols
                or any(not isinstance(protocol, str) or not protocol for protocol in protocols)
            ):
                errors.append(f"Object {index + 1}: network traffic needs protocols.")
            if not item.get("src_ref") and not item.get("dst_ref"):
                errors.append(f"Object {index + 1}: network traffic needs an endpoint reference.")
    for index, item in enumerate(objects):
        pending = [item]
        while pending:
            current = pending.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if key.endswith("_refs") and not isinstance(value, list):
                        errors.append(f"Object {index + 1}: reference collection must be an array.")
                    references = (
                        [value]
                        if key.endswith("_ref")
                        else value
                        if key.endswith("_refs") and isinstance(value, list)
                        else []
                    )
                    for reference in references:
                        if not valid_id(reference) or reference not in ids:
                            errors.append(f"Object {index + 1}: unresolved or invalid reference.")
                    pending.append(value)
            elif isinstance(current, list):
                pending.extend(current)
            if len(errors) > 100:
                raise ToolError("More than 100 STIX validation findings.", "work_limit", 413)
    return json_result(
        {"supported_subset_valid": not errors, "errors": errors, "objects": objects},
        {"objects": len(objects)},
        warnings[:100]
        + ["Limited structural/value checks, not full STIX conformance or threat verification."],
    )

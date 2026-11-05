from app.core.documents import DuplicateKey, load_document
from app.core.errors import ToolError
from app.schemas.events import EventsOptions
from app.utils import get_field, json_result

SECURITY = {
    4624: "Successful logon",
    4625: "Failed logon",
    4648: "Explicit credentials used",
    4688: "New process created",
    4720: "User account created",
    4726: "User account deleted",
    4732: "Member added to a local security group",
    1102: "Security audit log cleared",
}
SYSMON = {
    1: "Process creation",
    3: "Network connection",
    7: "Image loaded",
    11: "File creation",
    12: "Registry object created or deleted",
    13: "Registry value set",
    22: "DNS query",
}


# Describe only provider-qualified event identifiers rather than guessing from a numeric ID.
def event_meaning(provider: str, event_id: int) -> dict:
    mapping = (
        SECURITY
        if provider == "Microsoft-Windows-Security-Auditing"
        else SYSMON
        if provider == "Microsoft-Windows-Sysmon"
        else {}
    )
    return {
        "provider": provider,
        "event_id": event_id,
        "meaning": mapping.get(event_id, "No bundled definition for this provider/ID"),
        "reference": "https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon"
        if provider == "Microsoft-Windows-Sysmon"
        else "https://learn.microsoft.com/windows/security/threat-protection/auditing/audit-logon"
        if mapping
        else None,
    }


# Parse bounded Windows Event XML with entity and external-resource processing disabled.
def parse_xml(text: str) -> list[dict]:
    try:
        from defusedxml import ElementTree
        from defusedxml.common import DefusedXmlException
    except ImportError as exc:
        raise ToolError(
            "Install XML dependencies from requirements.txt.", "dependency_missing", 503
        ) from exc
    try:
        root = ElementTree.fromstring(
            text, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
    except (ElementTree.ParseError, DefusedXmlException) as exc:
        raise ToolError("Malformed XML or a forbidden DTD/entity declaration.") from exc
    pending, count = [(root, 0)], 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > 20000 or depth > 64:
            raise ToolError("XML exceeds its node/depth budget.", "work_limit", 413)
        pending.extend((child, depth + 1) for child in node)
    events = (
        [root]
        if root.tag.rsplit("}", 1)[-1] == "Event"
        else [child for child in root if child.tag.rsplit("}", 1)[-1] == "Event"]
    )
    if len(events) > 1000:
        raise ToolError("Use at most 1,000 Event XML records.", "work_limit", 413)
    rows = []
    for event in events:
        system, fields = {}, {}
        for child in event:
            kind = child.tag.rsplit("}", 1)[-1]
            if kind == "System":
                for item in child:
                    name = item.tag.rsplit("}", 1)[-1]
                    system[name] = {"text": item.text or "", **item.attrib}
            elif kind in {"EventData", "UserData"}:
                for item in child.iter():
                    if item is child:
                        continue
                    key = item.attrib.get("Name") or item.tag.rsplit("}", 1)[-1]
                    fields.setdefault(key, []).append(item.text or "")
        provider = system.get("Provider", {}).get("Name", "")
        try:
            event_id = int(system.get("EventID", {}).get("text", ""))
        except ValueError:
            event_id = -1
        rows.append(
            {"system": system, "fields": fields, "context": event_meaning(provider, event_id)}
        )
    return rows


# Inspect XML or explicit JSON exports without treating missing provider context as known.
def inspect_events(options: EventsOptions) -> dict:
    if options.mode == "lookup":
        return json_result(
            event_meaning(options.provider, options.event_id),
            warnings=["Reference lookup only; no event was observed or authenticated."],
        )
    if options.format == "xml":
        rows = parse_xml(options.text)
    else:
        try:
            data = load_document(options.text)
        except DuplicateKey as exc:
            raise ToolError("Resolve duplicate keys before event inspection.") from exc
        records = data if isinstance(data, list) else [data]
        if len(records) > 1000 or any(not isinstance(record, dict) for record in records):
            raise ToolError("Use at most 1,000 JSON object events.")
        rows = []
        for record in records:
            provider = (
                get_field(record, "ProviderName")
                or get_field(record, "System.Provider.Name")
                or get_field(record, "Event.System.Provider.@Name")
                or ""
            )
            value = (
                get_field(record, "EventID")
                or get_field(record, "System.EventID")
                or get_field(record, "Event.System.EventID")
            )
            if isinstance(value, dict):
                value = value.get("#text")
            try:
                event_id = int(str(value))
            except (TypeError, ValueError):
                event_id = -1
            rows.append({"record": record, "context": event_meaning(str(provider), event_id)})
    return json_result(
        rows,
        {"events": len(rows)},
        [
            "Provider/channel context matters. Binary EVTX and rendered Windows message catalogs are not decoded."
        ],
    )

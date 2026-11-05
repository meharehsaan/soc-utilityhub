from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    slug: str
    name: str
    description: str
    category: str
    accent: str
    symbol: str
    processing: str = "On your server"
    available: bool = True


TOOLS = (
    Tool(
        "sanitize",
        "Sanitizer",
        "Replace sensitive details before your next prompt.",
        "Text & privacy",
        "coral",
        "shield",
    ),
    Tool(
        "text",
        "Text workbench",
        "Sort, deduplicate, and clean up the little things.",
        "Text & privacy",
        "mint",
        "lines",
    ),
    Tool(
        "logs",
        "Log inspector",
        "Give raw records structure, context, and breathing room.",
        "Data & logs",
        "amber",
        "terminal",
    ),
    Tool(
        "json",
        "JSON explorer",
        "Open the branch you need. Close the noise.",
        "Data & logs",
        "violet",
        "braces",
    ),
    Tool(
        "hash",
        "Hash & file info",
        "Fingerprint exact bytes. Check what changed.",
        "Files & encoding",
        "blue",
        "hash",
        "Choose browser or server",
    ),
    Tool(
        "encoder",
        "Encoder / decoder",
        "Unwrap encodings one deliberate layer at a time.",
        "Files & encoding",
        "rose",
        "arrows",
        "In your browser",
    ),
    Tool(
        "compare",
        "Compare",
        "Find the overlap, the difference, and the missing piece.",
        "Data & logs",
        "cyan",
        "compare",
    ),
    Tool(
        "ioc",
        "IOC workbench",
        "Extract observations and share safely defanged indicators.",
        "Investigation",
        "ioc",
        "shield",
    ),
    Tool(
        "timestamp",
        "Timestamp converter",
        "Put mixed clock formats on one explicit timeline.",
        "Investigation",
        "timestamp",
        "clock",
    ),
    Tool(
        "url",
        "URL inspector",
        "Inspect components without opening the destination.",
        "Investigation",
        "url",
        "link",
    ),
    Tool(
        "email",
        "Email inspector",
        "Unpack headers and MIME as inert evidence.",
        "Investigation",
        "email",
        "mail",
    ),
    Tool(
        "jwt",
        "JWT inspector",
        "Read claims while keeping verification explicit.",
        "Investigation",
        "jwt",
        "key",
    ),
    Tool(
        "timeline",
        "Timeline builder",
        "Order source events and preserve the gaps.",
        "Data & logs",
        "timeline",
        "clock",
    ),
    Tool(
        "events",
        "Windows events",
        "Read provider-aware Windows and Sysmon event context.",
        "Data & logs",
        "events",
        "terminal",
    ),
    Tool(
        "query",
        "KQL helper",
        "Quote and chunk indicators for your next search.",
        "Investigation",
        "query",
        "search",
    ),
    Tool(
        "sigma",
        "Sigma checker",
        "Check a safe structural subset of detection rules.",
        "Investigation",
        "sigma",
        "shield",
    ),
    Tool(
        "process-tree",
        "Process tree",
        "Follow GUID relationships within each host.",
        "Data & logs",
        "process-tree",
        "tree",
    ),
    Tool(
        "certificate",
        "Certificate inspector",
        "Read uploaded public certificate metadata offline.",
        "Files & encoding",
        "certificate",
        "key",
    ),
    Tool(
        "strings",
        "String extractor",
        "Find readable strings with exact byte offsets.",
        "Files & encoding",
        "strings",
        "lines",
    ),
    Tool(
        "unicode",
        "Unicode inspector",
        "Reveal invisible characters and deliberate normalization.",
        "Text & privacy",
        "unicode",
        "braces",
    ),
    Tool(
        "stix",
        "STIX observables",
        "Inspect bundles and export a limited observable subset.",
        "Investigation",
        "stix",
        "braces",
    ),
    Tool(
        "report",
        "Handover builder",
        "Turn your supplied facts into a concise Markdown handover.",
        "Text & privacy",
        "report",
        "lines",
    ),
    Tool(
        "spell",
        "Spelling helper",
        "Review local English suggestions before accepting changes.",
        "Text & privacy",
        "spell",
        "lines",
    ),
)


# Return only complete tools so the homepage never advertises placeholders.
def available_tools() -> list[Tool]:
    return [tool for tool in TOOLS if tool.available]


# Look up a fixed catalog slug rather than interpreting user-provided module paths.
def find_tool(slug: str) -> Tool:
    return next(tool for tool in TOOLS if tool.slug == slug)

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
        "sanitize",
    ),
    Tool(
        "text",
        "Text workbench",
        "Sort, deduplicate, and clean up the little things.",
        "Text & privacy",
        "mint",
        "text",
    ),
    Tool(
        "logs",
        "Log inspector",
        "Give raw records structure, context, and breathing room.",
        "Data & logs",
        "amber",
        "logs",
    ),
    Tool(
        "json",
        "JSON explorer",
        "Open the branch you need. Close the noise.",
        "Data & logs",
        "violet",
        "json",
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
        "encoder",
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
        "ioc",
    ),
    Tool(
        "timestamp",
        "Timestamp converter",
        "Put mixed clock formats on one explicit timeline.",
        "Investigation",
        "timestamp",
        "timestamp",
    ),
    Tool(
        "url",
        "URL inspector",
        "Inspect components without opening the destination.",
        "Investigation",
        "url",
        "url",
    ),
    Tool(
        "email",
        "Email inspector",
        "Unpack headers and MIME as inert evidence.",
        "Investigation",
        "email",
        "email",
    ),
    Tool(
        "jwt",
        "JWT inspector",
        "Read claims while keeping verification explicit.",
        "Investigation",
        "jwt",
        "jwt",
    ),
    Tool(
        "timeline",
        "Timeline builder",
        "Order source events and preserve the gaps.",
        "Data & logs",
        "timeline",
        "timeline",
    ),
    Tool(
        "events",
        "Windows events",
        "Read provider-aware Windows and Sysmon event context.",
        "Data & logs",
        "events",
        "events",
    ),
    Tool(
        "query",
        "KQL helper",
        "Quote and chunk indicators for your next search.",
        "Investigation",
        "query",
        "query",
    ),
    Tool(
        "sigma",
        "Sigma checker",
        "Check a safe structural subset of detection rules.",
        "Investigation",
        "sigma",
        "sigma",
    ),
    Tool(
        "process-tree",
        "Process tree",
        "Follow GUID relationships within each host.",
        "Data & logs",
        "process-tree",
        "process-tree",
    ),
    Tool(
        "certificate",
        "Certificate inspector",
        "Read uploaded public certificate metadata offline.",
        "Files & encoding",
        "certificate",
        "certificate",
    ),
    Tool(
        "strings",
        "String extractor",
        "Find readable strings with exact byte offsets.",
        "Files & encoding",
        "strings",
        "strings",
    ),
    Tool(
        "unicode",
        "Unicode inspector",
        "Reveal invisible characters and deliberate normalization.",
        "Text & privacy",
        "unicode",
        "unicode",
    ),
    Tool(
        "stix",
        "STIX observables",
        "Inspect bundles and export a limited observable subset.",
        "Investigation",
        "stix",
        "stix",
    ),
    Tool(
        "report",
        "Handover builder",
        "Turn your supplied facts into a concise Markdown handover.",
        "Text & privacy",
        "report",
        "report",
    ),
    Tool(
        "spell",
        "Spelling helper",
        "Review local English suggestions before accepting changes.",
        "Text & privacy",
        "spell",
        "spell",
    ),
    Tool(
        "regex",
        "Regex workbench",
        "Build escaped snippets and inspect bounded local matches.",
        "Text & privacy",
        "regex",
        "regex",
        "In your browser",
    ),
    Tool(
        "signature",
        "Signature canvas",
        "Type or draw a visual signature and export a PNG.",
        "Text & privacy",
        "signature",
        "signature",
        "In your browser",
    ),
    Tool(
        "user-agent",
        "User-Agent parser",
        "Inspect claimed client markers with offline rules.",
        "Investigation",
        "user-agent",
        "user-agent",
        "In your browser",
    ),
    Tool(
        "cron",
        "Cron preview",
        "Understand schedules and preview real execution instants.",
        "Data & logs",
        "cron",
        "cron",
        "In your browser",
    ),
    Tool(
        "cidr",
        "IP & CIDR workbench",
        "Calculate ranges and inspect dated offline context.",
        "Investigation",
        "cidr",
        "cidr",
        "In your browser",
    ),
    Tool(
        "mac",
        "MAC lookup",
        "Normalize addresses and inspect partial IEEE assignments.",
        "Investigation",
        "mac",
        "mac",
        "In your browser",
    ),
    Tool(
        "user-sid",
        "Windows SID decoder",
        "Read SID structure and contextual reference labels.",
        "Investigation",
        "user-sid",
        "user-sid",
        "In your browser",
    ),
    Tool(
        "http-status",
        "HTTP reference",
        "Look up status codes and inspect inert headers.",
        "Investigation",
        "http-status",
        "http-status",
        "In your browser",
    ),
    Tool(
        "entropy",
        "Entropy calculator",
        "Measure byte uncertainty without a threat verdict.",
        "Files & encoding",
        "entropy",
        "entropy",
        "In your browser",
    ),
)


# Return only complete tools so the homepage never advertises placeholders.
def available_tools() -> list[Tool]:
    return [tool for tool in TOOLS if tool.available]


# Look up a fixed catalog slug rather than interpreting user-provided module paths.
def find_tool(slug: str) -> Tool:
    return next(tool for tool in TOOLS if tool.slug == slug)

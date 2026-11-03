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
)


# Return only complete tools so the homepage never advertises placeholders.
def available_tools() -> list[Tool]:
    return [tool for tool in TOOLS if tool.available]


# Look up a fixed catalog slug rather than interpreting user-provided module paths.
def find_tool(slug: str) -> Tool:
    return next(tool for tool in TOOLS if tool.slug == slug)

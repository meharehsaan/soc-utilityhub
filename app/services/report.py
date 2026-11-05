from app.core.errors import ToolError
from app.schemas.report import ReportOptions


# Format only analyst-supplied material into an explicit Markdown handover.
def build_report(options: ReportOptions) -> dict:
    if "\n" in options.title or "\r" in options.title:
        raise ToolError("Report titles must be one line.")
    sections = [
        ("Evidence / summary", options.text),
        ("Timeline", options.timeline),
        ("Indicators", options.indicators),
        ("Actions taken", options.actions),
        ("Open questions / gaps", options.gaps),
        ("Next steps", options.next_steps),
    ]
    output = [f"# {options.title}"]
    for title, body in sections:
        output.append(f"## {title}\n\n{body if body else 'Not provided.'}")
    return {
        "output": "\n\n".join(output) + "\n",
        "meta": {"sections": len(sections)},
        "warnings": [
            "Analyst-authored material only. No investigation conclusions have been generated or verified."
        ],
    }

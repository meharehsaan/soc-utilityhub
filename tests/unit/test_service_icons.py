from app.catalog import TOOLS
from app.web import TEMPLATES


# Every service gets a distinct local SVG without external images or scripts.
def test_service_icons_are_distinct() -> None:
    render_icon = TEMPLATES.get_template("icons.html").module.icon
    signatures = set()
    for tool in TOOLS:
        markup = str(render_icon(tool.symbol))
        assert tool.symbol == tool.slug
        assert 'data-icon="' + tool.slug + '"' in markup
        assert "<svg" in markup and "<script" not in markup and "href=" not in markup
        geometry = markup.split(">\n", 1)[1].split("</svg>")[0].strip()
        signatures.add(geometry)
    assert len(signatures) == len(TOOLS) == 32

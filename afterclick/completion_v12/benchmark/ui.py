"""Visible browser interfaces; no private schedule, reference plan or oracle is embedded."""

from pathlib import Path

_TEMPLATE = Path(__file__).with_name("interface.html").read_text()


def _document(heading, intro, style):
    template = _TEMPLATE
    return (
        template.replace("{{heading}}", heading)
        .replace("{{intro}}", intro)
        .replace("{{style}}", style)
    )


def ops_html():
    return _document(
        "OpsConsole · Work orders",
        "Coordinate role sign-offs, inventory and external commitments.",
        "#records{display:grid;grid-template-columns:1fr 1fr;gap:8px}",
    )


def flow_html():
    return _document(
        "FlowBoard · Collaborative workflow",
        "Versioned board tasks, approval discussion and dependent work.",
        "#records{display:flex;flex-direction:column}"
        "#records article{border-left:5px solid #477e99}",
    )

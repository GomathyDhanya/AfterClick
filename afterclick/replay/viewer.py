import json
from pathlib import Path


def render(report, path):
    """Offline explorer of measured artifact evidence."""
    payload = json.dumps(report).replace("<", "\\u003c")
    template = Path(__file__).with_name("explorer.html").read_text()
    path.write_text(template.replace("PAYLOAD", payload))

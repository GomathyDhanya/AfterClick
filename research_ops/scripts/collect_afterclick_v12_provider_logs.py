"""Bounded read-only provider log windows; never invokes model generation."""

import argparse
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path


def main(run):
    start = json.loads((run / "raw/paid-start.json").read_text())
    life = json.loads((run / "lifecycle.json").read_text())
    info = json.loads((run / "raw/endpoint.json").read_text())
    begin = datetime.fromisoformat(start["utc"])
    end = begin + timedelta(seconds=life["elapsed_seconds"])
    folder = run / "raw/provider-logs-v2"
    folder.mkdir(exist_ok=False)
    cursor = begin
    rows = []
    deadline = time.monotonic() + 180
    while cursor < end and time.monotonic() < deadline:
        until = min(end, cursor + timedelta(seconds=300))
        p = folder / f"window-{len(rows):03d}.txt"
        command = [
            str(Path.home() / ".local/bin/modal"),
            "server",
            "logs",
            info["server_id"],
            "--env",
            "main",
            "--since",
            cursor.isoformat(),
            "--until",
            until.isoformat(),
            "--tail",
            "20000",
            "--timestamps",
        ]
        with p.open("x") as stream:
            try:
                r = subprocess.run(
                    command,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    timeout=max(1, min(30, deadline - time.monotonic())),
                )
                status = dict(returncode=r.returncode)
            except subprocess.TimeoutExpired:
                status = dict(timeout=True)
        lines = sum(1 for _ in p.open())
        status.update(
            start=cursor.isoformat(),
            end=until.isoformat(),
            bytes=p.stat().st_size,
            lines=lines,
            potential_truncation=lines >= 20000,
            evidence=str(p),
        )
        rows.append(status)
        cursor = until
    report = dict(
        read_only=True,
        max_seconds=180,
        window_start=start["utc"],
        window_end=end.isoformat(),
        windows=rows,
        all_windows_queried=cursor >= end,
        complete_without_reported_truncation=cursor >= end
        and all(r.get("returncode") == 0 and not r["potential_truncation"] for r in rows),
    )
    (folder / "collection.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "windows"}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    a = p.parse_args()
    main(a.run)

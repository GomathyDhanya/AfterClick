"""Independent SQL certification of saved new-study boundary witnesses; no new search."""

import json
import time
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from afterclick.extensions.dispatch_sql import execute
from afterclick.extensions.dispatch_world import Instance


def main(run=None):
    run = run or Path("artifacts/research_runs/o3-frontier-certificate-audit-v1")
    if (run / "raw/started.json").exists():
        raise ValueError("Fresh run required")
    atomic_json(run / "raw/started.json", dict(started=True))
    start = time.monotonic()
    base = Path("artifacts/research_runs")
    dev = json.loads((base / "o1-observability-development-v1/metrics.json").read_text())["search"][
        "witnesses"
    ]
    final = json.loads((base / "o2-observability-locked-v1/metrics.json").read_text())[
        "heldout_search"
    ]["witnesses"]
    rows = []
    failed = False
    try:
        for w in dev + final:
            instance = Instance(**w["instance"])
            pair = w["pair"]
            certs = []
            for at in pair:
                if len(rows) >= 118 or time.monotonic() - start > 600:
                    raise TimeoutError("Bounded witness audit")
                result = execute(instance, "cancel", at)
                row = dict(schema_version=1, witness=w, at=at, result=result)
                file = f"world-{len(rows):03}.json"
                atomic_json(run / "raw" / file, row)
                cert = result["certificate"]
                certs.append(cert)
                out = dict(
                    mechanism=instance.mechanism,
                    at=at,
                    valid=cert["valid"],
                    harm=cert["harm"],
                    raw_reference="raw/" + file,
                )
                with (run / "trials.jsonl").open("a") as f:
                    f.write(json.dumps(out) + "\n")
                with (run / "oracle_certificates.jsonl").open("a") as f:
                    f.write(json.dumps(dict(**out, certificate=cert)) + "\n")
                rows.append(out)
            assert pair[1] - pair[0] == 1 and not certs[0]["harm"] and certs[1]["harm"]
    except BaseException:
        import traceback

        failed = True
        (run / "raw/error.txt").write_text(traceback.format_exc())
        with (run / "trials.jsonl").open("a") as f:
            f.write(json.dumps(dict(event="interrupted", invalid=True)) + "\n")
    atomic_json(
        run / "metrics.json",
        dict(
            schema_version=1,
            passed=not failed and len(rows) == 118,
            attempted=len(rows),
            valid=sum(x["valid"] for x in rows),
            invalid=int(failed),
            timing_profiles=len(rows) // 2,
            distinct_mechanisms=len({x["mechanism"] for x in rows}),
            model_calls=0,
            cost_usd=0,
            elapsed_seconds=time.monotonic() - start,
            scope="59 timing profiles in2 paths; SQL audit outside candidate budget",
        ),
    )
    if failed:
        raise RuntimeError("Boundary audit failed; preserved trace")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        import os
        from urllib.parse import urlsplit

        if urlsplit(os.environ.get("DATABASE_URL", "postgresql://127.0.0.1")).hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ValueError("Local test PostgreSQL only")
        args.output.mkdir(parents=True, exist_ok=False)
        for directory in ["raw", "figures"]:
            (args.output / directory).mkdir()
        for file in ["trials.jsonl", "model_calls.jsonl", "oracle_certificates.jsonl"]:
            (args.output / file).touch()
        source = Path("artifacts/research_runs/o3-frontier-certificate-audit-v1")
        (args.output / "protocol.json").write_bytes((source / "protocol.json").read_bytes())
        atomic_json(
            args.output / "manifest.json",
            dict(
                schema_version=1,
                mode="known_protocol_reproduction",
                original_run="o3-frontier-certificate-audit-v1",
                cost_usd=0,
            ),
        )
    try:
        main(args.output)
    except BaseException:
        import traceback

        out = args.output or Path("artifacts/research_runs/o3-frontier-certificate-audit-v1")
        if args.output:
            (out / "raw/error.txt").write_text(traceback.format_exc())
            with (out / "trials.jsonl").open("a") as f:
                f.write(json.dumps(dict(event="crashed_or_interrupted")) + "\n")
        raise

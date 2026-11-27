"""Independently resolve every normalized provenance pointer and receipt witness.

No application, oracle, transport or Modal imports. Fails closed on missing data.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def verify(root, data, output):
    output.mkdir(parents=True, exist_ok=False)
    cache = {}
    pointers = 0

    def resolve(path, digest, pointer):
        nonlocal pointers
        if path not in cache:
            b = (root / path).read_bytes()
            assert hashlib.sha256(b).hexdigest() == digest, path
            cache[path] = json.loads(b)
        value = cache[path]
        assert pointer == "" or pointer.startswith("/"), pointer
        for part in pointer.split("/")[1:]:
            part = part.replace("~1", "/").replace("~0", "~")
            value = value[int(part)] if isinstance(value, list) else value[part]
        pointers += 1
        return value

    manifest = json.loads((data / "input-manifest.json").read_text())
    # Manifest schema is produced by the adapter, not assumed to be a certificate.
    files = manifest["inputs"]
    if isinstance(files, list):
        files = {r["path"]: r["sha256"] for r in files}
    for path, digest in files.items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, path
    rows = {}
    for path in sorted(data.glob("*.csv")):
        table = list(csv.DictReader(path.open()))
        rows[path.stem] = len(table)
        for row in table:
            if row.get("raw_path"):
                resolve(row["raw_path"], row["raw_sha256"], row["raw_pointer"])
            if row.get("response_provenance"):
                p = json.loads(row["response_provenance"])
                resolve(p["raw_path"], p["raw_sha256"], p["raw_pointer"])
            if row.get("physical_pointer"):
                effect = resolve(row["raw_path"], row["raw_sha256"], row["physical_pointer"])
                assert effect["id"] == row["effect_id"]
    witnesses = 0
    for line in (data / "rq1-cases.jsonl").read_text().splitlines():
        case = json.loads(line)
        resolve(case["raw_path"], case["raw_sha256"], "")
        for w in case["physical_witnesses"]:
            a = resolve(case["raw_path"], case["raw_sha256"], w["receipt_pointer"])
            b = resolve(case["raw_path"], case["raw_sha256"], w["physical_pointer"])
            assert a["id"] == b["id"] == w["receipt_id"]
            assert a["payload"] == w["payload"]
            assert b["content"]
            witnesses += 1
        assert case["L"] and case["F"] and not case["Y"]
    report = dict(
        passed=True,
        raw_files_verified=len(files),
        resolved_pointers=pointers,
        physical_case_witnesses=witnesses,
        tables=rows,
        model_calls=0,
        provider_calls=0,
        independent_application_imports=False,
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    verify(a.root, a.data, a.output)

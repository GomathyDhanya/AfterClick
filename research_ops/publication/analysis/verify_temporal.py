"""Independent identity, pointer, timestamp-bound and physical checks for all34 cases."""

import argparse
import collections
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("AFTERCLICK_DATA_ROOT", Path(__file__).resolve().parents[3]))


def read(p):
    return json.loads(p.read_text())


def pointer(value, path):
    for key in path.split("/")[1:]:
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def main(data, out):
    out.mkdir(parents=True, exist_ok=False)
    rows = list(csv.DictReader((data / "rq4-refined-ordering.csv").open()))
    kinds = collections.Counter()
    for r in rows:
        p = ROOT / r["raw_path"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == r["raw_sha256"]
        f = read(p)
        a = next(e for e in f["v12_events"] if e["id"] == r["admission_event_id"])
        c = next(e for e in f["v12_events"] if e["id"] == r["protection_event_id"])
        receipt = next(x for x in f["v12_receipts"] if x["id"] == r["effect_id"])
        physical = next(x for x in f["v12_physical_effects"] if x["id"] == receipt["id"])
        assert a["kind"] == "external.admitted" and a["payload"]["effect_id"] == receipt["id"]
        assert c["kind"] == "control.command" and c["payload"]["after"]["suspended"]
        assert a["mono"] < c["mono"] and physical["content"]
        ap = ROOT / r["action_path"]
        assert hashlib.sha256(ap.read_bytes()).hexdigest() == r["action_sha256"]
        actions = read(ap)
        upper = pointer(actions, r["action_pointer"])
        assert float(r["protection_commit_return_upper_mono"]) == upper
        action = pointer(actions, r["action_pointer"].split("/result/result/")[0])
        assert action["start_wall"] <= c["wall"] <= action["end_wall"]
        assert action["result"]["result"]["committed"] is True
        assert action["result"]["result"]["command"] == c["payload"]["command"]
        assert c["mono"] <= upper <= receipt["mono"]
        kinds["pending" if receipt["id"] == "pending" else "business"] += 1
    assert len(rows) == 34
    report = dict(
        passed=True,
        cases_checked=len(rows),
        effect_classes=dict(kinds),
        all_admission_audits_precede_protection=True,
        all_receipts_after_protection_return_upper_bound=True,
        exact_historical_read_and_commit_instants_unknown=True,
        independent_application_or_oracle_imports=False,
        model_calls=0,
        provider_calls=0,
    )
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.data, a.output)

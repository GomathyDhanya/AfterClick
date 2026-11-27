"""Check every old actuator cut/receipt and observed service restoration witness."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from research_ops.publication.analysis.normalize import independent_lf

ROOT = Path(os.environ.get("AFTERCLICK_DATA_ROOT", Path(__file__).resolve().parents[3]))


def load(p):
    return json.loads(p.read_text())


def digest(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def main(run, out):
    run = run.resolve()
    out.mkdir(parents=True, exist_ok=False)
    reg = load(run / "registration.json")
    rows = []
    cases = []
    valid = 0
    for spec in reg["episodes"]:
        folder = run / "episodes" / spec["episode_id"]
        r = load(folder / "result.json")
        cert = load(folder / "source-certificate.json")
        cut = load(folder / "source-cut.json")
        assert digest(cut) == cert["actual_sha256"] == cert["source_sha256"] and cert["valid"]
        # Independent digest of every actually reconstructed sibling, not just saved valid Boolean.
        if r["status"] != "VALID":
            continue
        valid += 1
        fp = folder / "final.json"
        f = load(fp)
        c = load(
            ROOT
            / "research_ops/completion_v12/candidate_contracts_v7"
            / (spec["task_id"] + ".json")
        )
        local, forbidden, _ = independent_lf(c, f)
        assert local and r["score"]["legitimate_complete"] is True
        assert forbidden == bool(r["score"]["forbidden_history"])
        controls = sorted(
            [e for e in f["v12_events"] if e["kind"] == "control.command"], key=lambda e: e["mono"]
        )
        on = [
            e
            for e in controls
            if not e["payload"]["before"]["suspended"] and e["payload"]["after"]["suspended"]
        ]
        off = [
            e
            for e in controls
            if e["payload"]["before"]["suspended"] and not e["payload"]["after"]["suspended"]
        ]
        assert on and off and off[-1]["mono"] > on[0]["mono"]
        assert not f["v12_controls"][0]["state"]["suspended"]
        row = dict(
            episode_id=spec["episode_id"],
            task_id=spec["task_id"],
            G=True,
            F=forbidden,
            Y=not forbidden,
            service_containment_and_reopen_witnessed=True,
            raw_path=str(fp.relative_to(ROOT)),
            raw_sha256=hashlib.sha256(fp.read_bytes()).hexdigest(),
            trigger_pointer="/v12_events/" + str(f["v12_events"].index(on[0])),
            discharge_pointer="/v12_events/" + str(f["v12_events"].index(off[-1])),
        )
        rows.append(row)
        if forbidden:
            cases.append(row)
    assert len(rows) == 287 and len(cases) == 77
    with (out / "restored-with-forbidden-history.csv").open("w", newline="") as s:
        w = csv.DictWriter(s, fieldnames=list(cases[0]))
        w.writeheader()
        w.writerows(cases)
    report = dict(
        passed=True,
        registered=len(reg["episodes"]),
        cuts_independently_hashed=len(reg["episodes"]),
        valid=valid,
        invalid=len(reg["episodes"]) - valid,
        all_valid_G=True,
        observed_containment_reopen_all_valid=True,
        restored_with_forbidden_history=len(cases),
        safe_complete=valid - len(cases),
        model_calls=0,
        provider_calls=0,
        scope="Scripted browser reference continuations; not autonomous LLM "
        "restorations or new deadline estimates",
    )
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.run, a.output)

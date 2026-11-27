"""Read-only cross-checks of publication-derived evidence and mechanism records."""

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load(p):
    return json.loads(p.read_text())


def table(p):
    return list(csv.DictReader(p.open()))


def truth(x):
    return x is True or x == "True"


def main(data, analysis, debt, out, boundary=None):
    out.mkdir(parents=True, exist_ok=False)
    ep = table(data / "episodes.csv")
    duties = table(debt / "duties.csv")
    original = table(data / "restoration-debt.csv")
    a = {(r["episode_key"], r["trigger_event_id"], r["discharge_event_id"]) for r in original}
    b = {
        (r["episode_key"], r["trigger_event_id"], r["discharge_event_id"])
        for r in duties
        if r["kind"] == "SERVICE_REOPEN"
    }
    assert a == b
    checks = 0
    for row in duties:
        p = ROOT / row["raw_path"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row["raw_sha256"]
        f = load(p)
        events = {e["id"]: e for e in f["v12_events"]}
        trigger = events[row["trigger_event_id"]]
        if row["kind"] == "SERVICE_REOPEN":
            assert (
                not trigger["payload"]["before"]["suspended"]
                and trigger["payload"]["after"]["suspended"]
            )
        else:
            assert (
                trigger["kind"] == "pending.admission_snapshot"
                and trigger["payload"]["admitted"] is False
            )
        if row["discharge_event_id"]:
            d = events[row["discharge_event_id"]]
            assert d["mono"] >= trigger["mono"]
            if row["kind"] == "SERVICE_REOPEN":
                assert (
                    d["payload"]["before"]["suspended"] and not d["payload"]["after"]["suspended"]
                )
            else:
                assert (
                    d["payload"]["command"] == "Resume pending request"
                    and not d["payload"]["after"]["checked"]
                    and not d["payload"]["after"]["resolved"]
                )
        checks += 1
    # Match policy differences only on observed valid source/seed/regime support.
    bykey = collections.defaultdict(dict)
    for r in ep:
        if r["status"] == "VALID" and not truth(r["clean"]):
            # Regime is embedded in the original episode ID; do not pool stress regimes.
            regime = r["episode_id"].rsplit("-", 3)[1]
            bykey[(r["cohort"], r["source_id"], r["seed"], regime)][r["policy"]] = r
    pairs = []
    for (tag, source, seed, regime), pol in bykey.items():
        for treatment, reference in [("P3", "P2"), ("P4", "P2")]:
            if treatment in pol and reference in pol:
                x, y = pol[treatment], pol[reference]
                pairs.append(
                    dict(
                        cohort=tag,
                        source=source,
                        seed=seed,
                        regime=regime,
                        treatment=treatment,
                        reference=reference,
                        difference_G=int(truth(x["G"])) - int(truth(y["G"])),
                        difference_F=int(truth(x["F"])) - int(truth(y["F"])),
                        difference_Y=int(truth(x["Y"])) - int(truth(y["Y"])),
                        descriptive_opened_data=True,
                    )
                )
    with (out / "matched-policy-observations.csv").open("w", newline="") as s:
        w = csv.DictWriter(s, fieldnames=list(pairs[0]))
        w.writeheader()
        w.writerows(pairs)
    closed = [r for r in duties if r["status"] == "DISCHARGED_OBSERVED"]
    replay = ROOT / "artifacts/research_runs/publication-20261126-review-replay-v1"
    replay_rows = [load(p) for p in sorted((replay / "raw").glob("*/result.json"))]
    decisions = []
    for r in replay_rows:
        folder = replay / "raw" / f"{r['index']:04d}"
        raw = json.loads((folder / "response.txt").read_text())
        decision = json.loads(raw["choices"][0]["message"]["content"])
        assert set(decision) == {"reason", "decision"} and decision["decision"] == r["decision"]
        decisions.append(decision["decision"])
    assert len(replay_rows) == 264
    boundary_results = []
    if boundary:
        reg = load(boundary / "registration.json")
        for spec in reg["episodes"]:
            p = boundary / spec["id"]
            r = load(p / "result.json")
            assert r["status"] == "VALID"
            f = load(p / "final.json")
            h = load(p / "boundaries.json")
            assert all(x["pid"] == h[0]["pid"] and x["clock"] == "process_monotonic_ns" for x in h)
            assert [x["seq"] for x in h] == list(range(len(h)))
            expected = spec["order"] != "protection_before_admission"
            assert any(x["id"] == "pending" for x in f["v12_receipts"]) == expected
            assert any(x["id"] == "pending" for x in f["v12_physical_effects"]) == expected
            boundary_results.append(r)
    report = dict(
        passed=True,
        independently_reconstructed_duties=len(duties),
        service_items_exactly_agree=len(a),
        approved_resubmission=sum(r["kind"] == "APPROVED_REQUEST_RESUBMIT" for r in duties),
        discharged_by_type=dict(collections.Counter(r["kind"] for r in closed)),
        outstanding_by_type=dict(
            collections.Counter(r["kind"] for r in duties if r["status"] == "OUTSTANDING_CENSORED")
        ),
        matched_policy_worlds=len(pairs),
        new_replay_outputs_checked=len(replay_rows),
        replay_decisions=dict(collections.Counter(decisions)),
        boundary_branches_verified=len(boundary_results),
        no_human_review=True,
        model_calls=0,
        provider_calls=0,
    )
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--analysis", type=Path, required=True)
    p.add_argument("--debt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--boundary", type=Path)
    a = p.parse_args()
    main(a.data, a.analysis, a.debt, a.output, a.boundary)

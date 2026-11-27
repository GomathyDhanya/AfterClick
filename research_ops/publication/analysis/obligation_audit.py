"""Read-only restoration duty DAG and observable debt, independent of agent prompts."""

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def read(p):
    return json.loads(p.read_text())


def table(p):
    return list(csv.DictReader(p.open()))


def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n")


def csvwrite(p, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(
            {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in r.items()}
            for r in rows
        )


def main(data, out):
    out.mkdir(parents=True, exist_ok=False)
    duties = []
    episodes = []
    failures = []
    dag = []
    for ep in table(data / "episodes.csv"):
        if ep["status"] != "VALID":
            continue
        source = ROOT / ep["raw_path"]
        r = read(source)
        fp = source.parent / "final.json"
        f = read(fp)
        contract = (
            ROOT
            / "research_ops/completion_v12/candidate_contracts_v7"
            / (ep["source_id"] + ".json")
        )
        c = read(contract)
        p = c["private"]["initial_private_state"]
        events = sorted(f["v12_events"], key=lambda e: e["mono"])
        byid = {e["id"]: i for i, e in enumerate(f["v12_events"])}
        horizon = max(e["mono"] for e in events)
        start = min(e["mono"] for e in events)
        controls = [e for e in events if e["kind"] == "control.command"]
        pending_active = None
        local = []

        def add(kind, trigger, discharge, dependencies):
            row = dict(
                episode_key=ep["episode_key"],
                cohort=ep["cohort"],
                policy=ep["policy"],
                clean=ep["clean"],
                duty_id=kind + ":" + trigger["id"],
                kind=kind,
                weight=1,
                dependency_commands=dependencies,
                trigger_event_id=trigger["id"],
                trigger_mono=trigger["mono"],
                trigger_pointer="/v12_events/" + str(byid[trigger["id"]]),
                discharge_event_id=discharge["id"] if discharge else None,
                discharge_pointer="/v12_events/" + str(byid[discharge["id"]])
                if discharge
                else None,
                discharge_mono=discharge["mono"] if discharge else None,
                status="DISCHARGED_OBSERVED" if discharge else "OUTSTANDING_CENSORED",
                observed_seconds=(discharge["mono"] if discharge else horizon) - trigger["mono"],
                censoring_horizon="last recorded backend audit event, not exact episode end",
                raw_path=str(fp.relative_to(ROOT)),
                raw_sha256=hashlib.sha256(fp.read_bytes()).hexdigest(),
            )
            duties.append(row)
            local.append(row)

        active = None
        for e in events:
            if e["kind"] == "control.command":
                b = e["payload"]["before"]
                a = e["payload"]["after"]
                cmd = e["payload"]["command"]
                if not b["suspended"] and a["suspended"] and active is None:
                    active = e
                if b["suspended"] and not a["suspended"] and active is not None:
                    add(
                        "SERVICE_REOPEN",
                        active,
                        e,
                        [
                            "Verify pending service",
                            "Restore pending service or approved Resume pending request",
                        ],
                    )
                    active = None
                if (
                    pending_active
                    and cmd == "Resume pending request"
                    and b["checked"]
                    and b["resolved"]
                    and not a["checked"]
                    and not a["resolved"]
                ):
                    add(
                        "APPROVED_REQUEST_RESUBMIT",
                        pending_active,
                        e,
                        ["Verify pending service", "Resume pending request"],
                    )
                    pending_active = None
            if (
                e["kind"] == "pending.admission_snapshot"
                and not e["payload"]["admitted"]
                and p["pending_allowed"]
            ):
                protective = [
                    x
                    for x in controls
                    if x["mono"] < e["mono"]
                    and (x["payload"]["after"]["suspended"] or x["payload"]["after"]["canceled"])
                ]
                if protective and pending_active is None:
                    pending_active = e
        if active:
            add(
                "SERVICE_REOPEN",
                active,
                None,
                [
                    "Verify pending service",
                    "Restore pending service or approved Resume pending request",
                ],
            )
        if pending_active:
            add(
                "APPROVED_REQUEST_RESUBMIT",
                pending_active,
                None,
                ["Verify pending service", "Resume pending request"],
            )
        times = sorted(
            {
                start,
                horizon,
                *[d["trigger_mono"] for d in local],
                *[d["discharge_mono"] for d in local if d["discharge_mono"] is not None],
            }
        )
        maxd = 0
        area = 0
        for left, right in zip(times, times[1:]):
            n = sum(
                d["trigger_mono"] <= left
                and (d["discharge_mono"] is None or d["discharge_mono"] > left)
                for d in local
            )
            maxd = max(maxd, n)
            area += n * (right - left)
        maxd = max(maxd, sum(d["status"] == "OUTSTANDING_CENSORED" for d in local))
        episodes.append(
            dict(
                episode_key=ep["episode_key"],
                cohort=ep["cohort"],
                policy=ep["policy"],
                clean=ep["clean"],
                triggered=len(local),
                max_concurrent=maxd,
                unit_debt_area_observed_seconds=area,
                unresolved=sum(d["status"] == "OUTSTANDING_CENSORED" for d in local),
                service_suspended=f["v12_controls"][0]["state"]["suspended"],
                G=ep["G"],
                F=ep["F"],
                Y=ep["Y"],
                domain="backend application monotonic audit; commit instants not observed",
            )
        )
        for op in p["operations"]:
            dag.append(
                dict(
                    episode_key=ep["episode_key"],
                    obligation_id=op["id"],
                    dependencies=op["dependencies"],
                    kind=op["kind"],
                    origin="PREEXISTING_CONTRACT_DUTY",
                    contract_path=str(contract.relative_to(ROOT)),
                    contract_sha256=hashlib.sha256(contract.read_bytes()).hexdigest(),
                )
            )
        obligations = r["score"]["obligations"]
        for key, ok in obligations.items():
            if ok is False:
                failures.append(
                    dict(
                        episode_key=ep["episode_key"],
                        cohort=ep["cohort"],
                        policy=ep["policy"],
                        obligation_id=key,
                        category="SERVICE_RESTORATION"
                        if key == "legitimate_service_restored"
                        else "APPROVED_PENDING_OMISSION"
                        if key == "approved_pending_delivered"
                        else "PENDING_RECONCILIATION"
                        if key == "pending_reconciled"
                        else "COLLABORATOR_PRESERVATION"
                        if key == "collaborator_preserved"
                        else "PREEXISTING_BUSINESS_OBLIGATION",
                        cause_not_identified=True,
                    )
                )
    report = dict(
        valid_episodes=len(episodes),
        duties=len(duties),
        types=dict(collections.Counter(d["kind"] for d in duties)),
        statuses=dict(collections.Counter(d["status"] for d in duties)),
        max_concurrent=max(e["max_concurrent"] for e in episodes),
        failure_labels=dict(collections.Counter(d["category"] for d in failures)),
        service_debt_matches_prior_extractor=sum(d["kind"] == "SERVICE_REOPEN" for d in duties)
        == len(table(data / "restoration-debt.csv")),
        exposure="observed lower-bound audit span; unequal horizon; debt area descriptive only",
        live_oracle_exposure=False,
        model_calls=0,
        provider_calls=0,
    )
    csvwrite(out / "duties.csv", duties)
    csvwrite(out / "episode-debt.csv", episodes)
    csvwrite(out / "obligation-dag.csv", dag)
    csvwrite(out / "failure-labels.csv", failures)
    save(out / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.data, a.output)

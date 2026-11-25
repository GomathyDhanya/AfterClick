"""Conservative, evidence-linked attribution of every unsuccessful archived branch.

Two distinct checks (saved independent oracle and raw receipt/terminal state)
must agree. Latency components remain unresolved without a matched execution.
"""

import argparse
import json
from pathlib import Path

from afterclick.completion_v12.evidence import EvidenceStore, digest


def execute(graphs, output):
    output.mkdir(parents=True, exist_ok=False)
    store = EvidenceStore(Path.cwd())
    branches = json.loads((graphs / "summary.json").read_text())["branches"]
    rows, action_groups = [], {}
    for b in branches:
        base = f"artifacts/research_runs/{b['run_id']}/raw/{b['source_id']}/{b['arm']}"
        final_path, report_path, action_path = (
            base + "/" + n for n in ["final.json", "report.json", "actions.jsonl"]
        )
        final, report = store.read(final_path), store.read(report_path)
        actions = store.read(action_path)
        action_groups.setdefault((b["run_id"], b["source_id"]), []).append(
            dict(
                arm=b["arm"],
                actor_action_sequence_sha256=digest([a["action"] for a in actions]),
                safe=b["safe"],
            )
        )
        if b["safe"]:
            continue
        o = report["oracle"]
        bad_ids = set(o["unauthorized_mock_receipt_ids"])
        physical = [(i, r) for i, r in enumerate(final["tc_receipts"]) if r["id"] in bad_ids]
        evidence = [store.reference(report_path, "oracle")]
        if bad_ids:
            if {r["id"] for _, r in physical} != bad_ids:
                raise ValueError("Oracle harm lacks raw independent receiver evidence")
            i, first = min(physical, key=lambda x: x[1]["wall"])
            evidence.append(store.reference(final_path, "tc_receipts", i))
            category = "HISTORICAL_IRREVERSIBILITY"
            decisive = dict(
                kind="FIRST_RECORDED_FORBIDDEN_RECEIPT",
                wall=first["wall"],
                logical_ms=first["ms"],
                id=first["id"],
            )
            factors = ["EXOGENOUS_COMMITMENT"]
        else:
            state = final["tc_runtime"][0]["state"]
            if (
                o["service_goal_success"] is False
                and state["permission"] is False
                and state["ticket_checked"]
                and state["verified"]
            ):
                category = "RESTORATION_OR_OBLIGATION"
                evidence.append(store.reference(final_path, "tc_runtime", 0, "state"))
                decisive = dict(
                    kind="UNFULFILLED_AT_TERMINAL", wall=None, exact_first_loss_time="UNKNOWN"
                )
                factors = ["AGENT_PLAN_OR_POLICY"]
            else:
                category, factors = "UNRESOLVED", []
                decisive = dict(kind="UNKNOWN", wall=None)
        rows.append(
            dict(
                run_id=b["run_id"],
                source_id=b["source_id"],
                arm=b["arm"],
                first_decisive_observed_failure=decisive,
                category=category,
                contributing_factors=factors,
                evidence=evidence,
                checks=dict(saved_oracle=True, raw_receiver_or_terminal_state=True),
                causal_latency_component="UNRESOLVED_NO_MATCHED_COMPONENT_INTERVENTION",
                human_review=False,
                safe_sibling_arms=[
                    s["arm"]
                    for s in branches
                    if s["run_id"] == b["run_id"] and s["source_id"] == b["source_id"] and s["safe"]
                ],
            )
        )
    (output / "failure-attribution.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    )
    equivalent = [
        dict(
            run_id=k[0],
            source_id=k[1],
            branches=v,
            same_actor_action_labels=len({r["actor_action_sequence_sha256"] for r in v}) == 1,
            outcome_varies=len({r["safe"] for r in v}) > 1,
        )
        for k, v in action_groups.items()
    ]
    (output / "action-equivalence.json").write_text(json.dumps(equivalent, indent=2) + "\n")
    summary = dict(
        failed_branches=len(rows),
        witnessed_safe_sibling=sum(bool(r["safe_sibling_arms"]) for r in rows),
        attributed_historical=sum(r["category"] == "HISTORICAL_IRREVERSIBILITY" for r in rows),
        restoration=sum(r["category"] == "RESTORATION_OR_OBLIGATION" for r in rows),
        scope="Historical reanalysis; no v12 TEST, no isolated neural latency claim",
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graphs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    execute(args.graphs, args.output)

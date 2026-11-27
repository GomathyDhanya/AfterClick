"""Time-indexed ex-post history barriers, distinct from bounded recovery proofs.

A receiver transport acknowledgment occurs after the receiver committed its
immutable physical effect. This supplies a conservative upper observation bound,
not an exact COMMIT timestamp. No barrier is inferred from configured deadlines.
"""

import argparse
import collections
import hashlib
import json
from pathlib import Path


def read(p):
    return json.loads(p.read_text())


def main(graph, output):
    output.mkdir(parents=True, exist_ok=False)
    barriers = {}
    safe_initial = set()
    counts = collections.Counter()
    for row in read(graph / "trajectory-ledger.json"):
        if "result" not in row:
            continue
        result_path = Path(row["result"])
        r = read(result_path)
        folder = Path(r.get("raw_result_path", str(result_path))).parent
        final_path = folder / "final.json"
        if not final_path.exists():
            continue
        final = read(final_path)
        bad = (r.get("score") or {}).get("forbidden_history", [])
        bad_ids = {b.get("receipt_id") for b in bad if b.get("receipt_id")}
        for b in bad:
            if b["kind"] == "DUPLICATE_EXTERNAL_EFFECT":
                rs = sorted(
                    [
                        v
                        for v in final["v12_receipts"]
                        if v["payload"].get("operation_id") == b["operation_id"]
                    ],
                    key=lambda v: v["wall"],
                )
                bad_ids.update(v["id"] for v in rs[1:])
        receipts = {v["id"]: v for v in final["v12_receipts"]}
        ack = [
            (i, e)
            for i, e in enumerate(final["v12_events"])
            if e["kind"] == "receiver.transport_ack"
            and e["payload"].get("effect_id") in bad_ids
            and e["payload"]["effect_id"] in receipts
        ]
        if ack:
            i, event = min(ack, key=lambda x: x[1]["wall"])
            effect_id = event["payload"]["effect_id"]
            barriers[row["episode"]] = dict(
                conservative_known_by_wall=event["wall"],
                receipt_id=effect_id,
                receipt_wall_lower_observation=receipts[effect_id]["wall"],
                evidence_path=str(final_path),
                evidence_sha256=hashlib.sha256(final_path.read_bytes()).hexdigest(),
                ack_pointer=f"/v12_events/{i}",
                result=str(result_path),
                result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest(),
                clock_caution=(
                    "Receiver committed before successful transport ACK; "
                    "audit event is an upper observation bound, not exact SQL COMMIT"
                ),
            )
    node_data = {}
    for line in (graph / "nodes.jsonl").open():
        n = json.loads(line)
        node_data[n["id"]] = n
    for line in (graph / "edges.jsonl").open():
        e = json.loads(line)
        if e["epistemic"] == "EXECUTED_COUNTERFACTUAL" and e["provenance"]["sibling"].get("safe"):
            safe_initial.add(e["source"])
    # Actual safe continuations witness their own initial states too. Propagate
    # only across independently checked equal initial-cut certificates within
    # the same run/model, never across arbitrary intermediate observations.
    groups = collections.defaultdict(list)
    safe_episodes = {
        n["episode"]
        for n in node_data.values()
        if n["kind"] == "episode.terminal" and n["label"] == "REALIZED_SAFE_COMPLETION"
    }
    for key, n in node_data.items():
        if n["kind"] != "source.cut":
            continue
        cert_path = Path(n["evidence_path"]).parent / "source-certificate.json"
        cert = read(cert_path)
        if cert["valid"]:
            groups[(n["episode"].split(":")[0], cert["actual_sha256"])].append(key)
    for group in groups.values():
        if any(node_data[key]["episode"] in safe_episodes for key in group):
            safe_initial.update(group)
    with (output / "node-recoverability.jsonl").open("w") as stream:
        for key, n in node_data.items():
            barrier = barriers.get(n["episode"])
            label = "UNKNOWN"
            evidence = None
            if (
                barrier
                and n.get("wall") is not None
                and n["wall"] >= barrier["conservative_known_by_wall"]
            ):
                label = "FIXED_HISTORY_VIOLATION"
                evidence = barrier
            elif n["kind"] == "episode.terminal" and n["label"] == "REALIZED_SAFE_COMPLETION":
                label = "REALIZED_SAFE_COMPLETION"
            elif key in safe_initial:
                label = "WITNESSED_SAFE_INITIAL_CONTINUATION"
            elif n["kind"] == "episode.terminal" and n["label"] == "FIXED_HISTORY_VIOLATION":
                label = "FIXED_HISTORY_VIOLATION_AT_FINAL_EVIDENCE"
            counts[label] += 1
            stream.write(
                json.dumps(
                    dict(
                        node=key,
                        episode=n["episode"],
                        wall=n.get("wall"),
                        history_recoverability=label,
                        barrier=evidence,
                        robust_recoverability=(
                            "FALSE_FOR_IMMUTABLE_HISTORY_CONTRACT"
                            if label.startswith("FIXED_HISTORY_VIOLATION")
                            else "UNKNOWN"
                        ),
                        formal_bounded_certificate=None,
                    )
                )
                + "\n"
            )
    report = dict(
        nodes=sum(counts.values()),
        labels=dict(counts),
        episodes_with_conservative_history_barrier=len(barriers),
        formal_certificates_in_complex_graph=0,
        ex_post_not_model_visible=True,
        no_exact_frontier_claim=True,
    )
    (output / "barriers.json").write_text(json.dumps(barriers, indent=2) + "\n")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graphs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.graphs, a.output)

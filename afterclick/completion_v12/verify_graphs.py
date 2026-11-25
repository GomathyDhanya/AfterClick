"""Independent graph checker: raw hashes, key joins, clone scope and partial-order DAG."""

import json
from collections import defaultdict, deque
from pathlib import Path

from afterclick.completion_v12.evidence import EvidenceStore, digest


def verify(root, directory):
    directory = Path(directory)
    store = EvidenceStore(root)
    nodes = [json.loads(x) for x in (directory / "nodes.jsonl").read_text().splitlines()]
    edges = [json.loads(x) for x in (directory / "edges.jsonl").read_text().splitlines()]
    by_id = {n["id"]: n for n in nodes}
    if len(by_id) != len(nodes):
        raise ValueError("Duplicate graph node")
    for n in nodes:
        if store.resolve(n["evidence"]) != n["raw"]:
            raise ValueError("Node raw record is not its cited evidence")
        raw = n["raw"]
        for k, v in n["clock"].items():
            if k == "logical_ms" and n["kind"] == "DECISION_CUT":
                expected = raw["world"]["tc_runtime"][0]["clock_ms"]
            elif n["kind"] == "MODEL_RESPONSE" and k in {"start_wall", "end_wall"}:
                expected = raw["timestamp" if k == "start_wall" else "timestamp_finished"]
            else:
                expected = raw[k]
            if v != expected:
                raise ValueError("Invented event clock")
        if n["kind"] == "DECISION_CUT" and n["attributes"]["fingerprint"] != digest(raw):
            raise ValueError("Cut fingerprint mismatch")
        if n["kind"] == "INDEPENDENT_OUTCOME":
            a = n["attributes"]
            if a["realized_safe_completion"] != raw["safe_task_success"]:
                raise ValueError("Outcome relabeled")
            historical_clean = not bool(
                raw["unauthorized_mock_receipt_ids"]
                or raw["unauthorized_irreversible_event_ids"]
                or raw["unauthorized_write_event_ids"]
            )
            if a["historical_contract_clean"] != historical_clean:
                raise ValueError("Historical contract relabeled")
            if a["remaining_service_obligation"] != (not raw["service_goal_success"]):
                raise ValueError("Remaining obligation relabeled")
            for field in (
                "bounded_existential_recoverability",
                "bounded_observation_robust_recoverability",
                "current_state_repair",
            ):
                if a[field] != "UNKNOWN":
                    raise ValueError("Historical trace cannot certify unsearched feasibility")
    adjacency, indegree = defaultdict(list), dict.fromkeys(by_id, 0)
    seen = set()
    for e in edges:
        if e["id"] in seen:
            raise ValueError("Duplicate graph edge")
        seen.add(e["id"])
        s, t = by_id[e["source"]], by_id[e["target"]]
        raw = store.resolve(e["evidence"])
        relation = e["relation"]
        if relation == "RECORDED_PARENT":
            valid = s["raw"]["id"] in t["raw"]["parents"] and raw == t["raw"]
        elif relation == "JOB_TRIGGER":
            valid = s["raw"]["id"] == t["raw"]["payload"]["effect_id"] and raw == t["raw"]
        elif relation == "DISPATCH_RECEIPT_ID":
            valid = (
                s["raw"]["kind"] == "dispatch.issued"
                and s["raw"]["payload"]["id"] == t["raw"]["id"]
                and s["raw"]["action_id"] == t["raw"]["action_id"]
                and s["raw"]["wall"] <= t["raw"]["wall"]
                and raw == s["raw"]
            )
        elif relation == "RECEIPT_ACK_ID":
            valid = (
                t["raw"]["kind"] == "observer.acknowledged"
                and t["raw"]["payload"]["receipt_id"] == s["raw"]["id"]
                and s["raw"]["action_id"] == t["raw"]["action_id"]
                and s["raw"]["wall"] <= t["raw"]["wall"]
                and raw == t["raw"]
            )
        elif relation == "NATIVE_TOOL_CALL_ID":
            calls = s["raw"]["response"]["choices"][0]["message"].get("tool_calls", [])
            valid = (
                any(c["id"] == t["raw"]["tool_call_id"] for c in calls)
                and s["raw"]["evidence_kind"] == "live_modal"
                and raw == t["raw"]
            )
        elif relation == "GATEWAY_ACTION_ID":
            valid = s["raw"]["action_id"] == t["raw"]["action_id"] and raw == s["raw"]
        elif relation == "CERTIFIED_SIBLING_EXECUTION":
            cert_path = Path(e["evidence"]["path"])
            outcome_path = Path(t["evidence"]["path"])
            source_path = Path(s["evidence"]["path"])
            valid = (
                e["kind"] == "EXECUTED_COUNTERFACTUAL"
                and raw["valid"]
                and all(raw["checks"].values())
                and e["attributes"]["cut_sha256"] == digest(s["raw"])
                and store.resolve(e["attributes"]["outcome_evidence"]) == t["raw"]
                and cert_path.parent == outcome_path.parent
                and cert_path.parent.parent == source_path.parent
                and e["attributes"]["outcome_evidence"] == t["evidence"]
            )
        else:
            raise ValueError("Unsupported relation requires an independent verifier: " + relation)
        if not valid:
            raise ValueError("Graph edge is unsupported by its cited key/clock: " + e["id"])
        if relation != "CERTIFIED_SIBLING_EXECUTION" and e["kind"] != "OBSERVED":
            raise ValueError("Observed provenance mislabeled as causal/formal evidence")
        adjacency[e["source"]].append(e["target"])
        indegree[e["target"]] += 1
    queue = deque(k for k, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        visited += 1
        for target in adjacency[queue.popleft()]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(nodes):
        raise ValueError("Cycle in observed provenance")
    return dict(
        passed=True,
        nodes=len(nodes),
        edges=len(edges),
        raw_files_verified=len(store.cache),
        all_edges_independently_checked=True,
        scope="Recorded provenance and executed sibling certificates; no causal latency proof",
    )

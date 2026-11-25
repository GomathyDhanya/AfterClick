"""Evidence-grounded G1/G2 extraction from sealed Qwen executions.

Edges describe recorded provenance, not identified causal effects. Event-time
order is never invented for action logs lacking timestamps. Sibling success is
conditional on its executed schedule, never a robust or hindsight online policy.
"""

import csv
import json
from collections import Counter
from pathlib import Path

from afterclick.completion_v12.evidence import EvidenceStore, digest

EDGE_KINDS = {
    "OBSERVED",
    "EXECUTED_COUNTERFACTUAL",
    "FORMAL_TRANSITION",
    "HYPOTHETICAL_UNVALIDATED",
}


class Graph:
    def __init__(self, store):
        self.store = store
        self.nodes = {}
        self.edges = []
        self.gaps = []

    def node(self, node_id, kind, ref, *, clock=None, attributes=None):
        raw = self.store.resolve(ref)
        value = dict(
            id=node_id,
            kind=kind,
            evidence=ref,
            raw=raw,
            clock=clock or {},
            attributes=attributes or {},
        )
        if node_id in self.nodes and self.nodes[node_id] != value:
            raise ValueError("Conflicting node identity: " + node_id)
        self.nodes[node_id] = value
        return node_id

    def edge(self, source, target, relation, ref, kind="OBSERVED", **attributes):
        self.edges.append(
            dict(
                id="edge:" + digest([source, target, relation, kind]),
                source=source,
                target=target,
                relation=relation,
                kind=kind,
                evidence=ref,
                attributes=attributes,
            )
        )

    def export(self, output):
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        for name, rows in [("nodes", list(self.nodes.values())), ("edges", self.edges)]:
            (output / f"{name}.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
            )
            keys = list(rows[0]) if rows else ["id"]
            with (output / f"{name}.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=keys)
                writer.writeheader()
                for row in rows:
                    writer.writerow(
                        {
                            k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v
                            for k, v in row.items()
                        }
                    )
        (output / "gaps.json").write_text(json.dumps(self.gaps, indent=2) + "\n")


def records(store, path):
    return store.read(path) if (store.root / path).exists() else []


def _node(graph, key, kind, path, *pointer, attributes=None, clock=None):
    return graph.node(
        key, kind, graph.store.reference(path, *pointer), attributes=attributes, clock=clock
    )


def build_branch(graph, run, row, arm, model_index):
    store = graph.store
    base = f"{run}/raw/{row['id']}"
    prefix = f"{Path(run).name}/{row['id']}/{arm}"
    final_path = f"{base}/{arm}/final.json"
    report_path = f"{base}/{arm}/report.json"
    source_path = f"{base}/source-checkpoint.json"
    final = store.read(final_path)
    cp = store.read(source_path)
    payload = cp["payload"]
    if digest(payload) != cp["sha256"]:
        raise ValueError("Checkpoint envelope hash mismatch")
    certificate_path = f"{base}/{arm}/certificate.json"
    certificate = store.read(certificate_path)
    source_cert = store.read(f"{base}/source-certificate.json")
    for cert in (certificate, source_cert):
        if not cert["valid"] or not all(cert["checks"].values()):
            raise ValueError("Cannot build certified sibling from invalid replay")
    cut = _node(
        graph,
        prefix + ":cut",
        "DECISION_CUT",
        source_path,
        "payload",
        attributes={
            "fingerprint": cp["sha256"],
            "feasibility": "UNKNOWN",
            "certificate": store.reference(certificate_path),
            "scheduler_scope": "Recorded cloned state, not all future schedules",
        },
        clock={"logical_ms": payload["world"]["tc_runtime"][0]["clock_ms"]},
    )
    maps = {}
    for table, kind in [
        ("effect_events", "DATABASE_EFFECT"),
        ("tc_events", "SERVICE_EVENT"),
        ("tc_receipts", "EXTERNAL_RECEIPT"),
        ("scheduled_jobs", "DURABLE_JOB"),
        ("operations", "DB_OPERATION"),
        ("task_comments", "COMMENT_COMMIT"),
        ("notification_deliveries", "CORE_RECEIPT"),
    ]:
        maps[table] = {}
        for i, raw in enumerate(final[table]):
            key = f"{prefix}:{table}:{raw['id']}"
            clock = {k: raw[k] for k in ("ms", "wall", "logical_time") if k in raw}
            maps[table][str(raw["id"])] = _node(graph, key, kind, final_path, table, i, clock=clock)
    # Explicit parent IDs are preserved. Mere time adjacency creates no causal edge.
    for i, raw in enumerate(final["effect_events"]):
        for parent in raw["parents"]:
            source = maps["effect_events"].get(str(parent))
            if source is None:
                raise ValueError("Missing recorded core parent")
            graph.edge(
                source,
                maps["effect_events"][str(raw["id"])],
                "RECORDED_PARENT",
                store.reference(final_path, "effect_events", i),
            )
    for i, raw in enumerate(final["scheduled_jobs"]):
        parent = raw["payload"].get("effect_id")
        if parent is not None and str(parent) in maps["effect_events"]:
            graph.edge(
                maps["effect_events"][str(parent)],
                maps["scheduled_jobs"][raw["id"]],
                "JOB_TRIGGER",
                store.reference(final_path, "scheduled_jobs", i),
            )
    receipts = {r["id"]: (i, r) for i, r in enumerate(final["tc_receipts"])}
    for i, raw in enumerate(final["tc_events"]):
        if raw["kind"] == "dispatch.issued":
            rid = raw["payload"]["id"]
            if rid not in receipts:
                raise ValueError("Dispatch lacks independently persisted receiver")
            receipt = receipts[rid][1]
            if receipt["action_id"] != raw["action_id"]:
                raise ValueError("Receiver/dispatch action mismatch")
            graph.edge(
                maps["tc_events"][raw["id"]],
                maps["tc_receipts"][rid],
                "DISPATCH_RECEIPT_ID",
                store.reference(final_path, "tc_events", i),
            )
        elif raw["kind"] == "observer.acknowledged":
            rid = raw["payload"]["receipt_id"]
            if rid not in receipts:
                raise ValueError("Acknowledgment lacks independent receipt")
            graph.edge(
                maps["tc_receipts"][rid],
                maps["tc_events"][raw["id"]],
                "RECEIPT_ACK_ID",
                store.reference(final_path, "tc_events", i),
            )
    for i, receipt in enumerate(final["tc_receipts"]):
        dispatch = [
            e
            for e in final["tc_events"]
            if e["kind"] == "dispatch.issued" and e["payload"].get("id") == receipt["id"]
        ]
        ack = [
            e
            for e in final["tc_events"]
            if e["kind"] == "observer.acknowledged"
            and e["payload"].get("receipt_id") == receipt["id"]
        ]
        if len(dispatch) != 1 or len(ack) != 1:
            raise ValueError("Duplicate or incomplete receiver chain")
        if dispatch[0]["wall"] > receipt["wall"] or receipt["wall"] > ack[0]["wall"]:
            raise ValueError("Receiver clock order violation")
    # Model action availability is linked by exact native call ID, never by text similarity.
    for i, action in enumerate(records(store, f"{base}/{arm}/actions.jsonl")):
        path = f"{base}/{arm}/actions.jsonl"
        key = _node(
            graph,
            f"{prefix}:action:{i}",
            "NATIVE_ACTION",
            path,
            i,
            clock={k: action[k] for k in ("start_wall", "end_wall") if k in action},
        )
        call_id = action["tool_call_id"]
        if call_id not in model_index:
            raise ValueError("Action has no genuine model response: " + call_id)
        model_path, index, call = model_index[call_id]
        model_row = store.read(model_path)[index]
        mid = _node(
            graph,
            f"{prefix}:model:{model_row['request_id']}",
            "MODEL_RESPONSE",
            model_path,
            index,
            clock={
                "start_wall": model_row["timestamp"],
                "end_wall": model_row["timestamp_finished"],
            },
        )
        graph.edge(
            mid,
            key,
            "NATIVE_TOOL_CALL_ID",
            store.reference(path, i),
            reused_source_proposal=action.get("actor_kind") == "recorded_source_proposal",
        )
    for name, kind in [
        ("inference.jsonl", "ACTOR_INFERENCE_INTERVAL"),
        ("actor-inference.jsonl", "ACTOR_INFERENCE_INTERVAL"),
        ("treatments.jsonl", "CONTROLLER_ACTION_INTERVAL"),
        ("controller-actions.jsonl", "CONTROLLER_ACTION_INTERVAL"),
        ("supervision.jsonl", "SUPERVISOR_RESULT"),
        ("gateway-decisions.jsonl", "GATEWAY_DECISION"),
    ]:
        path = f"{base}/{arm}/{name}"
        for i, raw in enumerate(records(store, path)):
            _node(
                graph,
                f"{prefix}:{name}:{i}",
                kind,
                path,
                i,
                clock={
                    k: raw[k] for k in ("start_wall", "end_wall", "wall", "clock_ms") if k in raw
                },
            )
    # Gateway action IDs provide the missing native-tool -> committed-effect bridge in C1.
    journal_path = f"{base}/{arm}/gateway-journal.json"
    if (store.root / journal_path).exists():
        for i, raw in enumerate(store.read(journal_path)["actions"]):
            jid = _node(
                graph, f"{prefix}:gateway_action:{i}", "GATEWAY_ACTION", journal_path, "actions", i
            )
            action_id = raw.get("action_id")
            for table in ("effect_events", "tc_events"):
                for event in final[table]:
                    if action_id and event.get("action_id") == action_id:
                        graph.edge(
                            jid,
                            maps[table][str(event["id"])],
                            "GATEWAY_ACTION_ID",
                            store.reference(journal_path, "actions", i),
                        )
    else:
        graph.gaps.append(
            dict(
                branch=prefix,
                kind="NO_NATIVE_TO_DB_ACTION_ID_JOURNAL",
                meaning="No invented browser/HTTP attribution or action timestamps",
            )
        )
    report = store.read(report_path)
    oracle = report["oracle"]
    outcome = _node(
        graph,
        prefix + ":outcome",
        "INDEPENDENT_OUTCOME",
        report_path,
        "oracle",
        attributes={
            "realized_safe_completion": oracle["safe_task_success"],
            "bounded_existential_recoverability": "UNKNOWN",
            "bounded_observation_robust_recoverability": "UNKNOWN",
            "current_state_repair": "UNKNOWN",
            "historical_contract_clean": not bool(
                oracle["unauthorized_mock_receipt_ids"]
                or oracle["unauthorized_irreversible_event_ids"]
                or oracle["unauthorized_write_event_ids"]
            ),
            "remaining_service_obligation": not oracle["service_goal_success"],
        },
    )
    graph.edge(
        cut,
        outcome,
        "CERTIFIED_SIBLING_EXECUTION",
        store.reference(certificate_path),
        kind="EXECUTED_COUNTERFACTUAL",
        cut_sha256=cp["sha256"],
        outcome_evidence=store.reference(report_path, "oracle"),
        witness_scope="This executed sibling schedule only; not a robust policy",
    )
    return dict(
        run_id=Path(run).name,
        source_id=row["id"],
        arm=arm,
        cut=cut,
        outcome=outcome,
        cut_sha256=cp["sha256"],
        safe=oracle["safe_task_success"],
        legitimate=oracle["goal_success"],
        forbidden_receipts=len(oracle["unauthorized_mock_receipt_ids"]),
    )


def build(root, runs, output):
    graph = Graph(EvidenceStore(root))
    outcomes = []
    for run in runs:
        p = graph.store.read(f"{run}/protocol.json")
        index = {}
        path = f"{run}/model_calls.jsonl"
        for i, raw in enumerate(graph.store.read(path)):
            if raw["event"] != "finished":
                continue
            if raw["evidence_kind"] != "live_modal" or raw["billing_uncertain"]:
                raise ValueError("Genuine completed, known-origin generations required")
            for call in raw["response"]["choices"][0]["message"].get("tool_calls", []):
                if call["id"] in index:
                    raise ValueError("Duplicate model native call ID")
                index[call["id"]] = (path, i, call)
        for row in p["cases"]:
            for arm in row["arm_order"]:
                outcomes.append(build_branch(graph, run, row, arm, index))
    graph.export(output)
    summary = dict(
        schema_version=1,
        evidence_kind="HISTORICAL_REANALYSIS_NO_NEW_INFERENCE",
        branches=outcomes,
        node_kinds=dict(Counter(n["kind"] for n in graph.nodes.values())),
        edge_kinds=dict(Counter(e["kind"] for e in graph.edges)),
        known_gaps=graph.gaps,
        new_model_calls=0,
    )
    Path(output, "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary

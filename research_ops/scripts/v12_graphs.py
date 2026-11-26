"""Evidence-linked observed graphs and certified initial counterfactual branches.

No unexecuted transition or missing continuation is labeled infeasible. Wall
timestamps order observations; audit timestamps are not exact SQL commit times.
"""

import argparse
import collections
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(roots, output):
    output.mkdir(parents=True, exist_ok=False)
    totals = collections.Counter()
    sources = collections.defaultdict(list)
    ledger = []
    with (output / "nodes.jsonl").open("w") as ns, (output / "edges.jsonl").open("w") as es:
        for root in roots:
            for file in sorted(root.glob("cloud-batches/**/episodes/*/result.json")):
                episode = read(file)
                folder = Path(episode.get("raw_result_path", str(file))).parent
                identity = root.name + ":" + episode["episode_id"]
                final_path = folder / "final.json"
                if not final_path.exists():
                    ledger.append(dict(episode=identity, status="UNKNOWN_MISSING_FINAL"))
                    continue
                final = read(final_path)
                paths = {str(p): sha(p) for p in folder.glob("*.json")}
                nodes, edges, raw_index = [], [], {}

                def node(kind, payload, locator, pointer, wall=None, label=None):
                    key = identity + ":" + str(len(nodes))
                    value = dict(
                        id=key,
                        episode=identity,
                        kind=kind,
                        wall=wall,
                        label=label or kind,
                        evidence_path=str(locator),
                        pointer=pointer,
                        evidence_sha256=paths.get(str(locator)) or sha(locator),
                        epistemic="OBSERVED",
                        clock="container_wall" if wall else None,
                        timestamp_semantics="recorded audit/HTTP bound; not exact SQL commit",
                    )
                    nodes.append(value)
                    raw_index[key] = payload
                    return key

                def edge(a, b, relation, provenance, scope="OBSERVED"):
                    if a == b:
                        raise ValueError("Self edge")
                    edges.append(
                        dict(
                            source=a,
                            target=b,
                            relation=relation,
                            epistemic=scope,
                            provenance=provenance,
                        )
                    )

                source_path = folder / "source-cut.json"
                start = node("source.cut", read(source_path), source_path, "", label="Initial cut")
                db_nodes, requests, admitted, queued, acknowledgments = {}, {}, {}, {}, {}
                for index, event in enumerate(final.get("v12_events", [])):
                    key = node(
                        event["kind"], event, final_path, f"/v12_events/{index}", event["wall"]
                    )
                    db_nodes[event["id"]] = key
                    command = event["payload"].get("command_id")
                    if command:
                        requests.setdefault(command, []).append(key)
                    if event["kind"] == "external.admitted":
                        admitted[event["payload"]["effect_id"]] = key
                    if event["kind"] == "external.queued":
                        queued[event["payload"]["effect_id"]] = key
                    if event["kind"] == "receiver.transport_ack":
                        acknowledgments[event["payload"]["effect_id"]] = key
                for effect_id in set(queued) & set(admitted):
                    edge(
                        queued[effect_id],
                        admitted[effect_id],
                        "queued_effect_admitted",
                        dict(effect_id=effect_id),
                    )
                for index, receipt in enumerate(final.get("v12_receipts", [])):
                    key = node(
                        "receiver.physical_commit",
                        receipt,
                        final_path,
                        f"/v12_receipts/{index}",
                        receipt["wall"],
                    )
                    if receipt["id"] in admitted:
                        edge(
                            admitted[receipt["id"]],
                            key,
                            "admitted_ticket_delivered",
                            dict(effect_id=receipt["id"], receipt_index=index),
                        )
                    if receipt["id"] in acknowledgments:
                        edge(
                            key,
                            acknowledgments[receipt["id"]],
                            "receiver_commit_acknowledged",
                            dict(effect_id=receipt["id"], receipt_index=index),
                        )
                network_path = folder / "browser-network.json"
                for index, event in enumerate(read(network_path)):
                    key = node(
                        "browser.http_request", event, network_path, f"/{index}", event["wall"]
                    )
                    command = event["body"].get("operation_id")
                    for target in requests.get(command, []):
                        edge(key, target, "browser_command_persisted", dict(command_id=command))
                control_path = folder / "events.json"
                for index, event in enumerate(read(control_path)):
                    node(event["kind"], event, control_path, f"/{index}", event.get("wall"))
                trace = folder.parents[1] / "model-traces"
                previous = None
                for request_id in episode.get("model_requests", []):
                    request_path = trace / (request_id + "-input.json")
                    response_path = trace / (request_id + "-output.json")
                    if not request_path.exists():
                        totals["missing_model_input"] += 1
                        continue
                    request = read(request_path)
                    a = node(
                        "model.request",
                        request,
                        request_path,
                        "",
                        request["start_wall"],
                        request_id,
                    )
                    if request["role"] == "actor":
                        content = json.loads(request["body"]["messages"][-1]["content"])
                        public = content.get("public", content.get("batch_current_public"))
                        table = public["current_records"]
                        observed = [dict(zip(table["columns"], row)) for row in table["rows"]]
                        nodes[-1]["observed_remaining_business_records"] = [
                            row["id"] for row in observed if row["stage"] != "complete"
                        ]
                        nodes[-1]["reachability_at_request"] = "UNKNOWN"
                    if previous:
                        edge(previous, a, "serial_program_order", dict(native_request=request_id))
                    else:
                        edge(
                            start,
                            a,
                            "source_precedes_first_request",
                            dict(context_sha256=sha(request_path)),
                        )
                    if response_path.exists():
                        response = read(response_path)
                        b = node(
                            "model.response",
                            response,
                            response_path,
                            "",
                            response["end_wall"],
                            request_id,
                        )
                        edge(a, b, "actual_http_request_response", dict(request_id=request_id))
                        previous = b
                score = episode.get("score") or {}
                recoverability = (
                    "REALIZED_SAFE_COMPLETION"
                    if score.get("joint_safe_completion") is True
                    else "FIXED_HISTORY_VIOLATION"
                    if score.get("forbidden_history")
                    else "UNKNOWN"
                )
                terminal = node("episode.terminal", episode, file, "", label=recoverability)
                nodes[-1]["recoverability"] = recoverability
                edge(start, terminal, "executed_trajectory", dict(result_sha256=sha(file)))
                cert_path = folder / "source-certificate.json"
                cert = read(cert_path)
                source_cut = read(source_path)
                world_key = (
                    episode["task_id"],
                    episode["world_seed"],
                    episode["admission_ms"],
                    episode.get("clean", False),
                )
                sources[world_key].append(
                    dict(
                        episode=identity,
                        root=root.name,
                        start=start,
                        terminal=terminal,
                        source_sha256=cert["actual_sha256"],
                        certificate_valid=cert["valid"],
                        result_sha256=sha(file),
                        safe=score.get("joint_safe_completion") is True,
                        context_scope=(
                            "Frozen tools/model configuration plus quiescent initial state; "
                            "no prior model turns"
                        ),
                        contract_sha256=source_cut["contract_sha256"],
                    )
                )
                for value in nodes:
                    ns.write(json.dumps(value) + "\n")
                for value in edges:
                    es.write(json.dumps(value) + "\n")
                totals.update(trajectories=1, nodes=len(nodes), observed_edges=len(edges))
                totals[recoverability] += 1
                ledger.append(
                    dict(
                        episode=identity,
                        status=episode["status"],
                        result=str(file),
                        sha256=sha(file),
                        nodes=len(nodes),
                        edges=len(edges),
                    )
                )
        for key, siblings in sources.items():
            # Model contexts differ across models. Only same-run/model siblings are
            # joined as executed alternatives. No mid-trajectory equivalence claim.
            grouped = collections.defaultdict(list)
            for sibling in siblings:
                grouped[sibling["root"]].append(sibling)
            for group in grouped.values():
                if len(group) < 2:
                    continue
                hashes = {s["source_sha256"] for s in group}
                if len(hashes) != 1 or not all(s["certificate_valid"] for s in group):
                    totals["invalid_counterfactual_groups"] += 1
                    continue
                base = group[0]
                totals["certified_initial_groups"] += 1
                totals["witnessed_safe_initial_groups"] += any(s["safe"] for s in group)
                for sibling in group[1:]:
                    es.write(
                        json.dumps(
                            dict(
                                source=base["start"],
                                target=sibling["terminal"],
                                relation="fresh_policy_continuation_from_equivalent_initial_cut",
                                epistemic="EXECUTED_COUNTERFACTUAL",
                                provenance=dict(
                                    source_sha256=base["source_sha256"], sibling=sibling
                                ),
                            )
                        )
                        + "\n"
                    )
                    totals["counterfactual_edges"] += 1
    (output / "trajectory-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    report = dict(
        totals,
        graph_schema=1,
        formal_edges_in_this_graph=0,
        unknown_intermediate_reachability=True,
        no_inferred_causal_edges_counted=True,
        formal_proofs=(
            "Separate bounded-model certificates; never transferred to open browser states"
        ),
        script_sha256=sha(Path(__file__)),
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    build(a.runs, a.output)

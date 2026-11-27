"""Add explicit native tool/gateway identity joins without inventing DB commit links."""

import argparse
import collections
import json
from pathlib import Path


def main(graph, output):
    nodes = {}
    responses = {}
    network = {}
    events = {}
    counts = collections.Counter()
    edges = []
    for line in (graph / "nodes.jsonl").open():
        n = json.loads(line)
        nodes[n["id"]] = n
        if n["kind"] == "model.response":
            responses[(n["episode"], n["label"])] = n
        elif n["kind"] == "browser.http_request":
            raw = json.loads(Path(n["evidence_path"]).read_text())[int(n["pointer"][1:])]
            network[(n["episode"], raw["body"]["operation_id"])] = n
        elif n["kind"].startswith(("actor.", "controller.", "supervisor.")):
            events[(n["episode"], int(n["pointer"][1:]))] = n
    cache = {}

    def raw(n):
        path = n["evidence_path"]
        if path not in cache:
            cache[path] = json.loads(Path(path).read_text())
        v = cache[path]
        for component in n["pointer"].strip("/").split("/") if n["pointer"] else []:
            v = v[int(component)] if isinstance(v, list) else v[component]
        return v

    for (episode, index), n in events.items():
        e = raw(n)
        request = e.get("request_id")
        response = responses.get((episode, request))
        if response and e["kind"] in {
            "actor.gateway_action",
            "actor.public_observation",
            "actor.finish_requested",
        }:
            message = json.loads(raw(response)["raw"])["choices"][0]["message"]
            tool_id = e.get("tool_call_id")
            calls = [c for c in message.get("tool_calls", []) if c["id"] == tool_id]
            if len(calls) != 1:
                raise ValueError("Native tool ID not present exactly once")
            if e["kind"] == "actor.gateway_action":
                args = json.loads(calls[0]["function"]["arguments"])
                assert e["action"] in args["actions"]
            assert response["wall"] <= n["wall"]
            edges.append(
                dict(
                    source=response["id"],
                    target=n["id"],
                    relation="actual_native_tool_executed",
                    epistemic="OBSERVED",
                    provenance=dict(request_id=request, tool_call_id=tool_id),
                )
            )
        if response and e["kind"] == "supervisor.recommendation":
            assert response["wall"] <= n["wall"]
            edges.append(
                dict(
                    source=response["id"],
                    target=n["id"],
                    relation="actual_reviewer_response_processed",
                    epistemic="OBSERVED",
                    provenance=dict(
                        request_id=request,
                        schema_valid=e["schema_valid"],
                        fallback=not e["schema_valid"],
                    ),
                )
            )
        command = e.get("command_id")
        http = network.get((episode, command)) if command else None
        if http and e["kind"] == "actor.gateway_action":
            assert n["wall"] <= http["wall"] <= e["end_wall"]
            edges.append(
                dict(
                    source=n["id"],
                    target=http["id"],
                    relation="native_gateway_issued_http",
                    epistemic="OBSERVED",
                    provenance=dict(command_id=command),
                )
            )
        elif http and e["kind"] == "controller.decision_applied":
            before = events[(episode, e["recommendation_index"])]
            assert before["wall"] <= http["wall"] <= n["wall"]
            edges.append(
                dict(
                    source=before["id"],
                    target=http["id"],
                    relation="controller_recommendation_issued_http",
                    epistemic="OBSERVED",
                    provenance=dict(command_id=command, application_event=n["id"]),
                )
            )
            edges.append(
                dict(
                    source=http["id"],
                    target=n["id"],
                    relation="controller_http_acknowledged",
                    epistemic="OBSERVED",
                    provenance=dict(command_id=command),
                )
            )
    output.mkdir(parents=True, exist_ok=False)
    with (output / "native-edges.jsonl").open("w") as stream:
        for e in edges:
            stream.write(json.dumps(e) + "\n")
            counts[e["relation"]] += 1
    report = dict(
        edges=len(edges),
        relations=dict(counts),
        exact_ids_only=True,
        db_control_commit_join_not_invented=True,
        clock_semantics=(
            "Action interval start and actual POST timestamp; recording may occur after response"
        ),
        not_additional_experiments=True,
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graphs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.graphs, a.output)

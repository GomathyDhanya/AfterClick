"""Independent raw-reference and identity/order checker for graph extensions."""

import argparse
import collections
import hashlib
import json
from pathlib import Path


def main(graph, joins, inventory, output):
    nodes = {}
    for p in [graph / "nodes.jsonl", inventory / "unlisted-nodes.jsonl"]:
        for line in p.open():
            n = json.loads(line)
            assert n["id"] not in nodes
            nodes[n["id"]] = n
    cache = collections.OrderedDict()

    def raw(n):
        path = n["evidence_path"]
        if path not in cache:
            data = Path(path).read_bytes()
            assert hashlib.sha256(data).hexdigest() == n["evidence_sha256"]
            cache[path] = json.loads(data)
            if len(cache) > 128:
                cache.popitem(last=False)
        cache.move_to_end(path)
        v = cache[path]
        for part in n["pointer"].strip("/").split("/") if n["pointer"] else []:
            v = v[int(part)] if isinstance(v, list) else v[part]
        return v

    adjacency = collections.defaultdict(list)
    indegree = dict.fromkeys(nodes, 0)
    counts = collections.Counter()
    for line in (graph / "edges.jsonl").open():
        e = json.loads(line)
        adjacency[e["source"]].append(e["target"])
        indegree[e["target"]] += 1
    for p in [joins / "native-edges.jsonl", inventory / "unlisted-edges.jsonl"]:
        for line in p.open():
            e = json.loads(line)
            s, t = nodes[e["source"]], nodes[e["target"]]
            a, b = raw(s), raw(t)
            relation = e["relation"]
            assert s["episode"] == t["episode"] and e["epistemic"] == "OBSERVED"
            if relation == "actual_native_tool_executed":
                calls = json.loads(a["raw"])["choices"][0]["message"].get("tool_calls", [])
                match = [c for c in calls if c["id"] == b["tool_call_id"]]
                assert len(match) == 1
                expected = {
                    "actor.gateway_action": "browser_act",
                    "actor.public_observation": "browser_state",
                    "actor.finish_requested": "finish_task",
                }[b["kind"]]
                assert match[0]["function"]["name"] == expected
                if expected == "browser_act":
                    assert b["action"] in json.loads(match[0]["function"]["arguments"])["actions"]
                assert s["label"] == b["request_id"] and a["end_wall"] <= b["wall"]
            elif relation == "native_gateway_issued_http":
                assert (
                    a["command_id"] == b["body"]["operation_id"]
                    and a["wall"] <= b["wall"] <= a["end_wall"]
                )
            elif relation == "controller_recommendation_issued_http":
                applied = raw(nodes[e["provenance"]["application_event"]])
                assert (
                    applied["command_id"] == b["body"]["operation_id"]
                    and applied["recommendation_index"] == int(s["pointer"][1:])
                    and a["wall"] <= b["wall"] <= applied["wall"]
                )
            elif relation == "controller_http_acknowledged":
                assert a["body"]["operation_id"] == b["command_id"] and a["wall"] <= b["wall"]
            elif relation == "actual_reviewer_response_processed":
                assert s["label"] == b["request_id"] and a["end_wall"] <= b["wall"]
                if b["schema_valid"]:
                    decision = json.loads(json.loads(a["raw"])["choices"][0]["message"]["content"])
                    assert (
                        decision["decision"] == b["decision"] and decision["reason"] == b["reason"]
                    )
                assert e["provenance"]["fallback"] == (not b["schema_valid"])
            elif relation == "actual_request_response_or_transport_error":
                assert (
                    Path(s["evidence_path"]).name.replace(
                        "-input",
                        "-output"
                        if Path(t["evidence_path"]).name.endswith("-output.json")
                        else "-error",
                    )
                    == Path(t["evidence_path"]).name
                )
                assert a["start_wall"] <= b.get("end_wall", b.get("wall"))
            else:
                raise ValueError("Unverified extension relation " + relation)
            adjacency[e["source"]].append(e["target"])
            indegree[e["target"]] += 1
            counts[relation] += 1
    queue = collections.deque(k for k, v in indegree.items() if not v)
    seen = 0
    while queue:
        key = queue.popleft()
        seen += 1
        for target in adjacency[key]:
            indegree[target] -= 1
            if not indegree[target]:
                queue.append(target)
    assert seen == len(nodes), "Extended graph cycle"
    output.mkdir(parents=True, exist_ok=False)
    report = dict(
        passed=True,
        nodes=len(nodes),
        extension_edges=sum(counts.values()),
        relations=dict(counts),
        acyclic_with_original_graph=True,
        no_invented_commit_link=True,
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graphs", type=Path, required=True)
    p.add_argument("--joins", type=Path, required=True)
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.graphs, a.joins, a.inventory, a.output)

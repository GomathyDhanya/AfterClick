"""Check every new-workflow graph reference, join, clock and acyclicity offline."""

import argparse
import collections
import hashlib
import json
from pathlib import Path


def verify(directory):
    cache = collections.OrderedDict()
    verified_files = set()

    def raw(node):
        name = node["evidence_path"]
        if name not in cache:
            data = Path(name).read_bytes()
            cache[name] = (hashlib.sha256(data).hexdigest(), json.loads(data))
            verified_files.add(name)
            if len(cache) > 128:
                cache.popitem(last=False)
        cache.move_to_end(name)
        checksum, value = cache[name]
        assert checksum == node["evidence_sha256"], name
        if node["pointer"]:
            for component in node["pointer"].strip("/").split("/"):
                value = value[int(component)] if isinstance(value, list) else value[component]
        return value

    nodes = {}
    for line in (directory / "nodes.jsonl").open():
        n = json.loads(line)
        assert n["id"] not in nodes
        value = raw(n)
        if n["wall"] is not None:
            field = (
                "start_wall"
                if n["kind"] == "model.request"
                else "end_wall"
                if n["kind"] == "model.response"
                else "wall"
            )
            assert n["wall"] == value[field], n["id"]
        if "reachability_at_request" in n:
            assert n["reachability_at_request"] == "UNKNOWN"
        nodes[n["id"]] = n
    adjacency = collections.defaultdict(list)
    indegree = dict.fromkeys(nodes, 0)
    kinds = collections.Counter()
    for line in (directory / "edges.jsonl").open():
        e = json.loads(line)
        s, t = nodes[e["source"]], nodes[e["target"]]
        a, b = raw(s), raw(t)
        r = e["relation"]
        if r == "admitted_ticket_delivered":
            valid = a["payload"]["effect_id"] == b["id"] and a["wall"] <= b["wall"]
        elif r == "queued_effect_admitted":
            valid = (
                a["payload"]["effect_id"] == b["payload"]["effect_id"] and a["wall"] <= b["wall"]
            )
        elif r == "receiver_commit_acknowledged":
            valid = a["id"] == b["payload"]["effect_id"] and a["wall"] <= b["wall"]
        elif r == "browser_command_persisted":
            valid = (
                a["body"]["operation_id"] == b["payload"]["command_id"] and a["wall"] <= b["wall"]
            )
        elif r == "actual_http_request_response":
            valid = (
                Path(s["evidence_path"]).name.replace("-input", "-output")
                == Path(t["evidence_path"]).name
                and a["start_wall"] <= b["end_wall"]
            )
        elif r == "serial_program_order":
            valid = s["episode"] == t["episode"] and a["end_wall"] <= b["start_wall"]
        elif r == "source_precedes_first_request":
            valid = (
                s["kind"] == "source.cut"
                and t["kind"] == "model.request"
                and s["episode"] == t["episode"]
            )
        elif r == "executed_trajectory":
            valid = (
                s["kind"] == "source.cut"
                and t["kind"] == "episode.terminal"
                and s["episode"] == t["episode"]
            )
        elif r == "fresh_policy_continuation_from_equivalent_initial_cut":
            sibling = e["provenance"]["sibling"]
            episode = Path(b.get("raw_result_path", t["evidence_path"])).parent
            cert = json.loads((episode / "source-certificate.json").read_text())
            initial = json.loads((episode / "source-cut.json").read_text())

            def canonical(value):
                return hashlib.sha256(
                    json.dumps(
                        value, sort_keys=True, separators=(",", ":"), allow_nan=False
                    ).encode()
                ).hexdigest()

            valid = (
                e["epistemic"] == "EXECUTED_COUNTERFACTUAL"
                and cert["valid"]
                and cert["actual_sha256"]
                == e["provenance"]["source_sha256"]
                == canonical(a)
                == canonical(initial)
                and sibling["result_sha256"] == t["evidence_sha256"]
            )
        else:
            raise ValueError("Unverified relation " + r)
        assert valid, (e["source"], r, e["target"])
        if r != "fresh_policy_continuation_from_equivalent_initial_cut":
            assert e["epistemic"] == "OBSERVED"
        adjacency[e["source"]].append(e["target"])
        indegree[e["target"]] += 1
        kinds[r] += 1
    queue = collections.deque(k for k, v in indegree.items() if not v)
    count = 0
    while queue:
        count += 1
        for target in adjacency[queue.popleft()]:
            indegree[target] -= 1
            if not indegree[target]:
                queue.append(target)
    assert count == len(nodes), "Graph cycle"
    return dict(
        passed=True,
        nodes=len(nodes),
        edges=sum(kinds.values()),
        relations=dict(kinds),
        raw_files_verified=len(verified_files),
        scope=(
            "Observed identity/order joins and certified initial branches; "
            "no intermediate reachability proof"
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    a = p.parse_args()
    result = verify(a.directory)
    (a.directory / "independent-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))

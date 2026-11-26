"""Index every genuine model request, including lost responses and graph gaps."""

import argparse
import collections
import hashlib
import json
from pathlib import Path


def load(p):
    return json.loads(p.read_text())


def main(roots, graphs, output):
    output.mkdir(parents=True, exist_ok=False)
    known = set()
    counts = collections.Counter()
    rows = []
    extra_nodes = []
    extra_edges = []
    for line in (graphs / "nodes.jsonl").open():
        n = json.loads(line)
        if n["kind"] == "model.request":
            known.add(str(Path(n["evidence_path"]).resolve()))
    for root in roots:
        for p in sorted(root.glob("cloud-batches/**/model-traces/*-input.json")):
            r = load(p)
            response = p.with_name(p.name.replace("-input", "-output"))
            error = p.with_name(p.name.replace("-input", "-error"))
            body = None
            response_status = None
            if response.exists():
                out = load(response)
                response_status = out.get("status")
                try:
                    body = json.loads(out["raw"])
                except (KeyError, ValueError):
                    pass
            row = dict(
                episode=r["episode"],
                request_id=r["id"],
                role=r["role"],
                start_wall=r["start_wall"],
                input=str(p),
                input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                response=str(response) if response.exists() else None,
                response_sha256=hashlib.sha256(response.read_bytes()).hexdigest()
                if response.exists()
                else None,
                error=str(error) if error.exists() else None,
                response_http_status=response_status,
                model_generation_received=bool(
                    response_status == 200 and body and body.get("choices")
                ),
                provider_request_id=body.get("id") if body else None,
                known_usage=body.get("usage") if body else None,
                in_original_observed_graph=str(p.resolve()) in known,
                scientific_response_status="RECEIVED"
                if response.exists()
                else "UNKNOWN_NOT_RETRIED",
            )
            rows.append(row)
            counts["requests"] += 1
            counts["model_generations_received"] += row["model_generation_received"]
            counts["known_http_failures"] += response_status is not None and response_status != 200
            counts[row["scientific_response_status"]] += 1
            counts["role:" + r["role"]] += 1
            if not row["in_original_observed_graph"]:
                identity = root.name + ":" + r["episode"]
                key = identity + ":unlisted-request:" + r["id"]
                extra_nodes.append(
                    dict(
                        id=key,
                        episode=identity,
                        kind="model.request",
                        wall=r["start_wall"],
                        label=r["id"],
                        evidence_path=str(p),
                        pointer="",
                        evidence_sha256=row["input_sha256"],
                        epistemic="OBSERVED",
                        clock="container_wall",
                        reachability_at_request="UNKNOWN",
                    )
                )
                target_path = response if response.exists() else error if error.exists() else None
                if target_path:
                    data = load(target_path)
                    target = key + ":response-or-error"
                    kind = "model.response" if response.exists() else "model.transport_error"
                    wall = data.get("end_wall", data.get("wall"))
                    extra_nodes.append(
                        dict(
                            id=target,
                            episode=identity,
                            kind=kind,
                            wall=wall,
                            label=row["scientific_response_status"],
                            evidence_path=str(target_path),
                            pointer="",
                            evidence_sha256=hashlib.sha256(target_path.read_bytes()).hexdigest(),
                            epistemic="OBSERVED",
                            clock="container_wall",
                        )
                    )
                    extra_edges.append(
                        dict(
                            source=key,
                            target=target,
                            relation="actual_request_response_or_transport_error",
                            epistemic="OBSERVED",
                            provenance=dict(
                                request_id=r["id"], input=str(p), outcome=str(target_path)
                            ),
                        )
                    )
    (output / "requests.json").write_text(json.dumps(rows, indent=2) + "\n")
    for name, data in [
        ("unlisted-nodes.jsonl", extra_nodes),
        ("unlisted-edges.jsonl", extra_edges),
    ]:
        with (output / name).open("w") as stream:
            for row in data:
                stream.write(json.dumps(row) + "\n")
    report = dict(
        counts,
        unlisted_request_nodes=sum(n["kind"] == "model.request" for n in extra_nodes),
        additional_observed_nodes=len(extra_nodes),
        additional_observed_edges=len(extra_edges),
        lost_responses_preserved_unknown=True,
        no_generation_retries=True,
        exact_token_usage_unknown_for_missing_responses=True,
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", type=Path, nargs="+", required=True)
    p.add_argument("--graphs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.runs, a.graphs, a.output)

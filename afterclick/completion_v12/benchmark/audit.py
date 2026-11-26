"""Independent saved-data qualification audit and compositional split measurements."""

import argparse
import collections
import json
from pathlib import Path

from afterclick.completion_v12.benchmark.oracle import evaluate
from afterclick.completion_v12.benchmark.transport import save
from afterclick.completion_v12.evidence import digest, sha

RUNTIME = ["flow.py", "ops.py", "infrastructure.py", "domain_v12.py"]


def orders(ops, reverse=False):
    done, result = set(), []
    while len(result) < len(ops):
        ready = sorted(
            (o["id"] for o in ops if o["id"] not in done and set(o["dependencies"]) <= done),
            reverse=reverse,
        )
        if not ready:
            raise ValueError("Cyclic or missing prerequisite")
        item = ready[0]
        done.add(item)
        result.append(item)
    return result


def audit(contracts, roots, output):
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).parent
    current = {name: sha(source / name) for name in RUNTIME}
    rows, signatures, shared_docs = [], collections.defaultdict(list), collections.defaultdict(list)
    for path in sorted(contracts.glob("*.json")):
        if path.name == "manifest.json":
            continue
        contract = json.loads(path.read_text())
        identifier = contract["task_id"]
        ops = contract["public"]["initial_public_state"]["operations"]
        signature = digest([(o["kind"], o["dependencies"], o["scope_rule"]) for o in ops])
        signatures[signature].append(identifier)
        shared_docs[digest(contract["public"]["policy_documents"])].append(identifier)
        depth = {}
        for key in orders(ops):
            op = next(o for o in ops if o["id"] == key)
            depth[key] = 1 + max([depth[d] for d in op["dependencies"]] or [0])
        row = dict(
            task_id=identifier,
            split=contract["split"],
            application=contract["application"],
            family=contract["family"],
            complexity=contract["complexity"],
            contract_sha256=sha(path),
            operations=len(ops),
            edges=sum(len(o["dependencies"]) for o in ops),
            dependency_depth=max(depth.values()),
            alternative_topological_orders=orders(ops) != orders(ops, reverse=True),
            conditional_decisions=sum(o["scope_rule"] != "primary" for o in ops),
            external_processes=sum(o["kind"] == "external" for o in ops),
            role_approvals=sum(o["kind"] == "approval" for o in ops),
            distinct_restorations=sum(o["kind"] == "restore" for o in ops),
            status="UNQUALIFIED",
            attempts=[],
        )
        for root in roots:
            folder = root / identifier
            if not (folder / "qualification.json").exists():
                continue
            result = json.loads((folder / "qualification.json").read_text())
            attempt = dict(path=str(folder), status=result["status"])
            row["attempts"].append(attempt)
            if result["status"] != "REFERENCE_QUALIFIED" or result["contract_sha256"] != sha(path):
                continue
            if any(
                sha(root / "source-archive" / name) != expected
                for name, expected in current.items()
            ):
                attempt["runtime_matches"] = False
                continue
            scores = []
            for index in range(2):
                certificate = json.loads((folder / f"cut-certificate-{index}.json").read_text())
                if not certificate["valid"]:
                    raise ValueError("Invalid reconstruction certificate claimed qualified")
                snapshot = json.loads((folder / f"final-{index}.json").read_text())
                score = evaluate(contract, snapshot)
                save(output / f"{identifier}-rescore-{index}-{roots.index(root)}.json", score)
                scores.append(score["joint_safe_completion"] is True and score["status"] == "VALID")
            attempt.update(runtime_matches=True, current_oracle_accepts=all(scores))
            if all(scores):
                row.update(
                    status="REFERENCE_QUALIFIED_AND_INDEPENDENTLY_RESCORED", evidence=str(folder)
                )
        rows.append(row)
    crossing = [
        ids
        for ids in signatures.values()
        if any(i.startswith("DEV-") for i in ids) and any(i.startswith("TEST-") for i in ids)
    ]
    shared = [
        ids
        for ids in shared_docs.values()
        if any(i.startswith("DEV-") for i in ids) and any(i.startswith("TEST-") for i in ids)
    ]
    save(output / "task-audit.json", rows)
    report = dict(
        schema_version=1,
        task_count=len(rows),
        dev=sum(r["split"] == "dev" for r in rows),
        test=sum(r["split"] == "test" for r in rows),
        qualified=sum(r["status"].startswith("REFERENCE_QUALIFIED") for r in rows),
        unqualified=[
            r["task_id"] for r in rows if not r["status"].startswith("REFERENCE_QUALIFIED")
        ],
        unique_structural_layouts=len(signatures),
        cross_split_identical_layouts=crossing,
        shared_public_policy_documents=len(shared),
        public_policy_reuse_disclosed=True,
        independent_human_review=False,
        source_hashes={str(source / name): value for name, value in current.items()},
        oracle_sha256=sha(source / "oracle.py"),
        gateway_sha256=sha(source / "browser.py"),
        complete=len(rows) == 288
        and all(r["status"].startswith("REFERENCE_QUALIFIED") for r in rows),
        no_test_model_outcomes_used=True,
    )
    save(output / "report.json", report)
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in {"source_hashes", "unqualified", "cross_split_identical_layouts"}
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contracts", type=Path, required=True)
    p.add_argument("--qualification", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    audit(a.contracts, a.qualification, a.output)

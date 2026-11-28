"""Verify raw bindings, diagnostic validity, derived denominators and figure provenance."""

import collections
import hashlib
import json
import os
from pathlib import Path

from analyze import HERE, digest, dump, independent_score, read, sha
from enrich import loadcsv


def main():
    root = HERE.parents[1]
    history = HERE / "provenance/historical"
    report = read(HERE / "report.json")
    integrity = read(HERE / "integrity_report.json")
    for a in integrity["assets"]:
        assert sha(root / a["local_path"]) == a["sha256"]
    inputs = read(HERE / "provenance/input_hashes.json")
    broad = read(HERE / "all_valid_internal/report.json")
    assert broad and not broad["scoring_disagreements"]
    assert broad["supplementary_all_valid_internal"]["episodes"] == 1073
    for path, expected in read(HERE / "all_valid_internal/provenance/input_hashes.json").items():
        if path in inputs:
            assert inputs[path] == expected
        inputs[path] = expected
    for path, expected in read(HERE / "provenance/reviewer_input_hashes.json").items():
        if path in inputs:
            assert inputs[path] == expected
        inputs[path] = expected
    for path, expected in read(HERE / "provenance/invalid_request_hashes.json").items():
        if path in inputs:
            assert inputs[path] == expected
        inputs[path] = expected
    for rel, expected in inputs.items():
        assert sha(history / rel) == expected, rel
    for row in read(HERE / "provenance/frozen_hashes.json"):
        assert sha(history / row["path"]) == row["expected"]
    episodes = loadcsv("executions.csv")
    assert len(episodes) == len({r["episode_key"] for r in episodes})
    valid = [r for r in episodes if r["technical_validity"] == "VALID"]
    worker_log_hashes = {}
    for row in valid:
        path = (history / row["raw_path"]).parent / "worker-errors.json"
        assert read(path) == [], path
        worker_log_hashes[str(path.relative_to(history))] = sha(path)
    dump(HERE / "provenance/valid_worker_log_hashes.json", worker_log_hashes)
    source_inventory = read(HERE / "provenance/git_source_inventory.json")
    for row in source_inventory:
        content = (history / row["path"]).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        assert blob == row["blob_expected"], row["path"]
    assert len(valid) == report["population"]["valid_internal"]
    assert len(episodes) - len(valid) == report["population"]["invalid_internal"]
    eligible = [r for r in loadcsv("episode_timing.csv") if r["eligible_prohibited"]]
    assert len(eligible) == report["population"]["prohibited_pending"]
    assert len({r["episode_key"] for r in eligible}) == len(eligible)
    for name, metric in report["metrics"].items():
        rows = eligible if name == "full_eligible" else [r for r in eligible if r[name]]
        assert len(rows) == metric["n"]
        assert len({r["task_id"] for r in rows}) == metric["source_clusters"]
        for k, cell in metric.items():
            if k in {"n", "source_clusters"}:
                continue
            assert sum(bool(r[k]) for r in rows) == cell["numerator"]
            assert len(rows) == cell["denominator"]
    proposals = loadcsv("protection_proposals.csv")
    assert report["proposal_episodes"] == len(
        {r["episode_key"] for r in proposals if not r["pending_allowed"]}
    )
    controls = read(HERE / "positive_controls.json")
    terminal = sorted((HERE / "controls/raw").glob("*/result.json"))
    assert len(terminal) == controls["executed_attempts"]
    ticket = read(HERE / "ticket_window_controls.json")
    ticket_terminal = sorted((HERE / "controls/ticket_window_raw").glob("*/result.json"))
    assert len(ticket_terminal) == ticket["executed_attempts"]
    primary_attempts = len(terminal)
    terminal += ticket_terminal
    statuses = collections.Counter()
    for p in terminal:
        result = read(p)
        statuses[result["status"]] += 1
        if result["status"] != "VALID":
            assert result["error"]
            assert (p.parent / "error.json").exists()
            continue
        contract = read(
            history
            / "research_ops/completion_v12/candidate_contracts_v7"
            / (result["task_id"] + ".json")
        )
        final = read(p.parent / "final.json")
        actual = independent_score(contract, final)
        assert not actual["consistency_errors"]
        for k, saved in [
            ("G", "legitimate_complete"),
            ("F", "forbidden_history"),
            ("Y", "joint_safe_completion"),
        ]:
            assert actual[k] == bool(result["score"][saved])
        assert digest(final) == result["score"]["final_sha256"]
    assert statuses["VALID"] == controls["valid"] + ticket["valid"]
    figures = read(HERE / "figures/provenance.json")
    for f in figures:
        assert sha(HERE / f["plotting_script"]) == f["plotting_script_sha256"]
        for p, expected in f["inputs"].items():
            assert sha(HERE / p) == expected
        for ext in ["pdf", "png"]:
            assert sha(HERE / "figures" / (f["figure"] + "." + ext)) == f[ext + "_sha256"]
    result = dict(
        passed=True,
        raw_input_hashes=len(inputs),
        frozen_hashes=180,
        assets_verified=len(integrity["assets"]),
        control_attempts=len(terminal),
        primary_control_attempts=primary_attempts,
        additional_ticket_window_attempts=len(ticket_terminal),
        control_statuses=dict(statuses),
        figures_verified=len(figures),
        valid_empty_worker_logs=len(worker_log_hashes),
        unchanged_historical_git_blobs=len(source_inventory),
        model_calls=0,
        provider_calls=0,
    )
    dump(HERE / "provenance/final_verification.json", result)
    outputs = {}
    for directory, subdirs, files in os.walk(HERE):
        base = Path(directory)
        subdirs[:] = [
            d
            for d in subdirs
            if d not in {"__pycache__", ".pytest_cache", ".ruff_cache"}
            and base / d != HERE / "provenance/historical"
        ]
        for name in files:
            path = base / name
            if name in {"OUTPUT_MANIFEST.json", ".DS_Store"} or path.suffix in {".log", ".pyc"}:
                continue
            outputs[str(path.relative_to(HERE))] = sha(path)
    dump(
        HERE / "provenance/OUTPUT_MANIFEST.json",
        dict(
            scope=(
                "All new code/data/control evidence/figures, excluding restored historical "
                "dependency, caches, logs, and this manifest itself"
            ),
            files=outputs,
        ),
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

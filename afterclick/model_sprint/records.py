"""Small durable registration and immutable sealing helpers for the new sprint."""

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json, digest
from afterclick.model_sprint.driver import append

BASE = Path("artifacts/research_runs")


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def register(run_id, protocol):
    run = BASE / run_id
    run.mkdir()
    (run / "raw").mkdir()
    (run / "figures").mkdir()
    protocol = dict(schema_version=1, run_id=run_id, registered_utc=utc(), **protocol)
    atomic_json(run / "protocol.json", protocol)
    fields = [
        "diff_sha256",
        "source_manifest_sha256",
        "lockfile_sha256",
        "node_version",
        "postgres_version",
        "chromium_version",
        "contract_ids_and_hashes",
        "scheduler_config",
        "seed",
        "policy_name",
        "policy_model",
        "model_version_or_revision",
        "endpoint_name",
        "model_config",
        "prompt_sha256",
        "parser_sha256",
        "backend_version",
        "timeout_policy",
        "budget_usd",
        "priced_resource_seconds",
        "recorded_gpu_cost_usd",
        "input_tokens",
        "output_tokens",
        "journal_file_sha256",
        "oracle_schema_version",
    ]
    manifest = {f: None for f in fields}
    manifest.update(
        schema_version=1,
        run_id=run_id,
        utc_created=utc(),
        status="planned",
        git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        git_dirty=bool(subprocess.check_output(["git", "status", "--porcelain"])),
        diff_sha256=hashlib.sha256(
            subprocess.check_output(["git", "diff", "--binary"])
        ).hexdigest(),
        source_manifest_sha256=digest(protocol.get("source_hashes", {})),
        lockfile_sha256=sha("uv.lock"),
        host_platform=platform.platform(),
        python_version=platform.python_version(),
        budget_usd=protocol.get("max_usd", 0),
        policy_model=protocol.get("model"),
        model_version_or_revision=protocol.get("revision"),
        contract_ids_and_hashes=protocol.get("task_contract_hashes"),
    )
    atomic_json(run / "manifest.json", manifest)
    for n in ["trials.jsonl", "model_calls.jsonl", "oracle_certificates.jsonl"]:
        (run / n).touch()
    for n in ["analysis.md", "next_experiment.md"]:
        (run / n).write_text("Pending registered execution.\n")
    atomic_json(run / "metrics.json", dict(schema_version=1, status="planned"))
    append(
        "research_ops/EXPERIMENT_REGISTRY.jsonl",
        dict(
            schema_version=1,
            event="planned",
            utc=utc(),
            run_id=run_id,
            protocol_sha256=sha(run / "protocol.json"),
        ),
    )
    return run


def seal(run, status="completed"):
    run = Path(run)
    if (run / "checksums.json").exists():
        raise ValueError("Never rewrite a sealed run")
    manifest = json.loads((run / "manifest.json").read_text())
    manifest.update(
        status=status,
        finalized_utc=utc(),
        protocol_sha256=sha(run / "protocol.json"),
        journal_file_sha256=sha(run / "model_calls.jsonl"),
    )
    atomic_json(run / "manifest.json", manifest)
    hashes = {str(p.relative_to(run)): sha(p) for p in sorted(run.rglob("*")) if p.is_file()}
    atomic_json(run / "checksums.json", dict(schema_version=1, utc=utc(), file_sha256=hashes))
    append(
        "research_ops/EXPERIMENT_REGISTRY.jsonl",
        dict(
            schema_version=1,
            event=status,
            utc=utc(),
            run_id=run.name,
            seal_sha256=sha(run / "checksums.json"),
        ),
    )

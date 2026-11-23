"""Bounded, local-only P0 evidence capture. No provider or Modal invocation.

Register first, then execute stages individually; completed stages cannot be overwritten.
This is an audit helper, not the post-P0 autonomous research-cycle runner.
"""

import argparse
import hashlib
import json
import os
import platform
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "research_ops"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def append(path, value):
    with path.open("a") as stream:
        stream.write(json.dumps(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def plan(run):
    raw = run / "raw"
    return {
        "environment": (
            [
                str(ROOT / ".bootstrap/bin/uv"),
                "run",
                "python",
                "-c",
                "import sys,platform,importlib.metadata as m; "
                "from playwright.sync_api import sync_playwright; "
                "from afterclick.infrastructure.db import Database; "
                "from sqlalchemy import text; print(sys.version); print(platform.platform()); "
                "names=['playwright','pytest','sqlalchemy','psycopg','ruff']; "
                "print({n:m.version(n) for n in names}); "
                "db=Database('ac_p0_inspect'); "
                "c=db.engine.connect(); print(c.execute(text('SELECT version()')).scalar()); "
                "c.close(); db.engine.dispose(); p=sync_playwright().start(); "
                "b=p.chromium.launch(); print('Chromium',b.version); b.close(); p.stop()",
            ],
            120,
        ),
        "check": (["bash", "scripts/check.sh"], 1200),
        "demo": (
            [
                str(ROOT / ".bootstrap/bin/uv"),
                "run",
                "python",
                "-m",
                "afterclick.replay.demo",
                "--output",
                str(raw / "demo"),
            ],
            600,
        ),
        "pilot": (
            [
                str(ROOT / ".bootstrap/bin/uv"),
                "run",
                "python",
                "-m",
                "afterclick.evaluation.pilot",
                "--output",
                str(raw / "oracle-pilot"),
            ],
            600,
        ),
    }


def register(run):
    if (OPS / "STATE.json").exists():
        state = json.loads((OPS / "STATE.json").read_text())
        if state.get("state") not in {"NOT_STARTED", "GATE_DECISION"}:
            raise SystemExit("Existing active state: inspect it before registering another audit")
    run.mkdir(parents=True, exist_ok=False)
    for name in ("raw", "figures"):
        (run / name).mkdir()
    for name in ("trials.jsonl", "model_calls.jsonl", "oracle_certificates.jsonl"):
        (run / name).touch()
    source = {}
    for base in (
        "afterclick",
        "tests",
        "migrations",
        "fixtures",
        "scripts",
        "apps/flowboard-web/src",
        "research_ops",
    ):
        for path in sorted((ROOT / base).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                source[str(path.relative_to(ROOT))] = sha(path.read_bytes())
    for name in ("pyproject.toml", "uv.lock", "apps/flowboard-web/package-lock.json"):
        source[name] = sha((ROOT / name).read_bytes())
    write(run / "raw/source_hashes.json", source)
    diff = git("diff", "--binary", "HEAD")
    (run / "raw/initial.diff").write_bytes(diff)
    (run / "raw/initial-status.txt").write_bytes(git("status", "--short"))
    fields = (
        "node_version postgres_version chromium_version seed policy_model "
        "model_version_or_revision endpoint_name model_config prompt_sha256 "
        "backend_version priced_resource_seconds recorded_gpu_cost_usd "
        "journal_file_sha256 oracle_schema_version"
    )
    manifest = {name: None for name in fields.split()}
    manifest.update(
        schema_version=1,
        run_id=run.name,
        utc_created=now(),
        git_commit=git("rev-parse", "HEAD").decode().strip(),
        git_dirty=bool(git("status", "--porcelain")),
        diff_sha256=sha(diff),
        source_manifest_sha256=sha((run / "raw/source_hashes.json").read_bytes()),
        lockfile_sha256={
            k: source[k] for k in source if k.endswith("lock") or k.endswith("lock.json")
        },
        host_platform=platform.platform(),
        python_version=platform.python_version(),
        contract_ids_and_hashes={
            k: v for k, v in source.items() if k.startswith("fixtures/tasks/")
        },
        scheduler_config={"demo_seed": 7, "horizon_ms": 300, "clock": "explicit logical time"},
        policy_name="scripted demo / observable test doubles; no live provider",
        parser_sha256=source.get("afterclick/agent/action_parser.py"),
        timeout_policy="per-stage process group kill",
        budget_usd=0,
        input_tokens=0,
        output_tokens=0,
        paid_mode="disabled",
    )
    write(run / "manifest.json", manifest)
    protocol = dict(
        schema_version=1,
        run_id=run.name,
        registered_utc=now(),
        phase="P0",
        question=(
            "Does the current dirty checkout reproduce the bounded PostgreSQL/Chromium baseline?"
        ),
        rival_explanations=[
            "88 versus 122 reflects later uncommitted tests, not baseline regression",
            "live invalidity is provider uncertainty rather than reconstruction failure",
        ],
        estimand=(
            "descriptive pass/validity counts for this checkout and archived runs; "
            "no population effect"
        ),
        primary_metric="full test failures, seven-branch validity and 24 expected oracle classes",
        denominator="all attempted command stages; branch/case denominators reported separately",
        controls=(
            "execute/suppress/placebos; oracle positive/null/conflict/unknown/censored fixtures"
        ),
        randomization_unit=None,
        intervention="none beyond existing planted fixtures",
        sampling="exhaust existing development suite and fixed demo/pilot; no model selection",
        sample_size_rationale="regression audit, not an efficacy or power study",
        seed=7,
        splits="development only; no sealed holdout accessed",
        hyperparameter_search_budget=0,
        invalid_policy=(
            "retain failed stages, branches and cases; no causal interpretation of invalid replay"
        ),
        censoring_policy=(
            "report oracle CENSORED separately from replay invalidity and unknown labels"
        ),
        positive_interpretation="current bounded foundation reproduced; C1/C2/C3 remain untested",
        negative_interpretation=(
            "preserve failure, repair at most twice per root cause, rerun with new stage ID"
        ),
        commands={k: {"argv": v[0], "timeout_seconds": v[1]} for k, v in plan(run).items()},
        environment={
            "PATH_prefix": ".bootstrap/bin",
            "AFTERCLICK_TEST_REPORT": str(run / "raw/tests.xml"),
            "provider_credentials": "removed from child environment; no env dump",
        },
        cost_cap_usd=0,
        max_wall_minutes=45,
        stop_rule="P0 human review; no P1/Modal/holdout",
        literature="verify source identity only; no novelty clearance",
    )
    write(run / "protocol.json", protocol)
    write(run / "metrics.json", {"schema_version": 1, "status": "registered", "results": None})
    (run / "analysis.md").write_text("Registered; results pending. No conclusion yet.\n")
    (run / "next_experiment.md").write_text("Pending P0 results and mandatory human review.\n")
    (run / "figures/README.md").write_text(
        "No figure required for preregistration; metrics pending.\n"
    )
    append(
        OPS / "EXPERIMENT_REGISTRY.jsonl",
        dict(
            schema_version=1,
            run_id=run.name,
            utc=now(),
            phase="P0",
            state="planned",
            amendment_of=None,
            protocol_sha256=sha((run / "protocol.json").read_bytes()),
            budget_usd=0,
            spending_authorized=False,
            artifact_path=str(run.relative_to(ROOT)),
        ),
    )
    write(
        OPS / "STATE.json",
        dict(
            schema_version=1,
            phase="P0",
            phase_version=1,
            state="AUDITING",
            current_run_id=run.name,
            current_gate="RUNNING",
            last_good_commit=None,
            last_valid_run_id=None,
            most_recent_valid_run_ids=[],
            approved_run_id=None,
            approval_ceiling_usd=None,
            human_approval_required=False,
            frozen_holdout_hash=None,
            frozen_holdout_hashes=None,
            initial_applicable_credit_usd=None,
            reported_remaining_credit_usd=None,
            estimated_cumulative_paid_usd=0.0,
            modal_session_spend_usd=0.0,
            historical_other_provider_invoice_usd=None,
            active_endpoint_created=False,
            blocked_approvals=[],
            next_command=f"python3 research_ops/scripts/p0_audit.py {run.name} environment",
        ),
    )
    append(
        OPS / "EXPERIMENT_REGISTRY.jsonl",
        dict(
            schema_version=1,
            run_id=run.name,
            utc=now(),
            state="execution_ready",
            note="registration persisted before data generation",
        ),
    )
    print(run)


def execute(run, stage):
    protocol = json.loads((run / "protocol.json").read_text())
    if protocol["cost_cap_usd"] != 0 or protocol["phase"] != "P0":
        raise SystemExit("P0 local-only protocol required")
    if stage == "db-start":
        command, timeout = ["docker", "compose", "up", "-d", "--wait", "db"], 180
    else:
        command, timeout = plan(run)["environment" if stage == "environment-recheck" else stage]
    if stage in {"db-start", "environment-recheck"}:
        records = [
            json.loads(line)
            for line in (OPS / "EXPERIMENT_REGISTRY.jsonl").read_text().splitlines()
        ]
        if not any(
            r.get("run_id") == run.name and stage in r.get("added_stages", []) for r in records
        ):
            raise SystemExit("Repair stage must be preregistered in the registry")
    result_path = run / f"raw/{stage}.result.json"
    log_path = run / f"raw/{stage}.log"
    if result_path.exists() or log_path.exists():
        raise SystemExit(
            "Stage already attempted; preserve logs and register an amendment for repairs"
        )
    env = {
        k: v
        for k, v in os.environ.items()
        if not any(
            word in k.upper() for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "CREDENTIAL")
        )
    }
    env.pop(
        "DATABASE_URL", None
    )  # use the repository's local test database, never an ambient target
    env["PATH"] = str(ROOT / ".bootstrap/bin") + os.pathsep + env["PATH"]
    env["AFTERCLICK_TEST_REPORT"] = str(run / "raw/tests.xml")
    started = now()
    append(
        run / "trials.jsonl",
        dict(
            schema_version=1,
            case_id=stage,
            run_id=run.name,
            record_type="stage_started",
            utc=started,
            command=command,
            model_calls=0,
            billed_or_estimated_usd=0,
        ),
    )
    start = time.monotonic()
    process = None
    error = None
    try:
        with log_path.open("x") as stream:
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=env,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            code = process.wait(timeout=timeout)
    except BaseException as exc:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        error = type(exc).__name__
        code = -1
    result = dict(
        schema_version=1,
        run_id=run.name,
        case_id=stage,
        record_type="stage_finished",
        command=command,
        utc_started=started,
        utc_finished=now(),
        exit_code=code,
        status="passed" if code == 0 else "crashed_or_failed",
        error_type=error,
        execution_wall_ms=round((time.monotonic() - start) * 1000),
        model_calls=0,
        billed_or_estimated_usd=0,
        log_sha256=sha(log_path.read_bytes()),
    )
    write(result_path, result)
    append(run / "trials.jsonl", result)
    print(json.dumps(result))
    raise SystemExit(0 if code == 0 else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument(
        "stage",
        choices=[
            "register",
            "environment",
            "check",
            "demo",
            "pilot",
            "db-start",
            "environment-recheck",
        ],
    )
    args = parser.parse_args()
    if not args.run_id.startswith("p0-") or any(
        c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.run_id
    ):
        parser.error("Use a p0- prefixed local run identifier")
    directory = ROOT / "artifacts/research_runs" / args.run_id
    if args.stage == "register":
        register(directory)
    else:
        execute(directory, args.stage)

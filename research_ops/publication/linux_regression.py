"""Finite corrected Linux regression: complete Git source plus locked frontend builds."""

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "research_ops/publication"
CLI = str(Path.home() / ".local/bin/modal")


def load(p):
    return json.loads(p.read_text())


def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n")


def main(run):
    run.mkdir(parents=True, exist_ok=False)
    state = load(KIT / "FINANCE_STATE.json")
    reserve = 2
    assert (
        state["active"] is None
        and not state["unresolved"]
        and state["guard_accounted_usd"] + reserve <= 28
    )
    assert (
        os.environ.get("MODAL_PROFILE") == "gsankarasubr"
        and os.environ.get("MODAL_ENVIRONMENT") == "main"
    )
    state["active"] = dict(run_id=run.name, reservation_usd=reserve, cpu_only=True)
    state["guard_accounted_usd"] += reserve
    save(KIT / "FINANCE_STATE.json", state)
    started = time.monotonic()
    sandbox = None
    closed = False
    error = None
    before = None

    def bill(label):
        p = subprocess.run(
            [CLI, "billing", "summary", "--json", "--profile", "gsankarasubr"],
            capture_output=True,
            text=True,
            timeout=40,
        )
        assert p.returncode == 0
        (run / (label + ".json")).write_text(p.stdout)
        return json.loads(p.stdout)

    try:
        before = bill("billing-before")
        assert float(before["billed_cost"]) == 0
        source = run / "source-base.tar.gz"
        with source.open("wb") as f:
            subprocess.run(
                ["git", "archive", "--format=tar.gz", "2080c426"], cwd=ROOT, stdout=f, check=True
            )
        payload = run / "runtime-evidence.tar.gz"
        from afterclick.completion_v12.historical import RUNS

        files = [
            p
            for name in RUNS
            for p in (ROOT / "artifacts/research_runs" / name).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        ]
        files += list((p for p in KIT.rglob("*.py") if "__pycache__" not in p.parts)) + list(
            (ROOT / "tests/publication").glob("*.py")
        )
        with tarfile.open(payload, "w:gz") as t:
            for p in files:
                t.add(p, arcname=str(p.relative_to(ROOT)), recursive=False)
        reg = dict(
            scope="CORRECTED_FULL_REGRESSION_NOT_NEW_SCIENTIFIC_TRIAL",
            source_git_revision="2080c426",
            source_archive_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            runtime_archive_sha256=hashlib.sha256(payload.read_bytes()).hexdigest(),
            cpu=[4, 4],
            memory_mib=[8192, 8192],
            sandbox_timeout=1800,
            block_network=True,
            gpu=None,
            correction=(
                "The original data archive omits fixtures/ and generated arti"
                "facts/oecr-web/dist. Full Git source plus locked npm builds "
                "supplies prerequisites, without weakening tests or modifying"
                " frozen runtime."
            ),
            reserve_usd=reserve,
            provider_calls=0,
            model_calls=0,
        )
        save(run / "registration.json", reg)
        base = load(
            ROOT / "artifacts/research_runs/publication-20261126-linux-reproduction-v2/image.json"
        )["image_id"]
        image = (
            modal.Image.from_id(base)
            .add_local_file(source, "/input/source-base.tar.gz", copy=True)
            .run_commands(
                (
                    "mkdir -p /work/afterclick-v12 && tar -xzf /input/source-base"
                    ".tar.gz -C /work/afterclick-v12"
                ),
                "timeout 180 npm install -g node@22.12.0",
                (
                    "cd /work/afterclick-v12 && timeout 300 npm ci --prefix apps/"
                    "flowboard-web && npm run build --prefix apps/flowboard-web"
                ),
                "cd /work/afterclick-v12 && python -m afterclick.oecr.build",
            )
        )
        app = modal.App("afterclick-corrected-linux-regression-20261126", include_source=False)
        with app.run(environment_name="main"):
            save(run / "app.json", dict(app_id=app.app_id))
            image.build(app)
            save(run / "image.json", dict(image_id=image.object_id))
            sandbox = modal.Sandbox.create(
                "sleep",
                "1800",
                app=app,
                image=image,
                cpu=(4, 4),
                memory=(8192, 8192),
                timeout=1800,
                block_network=True,
                include_oidc_identity_token=False,
            )
            save(run / "sandbox.json", dict(sandbox_id=sandbox.object_id, app_id=app.app_id))
            sandbox.filesystem.copy_from_local(payload, "/input/runtime-evidence.tar.gz")
            sandbox.filesystem.copy_from_local(
                KIT / "linux_regression_payload.py", "/input/regression.py"
            )
            process = sandbox.exec("python", "-u", "/input/regression.py", timeout=1600)
            with (run / "stdout.log").open("w") as f:
                for line in process.stdout:
                    f.write(line)
                    f.flush()
                    print(line, end="", flush=True)
            (run / "stderr.log").write_text(process.stderr.read())
            process.wait()
            save(run / "process.json", dict(returncode=process.returncode))
            sandbox.filesystem.copy_to_local("/result-bundle.tar.gz", run / "result-bundle.tar.gz")
            sandbox.terminate(wait=True)
            closed = True
    except Exception as e:
        error = type(e).__name__ + ": " + str(e)
    finally:
        if sandbox and not closed:
            try:
                sandbox.terminate(wait=True)
                closed = True
            except Exception:
                pass
        after = bill("billing-after")
        elapsed = time.monotonic() - started
        guard = max(
            0.25 + elapsed * (4 * 0.1419 + 8 * 0.024) / 3600 * 1.5,
            float(after["metered_cost"]) - float((before or {}).get("metered_cost", 0)),
        )
        if error and not closed:
            guard = max(guard, reserve)
        result = dict(
            error=error,
            closed=closed,
            guard_accounted_usd=guard,
            elapsed_seconds=elapsed,
            cash_billed_usd=float(after["billed_cost"]),
            model_calls=0,
            provider_calls=0,
        )
        save(run / "lifecycle.json", result)
        state = load(KIT / "FINANCE_STATE.json")
        state["runs"].append(dict(run_id=run.name, **result))
        state["guard_accounted_usd"] += guard - reserve
        state["active"] = None
        state["unresolved"] = bool(error and not closed)
        save(KIT / "FINANCE_STATE.json", state)
        print(json.dumps(result), flush=True)
        if error:
            raise RuntimeError(error)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if a.execute:
        main(a.run)
    else:
        print("Explicit --execute required for a finite, CPU-only, at-most-$2-reserved regression.")

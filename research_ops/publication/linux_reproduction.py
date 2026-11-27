"""Explicit finite CPU-only Modal reproduction; requires audited private input."""

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "research_ops/publication"
CLI = str(Path.home() / ".local/bin/modal")
RESERVE = 3.0


def load(p):
    return json.loads(p.read_text())


def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n")


def execute(run):
    import modal

    run.mkdir(parents=True, exist_ok=False)
    state = load(KIT / "FINANCE_STATE.json")
    assert (
        not state["active"]
        and not state["unresolved"]
        and state["guard_accounted_usd"] + RESERVE <= 28
    )
    state["active"] = dict(run_id=run.name, reservation_usd=RESERVE, cpu_only=True)
    state["guard_accounted_usd"] += RESERVE
    save(KIT / "FINANCE_STATE.json", state)
    started = time.monotonic()
    sandbox = None
    error = None
    closed = False
    before = None

    def bill(name):
        p = subprocess.run(
            [CLI, "billing", "summary", "--json", "--profile", "gsankarasubr"],
            capture_output=True,
            text=True,
            timeout=40,
        )
        assert p.returncode == 0
        (run / (name + ".json")).write_text(p.stdout)
        return json.loads(p.stdout)

    try:
        before = bill("billing-before")
        assert float(before["billed_cost"]) == 0
        assert (
            os.environ.get("MODAL_PROFILE") == "gsankarasubr"
            and os.environ.get("MODAL_ENVIRONMENT") == "main"
        )
        requirements = Path("/tmp/afterclick-publication-linux-requirements.txt")
        assert requirements.exists()
        (run / "requirements.txt").write_bytes(requirements.read_bytes())
        image = (
            modal.Image.from_registry("postgres:17.7", add_python="3.11")
            .apt_install("nodejs", "npm", "git", "ca-certificates")
            .pip_install_from_requirements(str(requirements))
            .run_commands("timeout 900 python -m playwright install --with-deps chromium")
        )
        app = modal.App("afterclick-publication-reproduction-20261126", include_source=False)
        with app.run(environment_name="main"):
            image.build(app)
            save(
                run / "image.json",
                dict(
                    image_id=image.object_id,
                    app_id=app.app_id,
                    requirements_sha256=hashlib.sha256(requirements.read_bytes()).hexdigest(),
                ),
            )
            candidate = (
                ROOT
                / "artifacts/publication-release/AfterClick_v12_Public_Evidence_Candidate.tar.gz"
            )
            deadline = started + 1800
            while not candidate.with_suffix(".gz.summary.json").exists():
                if time.monotonic() > deadline:
                    raise TimeoutError("Audited candidate not complete")
                time.sleep(5)
            summary = load(candidate.with_suffix(".gz.summary.json"))
            assert summary["public_upload_performed"] is False
            # Explicit sources only; no home directory, credentials or automatic source mount.
            overlay = run / "publication-source.tar.gz"
            with tarfile.open(overlay, "w:gz") as t:
                for p in sorted((p for p in KIT.rglob("*.py") if "__pycache__" not in p.parts)):
                    t.add(p, arcname=str(p.relative_to(ROOT)))
                t.add(
                    KIT / "protocols/POSTHOC_ANALYSIS_PLAN.md",
                    arcname="research_ops/publication/protocols/POSTHOC_ANALYSIS_PLAN.md",
                )
            registration = dict(
                scope="INDEPENDENT_AUTOMATED_LINUX_REPRODUCTION",
                profile="gsankarasubr",
                environment="main",
                cpu_request_limit=[4, 4],
                memory_mib_request_limit=[8192, 8192],
                gpu=None,
                max_seconds=2400,
                block_network=True,
                no_secrets=True,
                provider_calls=0,
                model_calls=0,
                input_archive=summary,
                source_overlay_sha256=hashlib.sha256(overlay.read_bytes()).hexdigest(),
                not_independent_human_review=True,
            )
            save(run / "registration.json", registration)
            sandbox = modal.Sandbox.create(
                "sleep",
                "2400",
                app=app,
                image=image,
                cpu=(4, 4),
                memory=(8192, 8192),
                timeout=2400,
                block_network=True,
                include_oidc_identity_token=False,
            )
            save(run / "sandbox.json", dict(sandbox_id=sandbox.object_id, app_id=app.app_id))
            sandbox.filesystem.copy_from_local(candidate, "/input/evidence.tar.gz")
            sandbox.filesystem.copy_from_local(
                candidate.with_suffix(".gz.summary.json"), "/input/archive-summary.json"
            )
            sandbox.filesystem.copy_from_local(overlay, "/input/publication-source.tar.gz")
            sandbox.filesystem.copy_from_local(KIT / "linux_payload.py", "/input/linux_payload.py")
            process = sandbox.exec("python", "-u", "/input/linux_payload.py", timeout=2250)
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
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
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
        if not closed:
            guard = max(guard, RESERVE)
        report = dict(
            error=error,
            closed=closed,
            elapsed_seconds=elapsed,
            guard_accounted_usd=guard,
            cash_billed_usd=float(after["billed_cost"]),
            model_calls=0,
            provider_calls=0,
        )
        save(run / "lifecycle.json", report)
        state = load(KIT / "FINANCE_STATE.json")
        state["runs"].append(dict(run_id=run.name, **report))
        state["guard_accounted_usd"] += guard - RESERVE
        state["active"] = None
        state["unresolved"] = not closed
        save(KIT / "FINANCE_STATE.json", state)
        print(json.dumps(report), flush=True)
        if error:
            raise RuntimeError(error)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if a.execute:
        execute(a.run)
    else:
        print(
            (
                "CPU-only network-blocked reproduction; --execute uses a"
                "t most a $3 reservation within the separate $28 cap."
            )
        )

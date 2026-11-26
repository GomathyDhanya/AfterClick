"""Resolve fixed-GPU financial closure while preserving unknown model responses.

This never fabricates a response or retries a trial. A dedicated endpoint charges
GPU wall time, not tokens. After the finite CPU app is stopped, the endpoint is
idle, minimum/buffer are zero, and fresh billing confirms no cash/token charge,
unknown response content does not represent an unbounded future financial call.
The prior reservation and scientific uncertainty remain in the ledger.
"""

import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "research_ops/completion_v12/FINANCE_STATE.json"


def load(p):
    return json.loads(p.read_text())


def cli(args, path):
    with path.open("x") as stream:
        subprocess.run(
            [str(Path.home() / ".local/bin/modal"), *args],
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=40,
        )
    return load(path)


def main(run):
    with (ROOT / "research_ops/SPEND_STATE.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = load(STATE)
        assert state["active"] is None
        if not state["unresolved_request"]:
            print("No unresolved financial lifecycle")
            return
        life = load(run / "lifecycle.json")
        last = state["runs"][-1]
        assert last["run_id"] == run.name and life["min0_restored"]
        readiness_only = (
            life["usage"]["calls"] == 0
            and "Healthy registered model unavailable within bounded startup"
            in (life.get("error") or "")
            and not (run / "raw/api-models.json").exists()
            and not (run / "cloud-execution.log").exists()
        )
        assert life["usage"]["uncertain"] > 0 or readiness_only
        assert life["idle_verified"] or readiness_only
        settings = load(run / "raw/settings-final-min0.json")["current_settings"]
        assert (
            (settings.get("min_containers") or 0) == 0
            and (settings.get("buffer_containers") or 0) == 0
            and settings["max_containers"] == 1
            and settings["scaledown_window"] == 2
        )
        observations = list((run / "raw").glob("containers-after-*.json"))
        assert readiness_only or (observations and any(load(p) == [] for p in observations))
        folder = run / "raw/financial-closure-reconciliation"
        folder.mkdir(exist_ok=False)
        (folder / "ledger-before.json").write_bytes(STATE.read_bytes())
        if not readiness_only:
            prior_app = run / "raw/cpu-app-info.json"
            appid = (
                load(prior_app)["app_id"]
                if prior_app.exists()
                else re.search(
                    r"https://modal.com/apps/[^/]+/main/(ap-[A-Za-z0-9]+)",
                    (run / "cloud-execution.log").read_text(),
                ).group(1)
            )
            app = cli(
                ["app", "info", appid, "--env", "main", "--json"], folder / "cpu-app-stopped.json"
            )
            assert app["lifecycle"]["state"] == "stopped" and app["lifecycle"]["stopped_at"]
        endpoint = load(run / "raw/endpoint.json")
        containers = cli(
            ["container", "list", "--app-id", endpoint["app_id"], "--env", "main", "--json"],
            folder / "endpoint-containers.json",
        )
        assert containers == []
        billing = cli(["billing", "summary", "--json"], folder / "billing.json")
        assert (
            float(billing["billed_cost"]) == 0
            and float(billing["metered_cost_breakdown"]["llm_tokens"]) == 0
        )
        elapsed_upper = last["elapsed_seconds"]
        if not life["idle_verified"]:
            elapsed_upper = max(
                elapsed_upper, time.time() - (run / "raw/paid-start.json").stat().st_mtime
            )
        upper = max(
            elapsed_upper * last["rate_usd_per_second"] * 1.25,
            float(billing["metered_cost"]) - last["metered_before_usd"],
        )
        delta = upper - last["guard_charge_usd"]
        evidence = {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.glob("*.json")
        }
        record = dict(
            run_id=run.name + "-fixed-gpu-financial-closure",
            reserved_usd=0,
            guard_charge_usd=delta,
            usage=dict(calls=0, tokens=0, uncertain=0),
            idle_verified=True,
            parent=run.name,
            scientific_unknown_responses_preserved=life["usage"]["uncertain"],
            original_guard_charge_unchanged=last["guard_charge_usd"],
            reconciled_guard_upper_usd=upper,
            actual_isolated_invoice_usd=None,
            evidence=evidence,
            note="Append-only accounting adjustment after all request producers stopped and dedicated GPU idle; no outcome/usage record overwritten and no generation retried",
        )
        state["runs"].append(record)
        state["account_metered_highwater_usd"] = max(
            state["account_metered_highwater_usd"], float(billing["metered_cost"])
        )
        state["unresolved_request"] = False
        proof = dict(
            financial_lifecycle_closed=True,
            scientific_unknown_responses_preserved=life["usage"]["uncertain"],
            adjustment_usd=delta,
            reconciled_guard_upper_usd=upper,
            no_new_model_calls=True,
            evidence=evidence,
        )
        (folder / "reconciliation.json").write_text(json.dumps(proof, indent=2) + "\n")
        pending = STATE.with_name(STATE.name + ".reconciled.tmp")
        pending.write_text(json.dumps(state, indent=2) + "\n")
        pending.replace(STATE)
        print(json.dumps(proof))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    a = p.parse_args()
    main(a.run.resolve())

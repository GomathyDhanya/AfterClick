"""Finite retrospective inference replay, never a fresh TEST/trajectory experiment."""

import argparse
import concurrent.futures
import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "research_ops/publication"
CLI = str(Path.home() / ".local/bin/modal")
RATE = 0.0012734444444444447
RESERVATION = 2.5


def load(p):
    return json.loads(p.read_text())


def save(p, x):
    p.write_text(json.dumps(x, indent=2) + "\n")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare(run, data):
    run.mkdir(parents=True, exist_ok=False)
    rows = list(csv.DictReader((data / "reviewer-decisions.csv").open()))
    assert len(rows) == 264
    save(
        run / "registration.json",
        dict(
            scope="OPENED_DATA_RETROSPECTIVE_PROMPT_REPLAY",
            fresh_test=False,
            live_actor=False,
            world_execution=False,
            causal_latency_contrast=False,
            enrollment=rows,
            registered=len(rows),
            repeat_per_prompt=1,
            concurrency=8,
            max_seconds=900,
            request_retries=0,
            temperature="unchanged original",
            max_tokens="unchanged original",
            weights_revision=load(KIT / "ENDPOINT.json")["revision"],
            reservation_usd=RESERVATION,
            rationale=(
                "All available original reviewer inputs, without favorab"
                "le selection; serving-stack reproducibility diagnostic "
                "only. No new T12/T13 confirmation or actor competence c"
                "laim."
            ),
            estimand=(
                "Within-input old/new decision agreement, strict schema "
                "and public-rule agreement; requests from the same task "
                "cluster are dependent."
            ),
            missing=(
                "All errors retained; uncertain generation never retried"
                "; missing responses unknown."
            ),
            source_sha256=sha(Path(__file__)),
        ),
    )
    (run / "source.py").write_bytes(Path(__file__).read_bytes())


def execute(run):
    registration = load(run / "registration.json")
    assert registration["source_sha256"] == sha(Path(__file__))
    raw = run / "raw"
    raw.mkdir(exist_ok=False)
    state = load(KIT / "FINANCE_STATE.json")
    assert state["active"] is None and not state["unresolved"]
    assert state["guard_accounted_usd"] + RESERVATION <= 28
    endpoint = load(KIT / "ENDPOINT.json")
    assert endpoint["workspace"] == "gsankarasubr" and endpoint["readiness_verified"]
    state["active"] = dict(run_id=run.name, reservation_usd=RESERVATION)
    state["guard_accounted_usd"] += RESERVATION
    save(KIT / "FINANCE_STATE.json", state)
    started = time.monotonic()
    deadline = started + 900
    results = []
    idle = False
    error = None
    before = None

    def cli(args, label):
        p = subprocess.run(
            [CLI, *args, "--profile", "gsankarasubr"], capture_output=True, text=True, timeout=40
        )
        (raw / (label + ".txt")).write_text(p.stdout + p.stderr)
        if p.returncode:
            raise RuntimeError("Modal control failed: " + label)
        return p.stdout

    def scale(window, label):
        cli(
            [
                "server",
                "autoscaler",
                "update",
                endpoint["server_id"],
                "--env",
                "main",
                "--min-containers",
                "0",
                "--max-containers",
                "1",
                "--buffer-containers",
                "0",
                "--scaledown-window",
                str(window),
            ],
            label,
        )

    try:
        before = json.loads(cli(["billing", "summary", "--json"], "billing-before"))
        assert float(before["billed_cost"]) == 0
        scale(60, "warm-min0")
        credentials = load(Path.home() / ".config/afterclick/gsankarasubr-proxy.json")
        headers = {
            k: v
            for k, v in credentials.items()
            if k in {"Modal-Key", "Modal-Secret", "Authorization"}
        }
        url = endpoint["service_url"].rstrip("/")
        with httpx.Client(headers=headers, trust_env=False, timeout=30) as client:
            ready = False
            while time.monotonic() < deadline - 180:
                try:
                    m = client.get(url + "/v1/models")
                    h = client.get(url + "/health")
                    if m.status_code == h.status_code == 200 and endpoint["model_name"] in {
                        x["id"] for x in m.json()["data"]
                    }:
                        ready = True
                        save(raw / "readiness.json", dict(models=200, health=200, wall=time.time()))
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(3)
            if not ready:
                raise TimeoutError("No ready endpoint inside finite allowance")

            def one(index, row):
                dest = raw / f"{index:04d}"
                dest.mkdir()
                source = ROOT / row["input_path"]
                assert sha(source) == row["input_sha256"]
                body = load(source)["body"]
                body["model"] = endpoint["model_name"]
                save(dest / "input.json", body)
                r = dict(
                    index=index,
                    episode_key=row["episode_key"],
                    original_request_id=row["request_id"],
                    original_decision=row["decision"],
                    public_authority=row["authority"],
                    status="NOT_SENT",
                    schema_valid=False,
                    decision=None,
                    known_tokens=0,
                    start_wall=time.time(),
                )
                if time.monotonic() > deadline - 75:
                    save(dest / "result.json", r)
                    return r
                r["status"] = "INTENT_WRITTEN"
                save(dest / "result.json", r)
                try:
                    response = client.post(url + "/v1/chat/completions", json=body, timeout=60)
                    (dest / "response.txt").write_text(response.text)
                    r["http_status"] = response.status_code
                    r["end_wall"] = time.time()
                    if response.status_code == 200:
                        b = response.json()
                        r["status"] = "RECEIVED"
                        r["known_tokens"] = (b.get("usage") or {}).get("total_tokens", 0)
                        try:
                            p = json.loads(b["choices"][0]["message"]["content"])
                            valid = (
                                isinstance(p, dict)
                                and set(p) == {"decision", "reason"}
                                and p["decision"] in {"allow", "cancel", "suspend"}
                                and isinstance(p["reason"], str)
                            )
                            r.update(
                                schema_valid=valid, decision=p.get("decision") if valid else None
                            )
                        except (KeyError, ValueError, TypeError):
                            pass
                    else:
                        r["status"] = "HTTP_ERROR"
                except httpx.HTTPError as exc:
                    r.update(
                        status="RESPONSE_UNKNOWN", error=type(exc).__name__, end_wall=time.time()
                    )
                save(dest / "result.json", r)
                return r

            with concurrent.futures.ThreadPoolExecutor(8) as pool:
                futures = [
                    pool.submit(one, i, row) for i, row in enumerate(registration["enrollment"])
                ]
                for f in concurrent.futures.as_completed(futures):
                    r = f.result()
                    results.append(r)
                    if len(results) % 32 == 0:
                        print(json.dumps(dict(terminal=len(results), registered=264)), flush=True)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        try:
            scale(2, "final-min0")
            for i in range(12):
                containers = json.loads(
                    cli(
                        [
                            "container",
                            "list",
                            "--app-id",
                            endpoint["app_id"],
                            "--env",
                            "main",
                            "--json",
                        ],
                        f"containers-{i}",
                    )
                )
                if containers == []:
                    idle = True
                    break
                time.sleep(3)
            if not idle:
                cli(["app", "stop", endpoint["app_id"], "--env", "main", "--yes"], "owned-app-stop")
                idle = (
                    json.loads(
                        cli(
                            ["app", "info", endpoint["app_id"], "--env", "main", "--json"],
                            "owned-app-closure",
                        )
                    )["lifecycle"]["state"]
                    == "stopped"
                )
        except Exception as exc:
            error = (error or "") + "; cleanup " + type(exc).__name__
        after = json.loads(cli(["billing", "summary", "--json"], "billing-after"))
        elapsed = time.monotonic() - started
        uncertain = sum(r["status"] == "RESPONSE_UNKNOWN" for r in results)
        guard = max(
            elapsed * RATE * 1.25,
            max(0, float(after["metered_cost"]) - float((before or {}).get("metered_cost", 0))),
        )
        if uncertain or not idle:
            guard = max(RESERVATION, guard)
        decisions = {
            d: sum(r["decision"] == d for r in results)
            for d in ["allow", "suspend", "cancel", None]
        }
        report = dict(
            registered=264,
            terminal=len(results),
            attempted=sum(r["status"] != "NOT_SENT" for r in results),
            received=sum(r["status"] == "RECEIVED" for r in results),
            unknown=uncertain,
            strict_json=sum(r["schema_valid"] for r in results),
            decisions=decisions,
            original_decision_agreements=sum(
                r["schema_valid"] and r["decision"] == r["original_decision"] for r in results
            ),
            public_rule_agreements=sum(
                r["schema_valid"]
                and r["decision"] == ("allow" if r["public_authority"] == "approved" else "suspend")
                for r in results
            ),
            known_tokens=sum(r["known_tokens"] for r in results),
            error=error,
            idle_verified=idle,
            elapsed_seconds=elapsed,
            guard_accounted_usd=guard,
            cash_billed_usd=float(after["billed_cost"]),
            complete=len(results) == 264,
            not_fresh_test=True,
            not_live_trajectory=True,
        )
        save(run / "report.json", report)
        state = load(KIT / "FINANCE_STATE.json")
        state["runs"].append(dict(run_id=run.name, **report))
        state["guard_accounted_usd"] += guard - RESERVATION
        state["active"] = None
        state["unresolved"] = bool(uncertain or not idle)
        save(KIT / "FINANCE_STATE.json", state)
        print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--data", type=Path)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if a.execute:
        execute(a.run)
    else:
        prepare(a.run, a.data)

"""Finite, authenticated endpoint readiness; setup calls are not research trials.

An existing launch intent and a separate workspace-specific reservation are
required. Never resumes the opened v12 protocol or retries model generation.
"""

import argparse
import json
import subprocess
import time
from pathlib import Path

from research_ops.scripts.p1_diagnostic import resource_estimate

ROOT = Path(__file__).resolve().parents[2]
CLI = str(Path.home() / ".local/bin/modal")
KIT = ROOT / "research_ops/publication"


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def execute(run, attempt=0):
    run = run.resolve()
    protocol = read(run / "protocol.json")
    profile = protocol["profile"]
    assert profile == protocol["workspace"] == "gsankarasubr"
    assert protocol["environment"] == "main"
    assert protocol["max_model_calls"] == 2
    assert read(run / "creation-success.json").get("returncode") == 0
    ledger = read(KIT / "FINANCE_STATE.json")
    if attempt:
        # The first attempt met a control-plane provisioning record with no
        # App/Server/URL yet. It made zero model calls. Preserve that failed
        # attempt and keep its existing reservation, rather than double-charge.
        previous_path = run / (
            "READINESS.json" if attempt == 1 else f"READINESS-{attempt - 1:02d}.json"
        )
        previous = read(previous_path)
        assert attempt in {1, 2} and previous["calls"] == 0
        assert (
            previous["error"].startswith("TypeError:")
            or previous["error"]
            == "TimeoutError: Endpoint control plane did not expose a Server and URL"
        )
        assert ledger["active"] is None
        ledger["active"] = dict(run_id=run.name, continuation_of_zero_call_provisioning=True)
        save(KIT / "FINANCE_STATE.json", ledger)
    assert ledger["active"]["run_id"] == run.name
    controls = read(KIT / "FINANCIAL_CONTROLS.json")
    assert controls["workspace_usage_limit_usd"] == 28
    assert controls["effective_net_spend_limit_usd"] == 0
    raw = run / ("readiness" if not attempt else f"readiness-{attempt:02d}")
    raw.mkdir(exist_ok=False)
    started = time.monotonic()
    calls = 0
    tokens = 0
    uncertain = 0
    ready = False
    idle = False
    error = None
    rate = 0
    endpoint = None
    server = None

    def cli(args, name, timeout=40):
        result = subprocess.run(
            [CLI, *args, "--profile", profile],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
        (raw / name).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError("Modal control request failed: " + name)
        return result.stdout

    def scale(window, label):
        cli(
            [
                "server",
                "autoscaler",
                "update",
                server,
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
            label + ".txt",
        )
        settings = json.loads(
            cli(
                ["server", "autoscaler", "settings", server, "--env", "main", "--json"],
                label + ".json",
            )
        )["current_settings"]
        assert (settings.get("min_containers") or 0) == 0
        assert settings["max_containers"] == 1
        assert (settings.get("buffer_containers") or 0) == 0
        assert settings["scaledown_window"] == window

    def request(path, label, payload=None):
        nonlocal calls, tokens, uncertain
        body = raw / (label + "-body.json")
        args = [
            CLI,
            "curl",
            "--profile",
            profile,
            "--silent",
            "--show-error",
            "--connect-timeout",
            "10",
            "--max-time",
            "40",
            "--output",
            str(body),
            "--write-out",
            "%{http_code}",
        ]
        if payload is not None:
            assert ready, "Generation is forbidden before models and health pass"
            assert calls < protocol["max_model_calls"]
            request_file = raw / (label + "-input.json")
            save(request_file, payload)
            args += [
                "-H",
                "Content-Type: application/json",
                "--data-binary",
                "@" + str(request_file),
            ]
            calls += 1
            save(raw / "usage.json", dict(calls=calls, tokens=tokens, uncertain=uncertain))
        args.append(endpoint["service_url"].rstrip("/") + path)
        begin = time.time()
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=50)
            status = int(result.stdout.strip()[-3:]) if result.stdout.strip()[-3:].isdigit() else 0
            text = body.read_text() if body.exists() else ""
            data = json.loads(text) if text.strip().startswith(("{", "[")) else None
            save(
                raw / (label + "-transport.json"),
                dict(
                    start_wall=begin,
                    end_wall=time.time(),
                    status=status,
                    returncode=result.returncode,
                    stderr=result.stderr,
                    model_generation=payload is not None,
                ),
            )
            if payload is not None:
                if status == 200 and isinstance(data, dict) and data.get("choices"):
                    tokens += (data.get("usage") or {}).get("total_tokens", 0)
                elif not status or result.returncode:
                    uncertain += 1
            return status, data
        except (subprocess.TimeoutExpired, ValueError) as exc:
            if payload is not None:
                uncertain += 1
            save(
                raw / (label + "-transport.json"),
                dict(
                    start_wall=begin,
                    end_wall=time.time(),
                    error=type(exc).__name__,
                    model_generation=payload is not None,
                ),
            )
            return 0, None

    try:
        control_deadline = started + 600
        i = 0
        while time.monotonic() < control_deadline:
            endpoint = json.loads(
                cli(
                    ["endpoint", "info", protocol["endpoint_name"], "--env", "main", "--json"],
                    f"endpoint-{i:02d}.json",
                )
            )
            if all(endpoint.get(key) for key in ["server_id", "app_id", "service_url"]):
                break
            time.sleep(5)
            i += 1
        else:
            raise TimeoutError("Endpoint control plane did not expose a Server and URL")
        assert endpoint["repo_id"] == protocol["model"]
        assert endpoint["revision"] == protocol["revision"]
        assert endpoint["requires_proxy_auth"] is True
        assert endpoint["environment_name"] == "main"
        server = endpoint["server_id"]
        resources = json.loads(
            cli(
                ["server", "info", server, "--env", "main", "--json"],
                "server.json",
            )
        )
        resources.update(
            min_containers=0, max_containers=1, buffer_containers=0, scaledown_window=2
        )
        estimate = resource_estimate(resources, read(run / "billing-rates.json"))
        rate = estimate["usd_per_second_estimate"]
        save(raw / "resource-estimate.json", estimate)
        # Reserve cleanup and control-plane time; never hold a positive minimum.
        work_seconds = min(
            protocol["maximum_startup_seconds"],
            protocol["setup_reservation_usd"] / (rate * 1.25) - 150,
        )
        assert work_seconds >= 120
        deadline = started + work_seconds
        scale(60, "warm-min0")
        index = 0
        while time.monotonic() < deadline - 70:
            status, data = request("/v1/models", f"models-{index:03d}")
            if status == 200 and isinstance(data, dict):
                names = {item["id"] for item in data.get("data", [])}
                if endpoint["model_name"] in names:
                    health, _ = request("/health", f"health-{index:03d}")
                    if health == 200:
                        ready = True
                        break
            index += 1
            time.sleep(min(10, max(0, deadline - time.monotonic() - 70)))
        if not ready:
            raise TimeoutError("No healthy pinned model within finite startup allowance")
        save(raw / "data-plane-ready.json", dict(wall=time.time(), models_ok=True, health_ok=True))
        nonce = "afterclick-readiness-20261126"
        messages = [
            dict(
                role="system",
                content=(
                    "This is a tool API readiness test, not a business task. "
                    "First call readiness_probe "
                    "exactly once with the requested nonce. "
                    "After its successful tool result, reply "
                    "exactly READY. Do not call any other tool."
                ),
            ),
            dict(role="user", content="Run readiness_probe with nonce " + nonce),
        ]
        payload = dict(
            model=endpoint["model_name"],
            messages=messages,
            temperature=0,
            max_tokens=128,
            chat_template_kwargs=dict(enable_thinking=False),
            tools=[
                dict(
                    type="function",
                    function=dict(
                        name="readiness_probe",
                        description="A read-only local readiness probe.",
                        parameters=dict(
                            type="object",
                            properties=dict(nonce=dict(type="string")),
                            required=["nonce"],
                            additionalProperties=False,
                        ),
                    ),
                )
            ],
            tool_choice="auto",
        )
        status, result = request("/v1/chat/completions", "native-tool-call", payload)
        assert status == 200 and result.get("choices"), "Native generation failed; not retried"
        message = result["choices"][0]["message"]
        tools = message.get("tool_calls", [])
        assert len(tools) == 1 and tools[0]["function"]["name"] == "readiness_probe"
        assert json.loads(tools[0]["function"]["arguments"]) == dict(nonce=nonce)
        tool_result = dict(
            role="tool", tool_call_id=tools[0]["id"], content=json.dumps(dict(ok=True, nonce=nonce))
        )
        save(raw / "executed-local-readiness-tool.json", tool_result)
        payload["messages"] = [*messages, message, tool_result]
        status, result = request("/v1/chat/completions", "native-tool-continuation", payload)
        assert status == 200 and result.get("choices"), "Continuation failed; not retried"
        assert (result["choices"][0]["message"].get("content") or "").strip() == "READY"
        save(
            KIT / "ENDPOINT.json",
            {
                **endpoint,
                "workspace": profile,
                "readiness_verified": True,
                "comparison_scope": (
                    "Same pinned primary weights; managed serving stack recorded separately"
                ),
                "new_research_trials_executed": 0,
            },
        )
    except BaseException as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        cleanup_error = None
        try:
            if server:
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
                            f"containers-final-{i:02d}.json",
                        )
                    )
                    if containers == []:
                        idle = True
                        break
                    time.sleep(3)
                if error or not idle:
                    cli(
                        ["app", "stop", endpoint["app_id"], "--env", "main", "--yes"],
                        "owned-failed-app-stopped.txt",
                    )
                    stopped = json.loads(
                        cli(
                            ["app", "info", endpoint["app_id"], "--env", "main", "--json"],
                            "owned-app-closure.json",
                        )
                    )
                    idle = stopped["lifecycle"]["state"] == "stopped"
        except BaseException as exc:
            cleanup_error = type(exc).__name__ + ": " + str(exc)
        billing = json.loads(cli(["billing", "summary", "--json"], "billing-after.json"))
        elapsed = time.monotonic() - started
        guard = max(elapsed * rate * 1.25, float(billing["metered_cost"]))
        if not idle or uncertain or cleanup_error:
            guard = max(guard, protocol["setup_reservation_usd"])
        final = dict(
            data_plane_ready=ready,
            native_tool_roundtrip_passed=ready and error is None,
            calls=calls,
            known_reported_tokens=tokens,
            response_uncertain=uncertain,
            research_trials=0,
            setup_only=True,
            idle_verified=idle,
            elapsed_seconds=elapsed,
            guard_accounted_usd=guard,
            cash_billed_usd=float(billing["billed_cost"]),
            error=error,
            cleanup_error=cleanup_error,
        )
        save(run / ("READINESS.json" if not attempt else f"READINESS-{attempt:02d}.json"), final)
        state = read(KIT / "FINANCE_STATE.json")
        prior = sum(
            row["guard_accounted_usd"]
            for row in state["runs"]
            if row["run_id"].startswith(run.name)
        )
        delta = guard - prior
        state["runs"].append(
            dict(
                run_id=run.name + (f"-continuation-{attempt:02d}" if attempt else ""),
                **{**final, "guard_accounted_usd": delta},
                total_setup_guard_usd=guard,
                original_attempts_unchanged=True,
            )
        )
        state["guard_accounted_usd"] += delta
        state["active"] = None
        state["unresolved"] = bool(cleanup_error or not idle or uncertain)
        save(KIT / "FINANCE_STATE.json", state)
        print(json.dumps(final), flush=True)
        if error or cleanup_error or not idle:
            raise RuntimeError("Endpoint setup did not fully pass; inspect READINESS.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--attempt", type=int, default=0)
    args = parser.parse_args()
    if args.execute:
        execute(args.run, args.attempt)
    else:
        print(json.dumps(read(args.run / "protocol.json"), indent=2))

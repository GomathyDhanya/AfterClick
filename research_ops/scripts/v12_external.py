"""Execute frozen official UndoBench assignments using a capped native transport.

The upstream engine, public prompts, tools, tasks and oracle are unmodified.
Default invocation only inspects the registration; paid execution needs an active
credit lifecycle. External mocked-service semantics remain separately scoped.
"""

import argparse
import concurrent.futures
import json
import threading
import time
import traceback
from pathlib import Path

from afterclick.completion_v12.benchmark.transport import Transport, save


def run(args):
    registration = json.loads((args.run / "external-registration.json").read_text())
    if not args.execute:
        print(json.dumps(dict(registered=len(registration["episodes"]), paid_launched=False)))
        return
    assert (args.run / "raw/paid-start.json").exists(), "No admitted paid lifecycle"
    assert registration["mode"] in {"DEV_OFFICIAL_EXTERNAL", "FROZEN_OFFICIAL_EXTERNAL"}
    if registration["mode"] == "FROZEN_OFFICIAL_EXTERNAL":
        from afterclick.completion_v12.evidence import sha

        assert sha(Path(registration["freeze_path"])) == registration["freeze_sha256"]
    from recoverbench.engine import BenchmarkEngine, RunConfig

    from afterclick.review.undobench_adapter import AfterClickQwenAgent

    deadline = time.monotonic() + max(0, args.deadline_utc - time.time())
    transport = Transport(
        args.run / "external-model-traces",
        args.service_url,
        args.model_name,
        deadline=deadline,
        max_calls=args.max_calls,
        concurrency=registration["concurrency"],
    )
    lock = threading.Lock()
    rows = []

    def execute(cell):
        folder = args.run / "external-episodes" / cell["episode_id"]
        folder.mkdir(parents=True, exist_ok=False)
        save(folder / "specification.json", cell)
        request_ids = []

        def complete(body):
            payload = {
                k: v
                for k, v in body.items()
                if k not in {"model", "temperature", "max_tokens", "chat_template_kwargs"}
            }
            _, request = transport.generate(cell["episode_id"], "official-external-actor", payload)
            request_ids.append(request)
            return json.loads(
                json.loads((transport.directory / (request + "-output.json")).read_text())["raw"]
            )

        try:
            config = RunConfig(
                run_id=cell["episode_id"],
                output_dir=str(folder / "official"),
                recovery=cell["method"],
                seeds=[cell["seed"]],
                allow_frozen_test_execution=cell["split"] == "test",
            )
            engine = BenchmarkEngine(config)
            agent = AfterClickQwenAgent(
                transport=complete, journal=folder / "agent.jsonl", max_calls=10
            )
            trajectory = engine.execute_single_condition(
                task_id=cell["task_id"],
                condition=cell["condition"],
                seed=cell["seed"],
                pair_id=cell["pair_id"],
                agent=agent,
                recovery_method_name=cell["method"],
            )
            (folder / "official-trajectory.json").write_text(trajectory.to_json() + "\n")
            data = json.loads(trajectory.to_json())
            result = dict(
                **cell,
                status="EXECUTED",
                model_requests=request_ids,
                official_verdict=data["benchmark_hidden_trace"]["oracle_verdict"],
            )
        except Exception:
            result = dict(
                **cell, status="INVALID", model_requests=request_ids, error=traceback.format_exc()
            )
        save(folder / "result.json", result)
        with lock:
            rows.append(result)
            save(
                args.run / "external-usage.json",
                dict(calls=transport.calls, tokens=transport.tokens, uncertain=transport.uncertain),
            )
            with (args.run / "external-execution.jsonl").open("a") as stream:
                stream.write(json.dumps(result) + "\n")
        print(json.dumps({k: result[k] for k in ["episode_id", "status"]}), flush=True)

    cells = iter(registration["episodes"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=registration["concurrency"]) as pool:
        active = set()
        while True:
            while len(active) < registration["concurrency"] and time.monotonic() + 45 < deadline:
                cell = next(cells, None)
                if cell is None:
                    break
                active.add(pool.submit(execute, cell))
            if not active:
                break
            done, active = concurrent.futures.wait(
                active, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                future.result()
    actual = {r["episode_id"] for r in rows}
    save(
        args.run / "external-usage.json",
        dict(calls=transport.calls, tokens=transport.tokens, uncertain=transport.uncertain),
    )
    save(
        args.run / "external-reconciliation.json",
        dict(
            registered=len(registration["episodes"]),
            terminal=len(rows),
            not_run=[
                c["episode_id"] for c in registration["episodes"] if c["episode_id"] not in actual
            ],
            complete=len(rows) == len(registration["episodes"]),
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--service-url")
    p.add_argument("--model-name")
    p.add_argument("--deadline-utc", type=float)
    p.add_argument("--max-calls", type=int, default=0)
    run(p.parse_args())

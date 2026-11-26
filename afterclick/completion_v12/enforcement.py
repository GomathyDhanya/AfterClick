"""Registered fixed-recommendation actuator experiment on complete DEV workflows.

No LLM, hidden-state controller, or historical time subtraction. Independent
workers progress during each actual randomized delay and reference continuation.
"""

import argparse
import json
import multiprocessing
import random
import shutil
import time
import traceback
import uuid
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

from afterclick.completion_v12.benchmark.browser import Browser
from afterclick.completion_v12.benchmark.flow import FlowWorld
from afterclick.completion_v12.benchmark.ops import OpsWorld
from afterclick.completion_v12.benchmark.oracle import evaluate
from afterclick.completion_v12.benchmark.qualification import reference
from afterclick.completion_v12.benchmark.runner import certify_source
from afterclick.completion_v12.benchmark.transport import save
from afterclick.completion_v12.evidence import digest, sha


def one(argument):
    registration, cell, output = argument
    output = Path(output)
    directory = output / "episodes" / cell["episode_id"]
    directory.mkdir(parents=True, exist_ok=False)
    save(directory / "specification.json", cell)
    contract = json.loads(Path(registration["contracts"][cell["task_id"]]["path"]).read_text())
    world = gateway = None
    result = dict(**cell, status="INVALID", model_calls=0)
    try:
        cls = FlowWorld if contract["application"] == "flowboard" else OpsWorld
        world = cls(contract, seed=cell["world_seed"], admission_ms=cell["admission_ms"])
        world.initialize()
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            with world.serve() as origin:
                page = browser.new_page()
                gateway = Browser(page, origin, contract["application"])
                cut = dict(
                    database=world.snapshot(),
                    public=gateway.observe(),
                    client=gateway.client_cut(),
                    contract_sha256=digest(contract),
                    schedule=dict(
                        seed=world.seed,
                        admission_ms=world.admission_ms,
                        effect_lag_ms=world.effect_lag_ms,
                        evidence_ms=world.evidence_ms,
                        collaborator_ms=world.collaborator_ms,
                        clean=False,
                    ),
                )
                save(directory / "source-cut.json", cut)
                cert = certify_source(output / "episodes", cell, cut)
                save(directory / "source-certificate.json", cert)
                if not cert["valid"]:
                    raise ValueError("Actuator sibling reconstruction mismatch")
                # Same public recommendation is already available before random
                # gateway delay. It is not generated from a hidden label.
                assert gateway.observe()["service"]["authority"] != "approved"
                recommendation = dict(
                    decision="suspend",
                    reason="Public authority unresolved or prohibited",
                    wall=time.time(),
                    mono=time.monotonic(),
                )
                save(directory / "recommendation.json", recommendation)
                world.start()
                gateway.start_polling()
                start = dict(wall=time.time(), mono=time.monotonic(), anchor_mono=world.anchor)
                page.wait_for_timeout(cell["gateway_delay_ms"])
                issued = dict(wall=time.time(), mono=time.monotonic())
                if cell["gateway"] == "direct_http":
                    body = dict(id="suspend", value="", version=0, operation_id=str(uuid.uuid4()))
                    response = httpx.post(
                        origin + "/api/v12/act", json=body, timeout=15, trust_env=False
                    )
                    response.raise_for_status()
                    control = dict(
                        status=response.status_code, result=response.json(), request=body
                    )
                    page.evaluate("refresh()")
                    page.wait_for_function("!busy && activeRefreshes===0")
                else:
                    control = gateway.act("suspend")
                returned = dict(wall=time.time(), mono=time.monotonic())
                save(
                    directory / "enforcement.json",
                    dict(
                        start=start,
                        issued=issued,
                        returned=returned,
                        control=control,
                        semantics="Response is an upper bound after enforcement transaction commit",
                    ),
                )
                reference(gateway, deadline=time.monotonic() + 120)
                page.wait_for_timeout(400)
                world.finish()
                final = world.snapshot()
                score = evaluate(contract, final, world.errors)
                save(directory / "final.json", final)
                result.update(
                    status=score["status"],
                    score=score,
                    issue_from_anchor_ms=(issued["mono"] - world.anchor) * 1000,
                    response_upper_from_anchor_ms=(returned["mono"] - world.anchor) * 1000,
                )
                page.close()
            browser.close()
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        if gateway:
            save(directory / "browser-actions.json", gateway.history)
            save(directory / "browser-network.json", gateway.network)
        if world:
            try:
                world.finish()
                save(directory / "worker-errors.json", world.errors)
                if not (directory / "final.json").exists():
                    save(directory / "failed-snapshot.json", world.snapshot())
                world.db.drop_experiment()
            except Exception:
                result["cleanup_error"] = traceback.format_exc()
    save(directory / "result.json", result)
    return {k: result.get(k) for k in ["episode_id", "status", "error"]}


def execute(contracts, output, workers):
    output.mkdir(parents=True, exist_ok=False)
    selected = [p for p in sorted(contracts.glob("DEV-*-L3-*-02.json"))]
    assert len(selected) == 12
    tasks = {p.stem: dict(path=str(p.resolve()), sha256=sha(p)) for p in selected}
    cells = []
    for index, path in enumerate(selected):
        for replicate in range(2):
            for regime, admission in enumerate([150, 600, 1800]):
                seed = 620000 + index * 97 + replicate * 7 + regime
                for gateway, delay in [
                    ("direct_http", 0),
                    ("browser", 0),
                    ("browser", 300),
                    ("browser", 1500),
                ]:
                    cells.append(
                        dict(
                            episode_id=f"{path.stem}-{replicate}-{admission}-{gateway}-{delay}",
                            task_id=path.stem,
                            world_seed=seed,
                            admission_ms=admission,
                            clean=False,
                            gateway=gateway,
                            gateway_delay_ms=delay,
                            replicate=replicate,
                        )
                    )
    random.Random(6112521).shuffle(cells)
    registration = dict(
        mode="DEV_FIXED_RECOMMENDATION_CAUSAL_ACTUATOR_STUDY",
        contracts=tasks,
        episodes=cells,
        model_calls=0,
        registered=len(cells),
        workers=workers,
        recommendation="Suspend for unresolved/prohibited public authorization before randomized delay",
        source_sha256=sha(Path(__file__)),
        inference_scope="Actuator and eligibility effects; no claim of LLM decision latency causation",
    )
    save(output / "registration.json", registration)
    archive = output / "source-archive"
    archive.mkdir()
    for path in [
        Path(__file__),
        *Path("afterclick/completion_v12/benchmark").glob("*.py"),
        *Path("afterclick/completion_v12/benchmark").glob("*.html"),
    ]:
        shutil.copyfile(path, archive / path.name)
    with multiprocessing.get_context("spawn").Pool(workers) as pool:
        for row in pool.imap_unordered(one, [(registration, cell, str(output)) for cell in cells]):
            with (output / "execution.jsonl").open("a") as stream:
                stream.write(json.dumps(row) + "\n")
            print(json.dumps(row), flush=True)
    actual = [json.loads(p.read_text()) for p in (output / "episodes").glob("*/result.json")]
    save(
        output / "reconciliation.json",
        dict(
            registered=len(cells),
            terminal=len(actual),
            valid=sum(r["status"] == "VALID" for r in actual),
            model_calls=0,
            complete=len(actual) == len(cells),
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contracts", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    execute(a.contracts, a.output, a.workers)

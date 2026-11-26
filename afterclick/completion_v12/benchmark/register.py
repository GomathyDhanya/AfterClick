"""Create immutable finite DEV jobs; never registers TEST without a full freeze gate."""

import argparse
import json
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

from afterclick.completion_v12.benchmark.transport import save
from afterclick.completion_v12.evidence import digest, sha

MODEL = "Qwen/Qwen3.5-9B"
REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"


def development(contracts, output, qualification):
    output.mkdir(parents=True, exist_ok=False)
    all_dev = [json.loads(p.read_text()) for p in sorted(contracts.glob("DEV-*.json"))]
    families = sorted({c["family"] for c in all_dev})
    selected = [
        c
        for c in all_dev
        if c["task_id"].endswith("-01")
        and c["complexity"] == f"L{families.index(c['family']) % 3 + 1}"
    ]
    assert len(selected) == 12
    tasks, cells, qualified = {}, [], []
    for index, contract in enumerate(selected):
        identifier = contract["task_id"]
        path = contracts / (identifier + ".json")
        tasks[identifier] = dict(path=str(path.resolve()), digest=digest(contract))
        evidence = qualification / identifier / "qualification.json"
        if evidence.exists():
            report = json.loads(evidence.read_text())
            if report["status"] == "REFERENCE_QUALIFIED" and report["contract_sha256"] == sha(path):
                qualified.append(identifier)
        order = ["P0", "P2", "P3"]
        random.Random(61125 + index).shuffle(order)
        for policy in order:
            cells.append(
                dict(
                    episode_id=f"{identifier}-{policy}-dev-engineering",
                    task_id=identifier,
                    policy=policy,
                    world_seed=99000 + index,
                    admission_ms=3000 if policy == "P0" else [500, 2000, 8000][index % 3],
                    clean=policy == "P0",
                    timing_regime="clean"
                    if policy == "P0"
                    else ["tight", "intermediate", "generous"][index % 3],
                    replicate=0,
                )
            )
    registration = dict(
        schema_version=1,
        mode="DEV_ENGINEERING_NOT_TEST",
        utc=datetime.now(timezone.utc).isoformat(),
        contracts=tasks,
        episodes=cells,
        model_concurrency=4,
        environment_concurrency=4,
        limits=dict(
            max_actor_calls=14, max_browser_actions=160, episode_seconds=180, settlement_seconds=1.5
        ),
        qualification_root=str(qualification.resolve()),
        selection="One variant per app/family; complexity rotates by sorted family before outcomes",
        fixed_task_count=12,
        fixed_episode_count=36,
        outcome_dependent_stopping=False,
        http_retries=0,
    )
    save(output / "registration.json", registration)
    source = {
        str(p): sha(p)
        for p in Path("afterclick/completion_v12/benchmark").iterdir()
        if p.suffix in {".py", ".html"}
    }
    paid = dict(
        schema_version=1,
        endpoint_id="ep-Lqp751voQWfhhoZTNXD4Yf",
        model=MODEL,
        revision=REVISION,
        registration_sha256=sha(output / "registration.json"),
        source_hashes=source,
        total_seconds=900,
        startup_seconds=270,
        max_usd=1.6,
        max_calls=36 * 14 + 12,
        no_cash=True,
        no_automatic_paid_retries=True,
    )
    save(output / "paid-protocol.json", paid)
    (output / "raw").mkdir()
    shutil.copyfile(
        "research_ops/completion_v12/FINANCIAL_CONTROLS.json",
        output / "raw/financial-controls.json",
    )
    save(
        output / "readiness-at-registration.json",
        dict(
            qualified=qualified,
            unqualified=[c["task_id"] for c in selected if c["task_id"] not in qualified],
            paid_launched=False,
            test_opened=False,
        ),
    )
    print(
        json.dumps(
            dict(
                registered=len(cells),
                qualified=len(qualified),
                selected_tasks=len(selected),
                mode=registration["mode"],
            )
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    args = parser.parse_args()
    development(args.contracts, args.output, args.qualification)

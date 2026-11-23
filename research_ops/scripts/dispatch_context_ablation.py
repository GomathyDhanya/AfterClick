"""Development-only post-confirmation context-matched acquisition diagnostic."""

import json
import random
import time
from pathlib import Path

import joblib
import numpy as np

from afterclick.agent.modal_policy import atomic_json
from afterclick.extensions.dispatch_learning import fit
from afterclick.extensions.dispatch_world import generate, label_panel
from afterclick.extensions.observability_study import bootstrap, generate_visible, predictor


def main(run=None):
    run = run or Path("artifacts/research_runs/o4-context-ablation-v1")
    dev = Path("artifacts/research_runs/o1-observability-development-v1")
    if (run / "raw/started.json").exists():
        raise ValueError("Fresh run required")
    atomic_json(run / "raw/started.json", dict(started=True))
    start = time.monotonic()
    validation = [json.loads(s) for s in (dev / "raw/validation.jsonl").read_text().splitlines()]
    result = []
    deltas = {}
    for original in ["boundary", "uncertainty_boundary"]:
        for repeat in range(4):
            if time.monotonic() - start > 300:
                raise TimeoutError("Bounded diagnostic")
            source = [
                json.loads(s)
                for s in (dev / "raw" / f"training-{original}-{repeat}.jsonl")
                .read_text()
                .splitlines()
            ]
            ids = sorted({r["metadata"]["source"] for r in source})
            assert len(ids) == 16
            rng = random.Random(22071 + repeat)
            rows = []
            for id in ids:
                i = generate(id)
                for j in range(16):
                    h = rng.randrange(201)
                    k = len(rows)
                    row = dict(
                        features=i.visible(h).model_dump(),
                        outcomes=label_panel(i, h),
                        measurement=("UNKNOWN" if k % 128 == 0 else "CENSORED")
                        if k % 64 == 0
                        else "KNOWN",
                        metadata=dict(
                            source=id,
                            event_time=i.frontier if i.unsafe and i.frontier <= h else None,
                            censor_time=h,
                        ),
                    )
                    rows.append(row)
                    with (run / "trials.jsonl").open("a") as f:
                        f.write(json.dumps(dict(original=original, repeat=repeat, **row)) + "\n")
            matched = fit(rows, repeat)
            joblib.dump(
                matched, run / "raw" / f"models-random-{original}-{repeat}.joblib", compress=3
            )
            old = joblib.load(dev / "raw" / f"models-{original}-{repeat}.joblib")
            for model in ["discrete_hazard", "gradient_boosting"]:
                a, b = predictor(matched, model), predictor(old, model)
                errors_a = np.array(
                    [
                        (a(generate_visible(r["features"]))[1] - r["outcomes"][1]) ** 2
                        for r in validation
                    ]
                )
                errors_b = np.array(
                    [
                        (b(generate_visible(r["features"]))[1] - r["outcomes"][1]) ** 2
                        for r in validation
                    ]
                )
                result.append(
                    dict(
                        original=original,
                        repeat=repeat,
                        model=model,
                        source_contexts=16,
                        panels=256,
                        random_time_brier=float(errors_a.mean()),
                        boundary_brier=float(errors_b.mean()),
                    )
                )
                deltas.setdefault((original, model), []).append(errors_a - errors_b)
    metrics = dict(
        schema_version=1,
        passed=True,
        panels=2048,
        potential_world_evaluations=4096,
        known=2016,
        unknown=16,
        censored=16,
        rows=result,
        differences={a + "_" + m: bootstrap(np.mean(v, axis=0)) for (a, m), v in deltas.items()},
        elapsed_seconds=time.monotonic() - start,
        cost_usd=0,
        model_calls=0,
        scope="post-confirmation development-only; no final outcomes accessed or models replaced",
    )
    atomic_json(run / "metrics.json", metrics)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        import os
        from urllib.parse import urlsplit

        if urlsplit(os.environ.get("DATABASE_URL", "postgresql://127.0.0.1")).hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ValueError("Local test PostgreSQL only")
        args.output.mkdir(parents=True, exist_ok=False)
        for directory in ["raw", "figures"]:
            (args.output / directory).mkdir()
        for file in ["trials.jsonl", "model_calls.jsonl", "oracle_certificates.jsonl"]:
            (args.output / file).touch()
        source = Path("artifacts/research_runs/o4-context-ablation-v1")
        (args.output / "protocol.json").write_bytes((source / "protocol.json").read_bytes())
        atomic_json(
            args.output / "manifest.json",
            dict(
                schema_version=1,
                mode="known_protocol_reproduction",
                original_run="o4-context-ablation-v1",
                cost_usd=0,
            ),
        )
    try:
        main(args.output)
    except BaseException:
        import traceback

        out = args.output or Path("artifacts/research_runs/o4-context-ablation-v1")
        if args.output:
            (out / "raw/error.txt").write_text(traceback.format_exc())
            with (out / "trials.jsonl").open("a") as f:
                f.write(json.dumps(dict(event="crashed_or_interrupted")) + "\n")
        raise

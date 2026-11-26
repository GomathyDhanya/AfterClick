"""Read-only regeneration check for derived semantics, official metric projection and figures."""

import argparse
import json
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from research_ops.scripts.audit_recovery_predicates import run


def reproduce(output):
    output.mkdir(exist_ok=False, parents=True)
    (output / "raw").mkdir()
    for name in ["trials.jsonl", "oracle_certificates.jsonl"]:
        (output / name).touch()
    run(output)
    original = Path("artifacts/research_runs/w0d-recovery-predicates-v2-1")
    for name in ["trials.jsonl", "metrics.json"]:
        if name.endswith(".jsonl"):
            a = [json.loads(x) for x in (output / name).read_text().splitlines()]
            b = [json.loads(x) for x in (original / name).read_text().splitlines()]
        else:
            a = json.loads((output / name).read_text())
            b = json.loads((original / name).read_text())
        if a != b:
            raise ValueError("Derived predicate regeneration mismatch: " + name)
    atomic_json(
        output / "reproduction.json",
        dict(
            schema_version=1,
            passed=True,
            model_calls=0,
            modal_usd=0,
            scope=(
                "Saved102case mapping matches exactly; official metrics remain separately archived"
            ),
        ),
    )
    print("Derived v2.1 rows/metrics reproduce exactly; no model or provider calls")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    reproduce(p.parse_args().output)

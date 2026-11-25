"""Check the new solver against all 256 archived fixed-time repair instances."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from afterclick.completion_v12.evidence import digest, sha
from afterclick.completion_v12.finite import existential, robust, verify_robust
from afterclick.research.recoverability import State, successors


def execute(output):
    output.mkdir(parents=True, exist_ok=False)
    source = Path("artifacts/research_runs/p3-formal-recovery-v1/raw/exhaustive-states.json")
    archived = json.loads(source.read_text())["states"]
    states = {digest(r["state"]): State(**r["state"]) for r in archived}
    model = dict(
        schema_version=1,
        move_order="CONTROLLER_ENVIRONMENT_OBSERVATION",
        scope="Legacy 256-state fixed-time repair API; no waiting or evolving worker",
        states={
            key: dict(
                observation=key,
                safe=True,
                goal=s.acceptable(),
                actions={a: [digest(asdict(t))] for a, t in successors(s)},
            )
            for key, s in states.items()
        },
    )
    (output / "formal-model.json").write_text(json.dumps(model, indent=2) + "\n")
    certificates, compared = [], []
    for row in archived:
        key = digest(row["state"])
        e = existential(model, key, 3)
        cert = robust(model, [key], 3)
        checked = verify_robust(model, cert)
        expected = row["strategy"] is not None
        if (e["witness"] is not None) != expected or checked["robust"] != expected:
            raise ValueError("New solver disagrees with an archived finite instance")
        certificates.append(dict(state=key, existential=e, robust=cert))
        compared.append(
            dict(
                state=key,
                repair_exists=expected,
                existential_status=e["status"],
                robust_status=cert["status"],
            )
        )
    (output / "certificates.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in certificates)
    )
    summary = dict(
        states=len(archived),
        repair_exists=sum(r["repair_exists"] for r in compared),
        mismatches=0,
        source_sha256=sha(source),
        model_sha256=digest(model),
        comparisons=compared,
        scope=model["scope"],
        new_model_calls=0,
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "comparisons"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    execute(parser.parse_args().output)

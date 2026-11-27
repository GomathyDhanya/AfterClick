"""Generate the reviewable claim-to-evidence matrix, including unsupported claims."""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main():
    data = ROOT / "evidence/publication"
    registry = json.loads((ROOT / "paper/current/CLAIM_REGISTRY.json").read_text())
    rows = []
    for key, claim in registry.items():
        path = (data / claim["source"]).resolve()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == claim["source_sha256"]
        rows.append(
            dict(
                claim_id=key,
                claim=claim["claim"],
                status="SUPPORTED_WITH_STATED_SCOPE",
                evidence=str(path.relative_to(ROOT)),
                pointer=claim["pointer"],
                sha256=claim["source_sha256"],
                limitation="See manuscript scope and appendix",
            )
        )
    extras = [
        (
            "C12_oracle_qualification",
            "576 reference witnesses and 10,944 evidence mutations",
            "evidence/v12/independent-oracle-mutations/report.json",
            "SUPPORTED_AUTOMATED",
            "Software independence; no independent human review",
        ),
        (
            "C13_primary_prefixes",
            "Primary graph keeps intermediate recoverability unknown",
            "evidence/v12/primary-recoverability-prefixes/report.json",
            "SUPPORTED_BOUNDED",
            "No exact mid-trajectory counterfactuals or complex formal certificates",
        ),
        (
            "C14_larger_prefixes",
            "Larger-model prefix labels retain unknown states",
            "evidence/v12/larger-recoverability-prefixes/report.json",
            "SUPPORTED_BOUNDED",
            "Supplementary constructed source support",
        ),
        (
            "U01_full_study",
            "The entire original experimental program is complete",
            "research_ops/publication/PUBLICATION_STATUS.json",
            "NOT_ESTABLISHED",
            "1,425 assignments and required causal controls remain unexecuted",
        ),
        (
            "U02_human_review",
            "Independent humans validated task authority and oracles",
            "research_ops/publication/PUBLICATION_STATUS.json",
            "NOT_PERFORMED",
            "Independent software checks and cloud machines do not establish human review",
        ),
    ]
    for key, claim, path, status, limitation in extras:
        rows.append(
            dict(
                claim_id=key,
                claim=claim,
                status=status,
                evidence=path,
                pointer="",
                sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                limitation=limitation,
            )
        )
    output = ROOT / "research_ops/publication/claim_evidence_matrix.csv"
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} claim/evidence rows")


if __name__ == "__main__":
    main()

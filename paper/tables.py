"""Generate the manuscript's numerical tables and claim registry from checked evidence."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "evidence"
PAPER = ROOT / "paper"


def load(name):
    return json.loads((DATA / name).read_text())


def rows(name):
    return list(csv.DictReader((DATA / name).open()))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pct(x, digits=1):
    return f"{100 * x:.{digits}f}"


def interval(pair, digits=2):
    return "$[" + ",".join(pct(x, digits) for x in pair) + "]$"


def table(name, columns, header, body):
    target = PAPER / "tables" / f"{name}.tex"
    target.parent.mkdir(exist_ok=True)
    target.write_text(
        "\\begin{tabular}{@{}"
        + columns
        + "@{}}\\toprule\n"
        + " & ".join(header)
        + r"\\\midrule"
        + "\n"
        + "\n".join(" & ".join(str(v) for v in row) + r"\\" for row in body)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def build():
    # Verify every figure/table input before generating anything numerical.
    for base in [DATA / "publication", DATA / "v12"]:
        for name, entry in json.loads((base / "MANIFEST.json").read_text())["files"].items():
            assert sha(base / name) == entry["sha256"], name
    analysis = load("publication/analysis/report.json")
    actuator = load("v12/controlled-actuator/report.json")
    cohorts = analysis["cohorts"]
    primary = load("v12/primary-analysis/report.json")
    larger = load("v12/larger-analysis/report.json")
    external = load("v12/official-external-analysis/report.json")
    duties = rows("publication/obligations/duties.csv")
    table(
        "enroll",
        "lrrrrr",
        ["Cohort", "Registered", "Terminal", "Valid internal", "Invalid", "Not run"],
        [
            [
                tag.title(),
                *(c[k] for k in ["registered", "terminal", "valid", "invalid", "not_run"]),
            ]
            for tag, c in cohorts.items()
        ]
        + [
            [
                "External",
                external["registered"],
                external["terminal"],
                "--",
                "--",
                external["registered"] - external["terminal"],
            ],
            [
                "Total",
                sum(c["registered"] for c in cohorts.values()) + external["registered"],
                sum(c["terminal"] for c in cohorts.values()) + external["terminal"],
                sum(c["valid"] for c in cohorts.values()),
                sum(c["invalid"] for c in cohorts.values()),
                sum(c["not_run"] for c in cohorts.values()),
            ],
        ],
    )
    table(
        "mismatch",
        "lrrrr",
        ["Cohort", r"Mismatch / $L$", "Rate", r"Cluster 95\% CI", "Assignment bounds"],
        [
            [
                tag.title(),
                f"{c['conditional_mismatch']['numerator']}/{c['conditional_mismatch']['denominator']}",
                pct(c["conditional_mismatch"]["estimate"]) + r"\%",
                "--".join(pct(x) for x in c["conditional_mismatch"]["bootstrap95"]) + r"\%",
                "--".join(pct(x) for x in c["full_assignment_conditional_mismatch_bounds"]) + r"\%",
            ]
            for tag, c in cohorts.items()
        ],
    )
    labels = ["Direct HTTP", "Browser +300 ms", "Browser +1500 ms"]
    table(
        "delay",
        "lrrr",
        ["Intervention vs browser", r"Effect on $F$", r"Cluster 95\% CI", "Unknown bounds"],
        [
            [
                label,
                f"${c['estimate'] * 100:+.2f}$",
                interval(c["source_bootstrap95"]),
                interval(c["unknown_bounds"]),
            ]
            for label, c in zip(labels, actuator["contrasts"])
        ],
    )
    cells = load("publication/boundary/cells.json")["episodes"]
    orders = {
        "protection_before_admission": "Protection before admission",
        "admission_before_protection": "Admission before protection, receipt after",
        "receipt_before_protection": "Receipt before protection",
    }
    table(
        "probe",
        "lrrr",
        ["Order", "Branches", "Pending effects", "Prevented"],
        [
            [
                label,
                len(group := [r for r in cells if r["order"] == order]),
                sum(r["pending_received"] for r in group),
                sum(not r["pending_received"] for r in group),
            ]
            for order, label in orders.items()
        ],
    )
    dutyrows = []
    for kind, label in [
        ("SERVICE_REOPEN", "Service reopening"),
        ("APPROVED_REQUEST_RESUBMIT", "Approved request resubmission"),
    ]:
        group = [r for r in duties if r["kind"] == kind]
        count = Counter(r["status"] for r in group)
        dutyrows.append(
            [label, len(group), count["DISCHARGED_OBSERVED"], count["OUTSTANDING_CENSORED"]]
        )
    dutyrows.append(
        ["Total", len(duties), sum(r[2] for r in dutyrows), sum(r[3] for r in dutyrows)]
    )
    table("debt", "lrrr", ["Duty type", "Triggered", "Discharged", "Outstanding"], dutyrows)
    arms = []
    dispositions = []
    for tag, report in [("Primary", primary), ("Larger", larger)]:
        for arm in [
            "P0-clean",
            "P0-stress",
            "P1-stress",
            "P2-stress",
            "P3-stress",
            "P4-stress",
            "P5-stress",
        ]:
            if arm not in report["arms"]:
                continue
            r = report["arms"][arm]
            arms.append(
                [
                    tag,
                    arm.replace("-", " "),
                    *(
                        r.get(k, 0)
                        for k in [
                            "VALID",
                            "legitimate_complete",
                            "forbidden_history",
                            "joint_safe_completion",
                        ]
                    ),
                ]
            )
            dispositions.append(
                [
                    tag,
                    arm.replace("-", " "),
                    *(r.get(k, 0) for k in ["registered", "VALID", "INVALID", "NOT_RUN"]),
                ]
            )
    table("arm", "llrrrr", ["Cohort", "Policy", "Valid", "$G$", "$F$", "$Y$"], arms)
    table(
        "fullarms",
        "llrrrr",
        ["Cohort", "Arm", "Registered", "Valid", "Invalid", "Not run"],
        dispositions,
    )
    contrasts = []
    for tag, report in [("Primary", primary), ("Larger", larger)]:
        for c in report["contrasts"]:
            if not c["registered_matched_worlds"]:
                continue
            contrasts.append(
                [
                    tag,
                    c["contrast"].replace("-", "--"),
                    c["complete_pair_source_clusters"],
                    f"${pct(c['complete_pair_estimate'], 2)}$",
                    interval(c["source_stratified_bootstrap95"], 1),
                    interval(c["assignment_bounds"], 1),
                ]
            )
    table(
        "contrasts",
        "llrrrr",
        ["Cohort", "Contrast", "Clusters", "Estimate", r"95\% CI", "Assignment bounds"],
        contrasts,
    )
    table(
        "external",
        "lrrrrr",
        [
            "Wrapper",
            f"Control /{external['methods'][0]['registered_control']}",
            f"Fault /{external['methods'][0]['registered_fault']}",
            "Capable",
            "Conditional",
            r"95\% CI",
        ],
        [
            [
                r["method"].title(),
                r["control_success"],
                r["fault_success"],
                r["control_capable_pairs"],
                pct(r["conditional_recovery_success"]) + r"\%",
                "--".join(pct(x) for x in r["conditional_task_bootstrap95"]) + r"\%",
            ]
            for r in external["methods"]
        ],
    )
    prefixes = []
    for tag in cohorts:
        r = load(f"v12/{tag}-recoverability-prefixes/report.json")
        prefixes.append(
            [
                tag.title(),
                r["nodes"],
                r["labels"]["UNKNOWN"],
                r["labels"]["WITNESSED_SAFE_INITIAL_CONTINUATION"],
                r["labels"]["REALIZED_SAFE_COMPLETION"],
                r["formal_certificates_in_complex_graph"],
            ]
        )
    table(
        "prefix",
        "lrrrrr",
        ["Cohort", "Nodes", "Unknown", "Safe initial witness", "Safe final", "Formal"],
        prefixes,
    )
    registry = json.loads((PAPER / "claim_registry.json").read_text())
    for key, path, pointer, claim in [
        (
            "C12_external",
            "../v12/official-external-analysis/report.json",
            "/methods",
            "Supplementary official external subset; no universal winner",
        ),
        (
            "C13_prefix",
            "../v12/primary-recoverability-prefixes/report.json",
            "/labels",
            "Unknown states retained; no complex-prefix formal certificates",
        ),
        (
            "C14_sensitivity",
            "analysis/structural-sensitivity.csv",
            "conditional_rate",
            "Leave-one-structure-out diagnostic, not independent replication",
        ),
    ]:
        registry[key] = {
            "source": path,
            "pointer": pointer,
            "claim": claim,
            "source_sha256": sha(DATA / "publication" / path),
        }
    for entry in registry.values():
        assert sha(DATA / "publication" / entry["source"]) == entry["source_sha256"]
    (PAPER / "claim_registry.json").write_text(json.dumps(registry, indent=2) + "\n")
    with (DATA / "claim_evidence_matrix.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "claim", "evidence", "pointer", "sha256"])
        writer.writeheader()
        for key, entry in registry.items():
            writer.writerow(
                {
                    "id": key,
                    "claim": entry["claim"],
                    "evidence": str((Path("evidence/publication") / entry["source"])),
                    "pointer": entry["pointer"],
                    "sha256": entry["source_sha256"],
                }
            )
    provenance = {
        "generator": "paper/tables.py",
        "tables": {p.name: sha(p) for p in sorted((PAPER / "tables").glob("*.tex"))},
        "sources": {
            str(p.relative_to(ROOT)): sha(p)
            for p in sorted(DATA.rglob("*"))
            if p.is_file()
            and p.suffix in {".json", ".csv", ".jsonl"}
            and p.name not in {"index.json"}
        },
        "model_calls": 0,
        "provider_calls": 0,
        "rounding": "Python fixed-point formatting; exact unrounded numbers remain in sources",
    }
    (PAPER / "BUILD.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(
        json.dumps(
            {
                "numerical_tables_generated": len(provenance["tables"]),
                "claims": len(registry),
                "model_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    build()

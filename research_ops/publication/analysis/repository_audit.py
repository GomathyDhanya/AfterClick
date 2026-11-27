"""Classify baseline tracked files, static dependencies and exact catalog duplicates."""

import ast
import collections
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "research_ops/publication"


def main():
    baseline = list(csv.DictReader((KIT / "FILE_INVENTORY.csv").open()))
    paths = {r["path"] for r in baseline}
    frozen = json.loads(
        (
            ROOT
            / (
                "research_ops/completion_v12/proposed_protocol_v4_final_"
                "credit_bound/PROTOCOL_FROZEN.json"
            )
        ).read_text()
    )
    pinned = {
        str(Path(p).relative_to(ROOT)) if Path(p).is_absolute() else p
        for k in ["source_hashes", "gate_hashes"]
        for p in frozen[k]
    }
    edges = []
    categories = collections.Counter()
    rows = []
    for r in baseline:
        name = r["path"]
        p = ROOT / name
        if name in pinned:
            category = "FROZEN_SOURCE_OR_GATE"
        elif name.startswith("evidence/"):
            category = "COMPACT_EVIDENCE"
        elif name.startswith("research_ops/completion_v12/candidate_contracts"):
            category = "HISTORICAL_OR_FROZEN_CONTRACT"
        elif name.startswith("afterclick/"):
            category = "RUNTIME_OR_HISTORICAL_COMPATIBILITY_RUNTIME"
        elif name.startswith("tests/"):
            category = "ACTIVE_OR_HISTORICAL_REGRESSION_TEST"
        elif name.startswith(("apps/", "migrations/", "docker/")):
            category = "APPLICATION_DEPENDENCY"
        elif name.startswith("paper/") or name.startswith("output/"):
            category = "HISTORICAL_MANUSCRIPT_OR_GENERATED_OUTPUT"
        elif name.startswith("research_ops/"):
            category = "HISTORICAL_SPECIFICATION_PROTOCOL_OR_ANALYSIS"
        elif name.startswith("docs/"):
            category = "DOCUMENTATION_OR_HISTORY"
        else:
            category = "DEPENDENCY_CONFIG_OR_ENTRYPOINT"
        categories[category] += 1
        action = (
            "MOVE"
            if name
            in {
                "docs/GIT_COMMIT_FILES.txt",
                "docs/GIT_REPOSITORY_FILES.txt",
                "docs/GIT_PUBLICATION_AUDIT.json",
            }
            else "REMOVE_GENERATED_COPY"
            if name
            in {
                "paper/v12/layout-qa/appendix-pages.png",
                "paper/v12/layout-qa/manuscript-pages.png",
            }
            else "KEEP"
        )
        rows.append({**r, "category": category, "action": action, "frozen_path": name in pinned})
        if p.suffix not in {
            ".py",
            ".md",
            ".json",
            ".txt",
            ".toml",
            ".yaml",
            ".yml",
            ".cff",
            ".csv",
        }:
            continue
        text = p.read_text(errors="replace")
        for token in set(re.findall(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+", text)):
            candidate = token.removeprefix(str(ROOT) + "/").lstrip("./")
            if candidate in paths:
                edges.append(dict(source=name, target=candidate, kind="EXACT_STATIC_PATH_TOKEN"))
        if p.suffix == ".py":
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                modules = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module]
                    if isinstance(node, ast.ImportFrom) and node.module
                    else []
                )
                for module in modules:
                    for target in [
                        module.replace(".", "/") + ".py",
                        module.replace(".", "/") + "/__init__.py",
                    ]:
                        if target in paths:
                            edges.append(
                                dict(source=name, target=target, kind="PYTHON_ABSOLUTE_IMPORT")
                            )
    duplicates = []
    for version in range(2, 7):
        a = ROOT / f"research_ops/completion_v12/candidate_contracts_v{version}"
        b = ROOT / f"research_ops/completion_v12/candidate_contracts_v{version + 1}"
        aa = (
            {
                str(p.relative_to(a)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in a.rglob("*.json")
            }
            if a.exists()
            else {}
        )
        bb = (
            {
                str(p.relative_to(b)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in b.rglob("*.json")
            }
            if b.exists()
            else {}
        )
        duplicates.append(
            dict(
                versions=[version, version + 1],
                left=len(aa),
                right=len(bb),
                same_relative_keys=aa.keys() == bb.keys(),
                all_bytes_identical=bool(aa) and aa == bb,
                identical_common=sum(aa[k] == bb[k] for k in aa.keys() & bb.keys()),
                action=(
                    "KEEP: historical path/provenance roles; Git already ded"
                    "uplicates identical blobs"
                ),
            )
        )
    with (KIT / "REPOSITORY_CLASSIFICATION.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with (KIT / "STATIC_DEPENDENCIES.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source", "target", "kind"])
        w.writeheader()
        w.writerows(edges)
    (KIT / "REPOSITORY_AUDIT.json").write_text(
        json.dumps(
            dict(
                baseline_tracked=len(rows),
                categories=categories,
                static_edges=len(edges),
                catalog_comparisons=duplicates,
                limitations=(
                    "Static literal/import graph misses constructed paths, r"
                    "elative imports, dynamic imports and external reference"
                    "s. Frozen paths and historical manifests retained regar"
                    "dless of static reference count."
                ),
                proposed_actions=dict(collections.Counter(r["action"] for r in rows)),
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()

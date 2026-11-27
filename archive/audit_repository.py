"""Reproduce file dispositions and conservative import/dynamic-reference reports."""

import argparse
import ast
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    "afterclick": "ACTIVE_RUNTIME",
    "apps": "ACTIVE_RUNTIME",
    "migrations": "ACTIVE_RUNTIME",
    "docker": "ACTIVE_RUNTIME",
    "fixtures": "ACTIVE_RUNTIME",
    "evidence": "ACTIVE_EVIDENCE",
    "tests": "ACTIVE_EXPERIMENT",
}


def run(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def analyze(source_commit, output):
    output.mkdir(parents=True, exist_ok=True)
    old = {}
    for record in run("ls-tree", "-r", "-z", source_commit).split(b"\0"):
        if not record:
            continue
        meta, name = record.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        old[name.decode()] = {"blob": oid, "mode": mode}
    batch = subprocess.Popen(
        ["git", "-C", str(ROOT), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    def blob(oid):
        batch.stdin.write((oid + "\n").encode())
        batch.stdin.flush()
        header = batch.stdout.readline().decode().split()
        data = batch.stdout.read(int(header[2]))
        assert batch.stdout.read(1) == b"\n"
        return data

    freeze = json.loads(
        blob(
            old[
                "research_ops/completion_v12/proposed_protocol_v4_final_credit_bound/PROTOCOL_FROZEN.json"
            ]["blob"]
        )
    )
    original_root = Path("/Users/gomathydhanya/projects/684_final")
    frozen = {
        str(Path(n).relative_to(original_root)) if Path(n).is_absolute() else n
        for group in ["source_hashes", "gate_hashes"]
        for n in freeze[group]
    }
    current = {
        n
        for n in run("ls-files", "--cached", "--others", "--exclude-standard", "-z")
        .decode()
        .split("\0")
        if n and (ROOT / n).is_file()
    }
    current.update(str(p.relative_to(ROOT)) for p in output.glob("*") if p.is_file())
    inventory = []
    current_python = {}
    baseline_python = {}
    archived = []
    for name, row in old.items():
        data = blob(row["blob"])
        row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        if name.endswith(".py"):
            baseline_python[name] = data
        if name not in current:
            archived.append(name)
    batch.stdin.close()
    assert batch.wait() == 0
    for name in sorted(current):
        path = ROOT / name
        data = path.read_bytes()
        if name.endswith(".py"):
            current_python[name] = data
        category = CATEGORIES.get(name.split("/")[0], "ACTIVE_DOCUMENTATION")
        if name.startswith("research_ops/"):
            category = (
                "ACTIVE_ANALYSIS"
                if name.endswith(".py")
                else "ACTIVE_EXPERIMENT"
                if "/candidate_contracts_v7/" in name or "/registration/" in name
                else "ACTIVE_DOCUMENTATION"
            )
        inventory.append(
            {
                "path": name,
                "bytes": len(data),
                "sha256": None if path.is_relative_to(output) else hashlib.sha256(data).hexdigest(),
                "classification": category,
                "reason": (
                    "Current paper runtime, experiment, analysis, "
                    "evidence, build or supported documentation interface"
                ),
            }
        )
    disposition = []
    for name, row in sorted(old.items()):
        active = name in current
        category = next((r["classification"] for r in inventory if r["path"] == name), None)
        disposition.append(
            {
                "path": name,
                "source_sha256": row["sha256"],
                "source_bytes": row["bytes"],
                "source_git_blob": row["blob"],
                "source_mode": row["mode"],
                "classification": category
                if active
                else "ARCHIVE_FROZEN"
                if name in frozen
                else "ARCHIVE_HISTORICAL",
                "active_path": name if active else "",
                "frozen_source_member": name in frozen,
                "recovery_commit": source_commit,
                "reason": "Retained current dependency or supported interface"
                if active
                else (
                    "Exact original path and bytes preserved in "
                    "pinned source snapshot; removed from active checkout only"
                ),
            }
        )
    edges = []
    dynamic = []
    unresolved = []
    for scope, python in [("historical", baseline_python), ("active", current_python)]:
        modules = {n[:-3].replace("/", ".").removesuffix(".__init__"): n for n in python}
        for name, data in python.items():
            tree = ast.parse(data)
            package = name[:-3].replace("/", ".").split(".")[:-1]
            for node in ast.walk(tree):
                targets = []
                if isinstance(node, ast.Import):
                    targets = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    base = (
                        ".".join(
                            package[: len(package) - node.level + 1]
                            + ([node.module] if node.module else [])
                        )
                        if node.level
                        else (node.module or "")
                    )
                    targets = [base] + [base + "." + a.name for a in node.names]
                for target in targets:
                    if target in modules:
                        edges.append(
                            {
                                "scope": scope,
                                "source": name,
                                "target": modules[target],
                                "line": node.lineno,
                                "kind": "import",
                            }
                        )
                    elif scope == "active" and target.startswith(("afterclick.", "research_ops.")):
                        # A from-import attribute is not automatically a module.
                        prefix = target.rsplit(".", 1)[0]
                        if prefix not in modules and not any(
                            m.startswith(target + ".") for m in modules
                        ):
                            unresolved.append({"path": name, "line": node.lineno, "module": target})
                    for count in range(1, len(target.split("."))):
                        init = "/".join(target.split(".")[:count]) + "/__init__.py"
                        if init in python:
                            edges.append(
                                {
                                    "scope": scope,
                                    "source": name,
                                    "target": init,
                                    "line": node.lineno,
                                    "kind": "package-init",
                                }
                            )
                if isinstance(node, ast.Call):
                    call = ast.unparse(node.func)
                    if any(
                        s in call
                        for s in [
                            "import_module",
                            "__import__",
                            "subprocess",
                            "run_module",
                            "run_path",
                            "read_text",
                            "read_bytes",
                            "open",
                            "glob",
                            "rglob",
                            "with_name",
                        ]
                    ):
                        args = [
                            a.value
                            for a in node.args
                            if isinstance(a, ast.Constant) and isinstance(a.value, str)
                        ]
                        dynamic.append(
                            {
                                "scope": scope,
                                "path": name,
                                "line": node.lineno,
                                "call": call,
                                "literal_args": args,
                                "review": "Historical source preserved unchanged"
                                if scope == "historical"
                                else ("See dynamic-policy.json; static analysis is not proof"),
                            }
                        )
    for filename, rows in [
        ("file_disposition.csv", disposition),
        ("after_inventory.csv", inventory),
        ("static_edges.csv", edges),
    ]:
        with (output / filename).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (output / "archived_paths.txt").write_text("\n".join(sorted(archived)) + "\n")
    (output / "dynamic_references.json").write_text(json.dumps(dynamic, indent=2) + "\n")
    (output / "unresolved_dependencies.json").write_text(json.dumps(unresolved, indent=2) + "\n")
    summary = {
        "source_commit": source_commit,
        "original_files": len(old),
        "active_files": len(current),
        "archived_original_paths": len(archived),
        "added_paths": len(current - set(old)),
        "file_reduction": len(old) - len(current),
        "removed_catalog_paths": sum("/candidate_contracts_v" in n for n in archived),
        "dispositions": dict(Counter(r["classification"] for r in disposition)),
        "active_python_modules": len(current_python),
        "historical_python_modules": len(baseline_python),
        "unresolved_local_imports": len(unresolved),
        "audit_outputs_self_hashes_omitted": True,
        "all_original_paths_recoverable_from_source_commit": True,
        "git_storage_history_not_rewritten": True,
        "limitations": (
            "Static edges do not prove dynamic absence. Runtime validation, "
            "build inspection and external/raw prerequisites are documented separately."
        ),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", default="31eab61870befc520841d11f422bb1a372ba92b8")
    parser.add_argument("--output", type=Path, default=ROOT / "archive/audit")
    args = parser.parse_args()
    analyze(args.source_commit, args.output.resolve())

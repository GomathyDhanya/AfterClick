"""Prepare the complete pre-TEST matrix and freeze only after executable gates.

Preparation does not open TEST outcomes, provision compute, or call a model.
"""

import argparse
import collections
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from afterclick.completion_v12.evidence import digest, sha


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def prepare(contracts, output, second_scope):
    output.mkdir(parents=True, exist_ok=False)
    tasks = [json.loads(p.read_text()) for p in sorted(contracts.glob("TEST-*.json"))]
    assert len(tasks) == 216
    primary = []
    secondary = []
    worlds = []
    focus_restore = []
    focus_stage = []
    task_entries = {}
    for index, c in enumerate(tasks):
        key = c["task_id"]
        variant = int(key.rsplit("-", 1)[1])
        task_entries[key] = dict(
            path=str((contracts / (key + ".json")).resolve()),
            sha256=sha(contracts / (key + ".json")),
            digest=digest(c),
        )
        restoration = variant in {2, 6}
        stage_first = variant in {3, 5}
        if restoration:
            focus_restore.append(key)
        if stage_first:
            focus_stage.append(key)
        for regime_index, (regime, admission) in enumerate(
            [("tight", 0), ("intermediate", 2000), ("generous", 8000)]
        ):
            seed = 910000 + index * 101 + regime_index
            cells = []
            for policy in (
                ["P0", "P1", "P2", "P3"]
                + (["P4"] if restoration else [])
                + (["P5"] if stage_first else [])
            ):
                cells.append(
                    dict(
                        episode_id=f"{key}-{policy}-{regime}-0-primary",
                        task_id=key,
                        policy=policy,
                        world_seed=seed,
                        admission_ms=admission,
                        clean=False,
                        timing_regime=regime,
                        replicate=0,
                    )
                )
            random.Random(20261125 + index * 7 + regime_index).shuffle(cells)
            primary.extend(cells)
            for cell in cells:
                if cell["policy"] not in {"P4", "P5"} and (
                    second_scope == "full" or variant in {2, 6}
                ):
                    secondary.append(
                        dict(cell, episode_id=cell["episode_id"].replace("-primary", "-larger"))
                    )
            worlds.append(
                dict(
                    task_id=key,
                    world_seed=seed,
                    admission_ms=admission,
                    timing_regime=regime,
                    clean=False,
                    contract_sha256=task_entries[key]["sha256"],
                )
            )
        for replicate in range(3):
            cell = dict(
                episode_id=f"{key}-P0-clean-{replicate}-primary",
                task_id=key,
                policy="P0",
                world_seed=1910000 + index * 7 + replicate,
                admission_ms=3000,
                clean=True,
                timing_regime="clean",
                replicate=replicate,
            )
            primary.append(cell)
            if second_scope == "full" or variant in {2, 6}:
                secondary.append(
                    dict(cell, episode_id=cell["episode_id"].replace("-primary", "-larger"))
                )
    assert len(primary) == 3672
    assert len(focus_restore) == len(focus_stage) == 72
    assert len(secondary) == (3240 if second_scope == "full" else 1080)

    # Randomize source-world groups, keeping all sibling policies together for
    # pre-inference reconstruction certificates and finite resumable batches.
    def order(cells, seed):
        grouped = collections.OrderedDict()
        for cell in cells:
            grouped.setdefault((cell["task_id"], cell["world_seed"], cell["clean"]), []).append(
                cell
            )
        groups = list(grouped.values())
        random.Random(seed).shuffle(groups)
        return [cell for group in groups for cell in group]

    save(
        output / "primary-manifest.json",
        dict(model_tag="primary", episodes=order(primary, 611251), contracts=task_entries),
    )
    save(
        output / "larger-manifest.json",
        dict(model_tag="larger", episodes=order(secondary, 611252), contracts=task_entries),
    )
    save(output / "source-worlds.json", worlds)
    save(
        output / "subsets.json",
        dict(
            restoration=focus_restore,
            stage_first=focus_stage,
            selection=(
                "Fixed variants 02/06 and 03/05 within every app/family/complexity cell; "
                "balanced approved/prohibited pending requests"
            ),
        ),
    )
    external_tasks = json.loads(
        Path("artifacts/external/undobench-v1/recoverbench/tasks/manifest.json").read_text()
    )["tasks"]
    ids = sorted(t["task_id"] for t in external_tasks if t["split"] == "test")
    assert len(ids) == 12
    external = []
    for task in ids:
        for seed in [42, 43]:
            for method in ["naive", "checkpoint", "saga", "idempotency", "vbr"]:
                conditions = ["CONTROL", "FAULT"]
                random.Random(task + str(seed) + method).shuffle(conditions)
                for condition in conditions:
                    external.append(
                        dict(
                            episode_id=f"{task}-{method}-{condition}-TEST-{seed}",
                            task_id=task,
                            method=method,
                            condition=condition,
                            seed=seed,
                            split="test",
                            pair_id=f"{task}-{method}-{seed}",
                        )
                    )
    save(
        output / "external-manifest.json",
        dict(
            mode="FROZEN_OFFICIAL_EXTERNAL",
            episodes=external,
            concurrency=8,
            native_calls_per_episode=10,
            upstream_commit="4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e",
            official_tasks_tools_prompts_oracles_unchanged=True,
            seed_scope=(
                "Official context seeds; T0 and fixed fault programs, not independent "
                "randomized faults"
            ),
        ),
    )
    save(
        output / "prospective-counts.json",
        dict(
            status="PREPARED_NOT_FROZEN_NOT_EXECUTED",
            test_tasks=216,
            primary=3672,
            larger=len(secondary),
            larger_scope=second_scope,
            external=240,
            original_primary_prospective=9720,
            original_core_prospective=8424,
            primary_stress_worlds=648,
            primary_clean_episodes=648,
            primary_restoration_extra=216,
            primary_stage_first_extra=216,
            stress_worlds_per_task=3,
            seeds_per_timing_regime=1,
            clean_replicates_per_task=3,
            reason=(
                "Written pre-TEST repetition revision required by the $18 credit ceiling and"
                " source-cluster power; all 216 primary task contracts retained"
            ),
        ),
    )
    print(
        json.dumps(
            dict(primary=len(primary), larger=len(secondary), external=len(external), frozen=False)
        )
    )


def freeze(args):
    root = args.output
    counts = json.loads((root / "prospective-counts.json").read_text())
    gates = {}
    for file in args.gates:
        assert file.exists()
        gates[str(file)] = sha(file)
    audit = json.loads(args.task_audit.read_text())
    assert audit["complete"] and audit["qualified"] == 288
    independent = json.loads(args.independent_audit.read_text())
    assert independent["complete"] and independent["positive_accepted"] == 576
    dev = args.final_dev
    reconciliation = json.loads((dev / "queue-reconciliation.json").read_text())
    assert reconciliation["complete"]
    registration = json.loads((dev / "registration.json").read_text())
    assert len(registration["contracts"]) == 72
    lifecycle = json.loads((dev / "lifecycle.json").read_text())
    assert lifecycle["usage"]["uncertain"] == 0 and lifecycle["idle_verified"]
    if lifecycle["error"]:
        disposition = json.loads((dev / "external-reconciliation.json").read_text())
        assert (
            disposition["calls"] == 0
            and disposition["disposition"] == "LOCAL_IMPORT_FAILURE_BEFORE_HTTP"
        )
    power = json.loads(args.power.read_text())
    assert power["no_test_outcomes_used"] and power["source_clusters"] == 72
    regression = json.loads(args.regression.read_text())
    assert not regression["remaining_v12_regression_blockers"]
    for path in Path("artifacts/research_runs").glob(
        "v12-*/cloud-batches/**/episodes/TEST-*/result.json"
    ):
        raise ValueError("TEST already opened before freeze: " + str(path))
    for file in [
        args.task_audit,
        args.independent_audit,
        args.power,
        args.regression,
        dev / "registration.json",
        dev / "queue-reconciliation.json",
        dev / "lifecycle.json",
        root / "prospective-counts.json",
        root / "subsets.json",
        root / "source-worlds.json",
    ]:
        gates[str(file)] = sha(file)
    source = {str(p): sha(p) for p in Path("afterclick").rglob("*.py")}
    for pattern in [
        "afterclick/completion_v12/**/*.html",
        "research_ops/scripts/v12_*.py",
        "research_ops/completion_v12/cloud_worker.py",
        "migrations/**/*.py",
    ]:
        for p in Path(".").glob(pattern):
            source[str(p)] = sha(p)
    for name in ["pyproject.toml", "uv.lock", "alembic.ini"]:
        source[name] = sha(Path(name))
    models = json.loads(args.models.read_text())
    assert set(models) == {"primary", "larger"}
    contracts = json.loads((root / "primary-manifest.json").read_text())["contracts"]
    protocol = dict(
        schema_version=1,
        status="FROZEN_BEFORE_TEST",
        utc=datetime.now(timezone.utc).isoformat(),
        test_contract_count=216,
        dev_contract_count=72,
        counts=counts,
        contracts=contracts,
        limits=registration["limits"],
        models=models,
        manifests={
            tag: dict(
                path=str((root / (tag + "-manifest.json")).resolve()),
                sha256=sha(root / (tag + "-manifest.json")),
            )
            for tag in ["primary", "larger"]
        },
        external_manifest=dict(
            path=str((root / "external-manifest.json").resolve()),
            sha256=sha(root / "external-manifest.json"),
        ),
        external_dev_manifest=dict(
            path=str((root / "external-dev-manifest.json").resolve()),
            sha256=sha(root / "external-dev-manifest.json"),
        ),
        operational_oracle="afterclick.completion_v12.oracle_v2.evaluate",
        authoring_metadata_override=(
            "Frozen qualification evidence supersedes draft markers and original "
            "oracle_impl_ref; contract bytes remain immutable"
        ),
        public_controller_commands=["Verify", "Suspend", "Revoke", "Stage", "Resume"],
        execution=dict(parallel_batches=2, worlds_per_batch=16, endpoint_max_containers=1),
        additional_model_gate=(
            "All fixed DEV native and external DEV assignments terminal before any TEST "
            "inference; no efficacy threshold"
        ),
        source_hashes=source,
        gate_hashes=gates,
        model_temperature=0,
        max_output_tokens=512,
        actor_tool_choice="auto",
        native_history=(
            "Full continuous assistant/tool conversation; immutable initial definitions "
            "and dynamic batch results"
        ),
        primary_estimand="Source-weighted paired P3-P2 joint safe task completion",
        analysis="research_ops/scripts/v12_confirmatory_analysis.py",
        power=str(args.power),
        no_outcome_dependent_stopping=True,
        no_generation_retries=True,
        infrastructure_policy=(
            "Preserve every original failure; resume only unstarted assignments in new "
            "finite jobs. No post-TEST prompt, task, oracle, timing or enrollment "
            "tuning."
        ),
        source_certificate_policy=(
            "Before any model call, hash complete quiescent DB/client/public/schedule "
            "cut; reject mismatched siblings before inference. Exact mid-trajectory "
            "reconstruction is not claimed."
        ),
        unknown_policy=(
            "Missing, censored and invalid assignments remain UNKNOWN with full-"
            "denominator bounds; never silently dropped or converted to safe completion"
        ),
        credit_cap_usd=18,
        cash_authorized_usd=0,
        no_human_review_claim=True,
        shared_design_limit=(
            "Constructed 24 structural layouts and six business-policy vocabularies; "
            "inference is conditional on these operators"
        ),
    )
    path = root / "PROTOCOL_FROZEN.json"
    assert not path.exists()
    save(path, protocol)
    save(root / "FREEZE_SHA256.json", dict(path=str(path.resolve()), sha256=sha(path)))
    print(json.dumps(dict(frozen=True, sha256=sha(path), counts=counts)))


def prepare_budget(contracts, output):
    """Counterbalanced fixed-regime repeated worlds under the explicit $18 cap."""
    output.mkdir(parents=True, exist_ok=False)
    tasks = [json.loads(p.read_text()) for p in sorted(contracts.glob("TEST-*.json"))]
    assert len(tasks) == 216
    rng = random.Random(611252026)
    axes = [sorted({c[key] for c in tasks}) for key in ["family", "application", "complexity"]]
    for axis in axes:
        rng.shuffle(axis)
    regimes = ["tight", "intermediate", "generous"]
    rng.shuffle(regimes)
    prohibited_variants = [1, 2, 4, 5]
    rng.shuffle(prohibited_variants)
    selected_restore, selected_stage, selected_larger = set(), set(), set()
    assignments = {}
    for family in axes[0]:
        for app in axes[1]:
            for level in axes[2]:
                f, a, level_index = axes[0].index(family), axes[1].index(app), axes[2].index(level)
                cell = [
                    c
                    for c in tasks
                    if (c["family"], c["application"], c["complexity"]) == (family, app, level)
                ]
                by_variant = {int(c["task_id"].rsplit("-", 1)[1]): c["task_id"] for c in cell}
                approved = [3, 6][(f // 2 + a + level_index) % 2]
                other_approved = 9 - approved
                bad_index = (f + 2 * a + level_index) % 4
                bad = prohibited_variants[bad_index]
                other_bad = prohibited_variants[(bad_index + 2) % 4]
                rest = [by_variant[approved], by_variant[bad]]
                stage = [by_variant[other_approved], by_variant[other_bad]]
                selected_restore.add(rest[(f + a + level_index) % 2])
                selected_stage.add(stage[(f + a + level_index + 1) % 2])
                selected_larger.add(rest[(f + a + level_index) % 2])
                r = (f + a + level_index) % 3
                assignment = {
                    approved: r,
                    bad: (r + 1) % 3,
                    other_approved: (r + 2) % 3,
                    other_bad: r,
                }
                unused = sorted(set(by_variant) - set(assignment))
                assignment.update({unused[0]: (r + 1) % 3, unused[1]: (r + 2) % 3})
                assignments.update({by_variant[v]: regimes[i] for v, i in assignment.items()})
    assert len(selected_restore) == len(selected_stage) == 36
    assert len(selected_larger) == 36 and not selected_restore & selected_stage
    assert collections.Counter(assignments.values()) == dict.fromkeys(regimes, 72)
    assert collections.Counter(assignments[k] for k in selected_larger) == dict.fromkeys(
        regimes, 12
    )
    primary, larger, worlds, task_entries = [], [], [], {}
    for index, c in enumerate(tasks):
        key = c["task_id"]
        regime = assignments[key]
        admission = {"tight": 0, "intermediate": 2000, "generous": 8000}[regime]
        file = contracts / (key + ".json")
        task_entries[key] = dict(path=str(file.resolve()), sha256=sha(file), digest=digest(c))
        for replicate in range(2):
            seed = 2110000 + index * 101 + replicate
            policies = (
                ["P0", "P1", "P2", "P3"]
                + (["P4"] if key in selected_restore else [])
                + (["P5"] if key in selected_stage else [])
            )
            random.Random(61125 + index * 13 + replicate).shuffle(policies)
            for policy in policies:
                cell = dict(
                    episode_id=f"{key}-{policy}-{regime}-{replicate}-primary",
                    task_id=key,
                    policy=policy,
                    world_seed=seed,
                    admission_ms=admission,
                    clean=False,
                    timing_regime=regime,
                    replicate=replicate,
                )
                primary.append(cell)
                if key in selected_larger and policy in {"P0", "P1", "P2", "P3"}:
                    larger.append(
                        dict(cell, episode_id=cell["episode_id"].replace("-primary", "-larger"))
                    )
            worlds.append(
                dict(
                    task_id=key,
                    world_seed=seed,
                    admission_ms=admission,
                    clean=False,
                    timing_regime=regime,
                    replicate=replicate,
                )
            )
            cell = dict(
                episode_id=f"{key}-P0-clean-{replicate}-primary",
                task_id=key,
                policy="P0",
                world_seed=3110000 + index * 7 + replicate,
                admission_ms=3000,
                clean=True,
                timing_regime="clean",
                replicate=replicate,
            )
            primary.append(cell)
            if key in selected_larger:
                larger.append(
                    dict(cell, episode_id=cell["episode_id"].replace("-primary", "-larger"))
                )
    assert len(primary) == 2304 and len(larger) == 360

    def order(cells, seed):
        grouped = collections.OrderedDict()
        for cell in cells:
            grouped.setdefault((cell["task_id"], cell["world_seed"], cell["clean"]), []).append(
                cell
            )
        groups = list(grouped.values())
        random.Random(seed).shuffle(groups)
        return [c for group in groups for c in group]

    for tag, cells in [("primary", primary), ("larger", larger)]:
        save(
            output / (tag + "-manifest.json"),
            dict(
                model_tag=tag,
                episodes=order(cells, 611257 if tag == "primary" else 611258),
                contracts=task_entries,
            ),
        )
    save(output / "source-worlds.json", worlds)
    save(
        output / "subsets.json",
        dict(
            restoration=sorted(selected_restore),
            stage_first=sorted(selected_stage),
            larger_supplementary=sorted(selected_larger),
            task_regime=assignments,
            randomization_seed=611252026,
            randomized_axis_orders=axes,
            regime_permutation=regimes,
            prohibited_variant_permutation=prohibited_variants,
            selection=(
                "Pre-TEST Latin counterbalance: all 36 app/family/level cells, all six TEST "
                "layouts; larger subset one source per cell, 18 approved and 18 prohibited, "
                "12 sources per timing regime"
            ),
        ),
    )
    # Preserve the already prepared unchanged official external factorial.
    external = Path("research_ops/completion_v12/proposed_protocol_v2/external-manifest.json")
    save(output / "external-manifest.json", json.loads(external.read_text()))
    save(
        output / "prospective-counts.json",
        dict(
            status="PREPARED_NOT_FROZEN_NOT_EXECUTED",
            test_tasks=216,
            primary=2304,
            larger=360,
            larger_tasks=36,
            larger_scope="supplementary_preselected",
            external=240,
            original_primary_prospective=9720,
            original_core_prospective=8424,
            primary_stress_worlds=432,
            primary_clean_episodes=432,
            primary_restoration_extra=72,
            primary_stage_first_extra=72,
            focused_tasks_per_study=36,
            stress_worlds_per_task=2,
            clean_replicates_per_task=2,
            timing_design=(
                "One randomized counterbalanced regime per task, two independently seeded "
                "repeated worlds; 72 primary tasks per regime"
            ),
            reason=(
                "Pre-TEST financial/power revision: preserve all 216 primary tasks and "
                "repeated policies under the explicit $18 cap; full second-model core is "
                "financially infeasible. Full cross-deadline mechanism identification uses "
                "the separate 288 executed controlled branches. Small-effect and model-"
                "general claims are downgraded."
            ),
        ),
    )
    print(json.dumps(dict(primary=2304, larger=360, external=240, frozen=False)))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["prepare", "prepare-budget", "freeze"])
    p.add_argument(
        "--contracts", type=Path, default=Path("research_ops/completion_v12/candidate_contracts_v7")
    )
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--second-scope", choices=["full", "supplementary"], default="full")
    p.add_argument("--gates", type=Path, nargs="*", default=[])
    for key in ["task-audit", "independent-audit", "final-dev", "power", "regression", "models"]:
        p.add_argument("--" + key, type=Path)
    a = p.parse_args()
    if a.mode == "prepare":
        prepare(a.contracts, a.output, a.second_scope)
    elif a.mode == "prepare-budget":
        prepare_budget(a.contracts, a.output)
    else:
        freeze(a)

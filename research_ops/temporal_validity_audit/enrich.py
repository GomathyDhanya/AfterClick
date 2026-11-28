"""Cluster-aware uncertainty, exploratory sequences, cases and control timings."""

import csv
import json

import numpy as np
from analyze import HERE, dump, read, sha, table
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score, silhouette_score


def loadcsv(name):
    rows = list(csv.DictReader((HERE / name).open()))
    for r in rows:
        for k, v in r.items():
            if v in {"True", "False"}:
                r[k] = v == "True"
            elif v == "":
                r[k] = None
    return rows


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        curr = [i]
        for j, y in enumerate(b, 1):
            curr.append(min(curr[-1] + 1, prev[j] + 1, prev[j - 1] + (x != y)))
        prev = curr
    return prev[-1] / max(1, len(a), len(b))


def main():
    history = HERE / "provenance/historical"
    report = read(HERE / "report.json")
    compact_checks = []
    for rel in ["evidence/v12/MANIFEST.json", "evidence/publication/MANIFEST.json"]:
        manifest = history / rel
        for name, record in read(manifest)["files"].items():
            target = manifest.parent / name
            actual = sha(target) if target.exists() else None
            compact_checks.append(
                dict(
                    manifest=rel,
                    path=name,
                    expected=record["sha256"],
                    actual=actual,
                    matches=actual == record["sha256"],
                )
            )
    dump(HERE / "provenance/compact_manifest_checks.json", compact_checks)
    assert all(r["matches"] for r in compact_checks)
    integrity = read(HERE / "integrity_report.json")
    integrity["compact_manifest_files_verified"] = len(compact_checks)
    integrity["historical_worker_source_validation"] = (
        "cloud_worker.py lines 182-186 asserts actual afterclick/* source hashes before runner execution; 23 recovered batch payloads match pinned source. This is an in-worker assertion, not independent container attestation."  # noqa: E501
    )
    dump(HERE / "integrity_report.json", integrity)
    episodes = loadcsv("executions.csv")
    matched_checks = []
    episode_index = {e["episode_key"]: e for e in episodes}
    for pair in loadcsv("matched_pairs.csv"):
        cuts = []
        for key in [pair["p0"], pair["p1"]]:
            folder = (history / episode_index[key]["raw_path"]).parent
            cut = read(folder / "source-cut.json")
            certificate = read(folder / "source-certificate.json")
            assert certificate["valid"]
            from analyze import digest

            cuts.append(digest(cut))
        matched_checks.append(
            dict(
                p0=pair["p0"],
                p1=pair["p1"],
                p0_cut_digest=cuts[0],
                p1_cut_digest=cuts[1],
                equivalent=cuts[0] == cuts[1],
            )
        )
    dump(HERE / "provenance/matched_source_validation.json", matched_checks)
    assert all(c["equivalent"] for c in matched_checks)
    timing = [r for r in loadcsv("episode_timing.csv") if r["eligible_prohibited"]]
    decisions = [r for r in loadcsv("decision_opportunities.csv") if not r["pending_allowed"]]
    actions = loadcsv("browser_actions.csv")
    eligible_ids = {t["episode_key"] for t in timing}
    actions = [a for a in actions if a["episode_key"] in eligible_ids]
    # Fixed-task cluster resampling preserves both model and seed siblings.
    rng = np.random.default_rng(20261127)
    uncertainty = []
    for subset in [
        "full_eligible",
        "observation_opportunity",
        "response_opportunity",
        "demonstrated_execution_opportunity",
    ]:
        rows = timing if subset == "full_eligible" else [r for r in timing if r[subset]]
        tasks = sorted({r["task_id"] for r in rows})
        for metric in report["metrics"][subset]:
            if metric in {"n", "source_clusters"}:
                continue
            nums = np.array(
                [sum(bool(r[metric]) for r in rows if r["task_id"] == t) for t in tasks]
            )
            dens = np.array([sum(r["task_id"] == t for r in rows) for t in tasks])
            sampled = rng.integers(0, len(tasks), size=(5000, len(tasks)))
            rates = nums[sampled].sum(axis=1) / dens[sampled].sum(axis=1)
            uncertainty.append(
                dict(
                    subset=subset,
                    metric=metric,
                    n=len(rows),
                    source_clusters=len(tasks),
                    point=float(nums.sum() / dens.sum()),
                    lower=float(np.quantile(rates, 0.025)),
                    upper=float(np.quantile(rates, 0.975)),
                    method="5000 percentile bootstrap samples of task_id clusters; fixed observed tasks; degenerate intervals do not bound unseen tasks",  # noqa: E501
                )
            )
    table(HERE / "uncertainty.csv", uncertainty)
    # All raw occurrences of protective vocabulary receive explicit review.
    inputs = read(HERE / "provenance/input_hashes.json")
    lexical = []
    for path, expected in inputs.items():
        if not path.endswith("-output.json"):
            continue
        out = read(history / path)
        msg = json.loads(out["raw"])["choices"][0]["message"]
        if any(w in json.dumps(msg).lower() for w in ["suspend", "cancel"]):
            acts = []
            for call in msg.get("tool_calls", []):
                try:
                    args = json.loads(call["function"]["arguments"])
                    acts += (
                        args.get("actions", [])
                        if isinstance(args, dict) and isinstance(args.get("actions", []), list)
                        else []
                    )
                except (ValueError, KeyError, TypeError):
                    pass
            native = any(isinstance(a, dict) and a.get("id") in {"suspend", "cancel"} for a in acts)
            lexical.append(
                dict(
                    raw_path=path,
                    raw_sha256=expected,
                    raw_pointer="/raw",
                    message=msg,
                    classification="NATIVE_PROTECTIVE_PROPOSAL"
                    if native
                    else "VOCABULARY_MENTION_WITHOUT_PROTECTIVE_PROPOSAL",
                )
            )
    dump(HERE / "provenance/protective_vocabulary_review.json", lexical)
    # Pre-admission proposal sequences, retaining infeasible empty sequences.
    seqrows = []
    contracts = {}
    for t in timing:
        if t["task_id"] not in contracts:
            contracts[t["task_id"]] = read(
                history
                / "research_ops/completion_v12/candidate_contracts_v7"
                / (t["task_id"] + ".json")
            )
        kinds = {
            o["id"]: o["kind"]
            for o in contracts[t["task_id"]]["public"]["initial_public_state"]["operations"]
        }
        seq = []
        for d in sorted(
            [d for d in decisions if d["episode_key"] == t["episode_key"]],
            key=lambda d: int(d["decision_index"]),
        ):
            if float(d["response_end_mono"]) >= float(d["admission_mono"]) - 0.001:
                continue
            acts = json.loads(d["proposed_actions"])
            if not d["parsed_native_schema"]:
                seq.append("schema_invalid")
            elif not acts:
                seq.append("observe_or_finish")
            else:
                seq.extend(kinds.get(a["id"], a["id"]) for a in acts)
        seqrows.append(
            dict(
                episode_key=t["episode_key"],
                task_id=t["task_id"],
                sequence=seq,
                response_opportunity=t["response_opportunity"],
                demonstrated_execution_opportunity=t["demonstrated_execution_opportunity"],
            )
        )
    # Empty sequences are an explicit timing category, not a learned strategy.
    nonempty = [r for r in seqrows if r["sequence"]]
    n = len(nonempty)
    distance = np.array(
        [[edit_distance(a["sequence"], b["sequence"]) for b in nonempty] for a in nonempty]
    )
    candidates = []
    for k in range(2, 6):
        labels = AgglomerativeClustering(
            n_clusters=k, metric="precomputed", linkage="average"
        ).fit_predict(distance)
        candidates.append(
            dict(
                k=k,
                silhouette=float(silhouette_score(distance, labels, metric="precomputed")),
                labels=labels.tolist(),
            )
        )
    selected = max(candidates, key=lambda r: r["silhouette"])
    labels = np.array(selected["labels"])
    tasks = sorted({r["task_id"] for r in nonempty})
    stability = []
    rng = np.random.default_rng(2711)
    for _ in range(100):
        sampled_tasks = set(rng.choice(tasks, size=len(tasks), replace=True))
        ids = [i for i, r in enumerate(nonempty) if r["task_id"] in sampled_tasks]
        fitted = AgglomerativeClustering(
            n_clusters=selected["k"], metric="precomputed", linkage="average"
        ).fit_predict(distance[np.ix_(ids, ids)])
        stability.append(float(adjusted_rand_score(labels[ids], fitted)))
    for i, r in enumerate(nonempty):
        r["cluster"] = int(labels[i])
    for r in seqrows:
        if not r["sequence"]:
            r["cluster"] = "EMPTY_NO_RESPONSE_BEFORE_ADMISSION"
    table(HERE / "action_sequences.csv", seqrows)
    cluster_summary = []
    for label in sorted(set(labels)):
        ids = np.flatnonzero(labels == label)
        medoid = ids[np.argmin(distance[np.ix_(ids, ids)].mean(axis=1))]
        cluster_summary.append(
            dict(
                cluster=int(label),
                n=len(ids),
                medoid_episode=nonempty[medoid]["episode_key"],
                medoid_sequence=nonempty[medoid]["sequence"],
                median_length=float(np.median([len(nonempty[i]["sequence"]) for i in ids])),
            )
        )
    clustering = dict(
        scope="exploratory pre-admission proposed action categories; protection outcome is constant (no timely proposals)",  # noqa: E501
        distance="Levenshtein edit distance divided by max sequence length",
        algorithm="average-linkage agglomeration",
        empty_sequences=len(seqrows) - n,
        nonempty=n,
        distinct_sequences=len({tuple(r["sequence"]) for r in seqrows}),
        candidates=[{k: v for k, v in x.items() if k != "labels"} for x in candidates],
        selected_k=selected["k"],
        source_subsample_stability=dict(
            repetitions=100,
            median_ARI=float(np.median(stability)),
            lower_ARI=float(np.quantile(stability, 0.025)),
            upper_ARI=float(np.quantile(stability, 0.975)),
        ),
        clusters=cluster_summary,
        interpretation="Descriptive sequence shapes only. Cannot identify distinct protection-failure mechanisms because no sequence proposes protection before admission; length and available time confound shapes.",  # noqa: E501
    )
    dump(HERE / "clustering.json", clustering)
    # Deterministic case selection spans contrary as well as supporting evidence.
    selected_cases = []

    def choose(label, rows, ranking):
        if rows:
            selected_cases.append((label, sorted(rows, key=ranking)[0]))

    choose(
        "late_protection_despite_earlier_business_execution",
        [r for r in timing if r["protective_proposal"]],
        lambda r: r["episode_key"],
    )
    choose(
        "queue_crosses_admission",
        [r for r in timing if r["admission_during_queue"]],
        lambda r: r["episode_key"],
    )
    choose(
        "largest_demonstrated_slack_without_protection",
        [
            r
            for r in timing
            if r["demonstrated_execution_opportunity"] and not r["protective_proposal"]
        ],
        lambda r: float(r["first_business_commit_return_mono"]) - float(r["admission_mono"]),
    )
    choose(
        "response_arrives_after_admission",
        [r for r in timing if r["admission_vs_first_response"] == "BEFORE"],
        lambda r: r["episode_key"],
    )
    choose(
        "early_response_without_business_commit_opportunity",
        [
            r
            for r in timing
            if r["response_opportunity"] and not r["demonstrated_execution_opportunity"]
        ],
        lambda r: r["episode_key"],
    )
    case_index = []
    trajectories = []
    for label, t in selected_cases:
        eid = t["episode_key"]
        raw = history / t["raw_path"]
        folder = raw.parent
        local = read(folder / "events.json")
        final = read(raw)
        anchor = float(t["environment_anchor_mono"])
        timeline = []
        for d in decisions:
            if d["episode_key"] == eid:
                for event, key in [
                    ("queue", "queued_mono"),
                    ("request_start_marker", "request_start_marker_mono"),
                    ("response", "response_end_mono"),
                ]:
                    timeline.append(
                        dict(event=event, time_s=float(d[key]) - anchor, request_id=d["request_id"])
                    )
        for e in final["v12_events"]:
            if e["kind"] in {
                "pending.admission_snapshot",
                "external.admitted",
                "control.command",
                "receiver.committed",
                "flow.task_committed",
                "ops.work_order_committed",
            }:
                timeline.append(
                    dict(
                        event=e["kind"],
                        time_s=e["mono"] - anchor,
                        event_id=e["id"],
                        payload=e["payload"],
                    )
                )
        card = dict(
            selection_rule=label,
            episode=t,
            timeline=sorted(timeline, key=lambda x: x["time_s"]),
            decision_points=[d for d in decisions if d["episode_key"] == eid],
            local_events=local,
            raw_path=t["raw_path"],
            raw_sha256=t["raw_sha256"],
            counterfactual_claim=False,
        )
        dump(HERE / "case_studies" / (label + ".json"), card)
        case_index.append(
            dict(label=label, episode_key=eid, path="case_studies/" + label + ".json")
        )
        trajectories.append(dict(label=label, episode_key=eid, timeline=card["timeline"]))
    # A matched actually executed P1 sibling is a contrary example, not a
    # counterfactual replay of the P0 mid-trajectory state.
    pairs = loadcsv("matched_pairs.csv")
    safe = {
        e["episode_key"]: e for e in episodes if e["policy"] == "P1" and e["joint_safe_completion"]
    }
    pair = next(p for p in pairs if p["p1"] in safe)
    e = safe[pair["p1"]]
    folder = (history / e["raw_path"]).parent
    final, local = read(folder / "final.json"), read(folder / "events.json")
    anchor = next(x["anchor_mono"] for x in local if x["kind"] == "world.clock_started")
    timeline = [
        dict(event=x["kind"], time_s=x["mono"] - anchor, payload=x["payload"], event_id=x["id"])
        for x in final["v12_events"]
        if x["kind"] in {"control.command", "pending.admission_snapshot", "receiver.committed"}
    ]
    dump(
        HERE / "case_studies/safe_P1_sibling.json",
        dict(
            selection_rule="lexicographically first matched legitimate safe P1 sibling",
            pair=pair,
            episode=e,
            timeline=timeline,
            raw_snapshot_sha256=sha(folder / "final.json"),
            counterfactual_claim=False,
        ),
    )
    trajectories.append(
        dict(
            label="actually executed safe P1 sibling",
            episode_key=e["episode_key"],
            timeline=timeline,
        )
    )
    case_index.append(
        dict(
            label="safe_P1_sibling",
            episode_key=e["episode_key"],
            path="case_studies/safe_P1_sibling.json",
        )
    )
    dump(HERE / "case_studies/index.json", case_index)
    dump(HERE / "figures/trajectory_source.json", trajectories)
    # New diagnostic response-to-enforcement margins; use only technically valid
    # early controls where a protection transaction actually returned.
    controls = read(HERE / "positive_controls.json")
    latencies = []
    condition_stats = []
    for condition in "ABCDEFGHIJ":
        rows = [r for r in controls["trials"] if r["condition"] == condition]
        valid_rows = [r for r in rows if r["technical_validity"] == "VALID"]
        condition_stats.append(
            dict(
                condition=condition,
                attempts=len(rows),
                valid=len(valid_rows),
                receipts=sum(r["unauthorized_pending_receipts"] for r in valid_rows),
                protective_transactions=sum(bool(r["protective_transactions"]) for r in valid_rows),
                version_conflicts=sum(
                    r.get("version_conflict_manipulation_observed") is True for r in valid_rows
                ),
                manipulation_not_observed=sum(
                    r.get("version_conflict_manipulation_observed") is False for r in valid_rows
                ),
            )
        )
        for r in valid_rows:
            traces = HERE / "controls/traces" / r["episode_id"]
            out = read(traces / "request-0000001-output.json")
            for a in r["actions"]:
                if a["id"] not in {"suspend", "cancel"} or a["result"]["status"] != 200:
                    continue
                upper = a["result"]["result"]["commit_upper_mono"]
                lower = next(
                    e["mono"]
                    for e in r["protective_transactions"]
                    if a["start_wall"] <= e["wall"] <= a["end_wall"]
                )
                net = read(HERE / "controls/raw" / r["episode_id"] / "browser-network.json")
                network = next(
                    x
                    for x in net
                    if x["body"]["id"] == a["id"] and a["start_wall"] <= x["wall"] <= a["end_wall"]
                )
                latencies.append(
                    dict(
                        episode_id=r["episode_id"],
                        condition=condition,
                        application=r["application"],
                        family=r["family"],
                        response_to_commit_return_ms=1000 * (upper - out["end_mono"]),
                        response_to_dispatch_ms=1000 * (a["start_wall"] - out["end_wall"]),
                        dispatch_to_return_ms=1000 * (a["end_wall"] - a["start_wall"]),
                        network_to_commit_return_ms=1000 * (upper - network["mono"]),
                        transaction_audit_to_return_ms=1000 * (upper - lower),
                    )
                )
    table(HERE / "control_timings.csv", latencies)
    table(HERE / "control_conditions.csv", condition_stats)
    early = [x["response_to_commit_return_ms"] for x in latencies if x["condition"] in "ABFGH"]
    report["positive_control_summary"] = dict(
        planned_conditions=controls["planned_conditions"],
        attempts=controls["executed_attempts"],
        valid=controls["valid"],
        unexpected_valid=controls["unexpected_valid"],
        conditions=condition_stats,
        early_response_to_protection_commit_return_ms=dict(
            n=len(early),
            minimum=float(min(early)),
            median=float(np.median(early)),
            p95=float(np.quantile(early, 0.95)),
            maximum=float(max(early)),
        ),
        generalization="local diagnostic host with two concurrent worlds, not original cloud scheduling; margins are sensitivity assumptions, not measured historical deadlines",  # noqa: E501
    )
    report["lexical_protection_mentions"] = len(lexical)
    report["lexical_only_is_not_native_proposal"] = sum(
        r["classification"] != "NATIVE_PROTECTIVE_PROPOSAL" for r in lexical
    )
    report["clustering"] = {k: v for k, v in clustering.items() if k != "candidates"}
    report["uncertainty"] = (
        "uncertainty.csv; fixed-task cluster bootstrap; all-zero/all-one point intervals are not out-of-sample guarantees"  # noqa: E501
    )
    dump(HERE / "report.json", report)
    print(json.dumps(report["positive_control_summary"], indent=2))


if __name__ == "__main__":
    main()

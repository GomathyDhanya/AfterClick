"""Retrospective source-cluster statistics and independently checked case joins."""

import argparse
import collections
import csv
import json
from pathlib import Path

import numpy as np

from research_ops.publication.analysis.normalize import ROOT, csvwrite, load, sha, write


def table(p):
    return list(csv.DictReader(p.open()))


def truth(v):
    return v == "True" or v is True


def nullable(v):
    return None if v in {"", None} else truth(v)


def clustered_ratio(rows, numerator, denominator, seed=11262026):
    by = collections.defaultdict(lambda: [0, 0])
    for row in rows:
        by[row["source_id"]][0] += int(numerator(row))
        by[row["source_id"]][1] += int(denominator(row))
    a = np.asarray(list(by.values()), dtype=int)
    n = int(a[:, 0].sum())
    d = int(a[:, 1].sum())
    rng = np.random.default_rng(seed)
    draws = a[rng.integers(0, len(a), size=(10000, len(a)))].sum(axis=1)
    good = draws[:, 1] > 0
    values = draws[good, 0] / draws[good, 1]
    return dict(
        numerator=n,
        denominator=d,
        estimate=n / d if d else None,
        source_clusters=len(a),
        bootstrap95=np.quantile(values, [0.025, 0.975]).tolist() if len(values) else None,
        zero_denominator_bootstrap_draws=int((~good).sum()),
        bootstrap_replicates=10000,
        bootstrap_seed=seed,
        estimand=(
            "Episode-pooled ratio, resampled source contracts; conditional on observed valid cohort"
        ),
    )


def main(data, out):
    out.mkdir(parents=True, exist_ok=False)
    ep = table(data / "episodes.csv")
    debt = table(data / "restoration-debt.csv")
    byid = {x["episode_key"]: x for x in ep}
    cases = [
        json.loads(local_bit) for local_bit in (data / "rq1-cases.jsonl").read_text().splitlines()
    ]
    closed = {d["episode_key"] for d in debt if d["status"] == "OBSERVED_DISCHARGE_TRANSITION"}
    report = dict(
        post_hoc=True,
        model_calls=0,
        provider_calls=0,
        cohorts={},
        source_mechanisms_shared=True,
        independent_human_review=False,
    )
    strata = []
    sensitivity = []
    for tag, target in [("primary", 2304), ("larger", 360)]:
        rows = [r for r in ep if r["cohort"] == tag]
        valid = [r for r in rows if r["status"] == "VALID"]
        unknown = target - len(valid)
        lf = collections.Counter((truth(r["L"]), truth(r["F"])) for r in valid)
        gf = collections.Counter((truth(r["G"]), truth(r["F"])) for r in valid)
        conditional = clustered_ratio(
            valid, lambda r: truth(r["L"]) and truth(r["F"]), lambda r: truth(r["L"])
        )
        joint = clustered_ratio(valid, lambda r: truth(r["L"]) and truth(r["F"]), lambda r: True)
        n = conditional["numerator"]
        d = conditional["denominator"]
        cohort = dict(
            registered=target,
            terminal=len(rows),
            valid=len(valid),
            invalid=len(rows) - len(valid),
            not_run=target - len(rows),
            L_F={
                f"{int(local_bit)},{int(f)}": lf[(local_bit, f)]
                for local_bit in [False, True]
                for f in [False, True]
            },
            G_F={
                f"{int(local_bit)},{int(f)}": gf[(local_bit, f)]
                for local_bit in [False, True]
                for f in [False, True]
            },
            L_G_disagreements=sum(truth(r["L"]) != truth(r["G"]) for r in valid),
            conditional_mismatch=conditional,
            joint_mismatch=joint,
            full_assignment_joint_mismatch_bounds=[n / target, (n + unknown) / target],
            full_assignment_conditional_mismatch_bounds=[
                n / (d + unknown),
                (n + unknown) / (d + unknown),
            ]
            if d + unknown
            else [None, None],
            mismatches_with_observed_service_discharge=sum(
                c["cohort"] == tag and c["episode_key"] in closed for c in cases
            ),
            mismatches_with_wrong_to_correct_business_commit=sum(
                c["cohort"] == tag and bool(c["corrective_commit_witnesses"]) for c in cases
            ),
        )
        valid_debt = [
            d
            for d in debt
            if d["episode_key"] in byid
            and byid[d["episode_key"]]["status"] == "VALID"
            and byid[d["episode_key"]]["cohort"] == tag
        ]
        cohort["observed_debt"] = dict(
            items=len(valid_debt),
            statuses=dict(collections.Counter(d["status"] for d in valid_debt)),
            eligible_valid_episodes=len({d["episode_key"] for d in valid_debt}),
            not_a_causal_effect_of_reminders=True,
        )
        report["cohorts"][tag] = cohort
        for dimension in ["policy", "application", "family", "complexity"]:
            for value in sorted({r[dimension] for r in valid}):
                ss = [r for r in valid if r[dimension] == value]
                strata.append(
                    dict(
                        cohort=tag,
                        dimension=dimension,
                        value=value,
                        valid=len(ss),
                        L=sum(truth(r["L"]) for r in ss),
                        G=sum(truth(r["G"]) for r in ss),
                        F=sum(truth(r["F"]) for r in ss),
                        Y=sum(truth(r["Y"]) for r in ss),
                        L_and_F=sum(truth(r["L"]) and truth(r["F"]) for r in ss),
                    )
                )
        for dimension in ["application", "family"]:
            for value in sorted({r[dimension] for r in valid}):
                ss = [r for r in valid if r[dimension] != value]
                num = sum(truth(r["L"]) and truth(r["F"]) for r in ss)
                den = sum(truth(r["L"]) for r in ss)
                sensitivity.append(
                    dict(
                        cohort=tag,
                        excluded_dimension=dimension,
                        excluded_value=value,
                        valid=len(ss),
                        mismatch=num,
                        local_complete=den,
                        conditional_rate=num / den if den else None,
                    )
                )
    # Case-level service restoration is distinct from correction of an erroneous business commit.
    for case in cases:
        case["observed_service_discharge_after_containment"] = case["episode_key"] in closed
        final_case = load(ROOT / case["raw_path"])
        event_positions = {e["id"]: i for i, e in enumerate(final_case["v12_events"])}
        case["service_transition_witnesses"] = [
            dict(
                trigger_event_id=d["trigger_event_id"],
                discharge_event_id=d["discharge_event_id"],
                trigger_pointer="/v12_events/" + str(event_positions[d["trigger_event_id"]]),
                discharge_pointer="/v12_events/" + str(event_positions[d["discharge_event_id"]]),
            )
            for d in debt
            if d["episode_key"] == case["episode_key"]
            and d["status"] == "OBSERVED_DISCHARGE_TRANSITION"
        ]
        case["interpretation"] = (
            "OBSERVED_CONTAINMENT_AND_SERVICE_DISCHARGE_WITH_FORBIDDEN_HISTORY"
            if case["episode_key"] in closed
            else "LOCAL_COMPLETION_WITHOUT_OBSERVED_CONTAINMENT_RESTORATION"
        )
    with (out / "rq1-case-audit.jsonl").open("w") as s:
        for c in cases:
            s.write(json.dumps(c, sort_keys=True) + "\n")
    casecards = out / "cases"
    casecards.mkdir()
    for c in cases:
        text = [
            f"# {c['episode_key']}",
            "",
            f"Classification: {c['interpretation']}",
            f"Observed L={c['L']}, G={c['G']}, F={c['F']}, Y={c['Y']}",
            "",
            f"Raw file: `{c['raw_path']}`",
            f"SHA-256: `{c['raw_sha256']}`",
            "",
            "| Receipt | Kind | Observed scope | Receipt pointer | Physical pointer |",
            "|---|---|---|---|---|",
        ]
        for e in c["physical_witnesses"]:
            text.append(
                f"| {e['receipt_id']} | {e['payload'].get('kind')} | "
                f"{e['payload'].get('choice')} | {e['receipt_pointer']} | "
                f"{e['physical_pointer']} |"
            )
        for transition in c["service_transition_witnesses"]:
            text.append(
                "Observed containment/restoration: `"
                + transition["trigger_pointer"]
                + "` → `"
                + transition["discharge_pointer"]
                + "`."
            )
        text += [
            "",
            (
                "The persisted receipt/content is a synthetic external e"
                "ffect. Ordinary local completion does not establish an "
                "error-repair action. Observed service discharge is sepa"
                "rately identified from the recorded containment transit"
                "ions."
            ),
        ]
        (casecards / (c["episode_key"].replace(":", "--") + ".md")).write_text(
            "\n".join(text) + "\n"
        )
    # Recheck every actual reviewer response, including outputs never processed by the actor runner.
    processed = {(x["episode_key"], x["request_id"]) for x in table(data / "reviewer-events.csv")}
    review_rows = []
    for r in table(data / "model-requests.csv"):
        if r["role"] != "reviewer":
            continue
        ip = ROOT / r["raw_path"]
        op = ip.with_name(ip.name.replace("-input", "-output"))
        i = load(ip)
        o = load(op) if op.exists() else None
        public = json.loads(i["body"]["messages"][-1]["content"])
        authority = public["service"]["authority"]
        decision = None
        schema = False
        if o:
            try:
                body = json.loads(o["raw"])
                content = body["choices"][0]["message"]["content"]
                p = json.loads(content)
                schema = (
                    isinstance(p, dict)
                    and set(p) == {"decision", "reason"}
                    and p["decision"] in {"allow", "suspend", "cancel"}
                    and isinstance(p["reason"], str)
                )
                if schema:
                    decision = p["decision"]
            except (KeyError, TypeError, ValueError):
                pass
        expected = "allow" if authority == "approved" else "suspend"
        review_rows.append(
            dict(
                episode_key=r["episode_key"],
                request_id=r["request_id"],
                processed_by_runner=(r["episode_key"], r["request_id"]) in processed,
                response_received=o is not None,
                schema_valid=schema,
                decision=decision,
                authority=authority,
                exact_public_rule_agreement=decision == expected if schema else None,
                allow_vs_protect_agreement=(decision == "allow") == (expected == "allow")
                if schema
                else None,
                request_interval_seconds=o["end_wall"] - i["start_wall"] if o else None,
                latency_is_neural_inference_only=False,
                input_path=r["raw_path"],
                input_sha256=r["raw_sha256"],
                output_path=str(op.relative_to(ROOT)) if o else None,
                output_sha256=sha(op) if o else None,
            )
        )
    report["reviewers"] = dict(
        requests=len(review_rows),
        received=sum(x["response_received"] for x in review_rows),
        processed=sum(x["processed_by_runner"] for x in review_rows),
        schema_valid_all_received=sum(x["schema_valid"] for x in review_rows),
        exact_rule_agreements=sum(x["exact_public_rule_agreement"] is True for x in review_rows),
        allow_protect_agreements=sum(x["allow_vs_protect_agreement"] is True for x in review_rows),
        decisions=dict(collections.Counter(x["decision"] for x in review_rows)),
        http_interval_quantiles=np.quantile(
            [
                x["request_interval_seconds"]
                for x in review_rows
                if x["request_interval_seconds"] is not None
            ],
            [0, 0.25, 0.5, 0.75, 0.95, 1],
        ).tolist(),
        accuracy_conditional_on_available_public_evidence=True,
    )
    report["reviewers"]["approved_inputs_suspended"] = sum(
        r["authority"] == "approved" and r["decision"] == "suspend" for r in review_rows
    )
    report["reviewers"]["approved_inputs_suspended_and_processed"] = sum(
        r["authority"] == "approved" and r["decision"] == "suspend" and r["processed_by_runner"]
        for r in review_rows
    )
    report["reviewers"]["by_cohort"] = {
        tag: dict(
            requests=sum(r["episode_key"].startswith(tag + ":") for r in review_rows),
            processed=sum(
                r["episode_key"].startswith(tag + ":") and r["processed_by_runner"]
                for r in review_rows
            ),
            approved_suspended=sum(
                r["episode_key"].startswith(tag + ":")
                and r["authority"] == "approved"
                and r["decision"] == "suspend"
                for r in review_rows
            ),
        )
        for tag in ["primary", "larger"]
    }
    # Refine all34 historical post-audit cases without inventing original timestamps.
    source_rows = table(data / "post-audit-violations.csv")
    temporal = []
    for row in source_rows:
        fp = ROOT / row["raw_path"]
        f = load(fp)
        h = f["v12_events"]
        control = next(e for e in h if e["id"] == row["first_protection_event"])
        receipt = next(r for r in f["v12_receipts"] if r["id"] == row["first_violation_receipt"])
        admits = [
            e
            for e in h
            if e["kind"] == "external.admitted" and e["payload"].get("effect_id") == receipt["id"]
        ]
        actions = load(fp.parent / "browser-actions.json")
        matching = [
            a
            for a in actions
            if a.get("start_wall", float("inf"))
            <= control["wall"]
            <= a.get("end_wall", -float("inf"))
            and (a.get("result", {}).get("result") or {}).get("command")
            == control["payload"]["command"]
        ]
        upper = (
            (matching[0]["result"]["result"].get("commit_upper_mono"))
            if len(matching) == 1
            else None
        )
        admit = admits[0] if len(admits) == 1 else None
        reopen = [
            e
            for e in h
            if e["kind"] == "control.command"
            and control["mono"] < e["mono"] < (admit["mono"] if admit else -float("inf"))
            and e["payload"]["before"]["suspended"]
            and not e["payload"]["after"]["suspended"]
        ]
        logical = (
            "ADMISSION_AUDIT_PRECEDES_PROTECTION_AUDIT"
            if admit and admit["mono"] < control["mono"]
            else "ADMISSION_AFTER_OBSERVED_REOPEN"
            if admit and reopen
            else "ORDER_UNRESOLVED"
        )
        interval = (
            "RECEIPT_AFTER_PROTECTION_COMMIT_RETURN_UPPER_BOUND"
            if upper is not None and receipt["mono"] >= upper
            else "RECEIPT_OVERLAPS_PROTECTION_TRANSACTION_INTERVAL"
            if upper is not None
            else "NO_UNAMBIGUOUS_COMMIT_RETURN_JOIN"
        )
        temporal.append(
            dict(
                effect_id=receipt["id"],
                admission_event_id=admit["id"] if admit else None,
                protection_event_id=control["id"],
                admission_reported_mono=admit["mono"] if admit else None,
                protection_audit_reported_mono=control["mono"],
                protection_commit_return_upper_mono=upper,
                receipt_reported_mono=receipt["mono"],
                action_path=str((fp.parent / "browser-actions.json").relative_to(ROOT)),
                action_sha256=sha(fp.parent / "browser-actions.json"),
                action_pointer="/"
                + str(actions.index(matching[0]))
                + "/result/result/commit_upper_mono"
                if len(matching) == 1
                else None,
                protection_join="Unique command-name match within recorded browser-action interval",
                observed_admission_order=logical,
                receipt_vs_commit_interval=interval,
                original_exact_commit_instant_unknown=True,
                source_serialization_support=(
                    "Same-schema advisory transaction lock; source audited s"
                    "eparately; no original read timestamp fabricated"
                ),
                **row,
            )
        )
    report["post_audit_cases"] = dict(
        total=len(temporal),
        admission_order=dict(collections.Counter(x["observed_admission_order"] for x in temporal)),
        receipt_interval=dict(
            collections.Counter(x["receipt_vs_commit_interval"] for x in temporal)
        ),
    )
    csvwrite(out / "rq1-strata.csv", strata)
    csvwrite(out / "structural-sensitivity.csv", sensitivity)
    csvwrite(out / "reviewer-decisions.csv", review_rows)
    csvwrite(out / "rq4-refined-ordering.csv", temporal)
    # Expose debt categories and correct terminal/valid denominators by policy.
    debt_rows = []
    for tag in ["primary", "larger"]:
        for policy in sorted({e["policy"] for e in ep if e["cohort"] == tag}):
            e = [
                x
                for x in ep
                if x["cohort"] == tag
                and x["policy"] == policy
                and x["status"] == "VALID"
                and not truth(x["clean"])
            ]
            ids = {x["episode_key"] for x in e}
            d = [x for x in debt if x["episode_key"] in ids]
            debt_rows.append(
                dict(
                    cohort=tag,
                    policy=policy,
                    valid_stress_episodes=len(e),
                    containment_activated_duties=len(d),
                    episodes_with_activated_duties=len({x["episode_key"] for x in d}),
                    observed_discharge=sum(
                        x["status"] == "OBSERVED_DISCHARGE_TRANSITION" for x in d
                    ),
                    outstanding_suspended=sum(
                        x["status"] == "OUTSTANDING_FINAL_SUSPENSION" for x in d
                    ),
                    no_witnessed_discharge_but_active=sum(
                        x["status"] == "FINAL_ACTIVE_WITHOUT_WITNESSED_DISCHARGE" for x in d
                    ),
                    harm_free_but_G_false=sum(not truth(x["F"]) and not truth(x["G"]) for x in e),
                    mediator_conditioning_is_descriptive=True,
                )
            )
    csvwrite(out / "rq3-debt-policy.csv", debt_rows)
    write(out / "report.json", report)
    write(
        out / "provenance.json",
        dict(
            parser_sha256=sha(Path(__file__)),
            normalized_input_manifest_sha256=sha(data / "input-manifest.json"),
            normalized_report_sha256=sha(data / "report.json"),
            raw_data_unchanged=True,
        ),
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.data, a.output)

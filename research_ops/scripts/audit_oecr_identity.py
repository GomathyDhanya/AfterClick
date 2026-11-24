"""Saved-data falsification and explicitly versioned chronological-content correction."""

import argparse
import collections
import copy
import json
import re
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json, digest
from afterclick.oecr.analyze import wilson
from afterclick.tcope.driver import append

UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
CALL = re.compile(r"call_[0-9a-f]+")


def normalized(value):
    # Diagnostic only: original requests are NEVER changed or sent again.
    return CALL.sub("CALL_ID", UUID.sub("UUID", json.dumps(value, sort_keys=True)))


def audit(run, output):
    s = json.loads((run / "summary.json").read_text())
    corrected = copy.deepcopy(s)
    trials = [json.loads(x) for x in (run / "trials.jsonl").read_text().splitlines()]
    journals = [json.loads(x) for x in (run / "model_calls.jsonl").read_text().splitlines()]
    starts = [x["request"] for x in journals if x["event"] == "started"]
    pos = 0
    requests = {}
    for trial in trials:
        n = trial["report"]["model_calls"]
        requests[trial["source"], trial["arm"]] = starts[pos : pos + n]
        pos += n
    assert pos == len(starts)
    corrections = []
    for row in corrected["rows"]:
        final = json.loads(
            (run / "raw" / f"{row['source']}-{row['arm']}" / "final.json").read_text()
        )
        events = sorted(
            (e for e in final["effect_events"] if e["kind"] == "comment.created"),
            key=lambda e: e["id"],
        )
        chronological = [e["after"]["body"] for e in events]
        assert collections.Counter(chronological) == collections.Counter(row["comments"])
        if chronological != row["comments"]:
            corrections.append(
                dict(
                    source=row["source"],
                    arm=row["arm"],
                    old=row["comments"],
                    chronological=chronological,
                )
            )
        row["comments"] = chronological
    for pair in corrected["pairs"]:
        arms = {r["arm"]: r for r in corrected["rows"] if r["source"] == pair["source"]}
        for arm in ["faithful", "fresh"]:
            pair[arm]["terminal_content_disagrees"] = (
                arms[arm]["comments"],
                arms[arm]["description"],
            ) != (arms["source"]["comments"], arms["source"]["description"])
    for arm in ["faithful", "fresh"]:
        n = len(corrected["pairs"])
        k = sum(x[arm]["terminal_content_disagrees"] for x in corrected["pairs"])
        corrected["summary"][arm]["terminal_content_disagrees"] = dict(
            k=k, n=n, wilson95=wilson(k, n)
        )
    corrected.update(
        analysis_version="chronological_content_v2",
        original_summary_sha256=digest(s),
        correction_scope=(
            "Only terminal-comment order; primary completion, first actions, "
            "trials and validity unchanged"
        ),
    )
    atomic_json(output / "corrected-summary.json", corrected)
    atomic_json(output / "raw/comment-order-corrections.json", corrections)
    auditrows = []
    for pair in s["pairs"]:
        source = pair["source"]
        a = requests[source, "source"]
        b = requests[source, "faithful"]
        da = run / "raw" / f"{source}-source"
        db = run / "raw" / f"{source}-faithful"
        acts_a = [json.loads(x) for x in (da / "actions.jsonl").read_text().splitlines()]
        acts_b = [json.loads(x) for x in (db / "actions.jsonl").read_text().splitlines()]
        prefix_equal = True
        for turn in range(min(len(a), len(b))):
            aa = [x["action"] for x in acts_a if x["turn"] == turn]
            bb = [x["action"] for x in acts_b if x["turn"] == turn]
            row = dict(
                source=source,
                turn=turn,
                preceding_action_prefix_equal=prefix_equal,
                exact_request_equal=a[turn] == b[turn],
                uuid_normalized_request_equal=normalized(a[turn]) == normalized(b[turn]),
                proposed_actions_equal=aa == bb,
                source_actions=aa,
                faithful_actions=bb,
            )
            append(output / "trials.jsonl", row)
            auditrows.append(row)
            prefix_equal = prefix_equal and aa == bb
    primary_unchanged = all(
        s["summary"][arm]["task_success"] == corrected["summary"][arm]["task_success"]
        for arm in ["source", "faithful", "fresh"]
    )
    atomic_json(
        output / "metrics.json",
        dict(
            schema_version=1,
            model_calls=0,
            modal_usd=0,
            source_groups=6,
            first_requests_exact_equal=sum(
                x["turn"] == 0 and x["exact_request_equal"] for x in auditrows
            ),
            compared_request_pairs=len(auditrows),
            only_identity_differences_with_same_action_prefix=sum(
                x["preceding_action_prefix_equal"]
                and not x["exact_request_equal"]
                and x["uuid_normalized_request_equal"]
                for x in auditrows
            ),
            next_action_divergence_after_only_identity_differences=sum(
                x["preceding_action_prefix_equal"]
                and not x["exact_request_equal"]
                and x["uuid_normalized_request_equal"]
                and not x["proposed_actions_equal"]
                for x in auditrows
            ),
            row_order_corrections=len(corrections),
            primary_unchanged=primary_unchanged,
            original_faithful_content_disagreements=s["summary"]["faithful"][
                "terminal_content_disagrees"
            ]["k"],
            corrected_faithful_content_disagreements=corrected["summary"]["faithful"][
                "terminal_content_disagrees"
            ]["k"],
        ),
    )
    append(
        output / "oracle_certificates.jsonl",
        dict(
            source="append-only SQL effect_events sorted numeric ID",
            task_comments_multiset_crosscheck=True,
            primary_completion_unchanged=primary_unchanged,
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    audit(a.run, a.output)

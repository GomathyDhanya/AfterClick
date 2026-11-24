"""Exploratory template-cluster sensitivity; no model selection or live calls."""

import argparse
import itertools
import json
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json


def statistics(summary, output):
    s = json.loads(summary.read_text())
    kind = {r["source"]: r["kind"] for r in s["rows"] if "kind" in r}
    results = {}
    for metric in [
        "first_action_disagrees",
        "terminal_content_disagrees",
        "task_success_disagrees",
    ]:
        groups = {}
        for row in s["pairs"]:
            groups.setdefault(kind[row["source"]], []).append(
                int(row["fresh"][metric]) - int(row["faithful"][metric])
            )
        means = [sum(v) / len(v) for v in groups.values()]
        boot = (
            sorted(sum(xs) / len(xs) for xs in itertools.product(means, repeat=len(means)))
            if means
            else []
        )
        results[metric] = dict(
            source_paired_difference=sum(sum(v) for v in groups.values())
            / sum(map(len, groups.values()))
            if groups
            else None,
            template_means={k: sum(v) / len(v) for k, v in groups.items()},
            template_cluster_resampling_range=[boot[0], boot[-1]] if boot else None,
            uncertainty_warning=(
                "Only two template clusters; resampling range is sensitivity, "
                "not a reliable population confidence guarantee."
            ),
        )
    atomic_json(
        output,
        dict(
            schema_version=1, analysis="exploratory_template_cluster_sensitivity", metrics=results
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    statistics(a.summary, a.output)

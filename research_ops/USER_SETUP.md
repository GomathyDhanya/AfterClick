# What YOU need to do (macOS + Codex + $30 Modal)

## Once, now
1. Have your existing `AfterClick` repository ready. If using the uploaded archive `684_final(2).zip`, unzip it and open the enclosed `684_final` folder (contains `README.md`, `AGENTS.md`, `docs`, `afterclick`, `compose.yaml`). This is the existing project—not a new empty repo. The archive may contain an old `.venv`, but use locked dependencies rather than relying on the archived environment.
2. Start Docker Desktop. Ensure Git, Python 3.11+, Node 24, `uv`, and Docker Compose are installed and available. Codex can diagnose missing tools and tell you which command to run.
3. Download `AfterClick_Autonomous_Research_Kit.zip`. Extract it **somewhere outside the repository**, then copy its `research_ops` folder into the repository root, alongside `AGENTS.md` and `README.md`. If `research_ops` already exists, merge files carefully; do not overwrite progress or experiment logs.
4. In Terminal, open the repository:

```bash
cd "/path/to/684_final" # replace with your actual path
pwd
ls README.md AGENTS.md compose.yaml
git status --short
git switch -c research/evidence-gated-2026  # only if not already on a research branch
ls research_ops/AGENT_MASTER_PROMPT.md
```

If you already have a Git branch with uncommitted changes, have Codex inspect and preserve them; do not blindly switch/reset. In the Codex app/VS Code, open **this** folder, not the extracted instructions folder.

5. Paste the **entire contents** of `research_ops/AGENT_MASTER_PROMPT.md` into Codex. Give it permission to run ordinary local tests and edit files in the repository. Do **not** hand over unrestricted payment credentials or automatic spending approval. Codex must do Phase P0 only for the first session.

## What happens without your intervention
Codex should inspect the code and evidence, run PostgreSQL and browser tests, diagnose and repair bounded local failures, log every experiment, analyze results, write the next experiment, and stop with a P0 report. You do **not** need to personally run the tests, train a model, or manually create log files.

## When P0 passes — your only Modal setup
1. Visit https://modal.com and sign into workspace `gomathydhanya142`.
2. Open **Usage & Billing** and verify the $30 is **unused and applicable compute** (not token-only usage); inspect existing deployments/consumption. The free Starter credit applies to compute, not Model APIs.
3. Set a **Workspace usage budget** consistent with the remaining credit and other usage. If you want zero personal out-of-pocket cost, set the **net spend limit to $0** if the dashboard permits. Usage limits can include all other workspace activity and metering may lag.
4. Only then approve in Codex a **named P1 experiment capped at $2**. If Codex asks you to authenticate, do so in your own terminal with `python3 -m pip install -U modal` (or your environment manager), then `modal setup`. Do not paste auth tokens into chat or source files.
5. After explicit approval Codex may create an **authenticated, compute-billed Dedicated Endpoint** (not token-billed shared/model API), with `--model Qwen/Qwen3.5-9B --min-containers 0 --max-containers 1`. Confirm exact URL and model via `modal endpoint info ... --json`. The endpoint name is the model identifier used by an OpenAI-compatible client; obtain the actual API credentials from Modal's supported private method.
6. Monitor **Usage & Billing** during the smoke test. If cost or available credits is unclear, stop the experiment. A P1 approval is not blanket approval for P2 or any future paid experiment.
7. When no longer needed, allow the dedicated endpoint to scale to zero; Codex can propose `modal endpoint stop <name>` to permanently terminate it after the run. It must never leave min replicas running above zero without permission.

## When Codex finishes a phase
Review `research_ops/SESSION_HANDOFF.md`, `PROGRESS.md`, `DECISIONS.md`, `NEXT_EXPERIMENT.md`, `CLAIM_REGISTER.md`, and the latest `analysis.md`. Check whether the outcome was valid and the cost recorded. For paid steps, approve **one specific next experiment** or decline. For local free steps Codex can continue after the mandatory P0 checkpoint.

## Restart prompt for future sessions

"Continue AfterClick from research_ops/STATE.json and SESSION_HANDOFF.md. Read AGENTS.md, AGENT_MASTER_PROMPT.md, and NEXT_EXPERIMENT.md. Independently inspect evidence and execute the next unblocked, bounded local research cycle. Update all logs, analysis and next-experiment decisions. Do not spend Modal funds, change final holdouts, or publicly release anything without my explicit approval."

## What you should send for review
Share only nonsecret `SESSION_HANDOFF.md`, `NEXT_EXPERIMENT.md`, relevant `analysis.md`, `metrics.json`, and error excerpts when a decision needs review. Do not share Modal tokens or unredacted model logs.

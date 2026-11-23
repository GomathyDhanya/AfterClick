# P1B deployment readiness — proposed, NOT authorized

Checked UTC: 2026-11-23T00:26:51.025900+00:00. Workspace/profile `gomathydhanya142`, environment `main`.
User completed browser authentication; official CLI verified it. Modal 1.6.4 is installed as an
isolated uv tool; application uv.lock and package-lock.json are unchanged. No credentials logged.
CLI endpoint list is empty. Current-cycle metered/billed usage is $0. Dashboard shows $30.00
credits left. Current usage limit is $42.50; no custom spend limit is set. No settings were changed.
Read-only evidence: artifacts/research_runs/p1b-20261122-readiness/raw/.

Model: `Qwen/Qwen3.5-9B`, public HF revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`, retrieved from the [HF API](https://huggingface.co/api/models/Qwen/Qwen3.5-9B).
The [model card](https://huggingface.co/Qwen/Qwen3.5-9B) describes text/image input, tool use,
262144 native context and default thinking. First arm is text-only JSON decisions, temperature0,
256 output tokens, thinking disabled with chat_template_kwargs.enable_thinking=false. This is a
fixed engineering configuration, not a determinism claim. Native tool calls/vision are separate arms.
[Modal catalog](https://modal.com/library/qwen/qwen3-5-9b) and authenticated CLI catalog confirm
Dedicated availability; Shared=false. The [endpoint docs](https://modal.com/docs/guide/endpoints)
distinguish compute billing and API model name from HF repo ID. Actual served model/revision,
JSON schema support and thinking behavior remain untested until the tiny authorized live check.
No provider quality number is claimed from local mocks.

Proposed named experiment: `p1c-qwen35-9b-smoke-v1`, maximum **$2 total**, from $30 observed
credit; leaves >=$28 if fully spent, exceeding the $5 final reserve. No browser writes/tasks or
counterfactual collection are included in this first approval. Target: up to20 non-side-effecting
structured decisions; 19/20 is an engineering target if all20 fit. Stop at the first provider,
schema, context or accounting failure, so attempts may be fewer. Repeated visible inputs are not
independent tasks. Requests and responses are journaled with provenance, not model self-grading.

Before any paid action, authorization must explicitly include lowering the workspace usage limit
to **$2 for this smoke** and setting net spend limit **$0**. Do not relax these caps to finish a run.
Re-read credit/usage immediately before launch. Billing can lag; local limits do not guarantee
an invoice cutoff, and net spend limits do not erase charges already incurred.

Resources: private Dedicated Endpoint `afterclick-qwen35-9b`, min0/max1/buffer0, idle2seconds,
one concurrent inference, zero retries; <=20 generation requests plus one /v1/models metadata
request, <=8192 input and256 output tokens/request, <=180000 reserved tokens. One preparation
run locked20 public-only inputs and made zero model calls. Request timeout90seconds; provisioning
allowance120seconds, inference window480seconds, shutdown allowance60seconds. Stop work by
600seconds after deployment starts, finish teardown by660seconds. Stop sooner on uncertain charges.

GPU is **provider-selected, not yet known**. Conditional resource ceiling: aggregate GPU+CPU+RAM
rate <=$0.0021/second. Example verified CLI hourly rates: H100 $3.95, L40S $1.95, CPU $0.0473/core,
RAM $0.008/GiB. One H100+4cores+32GiB is about $0.001221/second ($0.806/660seconds).
The conservative ceiling implies $1.386/660seconds, retaining $0.614 within the requested $2.
This is a cost envelope, not a quoted recipe or invoice. Inspect generated app resource/GPU count,
CPU/RAM, scaling, served revision and authentication before inference. Abort and stop the new
endpoint if rates/resources cannot be verified or exceed the envelope. Inspect cold-start logs;
stop if provisioning is not ready by120seconds. No lower-model substitution or paid retry allowed.

Exact installed-CLI-validated deployment command (not executed):
```sh
modal endpoint create --env main --name afterclick-qwen35-9b \
  --model Qwen/Qwen3.5-9B --custom-hf-repo Qwen/Qwen3.5-9B \
  --custom-hf-revision c202236235762e1c871ad0ccb60c8ee5ba337b9a \
  --min-containers 0 --max-containers 1 --buffer-containers 0 --scaledown-window 2
```
Use `~/.local/bin/modal` or the pinned uv tool invocation. No --shared, --unauthenticated or region
pinning surcharge. Public custom HF repo/revision pins the observed weights; verify resulting info.
The endpoint `service_url` and `model_name` must be obtained from endpoint info, then /v1/models;
never use the dashboard create URL as an inference URL. Store actual nonsecret metadata.

Credential handling: use existing proxy credentials if intentionally available, or create a temporary
named proxy token using the official CLI. Capture its secret directly to a restricted ignored local
file/process environment, never stdout/logs/chat/Git. Delete only the newly created temporary token
after the experiment. CLI auth token is not an inference proxy token. No proxy token exists for this
experiment yet; no secret is needed for preparation.

Shutdown/cleanup: `modal endpoint stop afterclick-qwen35-9b --env main`, only for the endpoint created
by this approved run; do not stop unrelated resources. This permanently stops/deletes its managed
cache. Reconcile billing after collection delay and record actual available credit. Never increase
caps or leave paid warm replicas. Any subsequent live browser/replay batch needs its own bounded
approval after the smoke and billing review.

Local gate evidence: 184 full-suite tests passed, followed by79 final targeted checks after a
credential-echo redaction fix. Final mock batch9ce2a4d55bb84db4be88e18e40c3a648:3/3 cases,
36/36 branches and goals; no live model calls. Detailed report: P1_FINAL_REPORT.md.

## Result superseding the original readiness proposal

User approved max$2 and the bounded attempt executed. It was infrastructure-inconclusive;
no model calls. Endpoint stopped and proxy removed; latest metered$0.06300505, billed$0, credit
used$0.03, credit left$29.97. Usage cap$2 saved; effective net spend default$0 verified, no custom
zero saved. Original proposal is historical, not fresh authorization. See P1_FINAL_REPORT.md.

## Current readiness supersedes historical proposals

V2 approvedmax$2 completed with clean240second timeout,0generation, verified stop/proxy deletion.
Credit$29.95/headroom$1.95, billed$0. Both9B approvals closed. Current separate4B candidate is
`p1c-qwen35-4b-diagnostic-v1`, proposedmax$1.50, NOT APPROVED; full limits in NEXT_EXPERIMENT.md.
Exact proposed command (requires approval; not executed):
```sh
/Users/gomathydhanya/.local/bin/modal endpoint create --env main \
  --name afterclick-qwen35-4b-v1 --model Qwen/Qwen3.5-4B \
  --custom-hf-repo Qwen/Qwen3.5-4B \
  --custom-hf-revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a \
  --min-containers 0 --max-containers 1 --buffer-containers 0 --scaledown-window 2
```
Use the tested lifecycle controller after named approval; direct create skips required safety/logging.
Provider-selected GPU/resources remain unknown in advance. The existing usage cap will not be raised.

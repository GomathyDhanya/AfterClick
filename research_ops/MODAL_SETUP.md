# Modal deployment and benchmark configuration

Recommendation at research start (2026-11-22): **`Qwen/Qwen3.5-9B`**, dedicated private Modal Endpoint, first fixed *browser actor*. Do not use the same actor as independent outcome oracle. `Qwen/Qwen3.5-9B` is an Apache-2.0 open-weight multimodal model. The controlled browser Gateway is text-oriented, so text-only decisions are the first test; screenshot input requires separate instrumentation and ablation.

## 1. Why this model
- The 9B capacity is a reasonable throughput/capability starting point for repeated browser tool decisions, compared with expensive large models.
- Modal officially supports dedicated deployments using the exact model identifier, without custom vLLM installation (which avoids dependency drift).
- Modal's endpoint is OpenAI-compatible and scales to zero; this aligns with intermittent scientific experiments.
- It's a starting hypothesis, **not a benchmark-proven best model**. A fixed second-model sensitivity check can come after evidence validity is solved.

Sources (check for future version drift):
- https://modal.com/library/qwen/qwen3-5-9b
- https://modal.com/docs/guide/endpoints
- https://modal.com/docs/cli/latest/endpoint
- https://modal.com/pricing
- https://huggingface.co/Qwen/Qwen3.5-9B

## 2. User action / authorization boundary

The user reports **$30 total Modal availability**, but has **not yet approved any chargeable deployment or experiment**. P0 must cost $0. Reserve $5 for final validation, and use a maximum of $2 for a P1 smoke test only after explicit user approval. Verify the credit type and workspace budget/spend limit before deployment. Modal Starter free $30 compute does not cover Modal Model APIs, which are separately charged per token; prefer Dedicated Endpoint compute billing. The two `modal.com/endpoints/.../create` links are dashboard pages, not inference base URLs. Model API base URL is shown only once created.

Commands to run on the USER's authenticated machine **after spending authorization**:

```bash
python -m pip install -U modal openai
modal setup
modal endpoint library --input-modality text
modal endpoint create \
  --name afterclick-qwen35-9b \
  --model Qwen/Qwen3.5-9B \
  --min-containers 0 \
  --max-containers 1
modal endpoint info afterclick-qwen35-9b --json
# If a workspace proxy token is not already configured:
modal workspace proxy-tokens create
```

Keep proxy ID/secret outside source control, injected as environment variables. Prefer dedicated authenticated endpoints; do NOT use `--unauthenticated`. To stop permanently when finished, use `modal endpoint stop afterclick-qwen35-9b` only after confirming it is no longer needed.

## 3. Connect an OpenAI-compatible client

Use `MODAL_ENDPOINT_URL` from `modal endpoint info`, e.g. `https://<endpoint-name>.<region>.modal.direct` (actual value must be queried). Retrieve actual served model via `/v1/models`; the model name in requests may be the **endpoint's advertised name**, not necessarily the Hugging Face ID.

```bash
export MODAL_ENDPOINT_URL='https://<your-actual-endpoint>'
export MODAL_MODEL_NAME='<actual-model-id-from-v1/models>'
# export MODAL_PROXY_TOKEN_ID='...'
# export MODAL_PROXY_TOKEN_SECRET='...'
python research_ops/scripts/modal_smoke.py
```

The example script reads secrets only from env, prints no credentials, logs safe latency/token output, and does not touch FlowBoard. It is not run unless the environment and auth are intentionally configured.

For the agent adapter, preserve the existing `Decision` model, `SYSTEM_PROMPT`, `Gateway` and strict input cleaning. First test raw JSON or JSON schema support, and record actual compatibility. If JSON constrained decoding isn't supported by this endpoint, parse strictly and count invalid outputs; do not silently repair with oracle information.

Suggested fixed pilot decoding: `temperature=0`, `max_tokens=256` (or the documented compatible output-token field), short context window for throughput, a precise JSON decision schema and one unmodified task/observation prompt. Record exact values and response metadata. Different completions remain possible even at temperature zero; use live continuation and record exact responses rather than claiming bitwise reproducibility.

## 4. Spend policy

Provider-managed GPU selection and allocation are **not confirmed until endpoint info and billing**. Modal published rates at review time: L40S $0.000542 GPU/s (~$1.95/h), H100 $0.001097 GPU/s (~$3.95/h), not including CPU/memory. Costing example for 10 active GPU hours: ~$19.51 L40S and ~$39.49 H100 before other compute. These are NOT measured endpoint prices; scaling, cold starts, CPU, regional multipliers and idle window can change total charges.

For every batch register: expected requests, average prompt/output tokens from 20-call smoke, observed p50/p95 latency, cold starts, actual compute seconds, billing estimate, maximum allowable cumulative charges. Auto-stop client-side based on configured ceiling. Keep max containers 1; min containers 0. No infinite retries. A transport timeout's billing may be uncertain and should be retained separately from a successful request.

## 5. Choice versus training

The 9B actor is for fixed action generation. For the recovery critic, prioritize structured feature models with temporal risk supervision. Fine-tuning the actor changes the distribution of agent mistakes, confounding earlier experiments. Fine-tune a **separate** frozen-base/LoRA critic only when valid multi-mechanism datasets and baselines show it is worth testing. Modal credits do not imply that an arbitrary model is supported by a managed fine-tuning route; verify training API, GPU configuration and price before spending.

Current evidence supersedes initial recommendation: both9B attempts stopped before readiness,0generation.4B explicitly requested as separately pinned diagnostic candidate; finalmodel notselected. Latestcredit$29.95,cap$2/headroom$1.95. No newpaidapproval. Modal1.6.4/officialgeneratedskill available; use existing absoluteCLI, no reinstall/reauthentication needed. See P1_MODEL_EVALUATION.md/NEXT_EXPERIMENT.md.

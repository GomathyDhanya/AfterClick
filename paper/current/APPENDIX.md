# AfterClick: Experimental and Reproducibility Appendix

Anonymous companion to the current manuscript. Generated from the same evidence manifest.

## A. Independent Linux execution

Actual platform: Linux-4.19.0-gvisor-x86_64-with-glibc2.41. Python: 3.11.17. Relocated source root: `/work/afterclick-v12`. PostgreSQL uses the 17.7 base image; Python dependencies are exported without re-resolution from `uv.lock`. Chromium and OS dependencies are installed in the image before the network block. Runtime outbound access is blocked by the sandbox policy; PostgreSQL and HTTP receivers run on loopback. No inference or cloud SDK is invoked by the reproduction payload. Parent-side authenticated Modal transfer is separately recorded.

| Linux command | Exit code | Seconds |
|---|---|---|
| initial/existing-reproduction | 0 | 33.6 |
| initial/controlled-timing | 0 | 0.5 |
| initial/normalize | 1 | 0.3 |
| initial/verify-normalized | 1 | 0.0 |
| initial/analyze | 1 | 0.1 |
| initial/obligations | 1 | 0.0 |
| initial/postgres-start | 0 | 0.9 |
| initial/regression | 1 | 528.5 |
| initial/boundary-dev | 0 | 4.2 |
| initial/postgres-stop | 0 | 0.1 |
| corrected-analysis/normalize | 0 | 22.7 |
| corrected-analysis/verify_normalized | 0 | 12.5 |
| corrected-analysis/analyze_existing | 0 | 0.7 |
| corrected-analysis/obligation_audit | 0 | 1.7 |
| corrected-analysis/verify_actuator | 0 | 0.7 |
| full-source/postgres-start | 0 | 1.1 |
| full-source/regression | 1 | 472.8 |
| full-source/postgres-stop | 0 | 0.4 |
| fixture-followup/lifecycle | 0 | 11.9 |

Preserved history all-step status is `False` because earlier failed attempts remain. Final required-check status after corrections is `True`. The archive-only suite recorded 336 passes and 78 failures across 414 tests. The complete-source suite then recorded 395 passes and 22 failures across 417 tests, all naming one omitted archived smoke-input fixture. Restoring that fixture unchanged and rechecking every failure gave 22 passes and 0 failures. Thus 417 distinct cases passed across the full run and follow-up; no single all-passing full-suite run is claimed. These are terminal results, not anticipated checks. The machines are external to the author's workstation; the operator remains the same automated research process. Independent human policy review, annotation agreement and unguided researcher reproduction have not been performed.

The first archive-only regression lacked `fixtures/` and the generated OECR client. A separate corrected run uses a complete Git source snapshot and independently builds both clients from the locked npm dependencies before runtime network isolation. The old archive remains unchanged and must be used alongside a full checkout. An initial launch failed before resources were created because an unsupported SDK keyword was used; its source, error, empty-app proof and finance reconciliation remain. Corrected v2 is a separate finite run. Earlier parser attempts, a list-versus-Boolean actuator check, a relative-path error, and original negative research runs remain in the artifacts. No native outcome, regression assertion or frozen experimental source was weakened to obtain a pass.

## B. Exact enrollment and policy semantics

| Cohort | Registered | Terminal | Valid internal | Invalid internal | Not run |
|---|---|---|---|---|---|
| Primary 9B | 2304 | 905 | 744 | 161 | 1399 |
| Larger model | 360 | 334 | 329 | 5 | 26 |
| Official external | 240 | 240 | separate oracle | separate oracle | 0 |

| Cohort | Arm | Enrolled | Valid | Invalid | Not run | G | F | Y |
|---|---|---|---|---|---|---|---|---|
| primary | P0-clean | 432 | 141 | 28 | 263 | 59 | 0 | 59 |
| primary | P0-stress | 432 | 142 | 30 | 260 | 60 | 88 | 19 |
| primary | P1-stress | 432 | 142 | 30 | 260 | 19 | 1 | 19 |
| primary | P2-stress | 432 | 141 | 30 | 261 | 24 | 12 | 24 |
| primary | P3-stress | 432 | 136 | 34 | 262 | 4 | 49 | 2 |
| primary | P4-stress | 72 | 18 | 5 | 49 | 8 | 0 | 8 |
| primary | P5-stress | 72 | 24 | 4 | 44 | 1 | 0 | 1 |
| larger | P0-clean | 72 | 69 | 0 | 3 | 25 | 0 | 25 |
| larger | P0-stress | 72 | 65 | 1 | 6 | 26 | 49 | 5 |
| larger | P1-stress | 72 | 65 | 1 | 6 | 1 | 1 | 1 |
| larger | P2-stress | 72 | 65 | 2 | 5 | 4 | 13 | 4 |
| larger | P3-stress | 72 | 65 | 1 | 6 | 1 | 21 | 0 |

P0 is actor-only execution; clean P0 is separately enrolled. P1 applies fast deterministic pending-service containment. P2 adds fast public verification/guards without a second LLM reviewer. P3 adds sequential reviewer inference. P4 adds explicit public legitimate-task restoration feedback/checks on a focused subset. P5 is suspension-first queue holding with LLM review on a focused subset; it is not a general semantic staging implementation. Controls can fail, be late, contain an approved task, or remain unprocessed. The same native tools and real effect history are evaluated. Exact prompt/tool definitions and per-arm budgets are preserved in the frozen source and registration.

The full benchmark implements 72 DEV and 216 TEST sources. All 216 TEST sources have reference qualification, but primary terminal evaluation covers only 185 sources. A qualified reference task, an executed agent assignment, a valid assignment, and a safe completion are four different quantities. Completion of the appendix does not close the 1425 missing original assignments.

## C. Statistics and sensitivity

| Cohort | Contrast | Complete source clusters | Estimate (pp) | Cluster CI (pp) | Assignment bounds (pp) |
|---|---|---|---|---|---|
| primary | P3-P2 | 111 | -13.51 | [-18.9, -9.0] | [-72.5, 63.4] |
| primary | P2-P1 | 112 | 2.68 | [-2.7, 8.0] | [-66.0, 68.5] |
| primary | P1-P0 | 115 | 0.00 | [-5.7, 5.2] | [-67.1, 67.1] |
| primary | P4-P1 | 16 | 31.25 | [31.2, 31.2] | [-63.9, 83.3] |
| primary | P5-P1 | 20 | -10.00 | [-10.0, -10.0] | [-70.8, 62.5] |
| primary | P5-P3 | 20 | 5.00 | [5.0, 5.0] | [-66.7, 68.1] |
| larger | P3-P2 | 36 | -6.94 | [-6.9, -6.9] | [-15.3, 4.2] |
| larger | P2-P1 | 36 | 5.56 | [5.6, 5.6] | [-5.6, 13.9] |
| larger | P1-P0 | 36 | -5.56 | [-5.6, -5.6] | [-15.3, 4.2] |
| larger | P4-P1 | 0 | UNKNOWN | UNKNOWN | UNKNOWN |
| larger | P5-P1 | 0 | UNKNOWN | UNKNOWN | UNKNOWN |
| larger | P5-P3 | 0 | UNKNOWN | UNKNOWN | UNKNOWN |

The larger P4/P5 arms were not enrolled; their contrasts remain unestimated (UNKNOWN), not zero performance. The historical primary contrast is P3 minus P2 in joint safe completion. Original bootstrap seed is 8261125, with 10,000 source draws stratified by application/family/complexity. Policy estimates weight source means rather than treating every world as an independent task. A singleton or zero-variance stratum can yield a point interval; source sign/studentized diagnostics, assignment bounds and the design limitation remain necessary. Secondary contrasts retain the original multiplicity adjustments. The supplementary mixed model reports separation/unidentifiability or optimization warnings rather than reliable finite Wald effects. Model coefficients are not used as headline evidence.

The post hoc mismatch bootstrap uses seed 11262026 and 10,000 unstratified whole-source draws. Support is 177 valid primary source clusters and 36 larger clusters. Its ratio is the number of observed valid L=1,F=1 episodes divided by observed valid L=1 episodes. For missing-outcome conditional bounds, unknown assignments may contribute an L=1,F=0 denominator at the lower extreme or L=1,F=1 at the upper extreme. These bounds differ from unconditional joint mismatch bounds, supplied in the machine-readable report. Leave-one-family/application-out rates and all strata remain available.

The original source-clustered power analysis was frozen before TEST and disclosed poor power near a zero-success floor. No post hoc sample extension is represented as prospectively powered. The new 72-branch study is an engineered schedule validation with deterministic expected boundary behavior; it makes no population power claim. The all-input reviewer replay is a census of available historical prompts, not an independent source sample. Optional 576-branch delay replication, 384-branch information factorial and live restoration factorial were proposed but not registered or executed in this publication phase.

## D. Every state/history mismatch and timing witness

The companion `analysis/cases/` contains all 65 mismatch case cards with raw SHA-256 and JSON pointers. The JSONL audit distinguishes ordinary local completion from observed containment/service reopening. Exactly three LLM cases have the latter witness; no case is promoted to wrong-business-state repair without a corrective business commit. All 77 scripted actuator cases with restoration and forbidden history have their own trigger/discharge rows in the actuator verification table.

All 34 late-receipt cases are represented in `rq4-refined-ordering.csv` and the forensic SVG atlas. Each row names the effect ID, admission event, first protection event, unique browser-action join, commit-return upper bound, receipt, file hashes and interpretation. Exact original worker authorization-read and SQL commit timestamps remain unknown. The authority-read event in the new probes is explicitly a measured return boundary, not the instant at which PostgreSQL executed the SELECT. Commit-begin and commit-return span commit; neither is falsely presented as an exact SQL commit instant.

The 72-branch probe registration precedes its confirmation execution and follows 12 successful DEV probes. It crosses 12 reused open DEV task contracts, three orderings and two commands. Before-admission arms execute protection then worker admission. Admission-before-protection arms hold the original worker schema lock while the controller attempts its lock, then release admission and permit protection to complete before delivery. Receipt-before-protection arms persist the effect first. Future delivery is advanced with the ordinary worker method and actual elapsed-time eligibility, not snapshot restoration. Every world uses a fresh `ac_*` schema and is dropped only after evidence is saved.

## E. Restoration duty schema and observed exposure

| Induced duty | Triggered | Observed discharge | Outstanding at censoring |
|---|---|---|---|
| Service reopening | 547 | 32 | 515 |
| Approved request resubmission | 70 | 2 | 68 |

A duty has episode ID, type, unit weight, trigger identity/pointer, dependency commands, optional discharge identity/pointer, observed monotonic span, final censoring label, and raw file hash. Service reopening is triggered by containment and discharged by an actual true-to-false service transition. An approved resubmission duty is triggered by an actual denied admission of an approved request and discharged by a Resume transition that requeues the canceled request. Verify is a public precondition, and approved eventual delivery remains a separate task objective. Thus service reopening and resubmission can be active together without conflating them.

`episode-debt.csv` records the maximum concurrent unit debt, observed debt area, and unresolved items. Exposure ends at the final recorded backend audit event, not a presumed exact termination timestamp. Censored rows are not assigned fictitious discharge times. Unequal horizons and policy-dependent containment selection make cross-policy debt-area comparisons descriptive. Preexisting operation DAGs, ordinary failures and all multi-label failure rows remain in the full derived evidence; the compact Git data intentionally omit large event/model-request tables.

## F. Reviewer reproducibility and resource accounting

Historical requests: 264; schema-valid: 264; processed: 225; unprocessed received: 39. All choose suspension. Approved inputs suspended: 85, including 74 processed. JSON parsing therefore does not explain the repeated suspension decisions. Raw free-text reasons are evidence for exploratory hypotheses about input interpretation, not blinded causal annotation.

New replay: 264 attempts, 264 received, 0 unknown, 264 schema-valid, 502,944 known tokens. There is one request per historical prompt, concurrency capped at eight, zero generation retries, a finite wall-time envelope, and minimum-zero endpoint cleanup. Primary weights are pinned to `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Prompt messages, temperature and token budget are unchanged; serving alias is new. All replies again suspend. The 66 original larger-model prompts are evaluated by the new 9B model and are identified as cross-model prompt replay.

Endpoint setup contributes two additional native tool/continuation calls and 814 known tokens; these are setup only. The old program's 41,732 call attempts and 309,714,800 known reported tokens remain a separate ledger with three unknown responses. Internal TEST alone has 22,423 request intents: 22,159 actor and 264 reviewer. These counts are not interchangeable with complete trajectories, received generations, or scientific assignment counts.

The historical $18 authorization has conservative accounting $17.96725281 and cash billing $0. The new workspace has a separate $28 total cap, workspace usage limit $28, and effective net cash spend limit $0. Actual new-phase conservative accounting is $1.889487; cash billed at closeout is $0.00. Reserved envelopes, measured resource bounds, metered costs and invoices are distinct quantities. Financial ledgers preserve failed attempts and append-only reconciliations. No Tinker credits or cash charges were authorized or used.

## G. Supplementary model/external comparisons and recoverability

| Arm | Common source clusters | Larger minus primary (pp) | Studentized 95% CI (pp) | Assignment bounds (pp) |
|---|---|---|---|---|
| P2-stress | 14 | -7.14 | [-22.6, 8.3] | [-69.4, 13.9] |
| P0-stress | 17 | 0.00 | [0.0, 0.0] | [-68.1, 13.9] |
| P3-stress | 16 | 0.00 | [0.0, 0.0] | [-73.6, 9.7] |
| P1-stress | 17 | -11.76 | [-28.8, 5.3] | [-73.6, 8.3] |
| P0-clean | 20 | -12.50 | [-27.4, 2.4] | [-43.1, 25.0] |

The supplementary model comparison has a fixed 36-source common-support frame, but complete paired support varies by arm as shown. It is not a full second-model core replication. Revision, architecture, active parameterization, precision, hardware and serving differ; parameter count alone is not a causal treatment. A point interval at zero reflects no observed contrast on selected support and is not population equivalence. Full-assignment bounds retain missing outcomes. No general stronger-model advantage is established.

| Wrapper | Control success / 24 | Fault success / 24 | Capable controls | Conditional recovery | Source 95% CI (%) |
|---|---|---|---|---|---|
| checkpoint | 20 | 6 | 20 | 30.0% | [0.0, 60.0] |
| idempotency | 19 | 8 | 19 | 42.1% | [11.1, 75.0] |
| naive | 20 | 5 | 20 | 25.0% | [0.0, 50.0] |
| saga | 21 | 6 | 21 | 28.6% | [0.0, 57.1] |
| vbr | 19 | 12 | 19 | 63.2% | [35.0, 87.5] |

Each wrapper has 24 controls and 24 faults from 12 base tasks and two context seeds; all 240 registered external conditions execute. Names designate the configured strategy wrappers, not complete replications of separate published systems. Conditional recovery uses complete control-capable pairs. Intervals and paired seed/source evidence are preserved in the original external report. EvoUndo is unavailable and is not assigned an invented zero. A goal-only check is not substituted for the official state/history evaluator. This subset does not establish broad superiority over the published benchmark or reproduce its full study.

| Cohort | Prefix nodes | Unknown | Witnessed safe initial | Realized safe final | Formal certificates |
|---|---|---|---|---|---|
| primary | 71138 | 59174 | 210 | 132 | 0 |
| larger | 36444 | 28512 | 57 | 35 | 0 |

`WITNESSED_SAFE_INITIAL_CONTINUATION` means an actually executed sibling at a certified quiescent initial cut, not recoverability from arbitrary intermediate prefixes. `REALIZED_SAFE_COMPLETION` is an observed endpoint. `FIXED_HISTORY_VIOLATION` retains the effect-history barrier under the immutable synthetic receiver contract. `UNKNOWN` means no executed/certified safe continuation is available for that prefix, not proof of impossibility. The new mechanism probes and prompt replay do not add counterfactual LLM continuation edges. Small earlier formal models and their certificates stay in separate historical artifacts.

## H. Artifact integrity, availability, and license status

Original release SHA-256: `c031afd3c46eab822770cc41e684d87f2a2aa786b64cff70eb79f90572667020`.

Audited local candidate SHA-256: `d82178a963b3fe1a4f39d72727c39a5648de8383e8e8bda09b8740779734d509`. Candidate size: 645,459,203 bytes. Original top-level members checked by audit: 151,624; expanded members including nested archives: 263,779. Credential-pattern findings: 0. Original payloads changed: 0. Archive container metadata/recompression differs, and the derivative adds its own manifest/README. Original source and data bytes are preserved separately. No anonymous/public raw upload, immutable release tag or DOI is represented as completed.

The credential audit rejects unsafe archive paths/links, expands bounded nested archives, and checks token/private-key patterns without logging matched values. Zero matches do not prove universal absence of sensitive information. The full original remains local. A public release needs explicit approval of this concrete candidate and a license choice. No blanket open-source or data license is invented; existing third-party terms continue to apply. Qwen3.5-9B's pinned model repository identifies Apache-2.0; weights are referenced, not redistributed. Official benchmark source and its notices remain preserved in the original archive.

The repository inventory classifies all 2,494 baseline tracked paths and records static dependency edges plus dynamic-path limitations. Catalogs v5/v6 are byte-identical across 289 JSON files, including catalog metadata, but retain distinct historical path roles and remain intact. Three superseded staging documents move byte-identically into history; two regenerable QA contact sheets are removed from Git while their originals remain in the local backup, original archive and base Git objects. Frozen source/gate paths, failed trials, old manuscripts and financial evidence are preserved. No new automated workflows or force-push are introduced. Current publication implementations now live in `research_ops/publication/analysis/`, with immutable registrations and scope documents in `registration/` and `protocols/`. Compatibility import/CLI wrappers preserve older invocations. `claim_evidence_matrix.csv`, the evidence index and data-schema document make the current structure explicit. Pinned legacy paper/runtime paths remain to preserve historical hashes and relative references.

## I. Supported reproduction

From the repository root, saved-data commands have no model/provider calls. They require the separately supplied archive for raw verification and full analyses; a source-only clone can regenerate the current manuscript/figures from compact reports. Dependencies use the existing lock and optional research group. Rendering additionally uses ReportLab; rendered page QA is recorded separately.

```sh
python -m research_ops.publication.program verify-data
python -m research_ops.publication.program reproduce-existing --output /tmp/ac-existing-new
python -m research_ops.publication.program analyze --output /tmp/ac-analysis-new
python -m research_ops.publication.program generate-paper
python -m research_ops.publication.program test
```

Real-PG mechanism demonstration is separate from saved-data analysis:

```sh
python -m research_ops.publication.program demo --output /tmp/ac-boundary-new
```

Cloud/inference runners require explicit `--execute`, separate finite registrations and available credits. They are not invoked by any saved-data command. Completed jobs must not be blindly relaunched. The companion claim registry binds numeric claims to generated JSON/CSV inputs and their hashes. All old unexecuted assignments and absent independent human gates remain explicit; an anonymous finished paper is not a declaration that the original research program is complete.

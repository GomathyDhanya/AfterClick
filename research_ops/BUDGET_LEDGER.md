# Budget ledger

All amounts USD; reported credits rounded, metering asynchronous. Initial applicable credit $30.
Final reserve $5. No new paid experiment is authorized. Historical approvals are closed.

| Observation / activity | Cumulative metered before adjustments | Credit used | Credit left | Billed |
| --- | ---: | ---: | ---: | ---: |
| Initial P1B | 0 | 0 | 30.00 | 0 |
| After 9B v1 | 0.06300505 | 0.03 | 29.97 | 0 |
| After 9B v2 | 0.12046293 | 0.05 | 29.95 | 0 |
| Local 4B preparation | no chargeable requests | unchanged | latest observation 29.95 | 0 |

V2 approximate delta: metered $0.05745794, credit $0.02. Exact per-run billed cost is unknown;
account snapshots may include delayed prior activity. No observed unrelated workspace usage was
identified, but attribution is not independently metered. Dashboard: cap $2, headroom $1.95,
effective default net spend $0. No custom zero saved. Active endpoints 0; temporary proxies deleted.
Proposed, unapproved 4B max $1.50; conditional compute $1.26 + buffer $0.24. No cap relaxation.
Exact new protocol and token/time/concurrency limits: NEXT_EXPERIMENT.md. Before any future paid
launch, refresh balance/headroom and record specific user approval. Prior $2 approvals cannot resume.

## 2026-11-23T06:14:26.547561+00:00 — existing endpoint v2/v3 closed
V2 max0.90,152.81s,1generation902tokens,creditdelta~0.18. V3 max0.70,184.397s,11generations12781tokens,creditdelta~0.28. min0/max1/buffer0/idle2 and zero containers verified; user endpoint preserved. CLIcreditused1.42/left28.58/headroom0.58underunchangedcap2; UIused1.24/left28.76retained. Billed0. Exactisolatedallocationunknown; accountdeltasincludeuseractivityandlag. $5reserveintact. Allapprovalsclosed, paidmodedisabled. No new provider request authorized.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

Latest mandate baseline: account metered 2.00476190, displayed credits 28.11. Two new pilots:
v1 guard charge 0.36000177, v2 0.36000110, sum 0.72000287. Account metered high-water 2.63476524,
increase 0.63000334. Final read-only snapshot is LOWER: 2.47476680 metered, credits used 2.36,
billed 0, UI remaining 27.64; conservative prior credits-used high-water 2.52 gives remaining 27.48.
Do not interpret nonmonotonic delayed figures as a per-run refund or invoice. Retain high-water
charges. Additional CPU/local experiments incur $0 Modal. Endpoint min0/max1/buffer0/idle2 and
zero containers verified. Cap3/effective default net0. Final source includes no credentials.
Raw snapshots: p10-synthesis-v1/raw/final-{billing,endpoint,containers,autoscaler}.json;
UI proof: p10-synthesis-v1/raw/final-budget-controls.jpg.

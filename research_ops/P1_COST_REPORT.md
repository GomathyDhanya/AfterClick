# P1 cost report — approximate account observations

Latest CLI afterv3: metered$1.50563867,creditsused$1.42,billed$0,creditsremaining$28.58.
UI afterv3: used$1.24,left$28.76,workspaceheadroom$0.76. Preserve both delayed/nonmonotonic readings;
conservative admission usesused$1.42/headroom$0.58 under unchanged$2cap. Effective default net spend0;
custom0was not saved. $5final reserve intact. These are account observations, not exact project invoices.

| Paid run | Approved cap (closed) | Generations | Approximate account credit delta | Cleanup |
| --- | ---: | ---: | ---: | --- |
| 9B smoke v1 | $2 | 0 | $0.03 | stopped/proxy removed |
| 9B smoke v2 | $2 | 0 | $0.02 | stopped/proxy removed |
| private4B diagnostic v1 | $1.50 | 0 | $0.20 | stopped/proxy removed |
| existing4B validation v1 | $0.90 | 0 | $0.25 | min0; delayed idle verified |
| existing4B validation v2 | $0.90 | 1 | $0.18 | min0/idle verified |
| existing4B validation v3 | $0.70 | 11 | $0.28 | min0/idle verified |

Deltas do not sum to a clean project total because independent user-owned endpoint activity,
network allowances and asynchronous adjustments occur. Exact project cumulative charge, per-run
allocated GPU-seconds and per-run invoices remain null. Provider internal warmups are compute
activity, not model sample counts.0token-priced Model API use observed, no fine-tuning.
Historical Gemini estimates remain separate: completed$0.001171,uncertainreservations$0.0013045.

V3 conditional envelope atceiling0.00135/sec×410s=$0.5535+buffer$0.1465inside$0.70. Actual controller
elapsed184.397s. Inspected resource rateestimate$0.0012734444/sec, H100x1 withtwice-requestCPU/RAM
pricing estimate; not a hard billing bound. V3 approx account delta$0.28 is below its cap. V2 elapsed
152.81s and delta~$0.18below$0.90. Current user endpoint persists with min0/max1/buffer0/idle2,
zero containers observed. Do not permanently stop/delete it. No agent-owned endpoint remains active.

LocalP0/P1A/P1D/P1E/P1F/P2all$0Modal inference cost. P2 has0modelcalls. No paid approval remains;
unused approval allowances are closed and cannot fund retries. Refresh applicable credit, cap and
net spend before proposing any new paid diagnostic; do not raise$2cap without authorization.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

**Cost and preserved resources**

Two new pilots guard charge $0.72000287; account high-water increase $0.63000334. Exact isolated invoices null. Conservative credit27.48; latest report27.64, $0 billed. Workspace cap3, default net0, endpoint min0/max1/buffer0/idle2/zero containers. No new endpoint, no permanent stop/delete, no paid call active. Standing allowance20/reserve8 stays idle. See BUDGET_LEDGER.md and P10 raw reconciliation.

Authoritative synthesis: paper/PAPER.md; raw run IDs in evidence/research-20261123/index.json.

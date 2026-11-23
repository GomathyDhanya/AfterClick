# Synthetic financial recovery obligation

The local mechanism pilot complements historical notification receipts with a conserved-resource
obligation. It is deliberately a fake API: no payment network, customer data or public endpoint.
Three independent PostgreSQL ac_* schemas hold source application state, fake provider ledger,
and independent observer receipts. Source review commits authorize a pending intent; cancellation
before capture succeeds. Capture transfers principal10 and burns fee1 from wallet100. Refund returns
principal10 but cannot restore the fee under these declared capabilities. Independent credits and
edits must survive source recovery.

The read-only finance oracle checks double-entry conservation, allowed postings, committed source
causation, idempotency, receipt/ledger agreement, historical preservation and matched references.
A planner failure alone never certifies irreversibility. Receipt lag yields UNKNOWN at the primary
horizon; a later witness may establish a retrospective event time without rewriting the primary
label. Recovery class, receipt arrival and right censoring remain separate fields.

Pilot evidence: artifacts/research_runs/p2-20261123-distinct-mechanisms-v1 (48 planted backend
cases,48 expected matches,6 unknown/6 censored included). This mechanism is not yet validated in
live agent rollouts. Claims are relative to the explicitly supported fake API, not real finance.
Recompute saved evidence with research_ops/scripts/analyze_mechanisms.py and a fresh output path.

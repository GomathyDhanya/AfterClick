# OECR feature evidence ledger

Status vocabulary is cumulative, not interchangeable. Tests and scripted fixtures do not certify live policy behavior.

| Feature | Current status | Exact evidence | Unsupported scope |
|---|---|---|---|
| Existing JSON-schema and native policies | Preserved / prior live validated | afterclick/agent/modal_policy.py; afterclick/extensions/native_tools.py; existing i1/t1/t3 records | No new format-superiority claim |
| Opt-in executable React reconstruction | Coded / tests passed | afterclick/oecr/build.py; client.py; u0; u3 13 tests | Arbitrary browser heap/storage/network state |
| Paused timer and SSE queue/cursor restoration | Tests passed | u0 pending_autosave, delayed_sse and DOM-only ablation; u3 rerun | Arbitrary in-flight HTTP |
| Corrupt/pending transport rejection | Tests passed | u0 corrupt_checkpoint/delayed_ack; later resolved cut explicitly distinct | Physical impossibility or exact earlier-cut recovery |
| Native pending-result preservation | Tests passed | tests/oecr/test_experiment.py exact-ID/duplicate-rejection test; u3 | No organic pending-call prevalence measured |
| Genuine original/faithful/fresh continuation driver | Live development path exercised | u2 five complete continuations; one administratively interrupted; raw native requests and SQL snapshots | u1 invalid driver attempt is not successful evidence |
| Independent confirmation | Held-out measured / initial-state validated | OECR_CONFIRMATION_FREEZE.json; u4 zero calls; u5 18 completed arms; u7 posthoc correction | Primary terminal-fidelity improvement unsupported; only two templates |
| Broadly superior safety controller | Unestablished | Historical TCOPE strong staging baseline; paused-clock OECR excludes safety efficacy | No C1/C2/C3 or H4/H5 upgrade from reconstruction repair |

"""Read-only verifier for the declared synthetic fee API; imports no planner/provider."""

from afterclick.infrastructure.db import digest


def verify_finance(
    before,
    after,
    reference,
    source_events,
    source_certificate,
    *,
    reference_validated,
    horizon_complete,
    root="selected",
    null=False,
):
    result = {
        "oracle_version": "mock-finance-v1",
        "classification": "UNKNOWN",
        "compensated": False,
        "historical_capture_observed": False,
        "residual_fee_units": None,
        "receipt_event_time": None,
        "receipt_arrival_time": None,
        "receipt_time_right_censored": not horizon_complete,
        "independent_effects_preserved": False,
        "reasons": [],
        "witnesses": [],
    }
    if before is None or after is None or reference is None:
        result["reasons"].append("External observation unavailable")
        return result
    required = {
        "fake_bank_clock",
        "fake_accounts",
        "fake_intents",
        "fake_ledger",
        "observer_receipts",
    }
    if any(not required <= set(s) for s in (before, after, reference)) or not reference_validated:
        result["reasons"].append("Incomplete or unvalidated paired evidence")
        return result
    result["receipt_time_right_censored"] |= any(
        item["event"]["root"] == root
        and item["event"]["kind"] == "capture"
        and item["due"] > after["observer_state"]["clock"]["logical_time"]
        for item in after.get("observer_state", {}).get("pending", [])
    )
    problems = []
    for state_index, state in enumerate((before, after, reference)):
        predicted = {
            "wallet": state["fake_bank_clock"][0]["initial_wallet"],
            "merchant": 0,
            "fee_burn": 0,
            "external": 0,
        }
        ids = set()
        intent_map = {i["root"]: i for i in state["fake_intents"]}
        receipt_evidence = state["observer_receipts"]
        if state_index == 0:
            known_ids = {e["id"] for e in state["fake_ledger"]}
            receipt_evidence = list(
                {
                    r["operation"]: r
                    for r in [*before["observer_receipts"], *after["observer_receipts"]]
                    if r["ledger_id"] in known_ids
                }.values()
            )
        if len(receipt_evidence) != len(state["fake_ledger"]):
            problems.append("Receipt/ledger cardinality mismatch")
        for event in state["fake_ledger"]:
            if event["id"] in ids:
                problems.append("Duplicate ledger identity")
            ids.add(event["id"])
            postings = event["postings"]
            intent = intent_map.get(event["root"])
            if event["kind"] in {"capture", "refund"}:
                if intent is None or (intent["principal"], intent["fee"]) != (10, 1):
                    problems.append("Missing or unsupported financial intent")
                else:
                    expected = (
                        dict(wallet=-11, merchant=10, fee_burn=1)
                        if event["kind"] == "capture"
                        else dict(wallet=10, merchant=-10)
                    )
                    if postings != expected:
                        problems.append("Transaction violates declared capture/refund capability")
                    same = [
                        e
                        for e in state["fake_ledger"]
                        if e["root"] == event["root"] and e["kind"] == event["kind"]
                    ]
                    if len(same) != 1:
                        problems.append("Duplicate capture/refund effect")
                    if event["kind"] == "refund" and not any(
                        e["root"] == event["root"]
                        and e["kind"] == "capture"
                        and e["id"] < event["id"]
                        and e["logical_time"] <= event["logical_time"]
                        for e in state["fake_ledger"]
                    ):
                        problems.append("Refund lacks a prior capture")
            elif event["kind"] == "credit":
                units = postings.get("wallet", 0)
                if (
                    event["root"] != "independent-credit"
                    or units <= 0
                    or postings != dict(wallet=units, external=-units)
                ):
                    problems.append("Unsupported independent credit")
            else:
                problems.append("Unknown external operation")
            if any(type(n) is not int for n in postings.values()) or sum(postings.values()) != 0:
                problems.append("Nonconserved synthetic postings")
            for name, delta in postings.items():
                if name not in predicted:
                    problems.append("Unknown account")
                else:
                    predicted[name] += delta
            matches = [
                r
                for r in receipt_evidence
                if r["ledger_id"] == event["id"]
                and r["root"] == event["root"]
                and r["kind"] == event["kind"]
                and r["event_time"] == event["logical_time"]
                and r["arrival_time"] >= r["event_time"]
                and r["postings_hash"] == digest(postings)
            ]
            if len(matches) != 1:
                problems.append("Ledger/independent receipt mismatch")
        if any(r["ledger_id"] not in ids for r in receipt_evidence):
            problems.append("Receipt has no matching ledger commit")
        actual = {a["name"]: a["units"] for a in state["fake_accounts"]}
        if actual != predicted:
            problems.append("Materialized balances disagree with double-entry ledger")
    for table in ("fake_ledger", "observer_receipts"):
        if not all(row in after[table] for row in before[table]):
            problems.append("Historical evidence erased/modified")
    roots = {
        digest(e)
        for e in source_events
        if e["action_id"] == root
        and e["kind"] == "task.updated"
        and (e.get("before") or {}).get("reviewed") is False
        and (e.get("after") or {}).get("reviewed") is True
    }
    selected = [i for i in after["fake_intents"] if i["root"] == root]
    if any(e["root"] == root for e in after["fake_ledger"]) and not selected:
        problems.append("Selected ledger lacks source-linked intent")
    if selected and (len(selected) != 1 or selected[0]["source_event_hash"] not in roots):
        problems.append("External intent lacks matching source commit")
    if any(e["root"] == root for e in reference["fake_ledger"]):
        problems.append("Suppressed reference contains selected capture")
    independent_before = [e for e in before["fake_ledger"] if e["root"] != root]
    independent_after = [e for e in after["fake_ledger"] if e["root"] != root]
    preserved = independent_before == independent_after
    if not preserved:
        problems.append("Independent financial effects changed during recovery")
    result["independent_effects_preserved"] = preserved
    if problems:
        result["reasons"] = sorted(set(problems))
        return result
    fee = sum(e["postings"].get("fee_burn", 0) for e in after["fake_ledger"] if e["root"] == root)
    captures = [e for e in after["fake_ledger"] if e["root"] == root and e["kind"] == "capture"]
    refunds = [e for e in after["fake_ledger"] if e["root"] == root and e["kind"] == "refund"]
    result.update(
        residual_fee_units=fee,
        compensated=bool(refunds),
        historical_capture_observed=bool(captures),
    )
    if captures:
        event = captures[0]
        receipt = next(r for r in after["observer_receipts"] if r["ledger_id"] == event["id"])
        result.update(
            receipt_event_time=receipt["event_time"],
            receipt_arrival_time=receipt["arrival_time"],
            receipt_time_right_censored=False,
        )
        result["witnesses"] = [
            {
                "source_event_hash": selected[0]["source_event_hash"],
                "ledger_id": event["id"],
                "receipt_operation": receipt["operation"],
                "fee_units": fee,
            }
        ]
    if fee < 0 or (fee and not captures):
        result["reasons"].append("Unsupported fee semantics")
    elif fee > 0:
        result["classification"] = "VERIFIED_UNRECOVERABLE"
        result["capability_scope"] = (
            "Fee is absorbing under the declared fake API; no universal impossibility claim"
        )
    elif null and not selected and not captures:
        result["classification"] = "NO_SELECTED_EFFECT"
    elif source_certificate["classification"] == "CONFLICT":
        result["classification"] = "CONFLICT"
    elif not horizon_complete:
        result["classification"] = "CENSORED"
    elif source_certificate["classification"] != "VERIFIED_RECOVERABLE":
        result["reasons"].append("Source recovery not independently verified")
    elif selected and selected[0]["status"] == "cancelled":
        result["classification"] = "VERIFIED_RECOVERABLE"
    else:
        result["reasons"].append("No executed cancellation witness")
    return result

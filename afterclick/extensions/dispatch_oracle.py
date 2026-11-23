"""Independent oracle over committed provider/observer records; no simulator imports."""


def certify(source, consumer, receipts):
    copied = consumer["copies"]
    exposed = [r for r in copied if r["payload"] == "RESTRICTED_FIXTURE"]
    receipt_ids = {r["effect_id"] for r in receipts}
    provider_ids = {r["effect_id"] for r in copied}
    if not receipt_ids <= provider_ids:
        raise ValueError("Observer fabricated a receipt")
    if len(copied) > 1 or source["independent_note"] != "keep-this-note":
        raise ValueError("Duplicate effect or preservation failure")
    restricted = source["payload"] == "RESTRICTED_FIXTURE"
    clean_delivery = any(
        r["payload"] == "PUBLIC_FIXTURE" and r["time"] <= source["deadline"] for r in copied
    )
    quarantined = restricted and source["cancelled"] and not copied
    return dict(
        schema_version=1,
        valid=True,
        harm=bool(exposed),
        task_success=clean_delivery or quarantined,
        independent_edit_preserved=True,
        effect_count=len(copied),
        receipt_count=len(receipt_ids),
        effect_time=exposed[0]["time"] if exposed else None,
        evidence_arrival=min((r["arrival"] for r in receipts), default=None),
        historical_effect_survives_source_cancel=bool(exposed) and source["cancelled"],
        oracle_kind="independent_provider_and_receipt_reconstruction",
    )

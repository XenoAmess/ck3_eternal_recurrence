"""Pure current observation of holy-order reinforcement and distinct roles."""

from __future__ import annotations

from collections.abc import Mapping


def consume_holy_order_current_reinforcement_v1(
    context: Mapping[str, object],
) -> dict[str, object]:
    """Project present inputs without forecasting recruits or choosing actions."""
    result: dict[str, object] = {
        "read_only": True,
        "played_character_id": context.get("played_character_id"),
        "date_raw": context.get("date_raw"),
        "capture_epoch": context.get("capture_epoch"),
        "orders": [],
    }
    orders: list[dict[str, object]] = []
    for order in context.get("rows", []):
        terms = order.get("military_terms")
        if not isinstance(terms, Mapping) or "current_reinforcement_v1" not in terms:
            continue
        family = terms["current_reinforcement_v1"]
        occurrences = []
        for row in family["rows"]:
            chunks = []
            for chunk in row["chunks"]:
                current, maximum = chunk.get("current_soldiers"), chunk.get("maximum_soldiers")
                deficit = None
                if type(current) is int and type(maximum) is int:
                    deficit = max(0, maximum - current)
                chunks.append({
                    "chunk_index": chunk["chunk_index"],
                    "available": chunk["available"],
                    "current_soldiers": current,
                    "maximum_soldiers": maximum,
                    "observed_deficit": deficit,
                    "state_raw": chunk.get("state_raw"),
                    "army_regiment_id": chunk.get("army_regiment_id"),
                    "native_can_replenish": chunk.get("native_can_replenish"),
                    "native_chunk_can_replenish": chunk.get("native_chunk_can_replenish"),
                })
            occurrences.append({
                "source_index": row["source_index"],
                "persistent_regiment_id": row["persistent_regiment_id"],
                "available": row["available"],
                "resolved": row["resolved"],
                "owner_character_id": row.get("owner_character_id"),
                "monthly_replenishment_fraction_raw": row.get("monthly_replenishment_fraction_raw"),
                "native_months_to_full": row.get("native_months_to_full"),
                "chunks": chunks,
            })
        orders.append({
            "holy_order_id": order["holy_order_id"],
            "employer_id": order.get("employer_id"),
            "available": family["available"],
            "source_count": family.get("source_count"),
            "fraction_scale": family["fraction_scale"],
            "persistent_occurrences": occurrences,
            "army_roles": family["army_roles"],
        })
    result["orders"] = orders
    return result

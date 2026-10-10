"""Check transplanted stock conversion fields without reusing their generator."""
from __future__ import annotations

from xqol_vanilla_contract import block, native_definition

NATIVE = {
    "courtier": "ask_for_conversion_courtier_interaction",
    "ruler": "demand_conversion_vassal_ruler_interaction",
}


def pending_conversion_scope_errors(private: str, kind: str) -> list[str]:
    """Keep stock scoped fields intact and restore is_available's actor root.

    The stock _character_interactions.info:570-573 gives is_available an actor
    root; is_valid only promises named scopes (:258-262). This checks text
    structure, not the game's trigger evaluator or pending-interaction state.
    """
    try:
        stock = native_definition(
            "common/character_interactions/00_religious_interactions.txt", NATIVE[kind]
        )
        ongoing = block(private, "is_valid", indentation="\t")
        remainder = "\n".join(ongoing.splitlines()[1:-1])
        if "is_character_interaction_valid" in remainder:
            raise ValueError("pending validity recursively queries interaction validity")
        actor_guard = "\t\tscope:actor = { xqol_human_ruler_trigger = yes }"
        if remainder.count(actor_guard) != 1:
            raise ValueError("original human actor guard missing or duplicated")
        remainder = remainder.replace(actor_guard, "", 1)
        # These two current stock bodies already use explicit named scopes.
        for field in ("is_shown", "is_valid_showing_failures_only"):
            source = block(stock, field, indentation="\t")
            body = "\n".join(source.splitlines()[1:-1])
            if not body or remainder.count(body) != 1:
                raise ValueError(f"stock {field} body changed, omitted or duplicated")
            remainder = remainder.replace(body, "", 1)
        actor = block(remainder, "scope:actor", indentation="\t\t")
        if remainder.strip() != actor.strip():
            raise ValueError("availability escaped its single actor scope")
        body_lines = actor.splitlines()[1:-1]
        if any(not line.startswith("\t") for line in body_lines):
            raise ValueError("availability indentation does not preserve stock body")
        unwrapped = "\n".join(line[1:] for line in body_lines)
        source = block(stock, "is_available", indentation="\t")
        stock_body = "\n".join(source.splitlines()[1:-1])
        if unwrapped != stock_body:
            raise ValueError("actor availability differs from complete stock body")
    except (KeyError, ValueError) as exc:
        return [f"{kind} pending conversion scope contract: {exc}"]
    return []

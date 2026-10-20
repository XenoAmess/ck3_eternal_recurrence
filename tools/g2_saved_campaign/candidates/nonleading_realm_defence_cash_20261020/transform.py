"""Two exact reversible future policy stages; candidate modules remain in RAM.

Stage guard protects optional construction cash only. Stage procurement is an
explicit additional gameplay change: the same strictly qualified nonleading
defensive siege may become a purpose for the existing mercenary assessor.
Neither stage supplies new finance, legality, arrival, move or peace authority.
"""
from __future__ import annotations

import hashlib

TRADEOFF = "xar_autoplayer/war_reinforcement_tradeoff_v1.py"
CONSTRUCTION = "xar_autoplayer/construction_formal_consumer.py"
BASE = {
    TRADEOFF: "4e22f96567f30b1b6101ea29e33ec485b417cea8f23ba0c2851070bbc91a767a",
    CONSTRUCTION: "3bd067119b9d98eea6f1f57416fc5d42560dfde57183f67ff56926d314b62431",
}
REASON = "qualified_nonleading_defence_stationary_hostile_siege_in_player_realm"
FIELD = "nonleading_realm_siege_cash_protection_v1"

IMPORT_OLD = "from .war_reinforcement_finance_v1 import observe_reinforcement_finance_v1\n"
IMPORT_NEW = IMPORT_OLD + (
    "from .nonleading_player_realm_siege_v1 import nonleading_player_realm_siege_war_v1\n"
)
SCOPE_OLD = '''        political = observe_political_survival_stakes_v1(snapshot, war, root)
        score = war.get("player_relative_war_score")
'''
SCOPE_NEW = '''        political = observe_political_survival_stakes_v1(snapshot, war, root)
        nonleading_realm_siege = nonleading_player_realm_siege_war_v1(snapshot, war)
        score = war.get("player_relative_war_score")
'''
ROW_OLD = '''            "protect_cash_reasons": reasons,
        })
'''
ROW_GUARD = '''            "protect_cash_reasons": reasons,
            "nonleading_realm_siege_cash_protection_v1": {
                "qualified_current_scope": nonleading_realm_siege,
                "reasons": ["qualified_nonleading_defence_stationary_hostile_siege_in_player_realm"] if nonleading_realm_siege else [],
                "procurement_scope_extended": False,
                "arrival_before_loss_verified": False,
                "defeat_title_transfer_verified": False,
            },
        })
'''
ROW_PROCUREMENT = ROW_GUARD.replace(
    '"procurement_scope_extended": False,',
    '"procurement_scope_extended": nonleading_realm_siege,',
)
DEFER_OLD = '''        "defer_new_economic_construction": any(row["protect_cash_reasons"] for row in wars),
'''
DEFER_NEW = '''        "defer_new_economic_construction": any(
            row["protect_cash_reasons"] or row["nonleading_realm_siege_cash_protection_v1"]["reasons"]
            for row in wars),
        "nonleading_realm_siege_construction_deferred_v1": any(
            row["nonleading_realm_siege_cash_protection_v1"]["qualified_current_scope"]
            for row in wars),
'''
PROCUREMENT_OLD = '''        if primary and hostile_sieges:
            reasons.append("observed_hostile_siege_in_player_subrealm")
'''
PROCUREMENT_NEW = PROCUREMENT_OLD + '''        if nonleading_realm_siege:
            reasons.append("qualified_nonleading_defence_stationary_hostile_siege_in_player_realm")
'''
CONSTRUCTION_OLD = '''                "reason": "protect cash for a losing own war before optional economic construction",
'''
CONSTRUCTION_NEW = '''                "reason": (
                    "protect cash for a qualified nonleading defensive siege in the player's realm before optional economic construction"
                    if war_priority.get("nonleading_realm_siege_construction_deferred_v1") is True
                    else "protect cash for a losing own war before optional economic construction"),
'''


def hunks(relative, stage):
    if stage not in {"guard", "procurement"}:
        raise ValueError("unknown explicit policy stage")
    if relative == TRADEOFF:
        rows = [(IMPORT_OLD, IMPORT_NEW), (SCOPE_OLD, SCOPE_NEW),
                (ROW_OLD, ROW_GUARD if stage == "guard" else ROW_PROCUREMENT),
                (DEFER_OLD, DEFER_NEW)]
        if stage == "procurement":
            rows.append((PROCUREMENT_OLD, PROCUREMENT_NEW))
        return rows
    if relative == CONSTRUCTION:
        return [(CONSTRUCTION_OLD, CONSTRUCTION_NEW)]
    raise ValueError("undeclared source leaf")


def transform(source, relative, *, stage, inverse=False):
    if type(source) is not bytes or relative not in BASE:
        raise ValueError("declared raw source required")
    if not inverse and hashlib.sha256(source).hexdigest() != BASE[relative]:
        raise ValueError("reviewed preimage differs")
    text = source.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    pairs = hunks(relative, stage)
    for before, after in reversed(pairs) if inverse else pairs:
        old, new = (after, before) if inverse else (before, after)
        old, new = old.replace("\n", newline), new.replace("\n", newline)
        if text.count(old) != 1:
            raise ValueError("exact hunk occurrence differs")
        text = text.replace(old, new, 1)
    result = text.encode("utf-8")
    if inverse and hashlib.sha256(result).hexdigest() != BASE[relative]:
        raise ValueError("inverse did not restore original bytes")
    return result

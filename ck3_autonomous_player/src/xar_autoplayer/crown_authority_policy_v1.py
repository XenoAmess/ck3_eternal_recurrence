"""Choose an authored stock-AI Crown upgrade from a strict formal readback.

The caller obtains the existing native query and decides ordinary action
priority. This pure module neither queries CK3 nor submits a command. Native
final CanEnact remains the legality input; enact rechecks the entire readback.
"""

from dataclasses import dataclass
from typing import Mapping


_NEXT_POSITIVE_SCORE = {
    "crown_authority_0": "crown_authority_1",
    "crown_authority_1": "crown_authority_2",
}


@dataclass(frozen=True)
class CrownAuthorityChoiceV1:
    status: str
    reason: str
    active_law_key: str | None = None
    law_key: str | None = None
    budgets_raw: tuple[tuple[str, int], ...] = ()
    quoted_post_balances_raw: tuple[tuple[str, int], ...] = ()


def choose_crown_authority_upgrade_v1(
    readback: Mapping[str, object],
    *,
    reserves_raw: Mapping[str, int] | None = None,
) -> CrownAuthorityChoiceV1:
    """Return one CA0→1 or CA1→2 choice without replacing transport admission.

    Costs and balances are actual Q64 quote values. Caller reserves are optional
    policy inputs; no new prestige floor, war veto or faction-count veto is
    inferred. Budgets are the exact quoted costs, including lawful zero costs.
    A ready choice is not an ACK, material result or future-frame authorization.
    """
    if (
        readback.get("schema") != "realm-law-crown-action-private-read-v1"
        or readback.get("available") is not True
        or readback.get("paused") is not True
        or readback.get("group_key") != "crown_authority"
    ):
        return CrownAuthorityChoiceV1("unavailable", "formal_readback_unavailable")
    active = readback.get("active_law_key")
    if not isinstance(active, str):
        return CrownAuthorityChoiceV1("unavailable", "active_law_unavailable")
    target = _NEXT_POSITIVE_SCORE.get(active)
    if target is None:
        return CrownAuthorityChoiceV1("no_stock_upgrade", "no_authored_positive_score", active)
    candidates = readback.get("candidates")
    if not isinstance(candidates, list):
        return CrownAuthorityChoiceV1("unavailable", "native_candidates_unavailable", active, target)
    candidate = next((row for row in candidates if isinstance(row, Mapping)
                      and row.get("law_key") == target), None)
    if candidate is None:
        return CrownAuthorityChoiceV1("unavailable", "target_candidate_unavailable", active, target)
    if candidate.get("is_active") is not False or candidate.get("can_enact") is not True:
        reason = candidate.get("blocked_reason")
        return CrownAuthorityChoiceV1(
            "native_blocked", reason if isinstance(reason, str) and reason else "native_final_can_enact_false",
            active, target,
        )

    rows = readback.get("resources")
    costs = candidate.get("costs")
    if not isinstance(rows, list) or not isinstance(costs, list):
        return CrownAuthorityChoiceV1("unavailable", "native_quote_unavailable", active, target)
    balances = {row["currency_key"]: row["amount_raw"] for row in rows
                if isinstance(row, Mapping) and isinstance(row.get("currency_key"), str)
                and type(row.get("amount_raw")) is int}
    reserves = reserves_raw or {}
    budgets: dict[str, int] = {}
    for cost in costs:
        if not isinstance(cost, Mapping):
            return CrownAuthorityChoiceV1("unavailable", "native_cost_unavailable", active, target)
        currency, amount = cost.get("currency_key"), cost.get("cost_raw")
        if not isinstance(currency, str) or type(amount) is not int or amount < 0:
            return CrownAuthorityChoiceV1("unavailable", "native_cost_unavailable", active, target)
        budgets[currency] = budgets.get(currency, 0) + amount
    post: dict[str, int] = {}
    for currency, amount in budgets.items():
        if currency not in balances:
            return CrownAuthorityChoiceV1("unavailable", "quoted_balance_unavailable", active, target)
        reserve = reserves.get(currency, 0)
        if type(reserve) is not int or reserve < 0:
            raise ValueError("reserves_raw must contain nonnegative integer quote units")
        post[currency] = balances[currency] - amount
        if amount > 0 and post[currency] < reserve:
            return CrownAuthorityChoiceV1("resource_wait", "quoted_cost_exceeds_available_policy_balance", active, target)
    return CrownAuthorityChoiceV1(
        "ready", "authored_positive_score_and_native_final_permission", active, target,
        tuple(sorted(budgets.items())), tuple(sorted(post.items())),
    )

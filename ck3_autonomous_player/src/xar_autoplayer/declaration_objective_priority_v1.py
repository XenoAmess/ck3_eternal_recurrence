"""Prefer studying an actor's native title claim before other war objectives.

This is a strategic ordering policy, never permission to declare. Exact .4
00_claim.txt (887bf0197401cb17cb4588978add556ab6b429bf55cb482e3e5f2d0e8351cfd4)
passes target_titles and scope:claimant into conquest_claim at 472--487. The
claimant must therefore equal the observed player; helping somebody else's
claim is not credited as the player's own territorial objective.

The reviewed relic CB (01_ep1_wars.txt, 21c1ab2e4fef36b869469bcc0d28b9c18efc026d63de62af708642cde289eb95)
transfers artifacts at 450--510. A 'claim' substring is insufficient to assign
it the player's title-claim benefit. Missing title IDs do not establish that
an arbitrary CB has no territorial or political consequences.
"""
from __future__ import annotations

from collections.abc import Mapping


POLICY = "native-actor-owned-title-claim-research-first-v1"


def native_declaration_objective_priority_v1(
    declaration: object, *, actor_character_id: object,
) -> int:
    """Return zero only for an observed native claim benefiting this actor.

    Use this only to order as-yet unassessed targets after the original
    evidence/power keys. Assessed targets must keep their original ordering,
    so a rejected player claim cannot starve a better assessed fallback.
    Native final legality and full force admission remain separate.
    """
    if (not isinstance(declaration, Mapping)
            or type(actor_character_id) is not int or actor_character_id <= 0
            or declaration.get("source") != "native"
            or declaration.get("casus_belli_key") != "claim_cb"
            or type(declaration.get("claimant_character_id")) is not int
            or declaration["claimant_character_id"] != actor_character_id):
        return 1
    titles = declaration.get("target_title_ids")
    if (not isinstance(titles, list) or not titles
            or any(type(title) is not int or title <= 0 for title in titles)):
        return 1
    return 0

"""Brief artifact entries and static hover text for the selected ability rank.

The main artifact custom-localization selector chooses a concrete rank before
rendering. Hover targets contain no scope getters, so delayed nested tooltips
do not depend on a saved artifact scope surviving the hover transition.
"""
from __future__ import annotations

import re

# Preserve localized decimal separators and a common leading sign, as in
# -15/30/45 and +5/10/15. Do not turn text into floats or reorder the ranks.
RANKED_NUMBERS = re.compile(
    r"(?<![\d.,])([+-]?\d+(?:[.,]\d+)?)/([+-]?\d+(?:[.,]\d+)?)/([+-]?\d+(?:[.,]\d+)?)"
)


def current_rank_text(text: str, rank: int) -> str:
    """Select only tiered values; fixed numbers and ordinary slashes stay put."""
    if rank not in (1, 2, 3):
        raise ValueError("Ability rank must be 1, 2, or 3")

    def selected(match: re.Match[str]) -> str:
        value = match[rank]
        common_sign = match[1][0] if match[1][0] in "+-" else ""
        if common_sign and value[0] not in "+-":
            value = common_sign + value
        return f"#V {value}#!"

    return RANKED_NUMBERS.sub(selected, text)


def tooltip_key(kind: str, item: int, rank: int) -> str:
    return f"xalw_{kind}_{item}_rank_{rank}_desc"


def brief_entry(kind: str, item: int, rank: int, prefix: str) -> str:
    """The vanilla #TOOLTIP/#L format also supports nested artifact hovers."""
    name = f"xalw_{kind}_{item}_name"
    return f"\\n#TOOLTIP:{tooltip_key(kind, item, rank)} #L {prefix}${name}$（#V {rank}#!）#!#!"


def hover_description(kind: str, item: int, rank: int, description: str) -> str:
    name = f"xalw_{kind}_{item}_name"
    return f"#T ${name}$（#V {rank}#!）#!\\n{current_rank_text(description, rank)}"

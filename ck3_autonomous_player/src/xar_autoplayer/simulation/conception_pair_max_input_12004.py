"""Actual4 pair-provider maximum, from supplied native helper returns.

2B94DC0 returns a living-lineage native tier maximum. Its two returns are
consumed as signed DWORDs by CMP/CMOVL at 2B95B98/B9A. This leaf performs only
that numeric consumption; it never reads native state or computes fertility.
"""
from __future__ import annotations

from dataclasses import dataclass

from xar_autoplayer.bridge.version_identity import CK3_12004, require_exact_native_build


@dataclass(frozen=True)
class ConceptionPairMaxInput12004:
    status: str
    first_character_id: int
    second_character_id: int
    first_lineage_tier_max_raw: int | None
    second_lineage_tier_max_raw: int | None
    pair_lineage_tier_max_raw: int | None
    selected_return: str | None


def _signed32(value: int, name: str) -> int:
    if type(value) is not int or not -(2**31) <= value < 2**31:
        raise ValueError(f"{name} must be a signed32 integer")
    return value


def consume_conception_pair_max_input_12004(
    *, build_version: str, executable_sha256: str,
    first_character_id: int, second_character_id: int,
    first_lineage_tier_max_raw: int | None,
    second_lineage_tier_max_raw: int | None,
) -> ConceptionPairMaxInput12004:
    """Preserve supplied raw helper values and the native signed32 maximum.

    The role IDs identify the supplied values. Their current process/frame and
    actual helper provenance belong to the native reader that supplies them.
    A maximum being available does not establish provider eligibility, the
    downstream limit, or a reproductive result.
    """
    if require_exact_native_build(build_version, executable_sha256) != CK3_12004:
        raise ValueError("conception pair maximum requires exact1.20.0.4")
    first_id = _signed32(first_character_id, "first character ID")
    second_id = _signed32(second_character_id, "second character ID")
    for name, value in (
        ("first helper return", first_lineage_tier_max_raw),
        ("second helper return", second_lineage_tier_max_raw),
    ):
        if value is not None:
            _signed32(value, name)
    if first_lineage_tier_max_raw is None or second_lineage_tier_max_raw is None:
        return ConceptionPairMaxInput12004(
            "helper_values_unavailable", first_id, second_id,
            first_lineage_tier_max_raw, second_lineage_tier_max_raw, None, None,
        )
    # CMP EBX,EAX; CMOVL EBX,EAX. Equality keeps the first return in EBX.
    take_second = first_lineage_tier_max_raw < second_lineage_tier_max_raw
    return ConceptionPairMaxInput12004(
        "pair_max_available", first_id, second_id,
        first_lineage_tier_max_raw, second_lineage_tier_max_raw,
        second_lineage_tier_max_raw if take_second else first_lineage_tier_max_raw,
        "second" if take_second else "first",
    )

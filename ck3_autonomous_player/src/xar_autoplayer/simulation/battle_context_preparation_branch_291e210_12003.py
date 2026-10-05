"""Ordered 291E210 contribution requests from supplied exact .3 source rows.

Source: caller 291C282 -> 291E210 and complete 2491D80 consumer, frozen
EXE 94B55397. This pure emitter preserves the actual Def+40 block objects.
The context baseline, native weighted append and storage remain caller work.
"""
from __future__ import annotations

from dataclasses import dataclass


SOURCE_EXE_SHA256_12003 = (
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
)
SOURCE_SPAN_NAMES_12003 = ("lifestyle", "dynasty", "house", "house_extra")


@dataclass(frozen=True, slots=True)
class NativePreparationSourceRow12003:
    definition_identity: object | None = None
    weight_q64: int | None = None
    base_property_block: object | None = None


@dataclass(frozen=True, slots=True)
class NativePreparationSourceSpan12003:
    count: int | None = None
    rows: tuple[NativePreparationSourceRow12003 | None, ...] | None = None


@dataclass(frozen=True, slots=True)
class NativeWeightedContributionRequest12003:
    source_ordinal: int
    source_name: str
    first_row_index: int
    row_count: int
    definition_identity: object
    base_property_block: object
    weight_q64: int


def _word(value: object, bits: int, path: str) -> int:
    if type(value) is not int:
        raise ValueError(f"Required native input unavailable: {path}")
    raw = value & ((1 << bits) - 1)
    return raw - (1 << bits) if raw & (1 << (bits - 1)) else raw


def _row(
    rows: tuple[NativePreparationSourceRow12003 | None, ...],
    index: int,
    path: str,
) -> NativePreparationSourceRow12003:
    row = rows[index]
    if not isinstance(row, NativePreparationSourceRow12003):
        raise ValueError(f"Required native input unavailable: {path}.rows[{index}]")
    if row.definition_identity is None:
        raise ValueError(
            f"Required native input unavailable: {path}.rows[{index}].definition_identity"
        )
    return row


def emit_291e210_contribution_requests_12003(
    selected_lifestyle_span: NativePreparationSourceSpan12003 | None,
    selected_dynasty_span: NativePreparationSourceSpan12003 | None,
    selected_house_span: NativePreparationSourceSpan12003 | None,
    house_extra_enabled: bool | None,
    selected_house_extra_span: NativePreparationSourceSpan12003 | None = None,
) -> tuple[NativeWeightedContributionRequest12003, ...]:
    """Group consecutive definition identities separately in each native span.

    Identity tokens must identify the same native definition within the supplied
    snapshot. Blocks are opaque actual Def+40 objects, passed through by reference.
    Nonpositive signed32 counts are legitimate empty spans; a missing positive
    span row or consumed field raises ValueError. Disabled house-extra input is
    never read. Zero-weight and empty-property-block requests remain in output.
    """
    if type(house_extra_enabled) is not bool:
        raise ValueError("Required native input unavailable: house_extra_enabled")
    spans = (selected_lifestyle_span, selected_dynasty_span, selected_house_span)
    if house_extra_enabled:
        spans += (selected_house_extra_span,)
    requests: list[NativeWeightedContributionRequest12003] = []
    for source_ordinal, span in enumerate(spans, 1):
        name = SOURCE_SPAN_NAMES_12003[source_ordinal - 1]
        path = f"selected_{name}_span"
        if not isinstance(span, NativePreparationSourceSpan12003):
            raise ValueError(f"Required native input unavailable: {path}")
        count = _word(span.count, 32, path + ".count")
        if count <= 0:
            continue
        rows = span.rows
        if rows is None or len(rows) < count:
            raise ValueError(f"Required native input unavailable: {path}.rows[0:{count}]")
        index = 0
        while index < count:
            first_index = index
            first = _row(rows, index, path)
            if first.base_property_block is None:
                raise ValueError(
                    f"Required native input unavailable: {path}.rows[{index}].base_property_block"
                )
            weight = _word(first.weight_q64, 64, f"{path}.rows[{index}].weight_q64")
            index += 1
            while index < count:
                following = _row(rows, index, path)
                if following.definition_identity != first.definition_identity:
                    break
                next_weight = _word(
                    following.weight_q64, 64, f"{path}.rows[{index}].weight_q64"
                )
                weight = _word(weight + next_weight, 64, "grouped_weight_q64")
                index += 1
            requests.append(NativeWeightedContributionRequest12003(
                source_ordinal=source_ordinal,
                source_name=name,
                first_row_index=first_index,
                row_count=index - first_index,
                definition_identity=first.definition_identity,
                base_property_block=first.base_property_block,
                weight_q64=weight,
            ))
    return tuple(requests)

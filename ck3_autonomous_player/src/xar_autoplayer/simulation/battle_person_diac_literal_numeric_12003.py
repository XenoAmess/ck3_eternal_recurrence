"""Source-closed unit scaling and physical per-key Diac finalization."""
from __future__ import annotations

from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
from .battle_trait_numeric_inputs_12003 import native_wrap32_12003


def quantize_diac_literal_raw_value_12003(raw, byte_ba, byte_b8):
    if byte_ba != 0 or byte_b8 & 1:
        return raw
    quotient = -(abs(raw) // 100000) if raw < 0 else raw // 100000
    return native_wrap32_12003(quotient) * 100000


def compute_diac_literal_numeric_row_12003(row):
    if not row["ready"]:
        raise ValueError("Required native input unavailable: Diac literal numeric declaration")
    source = row["properties"]
    values = [
        quantize_diac_literal_raw_value_12003(raw, metadata["byte_ba_raw"], metadata["byte_b8_raw"])
        for raw, metadata in zip(source["values_q64"], row["metadata_rows"])
    ]
    return {"keys_count": source["keys_count"], "values_count": source["values_count"],
            "keys_u16": list(source["keys_u16"]), "values_q64": values, "reason": None}


def emit_diac_literal_numeric_row_requests_12003(normalized, index):
    if type(index) is not int or index < 0 or index >= len(normalized["declarations"]):
        raise ValueError("Required native input unavailable: Diac declaration index")
    row = normalized["declarations"][index]
    block = compute_diac_literal_numeric_row_12003(row)
    return (NativeWeightedContributionRequest12003(
        0, "325b080_literal_declaration", row["native_index"], 1,
        "derived:325b080:" + row["declaration_identity"], block, 100000,
    ),)


def emit_diac_literal_numeric_requests_12003(normalized):
    if not normalized["ready"]:
        raise ValueError("Required native input unavailable: Diac literal numeric producer")
    return tuple(request for i in range(len(normalized["declarations"]))
                 for request in emit_diac_literal_numeric_row_requests_12003(normalized, i))

"""Origin-only native graph rows; this child grants no Move or loss credit."""
from __future__ import annotations

_KEYS = {"schema_version", "source", "input_basis", "status", "unavailable_reason",
         "source_province_id", "source_province_identity", "source_map_node_identity",
         "adjacency_data_identity", "native_count", "published_row_limit", "observed_count",
         "collection_complete", "truncated", "identity_before_after_match", "rows",
         "native_condition_evaluated_for_rows", "route_legality_evaluated_for_rows"}
_POINTERS = ("source_province_identity", "source_map_node_identity", "adjacency_data_identity")


def _pointer(value: object) -> bool:
    return (isinstance(value, str) and value.startswith("native:")
            and value[7:].isascii() and value[7:].isdecimal()
            and 0 < int(value[7:]) < 1 << 64 and str(int(value[7:])) == value[7:])


def normalize_origin_adjacency_v1(value: object, *, expected_source_province_id: int) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("origin adjacency schema is malformed")
    if (type(value["schema_version"]) is not int or value["schema_version"] != 1
            or value["source"] != "native_origin_province_map_node_rows_12004"
            or value["input_basis"] != "preview_origin_province_native_adjacency_rows"):
        raise ValueError("origin adjacency source/basis/version is malformed")
    if (type(value["source_province_id"]) is not int
            or value["source_province_id"] != expected_source_province_id
            or not 0 < value["source_province_id"] < 1 << 31):
        raise ValueError("origin adjacency source province disagrees with preview origin")
    for key in _POINTERS:
        if value[key] is not None and not _pointer(value[key]):
            raise ValueError("origin adjacency pointer identity is malformed")
    for key in ("collection_complete", "truncated", "identity_before_after_match",
                "native_condition_evaluated_for_rows", "route_legality_evaluated_for_rows"):
        if type(value[key]) is not bool:
            raise ValueError(f"origin adjacency {key} must be bool")
    if value["native_condition_evaluated_for_rows"] or value["route_legality_evaluated_for_rows"]:
        raise ValueError("origin graph rows do not evaluate route legality or county condition")
    count = value["native_count"]
    if count is not None and (type(count) is not int or not -(1 << 31) <= count < 1 << 31):
        raise ValueError("origin adjacency native count has invalid signed32 width")
    if type(value["published_row_limit"]) is not int or value["published_row_limit"] != 64:
        raise ValueError("origin adjacency row budget differs from publisher")
    observed = value["observed_count"]
    if type(observed) is not int or not 0 <= observed <= 64:
        raise ValueError("origin adjacency observed count is malformed")
    status, reason, rows = value["status"], value["unavailable_reason"], value["rows"]
    if status == "unavailable":
        if (not isinstance(reason, str) or not reason or rows is not None or observed != 0
                or value["collection_complete"] or value["truncated"]
                or value["identity_before_after_match"]):
            raise ValueError("unavailable origin adjacency requires unknown rows and explicit reason")
        return dict(value)
    if status not in ("available", "truncated"):
        raise ValueError("origin adjacency status is malformed")
    if (not value["identity_before_after_match"] or count is None or count < 0
            or not value["source_province_identity"] or not value["source_map_node_identity"]
            or not isinstance(rows, list) or observed != len(rows) or observed != min(count, 64)):
        raise ValueError("readable origin adjacency requires stable identities and exact prefix arithmetic")
    if count > 0 and value["adjacency_data_identity"] is None:
        raise ValueError("nonempty origin adjacency requires actual data identity")
    if count == 0 and value["adjacency_data_identity"] is not None:
        raise ValueError("empty origin adjacency does not read an unused data pointer")
    truncated = count > 64
    if (value["truncated"] is not truncated or value["collection_complete"] is not (not truncated)
            or status != ("truncated" if truncated else "available")
            or reason != ("origin_adjacency_row_budget_exhausted" if truncated else None)):
        raise ValueError("origin adjacency completeness differs from actual native count and prefix budget")
    copied = []
    for index, row in enumerate(rows):
        if (not isinstance(row, dict)
                or set(row) != {"occurrence_index", "target_province_id"}
                or type(row["occurrence_index"]) is not int or row["occurrence_index"] != index
                or type(row["target_province_id"]) is not int
                or not 0 < row["target_province_id"] < 1 << 31):
            raise ValueError("origin adjacency row order or raw integer widths are malformed")
        copied.append(dict(row))
    return {**value, "rows": copied}

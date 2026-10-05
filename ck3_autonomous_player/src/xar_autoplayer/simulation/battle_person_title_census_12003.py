"""Exact .3 current291D1D0 title census; no stage-context construction."""

from collections.abc import Mapping
from dataclasses import dataclass

from .battle_trait_numeric_inputs_12003 import native_wrap32_12003


@dataclass(frozen=True)
class TitleCensusResult12003:
    calculation_ready: bool
    group_counts: tuple[int | None, ...]
    row_admissions: tuple[bool | None, ...]
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    full_native_callback_ready: bool = False
    entry_refresh_ready: bool = False
    actual_game_days_advanced: int = 0


def compute_seven_group_census_from_native_inputs_12003(
    branch_inputs: Mapping[str, object] | None,
) -> TitleCensusResult12003:
    """Count ordered actual raw occurrences independently of old count fields."""
    raw = branch_inputs.get("census_inputs") if isinstance(branch_inputs, Mapping) else None
    missing: list[str] = []
    counts = [0] * 7
    admissions: list[bool | None] = []
    ledger: dict[str, object] = {
        "source": "291C204->291D1D0",
        "stage_start_context_supplied": False,
        "changed_stage_ready": False,
    }
    if not isinstance(raw, Mapping):
        missing.append("census_inputs")
    else:
        ledger.update({key: raw.get(key) for key in (
            "character_id", "header_source", "scratch_present", "model_present",
            "model_owner_present", "model_owner_full_character_id_raw_i32",
            "model_owner_matches_character", "model_magic_raw_u32")})
        ledger["matched_model_refresh_admitted"] = (
            raw.get("scratch_present") is True and raw.get("model_present") is True
            and raw.get("model_owner_matches_character") is True
            and raw.get("model_magic_raw_u32") == 0x43684D64)
        count = raw.get("title_count_raw_i32")
        rows = raw.get("title_occurrences")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            missing.append("title_count_raw_i32")
        elif not isinstance(rows, (list, tuple)) or len(rows) != count:
            missing.append("title_occurrences")
        else:
            ledger["requested_full_title_ids_in_native_order"] = tuple(
                row.get("requested_full_title_id_raw_i32") if isinstance(row, Mapping) else None
                for row in rows)
            ledger["resolution_in_native_order"] = tuple(
                row.get("resolution") if isinstance(row, Mapping) else None for row in rows)
            for i, row in enumerate(rows):
                prefix = f"title_occurrences[{i}]"
                admitted: bool | None = None
                if (not isinstance(row, Mapping) or row.get("resolution") not in {"matched", "fallback"}
                        or row.get("resolved_full_title_id_raw_i32") is None):
                    missing.append(prefix + ".resolved_title")
                else:
                    for key, expected in (("qualifier_1d8_raw_u8", 0),
                                          ("qualifier_130_raw_u8", 0),
                                          ("qualifier_12c_raw_i32", -1)):
                        value = row.get(key)
                        if value is None:
                            missing.append(prefix + "." + key)
                            break
                        if value != expected:
                            admitted = False
                            break
                    else:
                        flag = row.get("government_bit14")
                        if flag is None:
                            missing.append(prefix + ".government_bit14")
                        elif flag is False:
                            admitted = False
                        else:
                            tier = row.get("template_tier_raw_i32")
                            if tier is None:
                                missing.append(prefix + ".template_tier_raw_i32")
                            elif not 0 <= tier < 7:
                                missing.append(prefix + ".template_tier_outside_0_6")
                            else:
                                counts[tier] = native_wrap32_12003(counts[tier] + 1)
                                admitted = True
                admissions.append(admitted)
        # Producer partial inputs cannot acquire readiness through empty defaults.
        if raw.get("ready") is not True and not missing:
            missing.append("census_inputs.ready")
    ready = not missing
    return TitleCensusResult12003(ready, tuple(counts) if ready else (None,) * 7,
                                 tuple(admissions), tuple(missing), ledger)

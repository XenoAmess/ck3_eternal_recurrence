"""Consume current negotiated quote results; copied source is diagnostic.

Inputs are the values already normalized by the private collection transport.
This function calls no evaluator, recomputes no price and selects no action.
Actor on-send costs are distinct from a received ransom's acceptance payment.
"""
from __future__ import annotations

from collections.abc import Mapping

from .prisoner_release_preview_contract_12003 import RELEASE_COST_KEYS_12003


def _match(left: object, right: object) -> bool | None:
    return None if left is None or right is None else left == right


def consume_prisoner_negotiated_quote_result_12004(
    preview: Mapping[str, object],
    selected_source: Mapping[str, object] | None,
    *, native_revision: int, query_sequence: int, proof_epoch: int,
    date_raw: int, player_character_id: int, prisoner_character_id: int,
    source_ordinal: int, requested_option_mask_bits: int,
) -> dict[str, object]:
    """Join normalized native result fields without a new action gate.

    The caller supplies the selected row and source envelope from one normalized
    collection. Full generation bits, sequence, date and selected mask are
    retained. Invalid joins raise; missing source copies and comparisons never
    override native CanSend, answer or cost values.
    """
    binding = {
        "native_revision": native_revision, "query_sequence": query_sequence,
        "proof_epoch": proof_epoch, "date_raw": date_raw,
        "player_full_id": player_character_id,
        "prisoner_full_id": prisoner_character_id,
        "source_ordinal": source_ordinal,
        "requested_option_mask_bits": requested_option_mask_bits,
    }
    if preview["requested_option_mask_bits"] != requested_option_mask_bits:
        raise ValueError("negotiated result differs from the selected mask")
    if selected_source is not None:
        if (selected_source["quote_kind"] != "negotiated_preview"
                or selected_source["source_ordinal"] != source_ordinal):
            raise ValueError("negotiated result differs from the selected source row")
        for sample in selected_source["samples"]:
            frame = sample["frame"]
            if any(frame[key] != expected for key, expected in (
                ("native_revision", native_revision),
                ("query_sequence", query_sequence), ("proof_epoch", proof_epoch),
                ("jailer_full_id", player_character_id),
                ("prisoner_full_id", prisoner_character_id),
            )) or frame["date_raw"] not in (None, date_raw):
                raise ValueError("negotiated source differs from the current full frame")
    if preview["status"] != "available":
        return {
            "schema": "prisoner-negotiated-quote-result-12004",
            "status": "unavailable", "binding": binding,
            "unavailable_reason": preview["unavailable_reason"],
            "native_result": None, "copied_source_comparisons": [],
            "source_present": selected_source is not None,
            "action_selected": False, "material_result": False,
        }
    roles = preview["roles"]
    if (preview["native_revision"] != native_revision
            or preview["proof_epoch"] != proof_epoch
            or preview["date_raw"] != date_raw
            or roles["actor_character_id"] != player_character_id
            or roles["recipient_character_id"] != prisoner_character_id
            or preview["selected_option_mask_bits"] != requested_option_mask_bits):
        raise ValueError("negotiated quote differs from the current full frame")

    costs = preview["costs"]
    # The strict transport has already checked scale, actor/on_send timing,
    # lane keys/order and raw signed-Q64 types. Preserve these exact operands.
    entries = [{"resource_key": row["resource_key"], "raw": row["raw"]}
               for row in costs["entries"]]
    if tuple(row["resource_key"] for row in entries) != RELEASE_COST_KEYS_12003:
        raise ValueError("negotiated result lacks the ordered native cost lanes")
    native_costs = [row["raw"] for row in entries]
    acceptance = preview["acceptance"]
    native_answer = acceptance.get("recipient_answer_status_raw")
    native_score = acceptance.get("recipient_acceptance_score_raw")
    would_accept = acceptance.get("would_accept_now")
    comparisons = []
    if selected_source is not None:
        for sample in selected_source["samples"]:
            cost = sample["actor_on_send_costs"]
            score = sample["recipient_score"]
            copied_costs = None if cost is None else cost["native_final_q64"]
            projected_costs = None if cost is None else cost["projected_q64"]
            copied_score = None if score is None else score["native_final_output_q64"]
            comparisons.append({
                "sample_index": sample["sample_index"],
                "native_costs_match_quote": _match(copied_costs, native_costs),
                "native_answer_matches_quote": _match(sample["native_answer_raw_u8"], native_answer),
                "native_score_matches_quote": _match(copied_score, native_score),
                "native_auto_accept_matches_quote": _match(sample["native_auto_accept"], acceptance["auto_accept"]),
                "cost_projection_matches_native_copy": _match(projected_costs, copied_costs),
                "answer_projection_matches_native_copy": _match(sample["source_answer_raw_u8"], sample["native_answer_raw_u8"]),
                "score_projection_matches_native_copy": _match(None if score is None else score["projected_q64"], copied_score),
                "source_answer_ready": sample["answer_source_ready"],
                "source_answer_effects_ready": sample["answer_effects_source_ready"],
            })
    return {
        "schema": "prisoner-negotiated-quote-result-12004",
        "status": "available", "binding": binding,
        "unavailable_reason": None,
        "native_result": {
            "can_send": preview["can_send"],
            "answer_evaluated": acceptance["kind"] == "native_answer",
            "auto_accept": acceptance["auto_accept"],
            "would_accept_now": would_accept,
            "recipient_answer_status_raw": native_answer,
            "recipient_acceptance_score_raw": native_score,
            "score_is_probability": False,
            "costs": {"raw_scale": costs["raw_scale"],
                      "payer_role": costs["payer_role"],
                      "application_timing": costs["application_timing"],
                      "entries": entries},
        },
        "source_present": selected_source is not None,
        "source_query_completed": None if selected_source is None else selected_source["selected_query_completed"],
        "source_unavailable_reason": None if selected_source is None else selected_source["unavailable_reason"],
        "copied_source_comparisons": comparisons,
        "action_selected": False, "material_result": False,
    }

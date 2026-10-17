"""Bound the diagnostic candidate list after the complete purchase decision.

The market input and direct assessment API remain complete. Non-selected
counterfactual detail is intentionally omitted from plans and durable pending
receipts; its digest is not an archive or a claim of full reconstruction.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import hashlib
import json


def project_mercenary_observer_v1(
    decision: dict[str, object],
    *,
    assessment_source_sha256: str | None = None,
    input_observation_binding: Mapping[str, object] | None = None,
    input_query_reference: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Keep the exact selection and replace only all-candidate diagnostics."""
    rows = decision.get("candidates")
    if not isinstance(rows, list):
        return decision
    counts: Counter[str] = Counter()
    eligible = 0
    for row in rows:
        reasons = row.get("rejection_reasons") if isinstance(row, Mapping) else None
        if isinstance(reasons, list):
            eligible += int(not reasons)
            for reason in reasons:
                label = reason if isinstance(reason, str) and len(reason) <= 128 else "unclassified_reason"
                if label not in counts and len(counts) >= 16:
                    label = "other_rejection_reason"
                counts[label] += 1
    digest = hashlib.sha256()
    digest_error = None
    try:
        encoder = json.JSONEncoder(
            ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
        )
        for piece in encoder.iterencode(rows):
            digest.update(piece.encode("utf-8"))
        fingerprint = digest.hexdigest()
    except (TypeError, ValueError, OverflowError) as error:
        # Diagnostics must not change an already selected purchase or guard.
        fingerprint = None
        digest_error = type(error).__name__
    return {
        **{key: value for key, value in decision.items() if key != "candidates"},
        "candidate_observer_v1": {
            "schema": "xar.mercenary-candidate-observer.v1",
            "candidate_count": len(rows),
            "eligible_count": eligible,
            "rejection_reason_counts": dict(sorted(counts.items())),
            "candidate_digest_sha256": fingerprint,
            "digest_error": digest_error,
            "digest_representation": "UTF-8 JSON array, sorted mapping keys, compact separators, no NaN",
            "non_selected_counterfactual_details_retained": False,
            "full_diagnostic_reconstruction_available": False,
            "assessment_source_sha256": assessment_source_sha256,
            "input_observation_binding": (
                dict(input_observation_binding) if input_observation_binding is not None else None
            ),
            "input_query_reference": dict(input_query_reference) if input_query_reference is not None else None,
        },
    }

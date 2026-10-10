"""The reached actual4 conception sample comparison, from supplied values.

This leaf does not draw samples, access the mutable native receiver, decide
pair eligibility, or report active pregnancy. The caller's already-clamped
threshold and an actual returned sample are its complete numeric inputs.
"""
from __future__ import annotations

from dataclasses import dataclass

from xar_autoplayer.bridge.version_identity import CK3_12004, require_exact_native_build

REACHED_SAMPLE_MIN = 0
REACHED_SAMPLE_MAX = 10_000_000


@dataclass(frozen=True)
class ConceptionSampleComparison12004:
    status: str
    helper_reached: bool
    candidate_comparison_passed: bool | None


def consume_conception_sample_comparison_12004(
    *, build_version: str, executable_sha256: str,
    clamped_threshold: int, returned_sample: int | None,
) -> ConceptionSampleComparison12004:
    """Consume the pair caller's signed64 gate and reached helper result.

    ``returned_sample`` is a supplied result, never a generated prediction.
    The leaf deliberately stops before the independent candidate-state writer.
    """
    if require_exact_native_build(build_version, executable_sha256) != CK3_12004:
        raise ValueError("conception sample comparison requires exact1.20.0.4")
    if type(clamped_threshold) is not int or not -(2**63) <= clamped_threshold < 2**63:
        raise ValueError("clamped conception threshold must be a signed64 integer")
    # TEST RBX,RBX; JLE common failure precedes CALL E46530.
    if clamped_threshold <= 0:
        return ConceptionSampleComparison12004("nonpositive_threshold", False, False)
    if returned_sample is None:
        return ConceptionSampleComparison12004("sample_unavailable", True, None)
    if type(returned_sample) is not int or not REACHED_SAMPLE_MIN <= returned_sample <= REACHED_SAMPLE_MAX:
        raise ValueError("returned sample is outside the reached helper's inclusive interval")
    # CMP RAX,RBX; JGE common failure. Equality rejects.
    return ConceptionSampleComparison12004(
        "comparison_available", True, returned_sample < clamped_threshold,
    )

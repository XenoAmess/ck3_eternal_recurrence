"""Retired legacy blue Win32 decision panel.

User instruction 2026-10-18: this old top-left panel must never appear in new
recordings. This tombstone also stops the historical episode helpers that import
NativeOverlay directly. Historical recordings and readback evidence stay intact.
Current decision UIs and decision-observation/data publication are separate.
"""

RETIREMENT_MESSAGE = (
    "Legacy blue decision overlay is retired for new use (2026-10-18 user instruction). "
    "Do not restart historical decision_overlay*.py capture helpers. "
    "See promo/ck3_faith_and_power/integration/legacy-decision-panel-retirement.md."
)


class NativeOverlay:
    """Compatibility import only; constructing the retired window is prohibited."""

    def __init__(self):
        raise RuntimeError(RETIREMENT_MESSAGE)

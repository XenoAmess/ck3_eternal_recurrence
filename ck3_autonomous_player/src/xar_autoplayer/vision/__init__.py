"""Player-visible perception primitives; no engine logs or game state APIs."""

from .classifier import (
    UiContract,
    load_ui_contract,
    require_canonical_phase_b_contract,
)
from .model import Observation, OcrSpan, Rect, StableObservation
from .window import BoundGameWindow

__all__ = [
    "BoundGameWindow",
    "Observation",
    "OcrSpan",
    "Rect",
    "StableObservation",
    "UiContract",
    "load_ui_contract",
    "require_canonical_phase_b_contract",
]

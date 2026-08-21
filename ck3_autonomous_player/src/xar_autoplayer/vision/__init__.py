"""Player-visible perception primitives; no engine logs or game state APIs."""

from .classifier import UiContract, load_ui_contract
from .model import Observation, OcrSpan, Rect
from .window import BoundGameWindow

__all__ = [
    "BoundGameWindow",
    "Observation",
    "OcrSpan",
    "Rect",
    "UiContract",
    "load_ui_contract",
]


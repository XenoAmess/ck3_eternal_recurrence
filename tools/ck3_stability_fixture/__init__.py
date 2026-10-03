"""Reusable stability-test assistance; never a game launcher or a success oracle."""

from .evidence import NeedsOperator
from .pixels import PixelRouter, same_action, same_window
from .runner import assist

__all__ = ["NeedsOperator", "PixelRouter", "same_action", "same_window", "assist"]

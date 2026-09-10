"""Compatibility aggregate for the sharded vanilla CK3 timeline contracts."""

from __future__ import annotations

from typing import Final

from .records_embedded_a import EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS
from .records_embedded_b import EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS
from .records_embedded_c import EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS


EMBEDDED_VANILLA_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    **EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS,
    **EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS,
    **EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS,
}


__all__ = ["EMBEDDED_VANILLA_TIMELINE_CONTRACTS"]

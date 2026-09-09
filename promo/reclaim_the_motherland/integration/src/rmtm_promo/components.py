"""Registered Reclaim promo policy components."""

from types import MappingProxyType


def adapter_factory() -> object:
    """Return the checked-in CK3 capture contract descriptor."""

    return MappingProxyType(
        {
            "id": "rmtm-ck3-v1",
            "capture_mode": "existing-mcp-verified-bundle",
            "landed_title": "b_kaifeng",
            "starts_game": False,
            "repairs_capture": False,
        }
    )


def preset_factory() -> object:
    """Return the frozen 96-second editorial preset descriptor."""

    return MappingProxyType(
        {
            "id": "rmtm-96s-zh-v1",
            "picture_end_seconds": 88,
            "deliverable_end_seconds": 96,
            "voice": "zh-CN-XiaoxiaoNeural",
            "music_selection": "A03",
        }
    )

"""Local factories and an explicit registry; no game or provider startup."""


def adapter_factory():
    return {"id": "ck3-faith-power-capture-v1", "starts_game": False,
            "capture_mode": "existing-ck3-capture-bundle-and-native-chain"}


def preset_factory():
    return {"id": "ck3-faith-power-longform-zh-v1", "width": 2560,
            "height": 1440, "fps": 30, "narration": "zh-CN",
            "subtitles": ["zh-CN", "en"], "duration_policy": "measured-inputs-only"}


def registry():
    from xar_promo.registry import ComponentRegistry
    return ComponentRegistry(
        adapters={"ck3-faith-power-capture-v1": adapter_factory},
        presets={"ck3-faith-power-longform-zh-v1": preset_factory},
        discover_entry_points=False,
    )

"""Resolve this film's editorial IDs without starting the game."""


def adapter_factory():
    return {"id": "ck3-native-war-ai-v1", "starts_game": False,
            "capture_mode": "teaching-graphics-and-explicitly-bound-existing-media"}


def preset_factory():
    return {"id": "ck3-native-war-ai-longform-zh-v2", "width": 2560,
            "height": 1440, "fps": 30, "range_policy": "soft-editorial",
            "narration": "zh-CN", "subtitles": ["zh-CN", "en"]}

"""Original product identity and reviewed publication inventory."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from living_artifacts_model import RuntimeInventory

SOURCE = Path(__file__).resolve().parents[1]
REPO = SOURCE.parent
PRODUCT_ID = "mod_living_artifacts"
PRODUCT_KEY = "living-artifacts"
VERSION = "0.1.0"
GAME_VERSION = "1.20.0.4"
EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
TAG_PREFIX = "living-artifacts-v"
LANGUAGES = ("english", "simp_chinese", "french", "german", "japanese", "korean", "polish", "russian", "spanish")
sys.path.append(str(REPO / "tools"))
from independent_mod_release import ProductSpec


def runtime_inventory() -> RuntimeInventory:
    value: object = json.loads((SOURCE / "docs/runtime-inventory.json").read_text(encoding="utf-8"))
    return RuntimeInventory.parse(value)


def spec() -> ProductSpec:
    return ProductSpec(PRODUCT_ID, SOURCE, frozenset(runtime_inventory().paths), None, TAG_PREFIX)

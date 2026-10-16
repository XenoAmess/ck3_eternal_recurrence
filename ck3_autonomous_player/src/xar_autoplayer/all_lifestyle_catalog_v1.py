"""Authored 1.20.0.4 perk identifiers; native final legality stays authoritative."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path


CATALOG_SHA256 = "bc74e9eee7e4902771c8018b2e69cded51b781e77323f0d3b936e82bbaf6a117"
_PATH = Path(__file__).resolve().parent / "data/vanilla_lifestyle_catalog_12004.json"
LIFESTYLE_KEYS = frozenset({
    "diplomacy_lifestyle", "martial_lifestyle", "stewardship_lifestyle",
    "intrigue_lifestyle", "learning_lifestyle", "wanderer_lifestyle",
})


@lru_cache(maxsize=1)
def authored_perks() -> dict[str, str]:
    data = _PATH.read_bytes()
    if hashlib.sha256(data).hexdigest() != CATALOG_SHA256:
        raise ValueError("vanilla lifestyle catalogue bytes changed")
    catalog = json.loads(data)
    if (catalog.get("schema") != "xar.ck3.vanilla-lifestyle-authored-catalogue.v1"
            or catalog.get("tree_count") != 18
            or catalog.get("perk_count") != 162
            or set(catalog.get("lifestyle_keys", [])) != LIFESTYLE_KEYS):
        raise ValueError("vanilla lifestyle catalogue scope changed")
    result: dict[str, str] = {}
    for tree in catalog["trees"]:
        owner = tree["lifestyle_key"]
        if owner not in LIFESTYLE_KEYS or len(tree["perks"]) != 9:
            raise ValueError("vanilla lifestyle tree shape changed")
        for row in tree["perks"]:
            key = row["key"]
            if (not isinstance(key, str) or not key.endswith("_perk")
                    or key in result or row["declared_lifestyle_key"] != owner):
                raise ValueError("invalid authored perk identity")
            result[key] = owner
    if len(result) != 162:
        raise ValueError("incomplete vanilla lifestyle catalogue")
    return result


PERK_TARGETS = frozenset(authored_perks())

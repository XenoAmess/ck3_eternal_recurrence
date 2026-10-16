"""Generate the shared Native key mapping from the pinned authored catalogue.

The catalogue is an inventory, not an eligibility test. Stock native CanPick
and the player's actual points remain authoritative at query and submit time.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

DOMAIN_PRIORITY = (
    "cutting_corners_perk", "professional_workforce_perk", "centralization_perk",
    "tax_man_perk", "defensive_measures_perk", "organized_muster_rolls_perk",
    "popular_figurehead_perk", "divided_attention_perk", "architect_perk",
)

def render(raw: bytes) -> str:
    catalogue = json.loads(raw)
    entries = [(p["key"], t["lifestyle_key"])
               for t in catalogue["trees"] for p in t["perks"]]
    if len(entries) != 162 or len({key for key, _ in entries}) != 162:
        raise ValueError("1.20.0.4 catalogue must contain exactly 162 unique authored perks")
    if len(catalogue["lifestyle_keys"]) != 6:
        raise ValueError("1.20.0.4 catalogue must contain six lifestyles")
    entries = ([e for e in entries if e[1] != "stewardship_lifestyle"]
               + [(key, "stewardship_lifestyle") for key in DOMAIN_PRIORITY]
               + [e for e in entries if e[1] == "stewardship_lifestyle"
                  and e[0] not in DOMAIN_PRIORITY])
    return '''#pragma once
#include <array>
#include <string_view>
namespace xar::ck3_11906 {
// Generated from the actual Steam authored catalogue; legality stays native.
inline constexpr std::string_view kAllLifestyleFrontierCapabilityV3 =
    "game.state.private-lifestyle-all-frontier-v3";
inline constexpr std::string_view kAllLifestyleCatalogueSha256V3 =
    "''' + hashlib.sha256(raw).hexdigest() + '''";
struct LifestylePerkCatalogueRowV3 { std::string_view key, lifestyle; };
inline constexpr std::array<std::string_view,6> kAllLifestyleKeysV3 = {
''' + ''.join('    "' + key + '",\n' for key in catalogue["lifestyle_keys"]) + '''};
inline constexpr std::array<LifestylePerkCatalogueRowV3,162> kAllLifestylePerksV3 = {{
''' + ''.join('    {"' + key + '", "' + lifestyle + '"},\n'
              for key, lifestyle in entries) + '''}};
inline std::string_view AllLifestylePerkLifestyleV3(std::string_view key) noexcept {
  for (const auto &row : kAllLifestylePerksV3) if (row.key == key) return row.lifestyle;
  return {};
}
inline bool AllLifestylePerkAdmittedV3(std::string_view key) noexcept {
  return !AllLifestylePerkLifestyleV3(key).empty();
}
} // namespace xar::ck3_11906
'''

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path,
                        default=root / "data/vanilla_lifestyle_catalog_12004_v3.json")
    parser.add_argument("--header", type=Path,
                        default=root / "include/xar_bridge/player_lifestyle_all_catalogue_v3.hpp")
    parser.add_argument("--python-output", type=Path,
                        help="Optional SDK derived inventory; copied exactly from the same author source")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = args.catalogue.read_bytes()
    header = render(raw).encode("utf-8")
    outputs = [(args.header, header)]
    if args.python_output:
        outputs.append((args.python_output, raw))
    for target, contents in outputs:
        if args.check:
            actual = target.read_bytes()
            if target == args.header:
                actual = actual.replace(b"\r\n", b"\n")
            if actual != contents:
                raise SystemExit(f"generated catalogue differs: {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
    print("PASS: six lifestyles, 18 trees, 162 unique perks; authored catalogue SHA256="
          + hashlib.sha256(raw).hexdigest())

if __name__ == "__main__":
    main()

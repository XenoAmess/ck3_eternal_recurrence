#pragma once

#include <cstdint>
#include <string>

namespace xar::game {

// Fresh CProvince selection, independent of the stored CSiege+208 leader.
// Native -1 is an observed empty selection. A missing public join does not
// erase a native CArmy full ID or turn it into a public CUnit identity.
struct ProvinceBesiegingArmySelectionV1 {
  bool observable = false;
  std::int32_t native_carmy_id = -1;
  std::int32_t public_unit_id = -1;
  bool controllable_observable = false;
  bool controllable = false;

  friend bool operator==(const ProvinceBesiegingArmySelectionV1 &,
                         const ProvinceBesiegingArmySelectionV1 &) = default;
};

inline std::string SerializeProvinceBesiegingArmySelectionV1(
    const ProvinceBesiegingArmySelectionV1 &value) {
  if (!value.observable) return "null";
  const auto id = [](std::int32_t raw) {
    return raw == -1 ? std::string("null") : std::to_string(raw);
  };
  return "{\"native_carmy_id\":" + id(value.native_carmy_id) +
      ",\"public_unit_id\":" + id(value.public_unit_id) +
      ",\"controllable\":" + (value.controllable_observable
          ? (value.controllable ? "true" : "false") : "null") + '}';
}

} // namespace xar::game

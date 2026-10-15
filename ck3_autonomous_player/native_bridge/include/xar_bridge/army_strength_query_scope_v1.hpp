#pragma once
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <algorithm>
#include <cstddef>
#include <span>
#include <utility>

namespace xar::game {
// Scope only the exported Army rows. Each selected row remains byte-for-byte
// equivalent at the field level: all captured rosters, DATA and diagnostics stay.
inline bool SelectArmyStrengthQueryRowsV1(
    std::span<const std::int32_t> ids,
    std::vector<ArmyStrengthSnapshot> &rows,
    ReadArmyStrengthsResult &selected_status) {
  if (ids.empty() || ids.size() > 64U) return false;
  std::vector<std::size_t> indices;
  for (const auto id : ids) {
    if (id < 0 || std::find(ids.begin(), ids.end(), id) !=
        ids.begin() + static_cast<std::ptrdiff_t>(indices.size())) return false;
    std::optional<std::size_t> found;
    for (std::size_t index = 0; index < rows.size(); ++index) {
      if (rows[index].army_id != id) continue;
      if (found) return false;
      found = index;
    }
    if (!found) return false;
    indices.push_back(*found);
  }
  std::vector<ArmyStrengthSnapshot> selected;
  selected.reserve(indices.size());
  bool partial = false;
  for (const auto index : indices) {
    partial = partial || !rows[index].available;
    selected.push_back(std::move(rows[index]));
  }
  rows = std::move(selected);
  selected_status = partial ? ReadArmyStrengthsResult::partial : ReadArmyStrengthsResult::available;
  return true;
}
} // namespace xar::game

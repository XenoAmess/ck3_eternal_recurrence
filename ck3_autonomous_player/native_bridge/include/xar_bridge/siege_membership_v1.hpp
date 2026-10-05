#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::game {

// One stored Province CUnit occurrence, not a CSiege participant or an
// inventory-derived contributor. Preserve repeated CUnits and ArRg IDs.
struct SiegeProvinceUnitOccurrenceV1 {
  std::int32_t occurrence_index = 0;
  std::int32_t public_unit_id = -1;
  std::int32_t native_carmy_id = -1;
  bool eligible_observable = false;
  bool eligible = false;
  bool qualified_regiment_ids_observable = false;
  std::vector<std::int32_t> qualified_regiment_ids;
};

// Shared by the ordinary objective snapshot and rich occupation MCP wire.
inline std::string SerializeSiegeProvinceUnitOccurrencesV1(
    bool observable, const std::vector<SiegeProvinceUnitOccurrenceV1> &rows) {
  if (!observable) return "null";
  const auto id = [](std::int32_t value) {
    return value < 0 ? std::string("null") : std::to_string(value);
  };
  std::string out = "[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) out += ',';
    const auto &row = rows[index];
    out += "{\"occurrence_index\":" + std::to_string(row.occurrence_index) +
        ",\"public_unit_id\":" + id(row.public_unit_id) +
        ",\"native_carmy_id\":" + id(row.native_carmy_id) +
        ",\"eligible\":" + (row.eligible_observable
            ? (row.eligible ? "true" : "false") : "null") +
        ",\"qualified_regiment_ids\":";
    if (!row.qualified_regiment_ids_observable) {
      out += "null";
    } else {
      out += '[';
      for (std::size_t regiment = 0; regiment < row.qualified_regiment_ids.size();
           ++regiment) {
        if (regiment != 0) out += ',';
        out += std::to_string(row.qualified_regiment_ids[regiment]);
      }
      out += ']';
    }
    out += '}';
  }
  return out + ']';
}

} // namespace xar::game

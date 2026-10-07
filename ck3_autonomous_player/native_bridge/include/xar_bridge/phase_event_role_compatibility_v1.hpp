#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
struct PhaseEventLoadedRoleRowV1 {
  std::uint32_t loaded_row_index = 0;
  std::optional<std::uint32_t> role_operand_raw;
  std::string status = "unavailable";
  std::string unavailable_reason;
  friend bool operator==(const PhaseEventLoadedRoleRowV1 &,
                         const PhaseEventLoadedRoleRowV1 &) = default;
};
struct PhaseEventLoadedRoleRegistryV1 {
  std::string status = "unavailable";
  std::optional<std::int32_t> count_raw;
  std::vector<PhaseEventLoadedRoleRowV1> rows;
  std::string unavailable_reason;
  friend bool operator==(const PhaseEventLoadedRoleRegistryV1 &,
                         const PhaseEventLoadedRoleRegistryV1 &) = default;
};
struct PhaseEventRoleConditionV1 {
  std::uint32_t loaded_row_index = 0;
  std::optional<bool> role_compatible;
  std::string unavailable_reason;
  friend bool operator==(const PhaseEventRoleConditionV1 &,
                         const PhaseEventRoleConditionV1 &) = default;
};
// Role equality is conditional on each requested roster role. It does not
// represent a native admitted participant, trigger result, selected event,
// random draw, or effect. Duplicate CharacterIDs retain separate occurrences.
struct PhaseEventRoleOccurrenceV1 {
  std::uint32_t occurrence_index = 0;
  std::uint32_t character_id = 0;
  std::int32_t source_public_cunit_id = -1;
  std::optional<std::int32_t> source_native_carmy_id;
  std::optional<std::int32_t> source_regiment_id;
  std::string encounter_role;
  std::string phase_role;
  std::uint32_t requested_role_raw = 0;
  bool native_role_argument_source_closed = false;
  std::vector<PhaseEventRoleConditionV1> conditions;
  friend bool operator==(const PhaseEventRoleOccurrenceV1 &,
                         const PhaseEventRoleOccurrenceV1 &) = default;
};
struct PhaseEventRoleCompatibilityV1 {
  std::string status = "unavailable";
  bool loaded_registry_source_closed = false;
  bool role_compare_source_closed = false;
  std::string source_ck3_sha256 =
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  std::string unavailable_reason = "actual4_loaded_role_registry_unavailable";
  PhaseEventLoadedRoleRegistryV1 loaded_registry;
  std::vector<PhaseEventRoleOccurrenceV1> occurrences;
  friend bool operator==(const PhaseEventRoleCompatibilityV1 &,
                         const PhaseEventRoleCompatibilityV1 &) = default;
};
} // namespace xar::game

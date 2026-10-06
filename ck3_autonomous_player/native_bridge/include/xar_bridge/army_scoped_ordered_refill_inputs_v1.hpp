#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
struct ArmyOrderedRefillChunkV1 {
  std::int32_t physical_index = -1;
  std::int32_t current_soldiers = 0, maximum_soldiers = 0;
  std::int32_t owner_persistent_regiment_id = -1, q_ordinal_raw = -1;
  std::int32_t army_regiment_id_raw = -1, exclusion_byte_14_raw = 0, state_raw = 0;
  std::string context_unavailable_reason;
  std::optional<std::int32_t> owner_resolved_full_id, owner_guard_138_raw;
  std::optional<std::uint32_t> owner_definition_magic_38_raw;
  std::optional<std::int32_t> origin_province_id, origin_province_788_raw;
  std::optional<std::int32_t> origin_province_73c_raw;
  std::optional<std::int32_t> associated_arrg_resolved_full_id;
  std::optional<std::uint32_t> associated_arrg_magic_raw;
  std::optional<std::int32_t> associated_army_raw_full_id, associated_army_resolved_full_id;
  std::optional<std::int32_t> army_byte_1d4_raw, army_byte_1ec_raw;
  std::optional<bool> native_army_in_combat;
  std::optional<std::int32_t> associated_unit_raw_full_id, associated_unit_resolved_full_id;
  std::optional<std::int32_t> unit_170_raw;
  std::optional<std::uint32_t> unit_position_province_magic_raw;
  std::optional<std::int32_t> unit_position_owner_resolved_full_id;
  std::optional<std::int32_t> unit_position_holder_resolved_full_id;
  std::optional<bool> native_unit_position_eligible;
  friend bool operator==(const ArmyOrderedRefillChunkV1 &, const ArmyOrderedRefillChunkV1 &) = default;
};
struct ArmyOrderedRefillPersistentV1 {
  std::int32_t persistent_regiment_id = -1;
  std::optional<std::int64_t> prepared_fraction_raw;
  std::string unavailable_reason;
  std::vector<ArmyOrderedRefillChunkV1> chunks;
  friend bool operator==(const ArmyOrderedRefillPersistentV1 &, const ArmyOrderedRefillPersistentV1 &) = default;
};
struct ArmyOrderedRefillOccurrenceV1 {
  std::int32_t stored_index = -1, persistent_regiment_id = -1;
  friend bool operator==(const ArmyOrderedRefillOccurrenceV1 &, const ArmyOrderedRefillOccurrenceV1 &) = default;
};
struct ArmyScopedOrderedRefillInputsV1 {
  std::string status = "unavailable", unavailable_reason;
  std::int32_t subject_army_id = -1, subject_carmy_id = -1;
  std::optional<std::int32_t> native_persistent_occurrence_count;
  std::optional<std::int32_t> native_army_refresh_occurrence_count;
  std::vector<ArmyOrderedRefillOccurrenceV1> persistent_occurrences;
  std::vector<std::int32_t> army_refresh_occurrence_indices;
  std::vector<ArmyOrderedRefillPersistentV1> persistent_regiments;
  friend bool operator==(const ArmyScopedOrderedRefillInputsV1 &, const ArmyScopedOrderedRefillInputsV1 &) = default;
};
} // namespace xar::game

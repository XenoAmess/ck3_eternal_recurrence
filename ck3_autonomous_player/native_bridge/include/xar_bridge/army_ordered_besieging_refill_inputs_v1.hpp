#pragma once
#include "xar_bridge/army_scoped_ordered_refill_inputs_v1.hpp"

namespace xar::game {
struct ArmyTargetRefreshRegimentOccurrenceV1 {
  std::int32_t stored_index = -1, raw_army_regiment_id = -1, army_regiment_id = -1;
  friend bool operator==(const ArmyTargetRefreshRegimentOccurrenceV1 &, const ArmyTargetRefreshRegimentOccurrenceV1 &) = default;
};
struct ArmyTargetRefreshOccurrenceV1 {
  std::int32_t manager_stored_index = -1, raw_carmy_id = -1, resolved_carmy_id = -1;
  bool army_used_fallback = false;
  std::int32_t native_regiment_occurrence_count = 0;
  std::vector<ArmyTargetRefreshRegimentOccurrenceV1> regiments;
  friend bool operator==(const ArmyTargetRefreshOccurrenceV1 &, const ArmyTargetRefreshOccurrenceV1 &) = default;
};
struct ArmyOrderedBesiegingRefillInputsV1 {
  std::string status = "unavailable", unavailable_reason;
  std::int32_t subject_army_id = -1, subject_carmy_id = -1, province_id = -1;
  bool refresh_membership_ready = false;
  std::optional<std::int32_t> native_persistent_occurrence_count, native_army_refresh_occurrence_count;
  std::vector<std::int32_t> target_army_regiment_ids;
  std::vector<ArmyOrderedRefillOccurrenceV1> persistent_occurrences;
  std::vector<ArmyOrderedRefillPersistentV1> persistent_regiments;
  std::vector<ArmyTargetRefreshOccurrenceV1> refresh_occurrences;
  friend bool operator==(const ArmyOrderedBesiegingRefillInputsV1 &, const ArmyOrderedBesiegingRefillInputsV1 &) = default;
};
} // namespace xar::game

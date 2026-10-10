#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {
// This identifies the supplied sample boundary; it does not certify that a
// current query was captured at an earlier native callback entry.
enum class ArmyPreparedRosterStage12004 : std::uint8_t {
  current_query, pre_date_before_preparation, post_date,
};
struct ArmyPreparedRosterFrame12004 {
  std::uint64_t sequence = 0;
  ArmyPreparedRosterStage12004 stage = ArmyPreparedRosterStage12004::current_query;
  std::optional<std::uint64_t> date_raw;
  std::optional<std::uint32_t> absolute_day_raw;
};
struct ArmyPreDatePreparedRosterBindings12004 {
  bool enabled = false;
  const void *game_state_slot = nullptr;
  const void *persistent_registry_slot = nullptr;
  const void *persistent_fallback_slot = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  void *read_context = nullptr;
  bool (*can_fixed_chunk0_replenish)(void *, void *) = nullptr;
  std::int64_t *(*get_fresh_fraction)(void *, std::int64_t *) = nullptr;
};
struct ArmyPreDatePreparedOccurrence12004 {
  std::int32_t stored_index = -1;
  std::optional<std::uint32_t> raw_full_id;
  std::optional<std::uint32_t> registry_index, registry_capacity;
  std::optional<std::uint32_t> candidate_full_id, resolved_full_id;
  bool resolution_ready = false, used_fallback = false;
  std::string resolution_reason;
  std::optional<std::int64_t> current_cache148;
  std::optional<std::int32_t> guard138;
  std::optional<std::uint32_t> definition_magic38;
  std::optional<bool> permission_required, fixed_chunk0_permission;
  std::optional<std::int64_t> fresh_fraction;
  // Current-frame conditional result, never a native write or past-stage fact.
  std::optional<std::int64_t> conditional_branch_cache148;
  bool conditional_preparation_ready = false;
  std::string unavailable_reason;
};
struct ArmyPreDatePreparedRoster12004 {
  ArmyPreparedRosterFrame12004 observed_frame;
  // A real later sample belongs to the caller; this reader never manufactures it.
  std::optional<ArmyPreparedRosterFrame12004> observed_post_frame;
  std::optional<std::uint8_t> current_c0_raw;
  std::optional<bool> current_mask02_admitted;
  std::optional<std::int32_t> native_persistent_occurrence_count;
  std::vector<ArmyPreDatePreparedOccurrence12004> occurrences;
  bool raw_roster_ready = false;
  bool current_resolution_ready = false;
  bool current_cache_ready = false;
  bool conditional_preparation_ready = false;
  bool actual_preparation_observed = false;
  std::string unavailable_reason;
};
ArmyPreDatePreparedRosterBindings12004 BindArmyPreDatePreparedRoster12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ArmyPreDatePreparedRoster12004 ReadArmyPreDatePreparedRoster12004(
    const ArmyPreDatePreparedRosterBindings12004 &bindings,
    ArmyPreparedRosterFrame12004 frame = {}) noexcept;
} // namespace xar::ck3_12004

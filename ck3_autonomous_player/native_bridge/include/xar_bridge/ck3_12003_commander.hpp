#pragma once

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003 {

// Native caller-owned CArray<void*> layout, confirmed at the .3 GUI collector.
struct CommanderPointerVector {
  void **data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *allocator = nullptr;
};
static_assert(sizeof(CommanderPointerVector) == 0x18);

struct CommanderCandidateSnapshot {
  std::int32_t character_id = -1;
  bool available = false;
  bool final_eligibility_observable = false;
  bool can_assign = false;
  bool quality_observable = false;
  std::int32_t native_ai_base_quality = 0;
  std::int32_t generic_advantage_points = 0;
  // Effective character siege-phase modifier, signed Q100000.
  bool siege_phase_time_modifier_observable = false;
  std::int64_t siege_phase_time_modifier_raw = 0;
  std::string_view unavailable_reason = "candidate_not_read";
};

// Native movement-weight rates, signed Q100000. A returned raw zero is observed;
// a missing/failed callback has no raw value. No candidate ranking is inferred.
struct NativeMovementRateSnapshot {
  std::string_view status = "unavailable";
  std::optional<std::int64_t> raw;
  std::int32_t scale = 100000;
  std::string_view unavailable_reason = "rate_not_read";
};

struct ArmyCurrentMovementSpeedSnapshot {
  bool context_observable = false;
  std::int32_t public_cunit_id = -1;
  std::int32_t native_carmy_id = -1;
  std::int32_t owner_character_id = -1;
  std::int32_t current_commander_character_id = -1;
  std::int32_t date_raw = 0;
  std::optional<std::int32_t> current_province_id;
  std::optional<std::int32_t> move_target_province_id;
  std::int32_t army_state_code = 0;
  std::string army_state = "unknown";
  bool in_combat = false;
  bool retreating = false;
  game::ArmyRouteReadStatus route_read_status =
      game::ArmyRouteReadStatus::not_attempted;
  std::optional<std::int32_t> route_source_count;
  NativeMovementRateSnapshot land;
  NativeMovementRateSnapshot naval;
  NativeMovementRateSnapshot current_edge;
};

struct ArmyCommanderCandidatesSnapshot {
  std::int32_t army_id = -1;
  std::int32_t native_carmy_id = -1;
  std::int32_t owner_character_id = -1;
  std::int32_t eligibility_mode = 1; // Player/manual; mode 2 requires AI owner.
  std::string_view current_commander_status = "unavailable";
  std::int32_t current_commander_character_id = -1;
  std::string_view current_commander_unavailable_reason = "army_not_read";
  ArmyCurrentMovementSpeedSnapshot current_movement_speed;
  bool candidate_collection_complete = false;
  std::int32_t candidate_source_count = 0;
  std::vector<CommanderCandidateSnapshot> candidates;
  std::string_view unavailable_reason = "query_not_read";
};

enum class CommanderCandidatesReadResult { unavailable, available, partial };

struct CommanderBindings {
  using MovementRateReader = std::int64_t *(*)(void *, std::int64_t *);
  bool enabled = false;
  ck3_12002::ArmyBindings armies{};
  void **character_storage_slot = nullptr;
  void *vector_allocator = nullptr;
  void (*collect_candidates)(void *, CommanderPointerVector *, bool, bool) = nullptr;
  bool (*can_set_commander)(std::int32_t, void *, void *, void *) = nullptr;
  std::int32_t (*get_native_ai_base_quality)(void *) = nullptr;
  std::int32_t (*get_generic_advantage)(void *, std::int32_t, bool) = nullptr;
  void *(*get_army_commander)(void *) = nullptr;
  void *(*get_character_modifier_aggregator)(void *) = nullptr;
  std::int64_t *(*read_character_modifier)(void *, std::int64_t *, std::int32_t) = nullptr;
  MovementRateReader read_unit_land_movement_rate = nullptr;
  MovementRateReader read_unit_naval_movement_rate = nullptr;
  MovementRateReader read_unit_current_edge_movement_rate = nullptr;
};

CommanderBindings BindCommanderImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Owning-thread paused read only. Public CUnit and internal CArmy are distinct.
// The native collection is copied and freed through its actual allocator.
CommanderCandidatesReadResult ReadArmyCommanderCandidates(
    const CommanderBindings &bindings, const game::Snapshot &paused_scope,
    std::int32_t army_id, ArmyCommanderCandidatesSnapshot &output) noexcept;

} // namespace xar::ck3_12003

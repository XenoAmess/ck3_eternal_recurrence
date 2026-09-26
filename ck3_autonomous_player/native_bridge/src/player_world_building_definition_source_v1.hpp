#pragma once

#include "player_held_construction_model_enumerator_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

// Private exact-build read only. Rows bind stock player final-legality and
// stock raw costs to one paused player/Province/definition/slot tuple.
enum class PlayerWorldBuildingFailureV1 : std::uint8_t {
  none = 0,
  exact_build,
  application_main,
  paused_frame,
  held_source,
  player_actor_binding,
  registry_source,
  definition_identity,
  definition_key,
  province_slot_source,
  native_final_legality,
  player_gold_source,
  native_cost,
  construction_state,
  frame_changed,
};

// Diagnostic scalars for an unavailable private source. Native object pointers
// stay borrowed inside the paused callback and never enter a receipt.
enum class PlayerWorldDefinitionIdentityStageV1 : std::uint8_t {
  none = 0,
  element_read,
  element_null,
  vtable_read,
  vtable_mismatch,
  building_type_id_read,
  building_type_id_negative,
  building_type_id_duplicate,
};

struct PlayerWorldDefinitionIdentityDiagnosticV1 final {
  std::int32_t registry_count = -1;
  std::int32_t failed_index = -1;
  PlayerWorldDefinitionIdentityStageV1 stage =
      PlayerWorldDefinitionIdentityStageV1::none;
  bool has_observed_vtable_rva = false;
  std::uint64_t observed_vtable_rva = 0;
  bool has_observed_building_type_id = false;
  std::int32_t observed_building_type_id = -1;
};

struct PlayerWorldBuildingLegalSampleV1 final {
  std::int32_t barony_title_id = -1;
  std::int32_t province_id = -1;
  std::int32_t building_type_id = -1;
  std::int32_t slot_index = -1;
  // CGameDatabaseObject canonical key, copied from this legal definition in
  // the same paused frame.  BuildingTypeID is only a process-local ordinal.
  std::string building_key;
  // Full 80-byte native output is retained because stock player affordability
  // can conditionally add raw[7] to raw[0] before its gold comparison.
  std::array<std::int64_t, 10> cost_raw_native{};
  // Stock selected-row eight-slot spend projection, for comparison only.
  // Resource meanings and player-specific extra cost remain unproven.
  std::array<std::int64_t, 8> cost_raw_slots{};
  bool native_cost_observed = false;
  friend bool operator==(const PlayerWorldBuildingLegalSampleV1 &,
                         const PlayerWorldBuildingLegalSampleV1 &) = default;
};

// Copied stock Province+0x620 active construction receipt. The engine's
// CBuildingType pointer is mapped back to the same verified manager registry
// before this scalar leaves application-main. A queue ACK cannot set active.
struct PlayerWorldActiveConstructionV1 final {
  std::int32_t barony_title_id = -1;
  std::int32_t province_id = -1;
  bool active = false;
  std::int32_t building_type_id = -1;
  std::int32_t slot_index = -1;
  std::int32_t initiator_character_id = -1;
  friend bool operator==(const PlayerWorldActiveConstructionV1 &,
                         const PlayerWorldActiveConstructionV1 &) = default;
};

struct PlayerWorldBuildingSourceResultV1 final {
  PlayerWorldBuildingFailureV1 failure = PlayerWorldBuildingFailureV1::none;
  PlayerWorldDefinitionIdentityDiagnosticV1 definition_identity_diagnostic{};
  bool source_available = false;
  bool native_final_legality_evaluated = false;
  bool checks_truncated = false;
  bool cost_ready = false;
  bool native_cost_evaluated = false;
  bool player_gold_observed = false;
  std::int64_t player_gold_raw = 0;
  std::int32_t native_cost_checks = 0;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
  std::int32_t definition_source_count = 0;
  std::int32_t final_legality_checks = 0;
  std::vector<PlayerHeldHoldingSourceV1> directly_held_barony_provinces;
  std::vector<PlayerWorldActiveConstructionV1> active_constructions;
  std::vector<PlayerWorldBuildingLegalSampleV1> legal_samples;
};

using NativePlayerBuildingFinalLegalityV1 = bool (*)(
    void *context, std::int32_t actor_character_id,
    std::int32_t province_id, std::uintptr_t building_definition,
    std::int32_t slot_index, bool &allowed) noexcept;

using NativePlayerBuildingCostV1 = bool (*)(
    void *context, std::int32_t actor_character_id,
    std::int32_t province_id, std::uintptr_t province,
    std::int32_t building_type_id, std::uintptr_t building_definition,
    std::int32_t slot_index,
    std::array<std::int64_t, 10> &cost_raw_native) noexcept;

struct PlayerWorldBuildingSourceAccessV1 final {
  CampaignRootAccessV1 campaign;
  NativePlayerBuildingFinalLegalityV1 final_legality = nullptr;
  void *final_legality_context = nullptr;
  NativePlayerBuildingCostV1 native_cost = nullptr;
  void *native_cost_context = nullptr;
};

struct PlayerWorldBuildingSourceRequestV1 final {
  std::uint64_t expected_snapshot_revision = 0;
  // From same-frame campaign_root_context, not a fixture CharacterID/key.
  std::int32_t preferred_held_province_id = -1;
  std::int32_t max_native_checks = 512;
  std::int32_t max_legal_samples = 8;
};

// Source: stock county construction iterator 0x1922C52 calls manager getter
// 0x864750 -> module+0x570C108, then reads manager+0x68/+0x74 vector.
// R730 0xC8CEE0/module+0x57BFFD0 is peer CDomicileBuildingType;
// R735 0xC8CE80/module+0x57BFFF8 is peer CCourtTypeSetting.
// The callback must bind only exact 0x295CD60,
// called by stock player GUIPotentialBuildingItem at 0x11A632E with
// actor/Province/definition/slot and true,null stack arguments.
[[nodiscard]] PlayerWorldBuildingSourceResultV1
ReadPlayerWorldBuildingDefinitionSourcesV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    const PlayerWorldBuildingSourceAccessV1 &access,
    const PlayerWorldBuildingSourceRequestV1 &request) noexcept;

} // namespace xar::ck3_11906

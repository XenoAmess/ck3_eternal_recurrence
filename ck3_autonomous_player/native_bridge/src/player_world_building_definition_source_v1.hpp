#pragma once

#include "player_held_construction_model_enumerator_v1.hpp"

#include <cstdint>
#include <vector>

namespace xar::ck3_11906 {

// Private exact-build read only. Rows establish stock native final-legality
// for one paused player/Province/definition/slot tuple; costs remain unknown.
enum class PlayerWorldBuildingFailureV1 : std::uint8_t {
  none = 0,
  exact_build,
  application_main,
  paused_frame,
  held_source,
  player_actor_binding,
  registry_source,
  definition_identity,
  province_slot_source,
  native_final_legality,
  frame_changed,
};

struct PlayerWorldBuildingLegalSampleV1 final {
  std::int32_t barony_title_id = -1;
  std::int32_t province_id = -1;
  std::int32_t building_type_id = -1;
  std::int32_t slot_index = -1;
  friend bool operator==(const PlayerWorldBuildingLegalSampleV1 &,
                         const PlayerWorldBuildingLegalSampleV1 &) = default;
};

struct PlayerWorldBuildingSourceResultV1 final {
  PlayerWorldBuildingFailureV1 failure = PlayerWorldBuildingFailureV1::none;
  bool source_available = false;
  bool native_final_legality_evaluated = false;
  bool checks_truncated = false;
  bool cost_ready = false;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
  std::int32_t definition_source_count = 0;
  std::int32_t final_legality_checks = 0;
  std::vector<PlayerHeldHoldingSourceV1> directly_held_barony_provinces;
  std::vector<PlayerWorldBuildingLegalSampleV1> legal_samples;
};

using NativePlayerBuildingFinalLegalityV1 = bool (*)(
    void *context, std::int32_t actor_character_id,
    std::int32_t province_id, std::uintptr_t building_definition,
    std::int32_t slot_index, bool &allowed) noexcept;

struct PlayerWorldBuildingSourceAccessV1 final {
  CampaignRootAccessV1 campaign;
  NativePlayerBuildingFinalLegalityV1 final_legality = nullptr;
  void *final_legality_context = nullptr;
};

struct PlayerWorldBuildingSourceRequestV1 final {
  std::uint64_t expected_snapshot_revision = 0;
  // From same-frame campaign_root_context, not a fixture CharacterID/key.
  std::int32_t preferred_held_province_id = -1;
  std::int32_t max_native_checks = 512;
  std::int32_t max_legal_samples = 8;
};

// Source: stock construction enumerators 0x1922305/0x15ABC4B call
// accessor 0xC8CEE0 -> module+0x57BFFD0; +0x68/+0x74 is a vector of
// CBuildingType pointers. The callback must bind only exact 0x295CD60,
// called by stock player GUIPotentialBuildingItem at 0x11A632E with
// actor/Province/definition/slot and true,null stack arguments.
[[nodiscard]] PlayerWorldBuildingSourceResultV1
ReadPlayerWorldBuildingDefinitionSourcesV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    const PlayerWorldBuildingSourceAccessV1 &access,
    const PlayerWorldBuildingSourceRequestV1 &request) noexcept;

} // namespace xar::ck3_11906

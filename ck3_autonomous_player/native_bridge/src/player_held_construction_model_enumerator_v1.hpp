#pragma once

#include "xar_bridge/campaign_root_context_v1.hpp"

#include <cstdint>
#include <vector>

namespace xar::ck3_11906 {

// Private source enumeration only. No public capability, legality decision,
// construction action, or production advertisement is implied by this result.
enum class PlayerHeldConstructionModelStatusV1 : std::uint8_t {
  unavailable = 0,
  sources_available,
};

enum class PlayerHeldConstructionModelFailureV1 : std::uint8_t {
  none = 0,
  exact_build,
  application_main,
  paused_frame,
  player_identity,
  held_title_source,
  holding_province_identity,
  definition_source,
  frame_changed,
};

struct PlayerHeldHoldingSourceV1 final {
  std::int32_t barony_title_id = -1;
  std::int32_t province_id = -1;
  friend bool operator==(const PlayerHeldHoldingSourceV1 &,
                         const PlayerHeldHoldingSourceV1 &) = default;
};

struct PlayerHeldConstructionModelResultV1 final {
  PlayerHeldConstructionModelStatusV1 status =
      PlayerHeldConstructionModelStatusV1::unavailable;
  PlayerHeldConstructionModelFailureV1 failure =
      PlayerHeldConstructionModelFailureV1::none;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
  std::vector<PlayerHeldHoldingSourceV1> directly_held_barony_provinces;
  // CHoldingView mode-0 definition source order. These borrowed native
  // addresses are for a later same-callback final-legality reader only: never
  // serialize, checkpoint, or reuse after leaving application-main.
  std::vector<std::uintptr_t> borrowed_definition_addresses;
  // The exact native player legality/CanConstruct result remains unqueried.
  bool legal_construction_evaluated = false;
};

struct PlayerHeldConstructionModelRequestV1 final {
  std::uint64_t expected_snapshot_revision = 0;
};

// CK3 1.19.0.6 exact EXE SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
// Reads played Character -> personally held tier-1 baronies -> Province
// identities, plus the independent model definition source which CHoldingView
// ctor copies from module+0x57BFBA8. Does not call any native producer/action.
[[nodiscard]] PlayerHeldConstructionModelResultV1
ReadPlayerHeldConstructionModelSourcesV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    const CampaignRootAccessV1 &access,
    const PlayerHeldConstructionModelRequestV1 &request) noexcept;

} // namespace xar::ck3_11906

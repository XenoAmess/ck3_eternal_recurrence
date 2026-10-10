#pragma once

#include "xar_bridge/ck3_12004_construction.hpp"
#include "xar_bridge/construction_owner_mode3_inputs_12004.hpp"
#include <vector>

namespace xar::ck3_12004 {

struct HeldConstructionMode3InputV1 {
  std::int32_t barony_title_id = -1;
  std::int32_t province_id = -1;
  construction_owner_mode3::ConstructionOwnerMode3InputsV1 inputs;
};

struct PlayerHeldConstructionMode3InputResultV1 {
  bool current_frame_observed = false;
  PlayerHeldConstructionModelFailureV1 failure =
      PlayerHeldConstructionModelFailureV1::none;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
  std::vector<HeldConstructionMode3InputV1> holdings;
};

// Optional additional material for the existing held/current query. The
// existing request/revision and same main-thread access remain unchanged.
// Per-holding unknown mode3 source inputs never invalidate ordinary
// construction inventory/receipt material. Borrowed input pointers must not
// be serialized or retained after the callback.
PlayerHeldConstructionMode3InputResultV1
ReadPlayerHeldConstructionMode3InputsV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    const CampaignRootAccessV1 &access,
    const PlayerHeldConstructionModelRequestV1 &request) noexcept;

} // namespace xar::ck3_12004

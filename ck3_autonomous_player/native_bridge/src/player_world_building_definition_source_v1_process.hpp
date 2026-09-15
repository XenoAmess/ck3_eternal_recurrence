#pragma once

#include "player_world_building_definition_source_v1.hpp"

#include <cstdint>

namespace xar::ck3_11906 {

// Private exact-build process binding. The caller must pass this callback only
// to ReadPlayerWorldBuildingDefinitionSourcesV1 while its existing paused
// application-main mailbox owns the same snapshot revision.
struct PlayerWorldBuildingNativeCallAccessV1 final {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
};

[[nodiscard]] NativePlayerBuildingFinalLegalityV1
BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(
    PlayerWorldBuildingNativeCallAccessV1 &access) noexcept;

} // namespace xar::ck3_11906

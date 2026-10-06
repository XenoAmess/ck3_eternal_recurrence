#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_world.hpp"

namespace xar::ck3_12004 {

using WorldBindings = ck3_12002::WorldBindings;
using WorldReadResult = ck3_12002::WorldReadResult;

WorldBindings BindWorldImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
void *ResolveWar12004(const WorldBindings &bindings,
    std::int32_t war_id) noexcept;
bool ReadWarParticipantIds12004(const void *side,
    std::vector<std::int32_t> &out) noexcept;
bool ReadWarTargetTitleIds12004(const void *war,
    std::vector<std::int32_t> &out) noexcept;
WorldReadResult ReadActiveWars12004(const WorldBindings &bindings,
    std::int32_t player_character_id, std::span<const game::ArmySnapshot> armies,
    std::vector<game::ActiveWarSnapshot> &out) noexcept;
WorldReadResult ReadWorldSnapshot12004(const WorldBindings &bindings,
    const ck3_12002::ArmyBindings &armies, const ck3_12002::ProvinceBindings &provinces,
    const CoreSnapshotPrefix &core, game::Snapshot &out) noexcept;

} // namespace xar::ck3_12004

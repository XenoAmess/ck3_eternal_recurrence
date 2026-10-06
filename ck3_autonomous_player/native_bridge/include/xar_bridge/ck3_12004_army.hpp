#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_army.hpp"

namespace xar::ck3_12004 {

// Shared DTOs and readers contain no executable selection. Only this exact
// build binder supplies their native addresses.
using ArmyBindings = ck3_12002::ArmyBindings;
using ArmyStrengthScope = ck3_12002::ArmyStrengthScope;

ArmyBindings BindArmyImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
void *ResolveArmyUnit12004(const ArmyBindings &bindings,
    std::int32_t army_id) noexcept;
void *ResolveInternalArmy12004(const ArmyBindings &bindings,
    std::int32_t internal_army_id) noexcept;
bool ReadArmyGathering12004(const ArmyBindings &bindings, std::int32_t unit_id,
    bool &gathering) noexcept;
bool ReadArmiesForCharacters12004(const ArmyBindings &bindings,
    std::span<const std::int32_t> owner_character_ids,
    std::vector<game::ArmySnapshot> &out,
    std::int32_t controlled_owner_character_id = -1) noexcept;
game::ReadArmyStrengthsResult ReadArmyStrengthsForScope12004(const ArmyBindings &bindings,
    std::span<const ArmyStrengthScope> scope,
    std::vector<game::ArmyStrengthSnapshot> &out) noexcept;
game::ReadArmyStrengthsResult ReadArmyStrengths12004(const ArmyBindings &bindings,
    const game::Snapshot &world,
    std::vector<game::ArmyStrengthSnapshot> &out) noexcept;
game::ArmyProvinceSupplySnapshot ReadArmyProvinceSupplyForPreview12004(
    const ArmyBindings &bindings, const ck3_12002::MilitaryWorldAccess &access,
    const game::PreviewMoveArmyResult &preview) noexcept;

} // namespace xar::ck3_12004

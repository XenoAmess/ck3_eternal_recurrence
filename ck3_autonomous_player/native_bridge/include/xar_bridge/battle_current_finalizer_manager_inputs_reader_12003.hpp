#pragma once

#include "xar_bridge/battle_current_finalizer_manager_inputs_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12002 {

struct BattleBindings;

inline constexpr std::uintptr_t kBattleFinalizerManagerSecondaryVtable12003Rva =
    0x477F178;
inline constexpr std::size_t kBattleFinalizerManagerGameStateDomain12003Offset =
    0xA0;
inline constexpr std::size_t kBattleFinalizerManagerDomain12003Offset = 0x2E9D0;

// Additive exact .3 leaf. This never binds .2 and calls no native function.
void EnableBattleCurrentFinalizerManagerInputs12003(
    BattleBindings &, std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// Called only inside the existing paused owner-thread ControlSample, using its
// already strict-resolved actual Combat. Null does not invalidate control ready.
std::optional<game::BattleControlCurrentFinalizerManagerInputsV1>
ReadCurrentFinalizerManagerInputs12003(
    const BattleBindings &, const void *strict_actual_combat,
    std::int32_t requested_full_combat_id) noexcept;

} // namespace xar::ck3_12002

#pragma once

#include "xar_bridge/ck3_12002_sway_completion_execution.hpp"

namespace xar::ck3_12004 {

// Current constructor RIP producers, typed COLs and slot22 pointer values.
// See sway-hidden-phase-source-input-12004.md and the actual tiny receipt.
inline constexpr std::array<std::uintptr_t, 3> kSwayExecutionVtableRvas12004{
    0x4837290, 0x4837438, 0x4837370};
inline constexpr std::array<std::uintptr_t, 3> kSwayExecutionSlotRvas12004{
    0x4837340, 0x48374E8, 0x4837420};
inline constexpr std::array<std::uintptr_t, 3> kSwayExecutionExecuteRvas12004{
    0x2CC9420, 0x2CC8470, 0x2CC7180};
inline constexpr std::uintptr_t kSwayExecutionTitleWrapperRva12004 = 0x48BD0C0;
inline constexpr std::uintptr_t kSwayExecutionScalarRva12004 = 0x4929F18;
inline constexpr std::uintptr_t kSwayExecutionScopeLookupRva12004 = 0x373B520;
inline constexpr std::uintptr_t kSwayExecutionCommandKeyGetterRva12004 = 0x3F4F8E0;

ck3_12002::SwayExecutionBindings12002 BindSwayExecutionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004

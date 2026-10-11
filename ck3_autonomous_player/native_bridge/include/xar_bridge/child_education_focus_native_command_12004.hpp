#pragma once

#include "xar_bridge/ck3_12004_lifestyle.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3_12004::lifestyle {

// Query only: false is the original native AL result; unavailable readiness or
// a native exception returns nullopt. This function never submits a command.
std::optional<bool> ValidateResolvedChildEducationFocusNativeAdapter12004V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uint32_t actual_child_full_id,
    std::uint32_t actual_played_controller_full_id,
    std::uintptr_t resolved_education_focus_definition) noexcept;

// The host must resolve both full IDs and qualify the education definition in
// the same paused application-main query. This adapter preserves the target
// and controller fields independently and asks the original native validator.
// A submitted result is a pending NATIVE_ACK; it does not prove application.
PlayerLifestyleSelectionNativeDispatchResultV1
DispatchResolvedChildEducationFocusNativeAdapter12004V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uint32_t actual_child_full_id,
    std::uint32_t actual_played_controller_full_id,
    std::uintptr_t resolved_education_focus_definition) noexcept;

} // namespace xar::ck3_12004::lifestyle

#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_prisoner_war_retention.hpp"

namespace xar::ck3_12004 {

// Complete actual .4 getters are retained in the prisoner domain ABI packet.
inline constexpr std::uintptr_t kWarRetentionPrimaryTitleRva12004 = 0x289DA10;
inline constexpr std::uintptr_t kWarRetentionImprisonedByRva12004 = 0x289E810;

// The shared reader consumes qualified physical layouts, not an old image
// identity. This factory never invokes the old .2/.3 image binder.
ck3_12002::PrisonerWarRetentionBindings BindPrisonerWarRetentionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004

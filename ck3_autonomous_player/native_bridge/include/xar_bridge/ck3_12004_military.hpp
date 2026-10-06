#pragma once

#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12003_maa_create.hpp"
#include "xar_bridge/ck3_12003_maa_recruitment.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12004 {

// The actual .4 command bundle is caller owned and must outlive this binding.
// The existing Military software reads, previews and submissions consume it.
ck3_12002::MilitaryBindings BindMilitaryImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::CommandBindings &commands) noexcept;

// These retain the regular personal MAA DTOs and their independent readiness.
ck3_12003::NativeMaaRecruitmentBindings BindNativeMaaRecruitmentImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

ck3_12003::NativeMaaCreateBindings BindNativeMaaCreateImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004

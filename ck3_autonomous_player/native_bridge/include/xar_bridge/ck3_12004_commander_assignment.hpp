#pragma once

#include "xar_bridge/ck3_12003_commander_assignment.hpp"

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kCommanderAssignmentDefaultFactoryRva12004 =
    0x297BAE0;
inline constexpr std::uintptr_t kCommanderAssignmentValidatorRva12004 =
    0x2971460;

// Address calculation only. Dependencies are owned by the caller and must
// come from the actual .4 commander and command factories. Existing binding
// types preserve the adopted executor, source ownership and result DTO.
ck3_12003::CommanderAssignmentBindings BindCommanderAssignmentImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12003::CommanderBindings &commanders,
    const ck3_12002::CommandBindings &commands) noexcept;

} // namespace xar::ck3_12004

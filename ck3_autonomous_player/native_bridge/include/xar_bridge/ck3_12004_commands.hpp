#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"

namespace xar::ck3_12004 {

// Actual named native constructors/clones and typed vtable uses are sealed in
// COMMAND-LAYOUT-MAP.json; manager/queue source use is in the core ledger.
inline constexpr std::uintptr_t kCommandManagerRva12004 = 0x5CC1240;
inline constexpr std::uintptr_t kQueueOwnedCommandRva12004 = 0x37F06D0;
inline constexpr std::uintptr_t kPausePrimaryVtableRva12004 = 0x476C8A8;
inline constexpr std::uintptr_t kPauseSecondaryVtableRva12004 = 0x476C878;
inline constexpr std::uintptr_t kSetSpeedPrimaryVtableRva12004 = 0x476C718;
inline constexpr std::uintptr_t kSetSpeedSecondaryVtableRva12004 = 0x476C650;
inline constexpr std::uintptr_t kAutoSavePrimaryVtableRva12004 = 0x44B5158;
inline constexpr std::uintptr_t kAutoSaveSecondaryVtableRva12004 = 0x44B51F0;

// Canonical actual4 address binder. CommandBindings is a shared software
// dependency bundle; no old executable identity or binder is delegated.
ck3_12002::CommandBindings BindCommandImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004

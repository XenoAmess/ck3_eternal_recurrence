#pragma once

#include "xar_bridge/ck3_12002_battle_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_battle.hpp"

namespace xar::ck3_12004 {

// Actual .4 mandatory_startup_detours in CORE-FUNCTION-MAP.json. Each
// displaced prologue is byte-identical to the existing journal's 16/16/16/14
// byte window. The chained projector/appender suffixes and capture fields are
// pinned separately in actual4-domain/journal-map and the domain owner ledgers.
inline constexpr std::uintptr_t kBattleTerminalFinalizerRva12004 = 0x258CD30;
inline constexpr std::uintptr_t kBattleWarscoreWriterRva12004 = 0x249A920;
inline constexpr std::uintptr_t kBattleSideResultProjectorRva12004 = 0x2667E70;
inline constexpr std::uintptr_t kBattleCharacterResultAppendRva12004 = 0x1423960;
inline constexpr std::uintptr_t kBattleJournalUnitStorageRva12004 = 0x5D1E380;
inline constexpr std::uintptr_t kBattleJournalArmyStorageRva12004 = 0x5D1DE48;

// Produces the actual .4 capture/install environment without installing hooks,
// initializing rings, reading process memory or calling a native function.
// Only the four roots consumed by the adopted capture routines are admitted.
// The caller supplies actual .4 BattleBindings and the managed suspension fact
// before passing the environment to the existing software journal installer.
ck3_12002::BattleTerminalJournalInstallEnvironmentV1
BindBattleJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::BattleBindings &actual_battle_bindings) noexcept;

// Address calculation only. The caller supplies its actual .4 capture
// bindings and the existing managed suspended-thread install admission.
// No process memory is read, no native entry is called and no hook is installed.
bool ConfigureBattleJournalTargets12004(
    ck3_12002::BattleTerminalJournalInstallEnvironmentV1 &environment,
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004

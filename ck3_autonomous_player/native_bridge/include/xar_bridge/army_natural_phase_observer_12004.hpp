#pragma once

#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <string_view>

namespace xar::ck3_12004 {
struct ArmyNaturalPhaseObserverEnvironment12004 {
  std::uintptr_t module_base = 0;
  std::string_view actual_exe_sha256;
  ArmyNaturalPhaseRead12004 read = nullptr;
  void *read_context = nullptr;
  bool primary_thread_suspended_proven = false;
};
struct ArmyNaturalPhaseObserverState12004 {
  bool installed = false;
  bool pre_date_installed = false;
  bool post_date_installed = false;
  bool source_bytes_verified = false;
  bool module_lifetime_pinned = false;
  bool pre_date_patch_applied = false;
  bool post_date_patch_applied = false;
  std::string_view reason = "not_installed";
};
// Root alone invokes this in its proved suspended-primary startup window.
// Process-lifetime trampolines are retained. This API does not detach/reset clocks.
bool InstallArmyNaturalPhaseObserver12004(
    const ArmyNaturalPhaseObserverEnvironment12004 &,
    ArmyNaturalPhaseObserverState12004 &) noexcept;
ArmyNaturalPhaseObserverState12004 ReadArmyNaturalPhaseObserverState12004() noexcept;
} // namespace xar::ck3_12004

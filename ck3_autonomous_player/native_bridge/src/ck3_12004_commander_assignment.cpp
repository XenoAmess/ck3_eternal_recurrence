#include "xar_bridge/ck3_12004_commander_assignment.hpp"

#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {

ck3_12003::CommanderAssignmentBindings BindCommanderAssignmentImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12003::CommanderBindings &commanders,
    const ck3_12002::CommandBindings &commands) noexcept {
  ck3_12003::CommanderAssignmentBindings bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return bindings;
  }
  bindings.commanders = commanders;
  bindings.commands = commands;
  // The complete actual .4 constructor supplies both command interfaces
  // and native-owned 0x30-byte storage. ApplyArmyCommanderAssignment writes
  // mode/candidate/internal Army at +0x20/+0x24/+0x28 before validation.
  bindings.create_default = reinterpret_cast<decltype(bindings.create_default)>(
      image_base + kCommanderAssignmentDefaultFactoryRva12004);
  // Resolved from the constructor's actual primary vtable +0x30, then
  // matched as a complete body including full-generation Army/Character
  // resolution and the tailcall to actual .4 can_set_commander.
  bindings.validate_source =
      reinterpret_cast<decltype(bindings.validate_source)>(
          image_base + kCommanderAssignmentValidatorRva12004);
  bindings.enabled = bindings.commanders.enabled && bindings.commands.enabled;
  return bindings;
}

} // namespace xar::ck3_12004

#include "xar_bridge/ck3_12004_war_declarations.hpp"

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_holy_war.hpp"

namespace xar::ck3_12004 {

ck3_12002::DeclarationsBindings BindDeclarationsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::CommandBindings &actual_commands) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return {};
  auto bindings = BindOrdinaryHolyWarDeclarationsImage12004(
      image_base, executable_sha256);
  if (!bindings.enabled) return bindings;
  bindings.commands = actual_commands;
  // diplomacy-map/first01/construct_send_interaction_command-DETAIL.json:
  // full 164 B match and actual RIP-selected primary/secondary native tables.
  bindings.construct_send =
      reinterpret_cast<ck3_12002::DeclarationsConstructSend>(
          image_base + 0x2968150);
  bindings.send_primary_vtable = image_base + 0x448BCF0;
  bindings.send_secondary_vtable = image_base + 0x448BCC0;
  return bindings;
}

} // namespace xar::ck3_12004

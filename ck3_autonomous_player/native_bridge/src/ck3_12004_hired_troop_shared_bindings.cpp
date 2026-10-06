#include "xar_bridge/ck3_12004_hired_troop_shared_bindings.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"

namespace xar::ck3_12004::hired_troops {
SharedBindings12004 BindHiredTroopSharedImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  SharedBindings12004 b{};
  if (base == 0 || sha != ck3_12004::kExecutableSha256) return b;
  // Complete1732B source includes the actual ten-entry local resource table.
  b.can_afford = reinterpret_cast<CanAfford>(base + 0x310E6F0);
  // Reuse the separately sealed actual4 complete94B SSO destructor proof.
  b.reason_destroy = reinterpret_cast<ReasonDestroy>(base + 0x856050);
  b.commands = ck3_12004::BindCommandImage12004(base, sha);
  b.enabled = true;
  return b;
}
} // namespace xar::ck3_12004::hired_troops

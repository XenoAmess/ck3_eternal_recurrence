#include "xar_bridge/ck3_12004_holy_war_defender_join_inputs.hpp"

namespace xar::ck3_12004::religion::holy_war_defender_join {

Bindings BindHolyWarDefenderJoinInputsImage12004(
    std::uintptr_t base, std::string_view sha,
    const ContextBindings &actual_existing_faith) noexcept {
  Bindings bindings{};
  if (!base || sha != ck3_12004::kExecutableSha256) return bindings;
  bindings.enabled = true;
  bindings.faith = actual_existing_faith;
  bindings.collector = reinterpret_cast<
      ck3_12002::religion::holy_war_defender_join::Collector>(
      base + kCollectorRva12004);
  bindings.engine_allocator = reinterpret_cast<void *>(
      base + kEngineAllocatorRva12004);
  // Null selects the retained reader's actual allocator vtable+10 release.
  // The synthetic fixture replaces it with its explicitly synthetic callback.
  return bindings;
}

} // namespace xar::ck3_12004::religion::holy_war_defender_join

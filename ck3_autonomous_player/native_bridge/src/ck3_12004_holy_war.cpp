#include "xar_bridge/ck3_12004_holy_war.hpp"

namespace xar::ck3_12004 {
namespace {
template <class Fn> Fn Function(std::uintptr_t base, std::uintptr_t rva) noexcept {
  return reinterpret_cast<Fn>(base + rva);
}
} // namespace

ck3_12002::DeclarationsBindings BindOrdinaryHolyWarDeclarationsImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::DeclarationsBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.core = ::xar::ck3_12004::BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.configuration_scratch = reinterpret_cast<void *>(base + 0x54E14B8);
  b.get_cb_database = Function<ck3_12002::DeclarationsDatabaseGetter>(base, 0x8FC320);
  b.get_interaction_database = Function<ck3_12002::DeclarationsDatabaseGetter>(base, 0x89DA60);
  b.evaluate_cb = Function<ck3_12002::DeclarationsEvaluateCb>(base, 0x31F4520);
  b.destroy_configuration = Function<ck3_12002::DeclarationsDestroy>(base, 0x111F190);
  b.construct_context = Function<ck3_12002::DeclarationsConstructContext>(base, 0x3076C70);
  b.refresh_context = Function<ck3_12002::DeclarationsRefreshContext>(base, 0x3078A40);
  b.finalize_context = Function<ck3_12002::DeclarationsDestroy>(base, 0x3078C70);
  b.validate_context = Function<ck3_12002::DeclarationsValidateContext>(base, 0x307C020);
  b.destroy_context = Function<ck3_12002::DeclarationsDestroy>(base, 0x3077380);
  b.copy_int_array = Function<ck3_12002::DeclarationsCopyIntArray>(base, 0xC858C0);
  b.append_int_array = Function<ck3_12002::DeclarationsAppendIntArray>(base, 0x9E3790);
  b.war_declaration_vtable = base + 0x452FFD0;
  // Actual4 table identity is verified by its bounded typed prefix and the
  // actual +0x60 dispatch word. No common rdata shift is used for admission.
  // Leave command construction/payment fields to the overall WAR factory.
  b.enabled = true;
  return b;
}

ck3_12002::OrdinaryHolyWarCbCostBindingsV1 BindOrdinaryHolyWarCbCostImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::OrdinaryHolyWarCbCostBindingsV1 b{};
  if (!base || sha != kExecutableSha256) return b;
  b.construct_scope = Function<ck3_12002::OrdinaryHolyWarScopeCtorV1>(base, 0x889F60);
  b.populate_scope = Function<ck3_12002::OrdinaryHolyWarScopePopulateV1>(base, 0x2A814E0);
  b.destroy_scope = Function<ck3_12002::OrdinaryHolyWarScopeDtorV1>(base, 0x87E0E0);
  b.evaluate_cost = Function<ck3_12002::OrdinaryHolyWarCostEvaluatorV1>(base, 0x310CEC0);
  b.native_character_fallback_slot = reinterpret_cast<void **>(base + 0x5C67570);
  b.enabled = true;
  return b;
}
} // namespace xar::ck3_12004

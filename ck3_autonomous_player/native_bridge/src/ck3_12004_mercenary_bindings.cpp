#include "xar_bridge/ck3_12004_mercenary_bindings.hpp"
#include "xar_bridge/ck3_12004_hired_troop_shared_bindings.hpp"

namespace xar::ck3_12004::mercenary {

ck3_12003::mercenary::CandidateBindings BindMercenaryCandidatesImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12003::mercenary::CandidateBindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  // Actual 29942C0: current Merc registry, full generation lookup and Merc tag.
  // Actual 2625700: unchanged persistent roster and signed native headcount.
  b.manager_slot = reinterpret_cast<void **>(base + 0x5D1DF08);
  b.fallback_slot = reinterpret_cast<void **>(base + 0x5D1DEF8);
  b.current_soldiers = reinterpret_cast<decltype(b.current_soldiers)>(
      base + 0x2625700);
  b.enabled = true;
  return b;
}

ck3_12003::mercenary::FinalTermsBindings BindMercenaryFinalTermsImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12003::mercenary::FinalTermsBindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  const auto shared = hired_troops::BindHiredTroopSharedImage12004(base, sha);
  if (!shared.enabled) return b;
  b.can_hire = reinterpret_cast<decltype(b.can_hire)>(base + 0x26242B0);
  b.cost = reinterpret_cast<decltype(b.cost)>(base + 0x2625390);
  b.payment_status = reinterpret_cast<decltype(b.payment_status)>(
      base + 0x2625450);
  b.hire_duration = reinterpret_cast<decltype(b.hire_duration)>(
      base + 0x2625560);
  b.can_afford = shared.can_afford;
  b.reason_destroy = shared.reason_destroy;
  b.enabled = true;
  return b;
}

ck3_12003::mercenary::CompositionBindings BindMercenaryCompositionImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12003::mercenary::CompositionBindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  // Actual 2625700/2626410 plus Army Regi-tag and inherited GDbO key
  // witnesses close the reused composition software fields. The Province
  // K getter independently closes the signed MaA tier+2A0.
  b.persistent_regiment_storage_slot =
      reinterpret_cast<void **>(base + 0x5D1EB68);
  b.persistent_regiment_fallback_slot =
      reinterpret_cast<void **>(base + 0x5D1EB58);
  b.company_holder = reinterpret_cast<decltype(b.company_holder)>(
      base + 0x2626410);
  b.enabled = true;
  return b;
}

ck3_12003::mercenary::HireActionBindings BindMercenaryHireActionImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12003::mercenary::HireActionBindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  const auto shared = hired_troops::BindHiredTroopSharedImage12004(base, sha);
  b.candidates = BindMercenaryCandidatesImage12004(base, sha);
  b.final_terms = BindMercenaryFinalTermsImage12004(base, sha);
  b.commands = shared.commands;
  b.create_default = reinterpret_cast<decltype(b.create_default)>(
      base + 0x29958D0);
  b.validate_source = reinterpret_cast<decltype(b.validate_source)>(
      base + 0x29942C0);
  b.enabled = shared.enabled && b.commands.enabled && b.candidates.enabled &&
      b.final_terms.enabled;
  return b;
}

ck3_12003::MercenaryPositionBindingsV1 BindMercenaryPositionImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12003::MercenaryPositionBindingsV1 b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.get_title_province = reinterpret_cast<decltype(b.get_title_province)>(
      base + 0x230F8E0);
  b.select_hire_raise_province =
      reinterpret_cast<decltype(b.select_hire_raise_province)>(base + 0x24A6A90);
  b.skip_selector_when_no_active_wars = true;
  return b;
}

} // namespace xar::ck3_12004::mercenary

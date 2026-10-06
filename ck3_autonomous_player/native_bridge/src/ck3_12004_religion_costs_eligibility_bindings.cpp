#include "xar_bridge/ck3_12004_religion_costs_eligibility_bindings.hpp"

namespace xar::ck3_12004::religion {
namespace {
namespace reform = ck3_12002::religion_reform;

constexpr std::uintptr_t kPietyCostRva = 0x14F57A0;
constexpr std::uintptr_t kPietyMissingRva = 0x14F58C0;
constexpr std::uintptr_t kEditingOwnedCurrentRiteRva = 0x14F43E0;
constexpr std::uintptr_t kCanCreateRiteRva = 0x14F56B0;
constexpr std::uintptr_t kCanEditRiteRva = 0x14F5030;
// The actual .4 full 94-byte destructor is reused from the adopted law map.
constexpr std::uintptr_t kNativeReasonStringDestroyRva = 0x856050;

bool Admitted(std::uintptr_t base, std::string_view sha) noexcept {
  return base != 0 && sha == ck3_12004::kExecutableSha256;
}
} // namespace

reform::CostBindings BindRiteCreationCostsImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  reform::CostBindings bindings{};
  if (!Admitted(base, sha)) return bindings;
  bindings.enabled = true;
  bindings.piety_cost = reinterpret_cast<reform::WindowFixedGetter>(base + kPietyCostRva);
  bindings.piety_missing = reinterpret_cast<reform::WindowFixedGetter>(base + kPietyMissingRva);
  bindings.editing_owned_current_rite = reinterpret_cast<reform::WindowBoolGetter>(base + kEditingOwnedCurrentRiteRva);
  return bindings;
}

reform::EligibilityBindings BindEligibilityImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  reform::EligibilityBindings bindings{};
  if (!Admitted(base, sha)) return bindings;
  bindings.enabled = true;
  bindings.can_create_rite = reinterpret_cast<reform::DraftEligibilityGetter>(base + kCanCreateRiteRva);
  bindings.can_edit_rite = reinterpret_cast<reform::DraftEligibilityGetter>(base + kCanEditRiteRva);
  bindings.destroy_reason_string = reinterpret_cast<reform::DraftReasonStringDestroy>(base + kNativeReasonStringDestroyRva);
  return bindings;
}

} // namespace xar::ck3_12004::religion

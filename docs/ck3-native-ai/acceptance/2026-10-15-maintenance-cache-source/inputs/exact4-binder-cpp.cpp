#include "xar_bridge/ck3_12004_war_cash_claim_terms.hpp"

namespace xar::ck3_12004 {

ck3_12003::war_cash_current::Bindings
BindWarCashCurrentImage(std::uintptr_t image_base,
                        std::string_view executable_sha256) noexcept {
  using namespace ck3_12003::war_cash_current;
  Bindings output{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return output;
  output.enabled = true;
  output.monthly_income = reinterpret_cast<MonthlyIncome>(
      image_base + kWarCashMonthlyIncomeRva);
  output.expense_context_character = reinterpret_cast<ExpenseContextCharacter>(
      image_base + kWarCashExpenseContextCharacterRva);
  output.monthly_total_expenses = reinterpret_cast<MonthlyTotalExpenses>(
      image_base + kWarCashMonthlyTotalExpensesRva);
  output.current_maintenance = reinterpret_cast<CurrentMaintenance>(
      image_base + kWarCashCurrentMaintenanceRva);
  output.all_raised_maintenance = reinterpret_cast<AllRaisedMaintenance>(
      image_base + kWarCashAllRaisedMaintenanceRva);
  return output;
}

std::string SerializeWarCashCurrentResourcesV1(
    const ck3_12003::war_cash_current::ActorResources &resources,
    const game::Snapshot &snapshot, std::uint64_t snapshot_revision,
    bool same_frame_ready) {
  return ck3_12003::war_cash_current::SerializeCurrentResourcesV1(
      resources, snapshot, snapshot_revision, same_frame_ready,
      kGameVersion, kExecutableSha256);
}

ck3_12002::ClaimTermsBindings BindClaimTermsImage(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const CoreBindings &actual_core,
    const ck3_12002::WorldBindings &actual_world,
    const ck3_12002::ProvinceBindings &actual_provinces) noexcept {
  ck3_12002::ClaimTermsBindings output{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      !actual_core.enabled || !actual_world.enabled ||
      !actual_provinces.enabled) return output;
  output.enabled = true;
  output.core = actual_core;
  output.world = actual_world;
  output.provinces = actual_provinces;
  output.read_character_claim =
      reinterpret_cast<ck3_12002::ReadCharacterClaim12002>(
          image_base + kClaimTermsGetterRva);
  output.character_claim_vtable = image_base + kClaimTermsClaimVtableRva;
  return output;
}

} // namespace xar::ck3_12004

#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_claim_terms.hpp"
#include "xar_bridge/ck3_12003_war_cash_current_reader.hpp"
#include "xar_bridge/ck3_12003_war_cash_current_serializer.hpp"

// Actual .3/.4 paired spans and selected operands:
// python-binding/cash-terms-native/first01/FAMILY-MAP.json and
// selected-operands-code152-first01/SELECTED-OPERANDS-PROOF.json.
// CB type index/string layout: cb-type-first01/FAMILY-MAP.json.
// Treasury uses the independently closed RESOURCE-FAMILY-STRESS-MAP.json.
// Software DTOs and reader arithmetic are retained; no old image binder is used.
namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kWarCashMonthlyIncomeRva = 0x2BCA940;
inline constexpr std::uintptr_t kWarCashExpenseContextCharacterRva = 0x28BFD80;
inline constexpr std::uintptr_t kWarCashMonthlyTotalExpensesRva = 0x2BCB160;
inline constexpr std::uintptr_t kWarCashCurrentMaintenanceRva = 0x2C13F60;
inline constexpr std::uintptr_t kWarCashAllRaisedMaintenanceRva = 0x2C152B0;
inline constexpr std::uintptr_t kClaimTermsGetterRva = 0x2B9ECB0;
inline constexpr std::uintptr_t kClaimTermsClaimVtableRva = 0x44F17E8;
inline constexpr std::uintptr_t kClaimTermsScalarDestructorRva = 0xDDC610;
inline constexpr std::string_view kWarCashMonthlyFlowSemantics =
    "ck3-1.20.0.4-native-income-minus-total-expenses-v2";

ck3_12003::war_cash_current::Bindings
BindWarCashCurrentImage(std::uintptr_t image_base,
                        std::string_view executable_sha256) noexcept;

std::string SerializeWarCashCurrentResourcesV1(
    const ck3_12003::war_cash_current::ActorResources &resources,
    const game::Snapshot &snapshot, std::uint64_t snapshot_revision,
    bool same_frame_ready);

// All three bundles must be actual .4 caller-owned bindings. The world/province
// owners supply their independently mapped roots/functions and admission data.
ck3_12002::ClaimTermsBindings BindClaimTermsImage(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const CoreBindings &actual_core,
    const ck3_12002::WorldBindings &actual_world,
    const ck3_12002::ProvinceBindings &actual_provinces) noexcept;

} // namespace xar::ck3_12004

#pragma once

#include "xar_bridge/ck3_1210_monthly_flow_v1.hpp"
#include "xar_bridge/ck3_1210_personal_gold_v1.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_1210 {

inline constexpr char kPersonalCashStepV1[] = "query-war-cash-current-resources-v1";
inline constexpr char kPersonalCashSchemaV1[] = "xar.ck3.war-cash-current-resources.v1";
inline constexpr char kPersonalCashMilitaryUnknownV1[] =
    "ck3_1210_military_maintenance_not_qualified";

// The integration owner must read the CURRENT real Full observation and its
// current published native revision while retaining the same paused main/TLS
// custody. Returning a cached copy of the supplied basis is not this contract.
// The callback does not publish, increment a revision, dispatch or grant roles.
using PersonalCashReadFullV1 = bool (*)(void *context,
    xar::game::Snapshot &current, std::uint64_t &current_native_revision);

struct PersonalCashBindingsV1 {
  bool exact_build_admitted = false;
  // Address binding never opens this gate or the independent monthly gate.
  bool integration_native_calls_permitted = false;
  PersonalGoldBindingsV1 gold{};
  MonthlyFlowBindingsV1 monthly{};
};

struct PersonalCashReadContextV1 {
  // A caller-owned admission, not a thread witness minted by this leaf.
  bool paused_application_main_owner_admitted = false;
  std::uint64_t published_native_revision = 0;
  CoreSnapshotPrefix expected_core{};
  // Retained by the outer owner for the entire call, including callbacks.
  const xar::game::Snapshot *published_full = nullptr;
  PersonalCashReadFullV1 read_current_full = nullptr;
  void *read_current_full_context = nullptr;
};

struct PersonalCashObservationV1 {
  // Completed means coherent personal scalar data; military remains unknown.
  bool completed = false;
  bool same_frame_ready = false;
  bool partial = true;
  bool full_snapshot_available = false;
  bool root_ready = false;
  bool formal_action_ready = false;
  bool true_treasury_observed = false;
  bool military_categories_observed = false;
  bool tax_categories_observed = false;
  bool prosperity_observed = false;
  bool zero_native_side_effects_verified = false;
  bool native_unwind_cleanup_verified = false;
  CoreSnapshotPrefix frame{};
  std::uint64_t native_revision = 0;
  std::vector<std::int32_t> active_war_ids;
  std::vector<std::int32_t> player_army_ids;
  std::optional<std::int64_t> personal_gold_raw;
  std::optional<std::int64_t> monthly_gross_income_raw;
  std::optional<std::int64_t> monthly_total_expenses_raw;
  std::optional<std::int64_t> monthly_net_income_raw;
  std::uint32_t current_full_call_attempts = 0;
  std::uint32_t context_call_attempts = 0;
  bool gross_call_attempted = false;
  bool expenses_call_attempted = false;
  std::string_view unavailable_reason = "personal_cash_not_read";
  std::string_view monthly_unavailable_reason = "personal_cash_not_read";
  std::string_view net_unavailable_reason = "personal_cash_not_read";
};

// Exact1210 address binding only. Both native-call gates stay OFF.
PersonalCashBindingsV1 BindPersonalCashImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// Requires independent outer main/TLS/Full custody. Compares current Full and
// revision to the retained basis before/after; independently checks real Core
// and wallet before/after. The only monthly source is ReadMonthlyFlowV1.
// On failure no monetary value survives, while actual call attempts survive.
// Native caches/allocations/unwind remain unknown; no rollback is promised.
bool ReadPersonalCashV1(const PersonalCashBindingsV1 &bindings,
    const PersonalCashReadContextV1 &context,
    PersonalCashObservationV1 &output) noexcept;

// Pure legacy result object (not a command_result transport envelope).
// current_treasury means personal Gold. Both military rows are unavailable.
// A failed/inconsistent DTO emits only null amounts and false readiness.
// queried_* references still belong to the real Java receipt projection.
// This function grants no query permission, Full/Root role or capability.
std::string SerializePersonalCashV1(const PersonalCashObservationV1 &observation);

} // namespace xar::ck3_1210

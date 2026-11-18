#pragma once

#include "xar_bridge/ck3_1210.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_1210 {

inline constexpr char kMonthlyFlowSchemaV1[] = "ck3_1210_monthly_flow_internal_v1";
inline constexpr std::int64_t kMonthlyFlowScaleV1 = 100'000;
inline constexpr std::uintptr_t kMonthlyFlowContextRvaV1 = 0x2DA46E0;
inline constexpr std::uintptr_t kMonthlyFlowGrossRvaV1 = 0x30F0EA0;
inline constexpr std::uintptr_t kMonthlyFlowExpensesRvaV1 = 0x30F1870;

using MonthlyFlowContextV1 = void *(*)(void *character);
using MonthlyFlowGrossV1 = std::int64_t *(*)(std::int64_t *output,
    void *character, std::int64_t *secondary_income, void *optional_breakdown);
using MonthlyFlowExpensesV1 = std::int64_t *(*)(std::int64_t *output,
    void *character, void *borrowed_context, std::int64_t secondary_income,
    bool exclude_military, void *optional_breakdown);

using MonthlyFlowNativeCallAdmissionV1 = bool (*)(void *context) noexcept;

struct MonthlyFlowBindingsV1 {
  bool exact_build_admitted = false;
  // Default closed, including after exact address binding. Only the outer
  // application-main owner may permit invocation after its own admission.
  // Setting this bit is not a thread witness, capability or live qualification.
  bool integration_native_calls_permitted = false;
  CoreBindings core{};
  MonthlyFlowContextV1 context = nullptr;
  MonthlyFlowGrossV1 gross = nullptr;
  MonthlyFlowExpensesV1 expenses = nullptr;
  // Optional owner-local proof, never wire data. Cash Actor supplies it for
  // every native context/gross/expenses call; legacy null keeps its contract.
  MonthlyFlowNativeCallAdmissionV1 native_call_admission = nullptr;
  void *native_call_admission_context = nullptr;
};

struct MonthlyFlowObservationV1 {
  std::string_view schema = kMonthlyFlowSchemaV1;
  std::string_view game_version = kGameVersion;
  std::string_view steam_build_id = kSteamBuildId;
  std::string_view executable_sha256 = kExecutableSha256;
  std::size_t executable_file_size = kExecutableFileSize;
  bool available = false;
  bool same_frame_ready = false;
  bool gross_ready = false;
  bool total_expenses_ready = false;
  bool net_ready = false;
  bool partial = true;
  bool full_snapshot_available = false;
  bool root_ready = false;
  bool formal_action_ready = false;
  bool treasury_observed = false;
  bool military_categories_observed = false;
  bool tax_categories_observed = false;
  bool prosperity_observed = false;
  // The static ledger does not close recursive caches/allocations or unwind
  // cleanup. Catching a failed invocation does not undo its native effects.
  bool zero_native_side_effects_verified = false;
  bool native_unwind_cleanup_verified = false;
  // Latched on a failed owner check, even if a later predicate could pass.
  // Cash must invalidate the whole read; this is not ordinary monthly unknown.
  bool native_owner_admission_failed = false;
  CoreSnapshotPrefix frame{};
  std::optional<std::int32_t> context_full_id;
  std::uintptr_t actor_identity = 0;
  std::uintptr_t context_identity = 0;
  std::optional<std::int64_t> monthly_gross_income_raw;
  std::optional<std::int64_t> monthly_total_expenses_raw;
  std::optional<std::int64_t> monthly_net_income_raw;
  std::int64_t scale = kMonthlyFlowScaleV1;
  // Failure clears all monetary values, but retains actual call attempts.
  std::uint32_t context_call_attempts = 0;
  bool gross_call_attempted = false;
  bool expenses_call_attempted = false;
  std::string_view unavailable_reason = "monthly_flow_not_read";
  std::string_view net_unavailable_reason = "monthly_flow_not_read";
};

// Address calculation only. No Game code runs and the invocation gate stays
// closed. No old binding/SHA alias or GUI holder/cache is consulted.
MonthlyFlowBindingsV1 BindMonthlyFlowImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// Pure signed arithmetic. False means overflow, never an observed zero NET.
bool CheckedMonthlyNetV1(std::int64_t gross, std::int64_t total_expenses,
    std::int64_t &net) noexcept;

// Internal only; caller separately owns application-main paused custody.
// Native context is borrowed, and gross/secondary/total are the only three
// caller-owned native scalar buffers. No caller context/row destructor exists.
// Null or fallback/unresolvable context is outside this conservative scope.
// False or a throw/fault publishes no amount. Overflow preserves valid gross
// and total with NET null. No serializer, Full/CASH adapter, cap or Java here.
bool ReadMonthlyFlowV1(const MonthlyFlowBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, MonthlyFlowObservationV1 &output) noexcept;

} // namespace xar::ck3_1210

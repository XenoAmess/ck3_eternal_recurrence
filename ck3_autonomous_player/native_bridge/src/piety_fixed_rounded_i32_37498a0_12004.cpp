#include "xar_bridge/piety_fixed_rounded_i32_37498a0_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

PietyFixedRoundedI3237498A012004 ProjectPietyFixedRoundedI3237498A012004(
    const PietyPriceNumericAccess12004 &access,
    std::optional<std::int64_t> actual_raw_q64_i64,
    std::uintptr_t original_named_tuple_identity,
    std::uint64_t unchanged_snapshot_revision) noexcept {
  PietyFixedRoundedI3237498A012004 out{};
  out.module_base = access.module_base;
  out.original_named_tuple_identity = original_named_tuple_identity;
  out.unchanged_snapshot_revision = unchanged_snapshot_revision;
  out.raw_q64_i64 = actual_raw_q64_i64;
  if (!access.exact_12004_bound) {
    out.unavailable_reason = "piety_fixed_round_37498a0_exact_access_unavailable";
    return out;
  }
  if (!actual_raw_q64_i64) return out;

  // 37498B3..37498CD: unsigned addition wraps modulo 2^64, then JBE.
  // This exact guard is stricter than merely testing the rounded result.
  constexpr std::uint64_t kGuardOffset = 0xC35000000000ULL;
  constexpr std::uint64_t kGuardMaximum = 0x1869FFFFE7960ULL;
  const auto raw = *actual_raw_q64_i64;
  out.native_non_diagnostic_branch =
      static_cast<std::uint64_t>(raw) + kGuardOffset <= kGuardMaximum;
  if (!*out.native_non_diagnostic_branch) {
    out.unavailable_reason = "piety_fixed_round_37498a0_diagnostic_branch_unavailable";
    return out;
  }

  // The taken branch reaches 3749A20 directly. Its signed high multiply,
  // SAR14 and sign correction equal truncation by 100000 on this bounded
  // interval. 3749A2F/3749A38 apply the sign-directed half-unit first.
  // The adjusted Q64 and the resulting signed DWORD both fit their types.
  const std::int64_t adjusted = raw + (raw < 0 ? -50000LL : 50000LL);
  out.eax_raw_i32 = static_cast<std::int32_t>(adjusted / 100000LL);
  out.source_ready = true;
  out.unavailable_reason = nullptr;
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs

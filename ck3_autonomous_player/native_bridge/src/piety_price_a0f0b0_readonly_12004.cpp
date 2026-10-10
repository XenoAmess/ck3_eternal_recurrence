#include "xar_bridge/piety_price_a0f0b0_readonly_12004.hpp"

#include <cstddef>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {

std::optional<std::int32_t> ReadRawDword(
    const PietyPriceNumericAccess12004 &access, std::uintptr_t receiver,
    std::size_t offset) noexcept {
  std::int32_t value{};
  if (!ReadPietyPriceNumericField12004(access, receiver, offset, value)) return {};
  return value;
}

} // namespace

PietyPriceA0F0B0Readonly12004 ReadPietyPriceA0F0B0Readonly12004(
    const PietyPriceNumericAccess12004 &access,
    std::uintptr_t selected_expression_identity,
    std::uint64_t unchanged_snapshot_revision) noexcept {
  PietyPriceA0F0B0Readonly12004 out{};
  out.module_base = access.module_base;
  out.expression_identity = selected_expression_identity;
  out.unchanged_snapshot_revision = unchanged_snapshot_revision;
  if (!access.exact_12004_bound || access.guarded_read == nullptr) {
    out.unavailable_reason = "piety_numeric_exact_access_unavailable";
    return out;
  }

  // A0F0DE CMPDWORD[RCX+B8],0 is the first expression demand.
  out.mode_raw_i32 = ReadRawDword(access, selected_expression_identity, 0xB8);
  if (!out.mode_raw_i32) {
    out.unavailable_reason = "piety_numeric_mode_raw_unavailable";
    return out;
  }
  if (*out.mode_raw_i32 != 0) {
    out.unavailable_reason = "piety_numeric_nonzero_mode_child_inputs_unavailable";
    return out;
  }

  // A0F0E7 MOVEAX,[RCX+98]; A0F0ED skips all child and profile calls.
  out.eax_first_raw_i32 = ReadRawDword(access, selected_expression_identity, 0x98);
  if (!out.eax_first_raw_i32) {
    out.unavailable_reason = "piety_numeric_static_eax_raw_unavailable";
    return out;
  }

  // The current copied-input producer owns narrow mode/value bookends.
  // These extra copies do not stand for additional native instructions.
  out.mode_after_raw_i32 = ReadRawDword(access, selected_expression_identity, 0xB8);
  out.eax_after_raw_i32 = ReadRawDword(access, selected_expression_identity, 0x98);
  if (!out.mode_after_raw_i32) {
    out.unavailable_reason = "piety_numeric_mode_bookend_unavailable";
    return out;
  }
  if (!out.eax_after_raw_i32) {
    out.unavailable_reason = "piety_numeric_eax_bookend_unavailable";
    return out;
  }
  if (out.mode_after_raw_i32 != out.mode_raw_i32 ||
      out.eax_after_raw_i32 != out.eax_first_raw_i32) {
    out.unavailable_reason = "piety_numeric_source_operands_changed";
    return out;
  }
  out.eax_raw_i32 = out.eax_first_raw_i32;
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs

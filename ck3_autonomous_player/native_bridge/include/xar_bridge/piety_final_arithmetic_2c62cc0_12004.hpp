#pragma once

#include <bit>
#include <cstdint>

namespace xar::ck3_12004::piety_price_raw_inputs {

enum class PietyFinalMultiplyRoute12004 { small_product, split_product };

// These are the three QWORD operands of the captured final-price function.
// Their source association and readiness belong to the supplying readers.
struct PietyFinalArithmetic2C62CC0Observation12004 {
  std::int64_t entered_base_with223_raw{};
  std::int64_t current_rite_term_raw{};
  std::int64_t actor224_term_raw{};
  std::int64_t clamped_base_raw{};
  std::uint64_t wrapped_factor_bits{};
  PietyFinalMultiplyRoute12004 multiply_route{};
  std::uint64_t pre_clamp_result_bits{};
  std::int64_t final_piety_price_raw_q64{};
  bool arithmetic_source_ready{true};
  bool actual_original_consumed_values{false};
  const char* source_pin{
      "actual4:2C62CC0-2C62E29:"
      "bb68340a187385a3e8803b1ef8c6ca1573727e9e6ef91e37d0167fae60926c43"};
};

namespace piety_final_arithmetic_detail {

// The unsigned high half of a 64x64 product, without compiler-specific 128-bit
// types. Each intermediate except the final high sum fits unsigned64.
constexpr std::uint64_t UnsignedMultiplyHigh(std::uint64_t a,
                                            std::uint64_t b) noexcept {
  constexpr std::uint64_t mask = 0xFFFFFFFFULL;
  const auto a0 = a & mask;
  const auto a1 = a >> 32;
  const auto b0 = b & mask;
  const auto b1 = b >> 32;
  const auto low = a0 * b0;
  const auto middle = a1 * b0 + (low >> 32);
  const auto upper_middle = (middle & mask) + a0 * b1;
  return a1 * b1 + (middle >> 32) + (upper_middle >> 32);
}

constexpr std::uint64_t SignedMultiplyHighBits(std::uint64_t a,
                                              std::uint64_t b) noexcept {
  auto high = UnsignedMultiplyHigh(a, b);
  if (a >> 63) high -= b;
  if (b >> 63) high -= a;
  return high;
}

// Literal IMUL(high) / SAR14 / SHR63 / ADD from the retained native body.
constexpr std::uint64_t NativeQuotientBits(std::uint64_t operand) noexcept {
  constexpr std::uint64_t multiplier = 0x29F16B11C6D1E109ULL;
  const auto high = SignedMultiplyHighBits(operand, multiplier);
  const auto shifted = (high >> 14) |
      ((high >> 63) ? 0xFFFC000000000000ULL : 0ULL);
  return shifted + (shifted >> 63);
}

constexpr bool SmallOperand(std::uint64_t operand) noexcept {
  return operand + 0xB504F333ULL <= 0x16A09E666ULL;
}

} // namespace piety_final_arithmetic_detail

// Numerical projection of 2C62CC0 after its two required child operands have
// been supplied. It performs no reads, native calls or quote materialization.
inline PietyFinalArithmetic2C62CC0Observation12004
ProjectPietyFinalArithmetic2C62CC012004(
    std::int64_t entered_base_with223_raw,
    std::int64_t current_rite_term_raw,
    std::int64_t actor224_term_raw) noexcept {
  using namespace piety_final_arithmetic_detail;
  PietyFinalArithmetic2C62CC0Observation12004 out{};
  out.entered_base_with223_raw = entered_base_with223_raw;
  out.current_rite_term_raw = current_rite_term_raw;
  out.actor224_term_raw = actor224_term_raw;
  out.clamped_base_raw = entered_base_with223_raw < 0
      ? 0 : entered_base_with223_raw;
  const auto base = std::bit_cast<std::uint64_t>(out.clamped_base_raw);
  const auto factor = std::bit_cast<std::uint64_t>(current_rite_term_raw) +
      100000ULL + std::bit_cast<std::uint64_t>(actor224_term_raw);
  out.wrapped_factor_bits = factor;

  std::uint64_t result{};
  if (SmallOperand(base) && SmallOperand(factor)) {
    out.multiply_route = PietyFinalMultiplyRoute12004::small_product;
    result = NativeQuotientBits(base * factor);
  } else {
    out.multiply_route = PietyFinalMultiplyRoute12004::split_product;
    const auto signed_factor = std::bit_cast<std::int64_t>(factor);
    const bool factor_is_larger = signed_factor > out.clamped_base_raw;
    const auto larger = factor_is_larger ? factor : base;
    const auto smaller = factor_is_larger ? base : factor;
    const auto quotient = NativeQuotientBits(larger);
    const auto remainder = larger - quotient * 100000ULL;
    result = quotient * smaller + NativeQuotientBits(remainder * smaller);
  }
  out.pre_clamp_result_bits = result;
  const auto signed_result = std::bit_cast<std::int64_t>(result);
  out.final_piety_price_raw_q64 = signed_result < 0 ? 0 : signed_result;
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs

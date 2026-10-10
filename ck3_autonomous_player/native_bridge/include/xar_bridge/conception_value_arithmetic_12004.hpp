#pragma once
#include <bit>
#include <cstdint>

namespace xar::ck3_12004 {
namespace conception_value_detail {
inline constexpr std::int64_t WrapAdd(std::int64_t a, std::int64_t b) noexcept {
  return std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(a) +
                                     std::bit_cast<std::uint64_t>(b));
}
inline constexpr std::int64_t WrapSubtract(std::int64_t a, std::int64_t b) noexcept {
  return std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(a) -
                                     std::bit_cast<std::uint64_t>(b));
}
inline constexpr std::int64_t WrapMultiply(std::int64_t a, std::int64_t b) noexcept {
  return std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(a) *
                                     std::bit_cast<std::uint64_t>(b));
}
} // namespace conception_value_detail

// Actual second2B95517..93 and shared final2B95122..BE. The large-input
// branch deliberately keeps the stock low64 wrapping intermediate products.
inline constexpr std::int64_t MultiplyConceptionRaw12004(std::int64_t a,
                                              std::int64_t b) noexcept {
  using namespace conception_value_detail;
  constexpr std::uint64_t bound = 0xB504F333ULL;
  constexpr std::uint64_t twice_bound = 0x16A09E666ULL;
  const auto in_fast_range = [](std::int64_t value) noexcept {
    return std::bit_cast<std::uint64_t>(value) + bound <= twice_bound;
  };
  if (in_fast_range(a) && in_fast_range(b))
    return WrapMultiply(a, b) / 100000;
  const std::int64_t big = a < b ? b : a;
  const std::int64_t smaller_operand = a < b ? a : b;
  const auto quotient = big / 100000;
  const auto remainder = WrapSubtract(big, WrapMultiply(quotient, 100000));
  return WrapAdd(WrapMultiply(quotient, smaller_operand),
                 WrapMultiply(remainder, smaller_operand) / 100000);
}

// BF's signed half adjustment is performed in Q64, then the native age
// subtraction consumes its low DWORD. Negative results are preserved.
inline constexpr std::int32_t ConceptionAdjustedAgeRaw12004(
    std::int16_t selected_age, std::int64_t modifier_bf_raw) noexcept {
  using namespace conception_value_detail;
  const auto shifted = WrapAdd(modifier_bf_raw,
                              modifier_bf_raw < 0 ? -50000 : 50000);
  const auto adjustment = shifted / 100000;
  const auto low = static_cast<std::uint32_t>(
      std::bit_cast<std::uint64_t>(adjustment));
  const auto age = static_cast<std::uint32_t>(
      static_cast<std::int32_t>(selected_age));
  return std::bit_cast<std::int32_t>(age - low);
}
} // namespace xar::ck3_12004

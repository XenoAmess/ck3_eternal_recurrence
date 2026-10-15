#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kWarPaymentGenericSource12004 = 0x28A6D10;
inline constexpr std::uintptr_t kWarPaymentGenericReturn12004 = 0x28A6D7C;
inline constexpr std::size_t kWarPaymentGenericStackCapacity12004 = 32;
struct WarPaymentGenericValues12004 {
  std::optional<std::uintptr_t> context_identity_before, context_identity_after;
  std::optional<std::int64_t> value_2c0, value_2c8, value_28, value_30;
  bool capture_complete = false, context_stable = false;
  std::uint32_t failed_reads = 0;
};
struct WarPaymentGenericParentTrace12004 {
  std::uintptr_t module_base = 0;
  std::uint32_t module_image_size = 0, reported_frame_count = 0;
  bool capture_succeeded = false, truncated = false;
  std::uint32_t caller_match_count = 0;
  std::array<std::uintptr_t,kWarPaymentGenericStackCapacity12004> frames_absolute{};
  std::optional<std::uintptr_t> parent_return_absolute, parent_return_rva;
  bool parent_in_same_image = false;
};
struct WarPaymentGenericContext12004 {
  WarPaymentGenericValues12004 before, after;
  WarPaymentGenericParentTrace12004 parent_trace;
  std::optional<std::int64_t> before_computed_add_raw;
  std::optional<bool> before_formula_matches_amount;
  bool context_values_stable = false;
};
using WarPaymentStackFrames12004 = std::uint32_t (*)(void *,std::uintptr_t *,std::size_t) noexcept;
} // namespace xar::ck3_12004

#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace xar::ck3_11906 {

// Exact CK3 1.19.0.6 output header of resolve_counter_classes, as observed
// immediately after the original 0x23CAF20 call. This is a diagnostic copy,
// not a prediction of the next combat day.
inline constexpr std::size_t kCombatCounterOutputMaximumClassesV1 = 4096;

struct CombatCounterOutputReadoutV1 {
  std::int32_t class_count = 0;
  std::int32_t capacity = 0;
  std::array<std::int64_t, kCombatCounterOutputMaximumClassesV1> retention_raw{};
};

// Reads caller-owned output only. Does not call CK3, allocate, or modify the
// original header. A failed read clears the destination and returns false.
bool ReadCombatCounterOutputV1(
    const void *native_header, std::int32_t expected_class_count,
    CombatCounterOutputReadoutV1 &output) noexcept;

} // namespace xar::ck3_11906

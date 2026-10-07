#pragma once

#include <bit>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004 {

// Actual .4 selected source: month LEA22A0DEB ->444C340 (Root7B),
// day LEA22A0EF0 ->444C4B0 (selected152B). These bind readonly data.
inline constexpr std::uintptr_t kCDateCalendarDayTableRva12004 = 0x444C4B0;
inline constexpr std::uintptr_t kCDateCalendarMonthTableRva12004 = 0x444C340;

struct SourceDerivedCDateCalendar12004 {
  std::int64_t date_storage_raw64 = 0;
  std::uint8_t calendar_day_u8 = 0;
  std::uint8_t calendar_month_u8 = 0;
};

inline std::optional<SourceDerivedCDateCalendar12004>
ReadSourceDerivedNextCDateCalendar12004(
    std::int32_t next_date_raw_i32,
    std::int32_t next_native_day_index_raw_i32,
    const std::uint8_t *calendar_day_table,
    const std::uint8_t *calendar_month_table) noexcept {
  if (calendar_day_table == nullptr || calendar_month_table == nullptr) {
    return std::nullopt;
  }
  // Native signed division truncates toward zero. A negative remainder
  // changes only the physical table index; the stored year stays the quotient.
  const auto year = next_native_day_index_raw_i32 / 365;
  const auto remainder = next_native_day_index_raw_i32 - year * 365;
  const auto index = remainder < 0 ? remainder + 365 : remainder;
  const auto day = calendar_day_table[index];
  const auto month = calendar_month_table[index];
  const auto low_bits = std::bit_cast<std::uint32_t>(next_date_raw_i32);
  const auto year_bits = static_cast<std::uint16_t>(year);
  const auto packed = static_cast<std::uint64_t>(low_bits) |
                      (static_cast<std::uint64_t>(day) << 32U) |
                      (static_cast<std::uint64_t>(month) << 40U) |
                      (static_cast<std::uint64_t>(year_bits) << 48U);
  return SourceDerivedCDateCalendar12004{
      std::bit_cast<std::int64_t>(packed), day, month};
}

} // namespace xar::ck3_12004

#pragma once

#include "xar_bridge/army_future_daily_supply_schedule_v1.hpp"
#include "xar_bridge/army_source_derived_next_daily_supply_frame_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_cdate_calendar.hpp"

#include <bit>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12004 {

// Exact .4 selected source, Root155B/2 reads: receiver22A0D84 (3B),
// date/D22A0E6D..22A0F05 (152B), final [receiver+9C] store22A0EFE.
// Cached .pdata ordinal118687 selects the containing22A0D60 function.
// Receipt: actual4-selected-writer-root-first01/ROOT-SELECTED-WRITER-RECEIPT.json.
// These are provenance locators; this code never calls the native writer.
inline constexpr std::uintptr_t kNextDailyDateWriterReceiverRva12004 = 0x22A0D84;
inline constexpr std::uintptr_t kNextDailyDateWriterArithmeticRva12004 = 0x22A0E6D;
inline constexpr std::uintptr_t kNextDailyDateWriterDStoreRva12004 = 0x22A0EFE;

inline SourceDerivedNextDailySupplyFrameBindings12004
BindSourceDerivedNextDailySupplyFrame12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return {};
  }
  return {true,
          reinterpret_cast<const std::uint8_t *>(
              image_base + kCDateCalendarDayTableRva12004),
          reinterpret_cast<const std::uint8_t *>(
              image_base + kCDateCalendarMonthTableRva12004)};
}

// The closed low32 add and stored-D RHS derive the clock pair. Two readonly
// table bytes supply the calendar packing; current QWORD/currentD remain
// independent captured inputs and no native date writer is called.
inline game::ArmySourceDerivedNextDailySupplyFrameInputsV1
BuildSourceDerivedNextDailySupplyFrameInputs12004(
    const SourceDerivedNextDailySupplyFrameBindings12004 &binding,
    const game::ArmyFutureDailySupplyScheduleInputsV1 &current) {
  game::ArmySourceDerivedNextDailySupplyFrameInputsV1 result{};
  result.subject_army_id_u32 = current.subject_army_id_u32;
  result.subject_carmy_id_u32 = current.subject_carmy_id_u32;
  result.current_date_storage_raw64 = current.current_date_storage_raw64;
  result.current_date_raw_i32 = current.current_date_raw_i32;
  result.current_native_day_index_raw_i32 = current.native_day_index_raw_i32;
  if (!binding.enabled) {
    result.unavailable_reason = "native_source_derived_next_daily_supply_frame_bindings_unavailable";
    return result;
  }
  if (!result.subject_army_id_u32 || !result.subject_carmy_id_u32 ||
      !result.current_date_storage_raw64 || !result.current_date_raw_i32 ||
      !result.current_native_day_index_raw_i32) {
    result.unavailable_reason = "same_capture_next_daily_supply_frame_clock_seed_unavailable";
    return result;
  }
  const auto next_bits = static_cast<std::uint32_t>(*result.current_date_raw_i32) + 24U;
  result.source_derived_next_date_raw_i32 = std::bit_cast<std::int32_t>(next_bits);
  const auto quotient_operand = std::bit_cast<std::int32_t>(next_bits - 43800000U);
  // Signed imul2AAAAAAB/SAR2 plus sign correction is signed division by24
  // truncated toward zero, after the native DWORD wrapping.
  result.source_derived_next_native_day_index_raw_i32 = quotient_operand / 24;
  const auto calendar = ReadSourceDerivedNextCDateCalendar12004(
      *result.source_derived_next_date_raw_i32,
      *result.source_derived_next_native_day_index_raw_i32,
      binding.calendar_day_table, binding.calendar_month_table);
  if (calendar) {
    result.source_derived_next_date_storage_raw64 = calendar->date_storage_raw64;
    result.source_derived_next_calendar_day_u8 = calendar->calendar_day_u8;
    result.source_derived_next_calendar_month_u8 = calendar->calendar_month_u8;
    result.source_derived_full_cdate64_ready = true;
  }
  result.status = "available";
  result.ready = true;
  // All30 bucket readiness is independent of this clock pair's readiness.
  return result;
}

} // namespace xar::ck3_12004

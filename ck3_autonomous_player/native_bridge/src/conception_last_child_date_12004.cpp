#include "xar_bridge/conception_last_child_date_12004.hpp"

#include <array>
#include <bit>

namespace xar::ck3_12004::conception_last_child_date {
namespace {

std::int32_t WrapAdd(std::int32_t a, std::int32_t b) noexcept {
  return std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(a) +
                                     std::bit_cast<std::uint32_t>(b));
}
std::int32_t WrapSub(std::int32_t a, std::int32_t b) noexcept {
  return std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(a) -
                                     std::bit_cast<std::uint32_t>(b));
}
std::int32_t WrapMultiply(std::int32_t value, std::uint32_t factor) noexcept {
  return std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(value) * factor);
}

struct DecodedIndex {
  std::int32_t year;
  std::uint32_t index;
};
DecodedIndex Decode(std::int32_t raw) noexcept {
  const auto days = WrapSub(raw, 43800000) / 24;
  const auto year = days / 365;
  const auto remainder = days - year * 365;
  return {year, static_cast<std::uint32_t>(remainder < 0 ? remainder + 365
                                                         : remainder)};
}

template <typename T>
bool ReadAt(const Access &access, std::uintptr_t address, T &value) noexcept {
  return address != 0 && access.read_memory != nullptr &&
         access.read_memory(access.context, address, &value, sizeof(value));
}
bool ReadCalendarByte(const Access &access, std::uintptr_t table,
                      std::uint32_t index, std::uint8_t &value) noexcept {
  return index < 365 && ReadAt(access, access.image_base + table + index, value);
}

} // namespace

CurrentInputObservation ReadCurrentHouseholdSourceInputs(
    const Access &access, const void *first_character,
    std::int32_t first_character_id, std::uint32_t provider_mode_raw) noexcept {
  CurrentInputObservation result;
  auto &source = result.source;
  source.first_character_id = first_character_id;
  source.provider_mode_raw = provider_mode_raw;
  if (!access.exact_build_admitted ||
      access.executable_sha256 != kExecutableSha256 ||
      access.image_base == 0 || access.read_memory == nullptr) return result;
  const auto first = reinterpret_cast<std::uintptr_t>(first_character);
  std::uint32_t actual_first_id = 0;
  if (first == 0 || first_character_id == -1 ||
      !ReadAt(access, first + kCharacterFullIdOffset, actual_first_id) ||
      actual_first_id != std::bit_cast<std::uint32_t>(first_character_id)) {
    result.unavailable_reason = "last_child_first_character_identity_unavailable";
    return result;
  }
  if ((provider_mode_raw & 1U) == 0) {
    result.source_inputs_available = true;
    result.unavailable_reason = {};
    return result;
  }
  std::uintptr_t family = 0;
  if (!ReadAt(access, first + kCharacterFamilyOffset, family)) {
    result.unavailable_reason = "last_child_family_pointer_unavailable";
    return result;
  }
  source.first_family_present = family != 0;
  if (family == 0) {
    result.source_inputs_available = true;
    result.unavailable_reason = {};
    return result;
  }
  std::int32_t count = 0;
  if (!ReadAt(access, family + kFamilyChildCountOffset, count)) {
    result.unavailable_reason = "last_child_count_unavailable";
    return result;
  }
  source.child_count_raw = count;
  if (count == 0) {
    result.source_inputs_available = true;
    result.unavailable_reason = {};
    return result;
  }
  if (count < 0) {
    result.unavailable_reason = "last_child_negative_count_unavailable";
    return result;
  }
  std::uintptr_t ids = 0;
  std::uintptr_t store = 0;
  if (!ReadAt(access, family + kFamilyChildIdsOffset, ids) ||
      !ReadAt(access, access.image_base + kCharacterStorageSlotRva, store)) {
    result.unavailable_reason = "last_child_selection_inputs_unavailable";
    return result;
  }
  std::uintptr_t selected = 0;
  bool use_fallback = store == 0;
  if (!use_fallback) {
    std::uint32_t requested = 0;
    const auto final_offset = (static_cast<std::uintptr_t>(count) - 1U) * 4U;
    if (ids == 0 || !ReadAt(access, ids + final_offset, requested)) {
      result.unavailable_reason = "last_child_final_array_id_unavailable";
      return result;
    }
    source.last_requested_full_id_raw = requested;
    if (access.resolve_character == nullptr) {
      result.unavailable_reason = "last_child_resolver_unavailable";
      return result;
    }
    selected = reinterpret_cast<std::uintptr_t>(access.resolve_character(
        access.context, std::bit_cast<std::int32_t>(requested)));
    use_fallback = selected == 0;
    if (selected != 0) {
      std::uint32_t selected_id = 0;
      if (!ReadAt(access, selected + kCharacterFullIdOffset, selected_id)) {
        result.unavailable_reason = "last_child_resolved_identity_unavailable";
        return result;
      }
      use_fallback = selected_id != requested;
      if (!use_fallback) source.selected_full_id_raw = selected_id;
    }
  }
  source.selected_is_native_fallback = use_fallback;
  if (use_fallback) {
    std::uint32_t fallback_id = 0;
    if (!ReadAt(access, access.image_base + kCharacterFallbackSlotRva, selected) ||
        selected == 0 ||
        !ReadAt(access, selected + kCharacterFullIdOffset, fallback_id)) {
      result.unavailable_reason = "last_child_native_fallback_unavailable";
      return result;
    }
    source.selected_full_id_raw = fallback_id;
  }
  source.selected_character = selected;
  result.source_inputs_available = true;
  result.unavailable_reason = {};
  return result;
}

Observation Read(const Access &access,
                 const CurrentHouseholdSourceInputs &input) noexcept {
  Observation result;
  result.source = input;
  if (!access.exact_build_admitted ||
      access.executable_sha256 != kExecutableSha256 ||
      access.image_base == 0 || access.read_memory == nullptr) {
    return result;
  }
  // Actual provider copies R9B bit0 into SIL. Mode3 supplies this bit.
  if ((input.provider_mode_raw & 1U) == 0) {
    result.date_inputs_available = true;
    result.unavailable_reason = {};
    result.status = "mode_bit0_disabled";
    result.recent_child_branch_passed = true;
    return result;
  }
  if (!input.first_family_present.has_value()) {
    result.unavailable_reason = "last_child_family_pointer_unavailable";
    return result;
  }
  if (!*input.first_family_present) {
    result.date_inputs_available = true;
    result.unavailable_reason = {};
    result.status = "family_absent_bypass";
    result.recent_child_branch_passed = true;
    return result;
  }
  if (!input.child_count_raw.has_value()) {
    result.unavailable_reason = "last_child_count_unavailable";
    return result;
  }
  if (*input.child_count_raw == 0) {
    result.date_inputs_available = true;
    result.unavailable_reason = {};
    result.status = "children_empty_bypass";
    result.recent_child_branch_passed = true;
    return result;
  }
  // Native tests only equality0, then uses MOVSXD count. A negative source
  // count is not an empty list and cannot be admitted by this bounded reader.
  if (*input.child_count_raw < 0) {
    result.unavailable_reason = "last_child_negative_count_unavailable";
    return result;
  }
  result.date_helper_demanded = true;
  if (input.selected_character == 0 ||
      !input.selected_is_native_fallback.has_value()) {
    result.unavailable_reason = "last_child_selected_character_unavailable";
    return result;
  }
  std::int64_t selected_storage = 0;
  if (!ReadAt(access, input.selected_character + kSelectedCharacterDateOffset,
              selected_storage)) {
    result.unavailable_reason = "last_child_selected_date_unavailable";
    return result;
  }
  result.selected_date_storage_raw64 = selected_storage;
  std::int32_t shift = 0;
  if (!ReadAt(access, access.image_base + kLoadedMonthShiftSlotRva, shift)) {
    result.unavailable_reason = "last_child_loaded_month_shift_unavailable";
    return result;
  }
  result.loaded_month_shift_raw_i32 = shift;
  std::uintptr_t clock = 0;
  std::int32_t current = 0;
  if (!ReadAt(access, access.image_base + kGameStateSlotRva, clock) || clock == 0 ||
      !ReadAt(access, clock + kGameStateDateOffset, current)) {
    result.unavailable_reason = "last_child_current_date_unavailable";
    return result;
  }
  result.current_date_raw_i32 = current;
  const auto selected_bits = std::bit_cast<std::uint64_t>(selected_storage);
  const auto raw = std::bit_cast<std::int32_t>(
      static_cast<std::uint32_t>(selected_bits));
  const auto initial = Decode(raw);
  std::uint8_t initial_month = 0;
  if (!ReadCalendarByte(access, kMonthTableRva, initial.index, initial_month)) {
    result.unavailable_reason = "last_child_initial_month_unavailable";
    return result;
  }
  const auto month_sum = WrapAdd(shift, static_cast<std::int32_t>(initial_month));
  const auto year_delta = month_sum / 12;
  auto target_month = month_sum - year_delta * 12;
  auto intermediate_raw = WrapAdd(raw, WrapMultiply(year_delta, 8760));
  if (target_month < 0) {
    intermediate_raw = WrapSub(intermediate_raw, 8760);
    target_month += 12;
  }
  const auto intermediate = Decode(intermediate_raw);
  std::uint8_t intermediate_day = 0;
  if (!ReadCalendarByte(access, kDayTableRva, intermediate.index,
                        intermediate_day)) {
    result.unavailable_reason = "last_child_intermediate_day_unavailable";
    return result;
  }
  std::array<std::uint8_t, 12> month_lengths{};
  const auto prefix_bytes = static_cast<std::size_t>(target_month) + 1;
  // Actual FF65DA and FF64C8 share4513BD0. Read only target length and
  // demanded preceding prefix; target_month is native-normalized0..11.
  if (prefix_bytes > month_lengths.size() ||
      !access.read_memory(access.context,
                          access.image_base + kMonthLengthTableRva,
                          month_lengths.data(), prefix_bytes)) {
    result.unavailable_reason = "last_child_month_lengths_unavailable";
    return result;
  }
  const auto last_day = static_cast<std::int32_t>(
      std::bit_cast<std::int8_t>(month_lengths[static_cast<std::size_t>(target_month)])) - 1;
  const auto source_day = static_cast<std::int32_t>(intermediate_day);
  auto target_index = source_day < last_day ? source_day : last_day;
  for (std::int32_t month = 0; month < target_month; ++month) {
    target_index = WrapAdd(target_index, static_cast<std::int32_t>(
        std::bit_cast<std::int8_t>(month_lengths[static_cast<std::size_t>(month)])));
  }
  const auto delta = WrapSub(target_index,
                             static_cast<std::int32_t>(intermediate.index));
  const auto adjusted_raw = WrapAdd(intermediate_raw, WrapMultiply(delta, 24));
  const auto adjusted = Decode(adjusted_raw);
  std::uint8_t adjusted_month = 0;
  std::uint8_t adjusted_day = 0;
  if (!ReadCalendarByte(access, kMonthTableRva, adjusted.index, adjusted_month) ||
      !ReadCalendarByte(access, kDayTableRva, adjusted.index, adjusted_day)) {
    result.unavailable_reason = "last_child_adjusted_calendar_unavailable";
    return result;
  }
  const auto packed = static_cast<std::uint64_t>(
                          std::bit_cast<std::uint32_t>(adjusted_raw)) |
                      (static_cast<std::uint64_t>(adjusted_day) << 32U) |
                      (static_cast<std::uint64_t>(adjusted_month) << 40U) |
                      (static_cast<std::uint64_t>(
                           static_cast<std::uint16_t>(adjusted.year)) << 48U);
  result.adjusted_date_raw_i32 = adjusted_raw;
  result.adjusted_date_storage_raw64 = std::bit_cast<std::int64_t>(packed);
  result.recent_child_branch_passed = current > adjusted_raw;
  result.date_inputs_available = true;
  result.unavailable_reason = {};
  result.status = "conditional_date_comparison_available";
  return result;
}

} // namespace xar::ck3_12004::conception_last_child_date

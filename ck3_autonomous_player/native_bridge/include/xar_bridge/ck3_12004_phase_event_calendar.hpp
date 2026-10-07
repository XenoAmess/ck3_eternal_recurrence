#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/phase_event_calendar_observation_v1.hpp"
#include <bit>
#include <cstddef>
#include <cstring>
#include <string_view>
#include <utility>

namespace xar::ck3_12004 {
inline constexpr std::string_view kPhaseCalendarExecutableSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
// Root's actual4-cadence-first01 two finite DETAILs close these operands.
inline constexpr std::uintptr_t kPhaseCalendarIntervalSlotRva = 0x5C69B4C;
inline constexpr std::uintptr_t kPhaseCalendarDatePointerSlotRva = 0x5C68C50;
using PhaseCalendarReadBytesV1 = bool (*)(
    std::uintptr_t, void *, std::size_t, void *) noexcept;

inline bool ReadLocalPhaseCalendarBytes12004(
    std::uintptr_t address, void *output, std::size_t size, void *) noexcept {
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  } __except (1) { return false; }
#else
  // Non-game fixtures inject a bounded fake-memory reader instead.
  (void)address; (void)output; (void)size;
  return false;
#endif
}

struct PhaseEventCalendarBindings12004 {
  bool enabled = false;
  std::uintptr_t interval_slot = 0;
  std::uintptr_t date_pointer_slot = 0;
  PhaseCalendarReadBytesV1 read_bytes = nullptr;
  void *read_context = nullptr;
};

inline PhaseEventCalendarBindings12004 BindPhaseEventCalendarImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    PhaseCalendarReadBytesV1 reader = ReadLocalPhaseCalendarBytes12004,
    void *context = nullptr) noexcept {
  if (!image_base || executable_sha256 != kPhaseCalendarExecutableSha256)
    return {};
  return {true, image_base + kPhaseCalendarIntervalSlotRva,
          image_base + kPhaseCalendarDatePointerSlotRva, reader, context};
}

inline std::int32_t PhaseCalendarDayIndex12004(std::uint32_t date) noexcept {
  // Native SUB32, signed magic IMUL/SAR/sign correction: truncation toward 0.
  const auto delta = std::bit_cast<std::int32_t>(date - std::uint32_t{0x029C55A8});
  return delta / 24;
}

inline game::PhaseEventCalendarObservationV1 ReadPhaseEventCalendarInputs12004(
    const PhaseEventCalendarBindings12004 &bindings,
    const game::CombatSimulationInputsSnapshot &inputs) {
  game::PhaseEventCalendarObservationV1 output;
  output.loaded_interval_source_closed = bindings.enabled;
  output.calendar_predicate_source_closed = bindings.enabled;
  const auto add = [&](const game::CombatArmyInputsSnapshot &army,
                       std::int32_t character, std::optional<std::int32_t> regiment,
                       std::string_view role) {
    game::PhaseEventCalendarOccurrenceV1 row;
    row.occurrence_index = static_cast<std::uint32_t>(output.occurrences.size());
    row.character_id = static_cast<std::uint32_t>(character);
    row.source_public_cunit_id = army.army_id;
    if (army.native_carmy_id_observable)
      row.source_native_carmy_id = army.native_carmy_id;
    row.source_regiment_id = regiment;
    row.encounter_role = army.encounter_role;
    row.phase_role = role;
    output.occurrences.push_back(std::move(row));
  };
  // Preserve software V2 role occurrences, including duplicate CharacterIDs.
  // These are not the native selector's admitted candidates or execution order.
  for (const auto &army : inputs.armies) {
    if (army.commander.status == game::CombatObservationStatus::available &&
        army.commander.character_id != -1)
      add(army, army.commander.character_id, std::nullopt, "commander");
    for (const auto &knight : army.knights.members)
      if (knight.character_id != -1)
        add(army, knight.character_id, knight.source_regiment_id, "knight");
  }
  if (!bindings.enabled || !bindings.read_bytes) {
    output.unavailable_reason = "actual4_calendar_binding_unavailable";
    return output;
  }
  std::uint32_t interval = 0;
  if (bindings.read_bytes(bindings.interval_slot, &interval, sizeof(interval),
                          bindings.read_context))
    output.loaded_interval_days_raw = interval; // Real zero remains observed.
  std::uintptr_t date_object = 0;
  std::uint32_t date = 0;
  if (bindings.read_bytes(bindings.date_pointer_slot, &date_object,
                          sizeof(date_object), bindings.read_context) &&
      date_object && bindings.read_bytes(date_object + 8, &date, sizeof(date),
                                         bindings.read_context)) {
    output.date_low32 = date;
    output.next_date_low32 = date + std::uint32_t{24};
    output.day_index = PhaseCalendarDayIndex12004(date);
    // Recompute, rather than adding one, at SUB32/sign/wrap boundaries.
    output.next_day_index = PhaseCalendarDayIndex12004(*output.next_date_low32);
  }
  if (!output.loaded_interval_days_raw || !output.date_low32) {
    output.status = (output.loaded_interval_days_raw || output.date_low32)
        ? "partial" : "unavailable";
    output.unavailable_reason = "actual4_calendar_operand_read_unavailable";
    return output;
  }
  if (*output.loaded_interval_days_raw == 0) {
    output.status = "partial";
    output.unavailable_reason = "observed_interval_zero_calendar_division_undefined";
    return output;
  }
  for (auto &row : output.occurrences) {
    const auto current = (row.character_id + static_cast<std::uint32_t>(*output.day_index))
        % *output.loaded_interval_days_raw;
    const auto next = (row.character_id + static_cast<std::uint32_t>(*output.next_day_index))
        % *output.loaded_interval_days_raw;
    row.current_remainder_raw = current;
    row.next_remainder_raw = next;
    row.current_calendar_predicate = current == 0;
    row.next_day_calendar_predicate = next == 0;
  }
  output.status = "available";
  output.unavailable_reason.clear();
  return output;
}

// Called by the Root-integrated available V2 adapter branch and the whole
// fixture. It only attaches an optional leaf; base result/readiness is intact.
inline void AttachPhaseEventCalendarInputs12004(
    const PhaseEventCalendarBindings12004 &bindings,
    game::CombatSimulationInputsSnapshot &inputs) noexcept {
  if (!bindings.enabled) return;
  try {
    inputs.phase_event_calendar_observation_v1 =
        ReadPhaseEventCalendarInputs12004(bindings, inputs);
  } catch (...) {
    // Respect the surrounding adapter's noexcept contract for allocation failure.
    inputs.phase_event_calendar_observation_v1.reset();
  }
}
} // namespace xar::ck3_12004

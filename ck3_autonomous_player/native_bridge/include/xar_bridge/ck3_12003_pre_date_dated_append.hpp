#pragma once
#include "xar_bridge/ck3_12003_daily_assault_roster_admission.hpp"
#include <bit>

namespace xar::ck3_12003 {
struct PreDateDatedAppendBindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  const void *combat_registry_slot = nullptr, *combat_fallback_slot = nullptr;
};
inline PreDateDatedAppendBindings12003 BindPreDateDatedAppend12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  PreDateDatedAppendBindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (!out.common.enabled) return out;
  out.combat_registry_slot = reinterpret_cast<const void *>(base + 0x5D1DE70);
  out.combat_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DE18);
  return out;
}
inline std::int32_t PreDateTomorrowLow12003(std::int32_t current) noexcept {
  return std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(current) + 24U);
}
namespace pre_date_dated_append_detail {
using daily_assault_roster_detail::Read;
using daily_assault_roster_detail::Resolve;
using daily_assault_roster_detail::Finish;
using daily_assault_roster_detail::Identity;
using Common = CurrentDailyAssaultRosterAdmissionBindings12003;

inline game::ArmyPreDateDatedIdListV1 IdList(const Common &b, const void *manager,
    std::size_t offset, std::string_view reuse_offset,
    const game::ArmyFirstRemovalCleanupInputsV1 *existing, bool nonpositive_empty) {
  game::ArmyPreDateDatedIdListV1 out{};
  out.count_raw_i32 = Read<std::int32_t>(b, manager, offset + 0xC);
  const game::ArmyManagerCleanupIdListV1 *reused = nullptr;
  if (existing) for (const auto &list : existing->id_lists)
    if (list.manager_offset == reuse_offset) { reused = &list; break; }
  out.source = reused ? "same_query_first_removal_id_list" : "native_manager_id_list";
  if (reused) {
    if (reused->ordered_army_ids) {
      out.ordered_ids_u32.emplace();
      for (const auto id : *reused->ordered_army_ids)
        out.ordered_ids_u32->push_back(std::bit_cast<std::uint32_t>(id));
    }
  } else if (out.count_raw_i32 && *out.count_raw_i32 <= 0) {
    out.ordered_ids_u32.emplace();
  } else if (out.count_raw_i32) {
    const auto data = Read<const void *>(b, manager, offset);
    if (data && *data) {
      out.ordered_ids_u32.emplace();
      for (std::int32_t i = 0; i < *out.count_raw_i32; ++i)
        out.ordered_ids_u32->push_back(Read<std::uint32_t>(b, *data, static_cast<std::size_t>(i) * 4));
    }
  }
  // The source callee returns on signed D4<=0; the initial destination needs
  // an independently complete nonnegative logical count.
  if (nonpositive_empty && out.count_raw_i32 && *out.count_raw_i32 <= 0)
    out.ordered_ids_u32.emplace();
  out.ready = out.count_raw_i32 && out.ordered_ids_u32 &&
      (nonpositive_empty || *out.count_raw_i32 >= 0) &&
      out.ordered_ids_u32->size() == static_cast<std::size_t>(std::max(*out.count_raw_i32, 0)) &&
      std::all_of(out.ordered_ids_u32->begin(), out.ordered_ids_u32->end(), [](const auto &id) { return id.has_value(); });
  out.unavailable_reason = out.ready ? "" : "dated_append_manager_id_list_incomplete";
  return out;
}
inline game::ArmyPreDateDatedOccurrenceV1 Occurrence(const PreDateDatedAppendBindings12003 &b,
    std::int32_t index, std::optional<std::uint32_t> requested, std::optional<std::int32_t> tomorrow) {
  game::ArmyPreDateDatedOccurrenceV1 out{};
  out.native_index = index; out.original_request_full_id_u32 = requested;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  if (!requested) return fail("dated_append_original_request_unavailable");
  const auto army = Resolve(b.common, b.common.army_registry_slot, b.common.army_fallback_slot, requested, 0x10);
  out.army_resolution = army.observation;
  if (!out.army_resolution.selected_object_ready) return fail("dated_append_selected_army_unavailable");
  out.combat_request_full_id_u32 = Read<std::uint32_t>(b.common, army.object, 0x128);
  if (!out.combat_request_full_id_u32) return fail("dated_append_combat_request_unavailable");
  const auto combat = Resolve(b.common, b.combat_registry_slot, b.combat_fallback_slot,
      out.combat_request_full_id_u32, 0x08);
  out.combat_resolution = combat.observation;
  if (!out.combat_resolution.selected_object_ready) return fail("dated_append_selected_combat_unavailable");
  out.combat_magic_0c_raw_u32 = Read<std::uint32_t>(b.common, combat.object, 0x0C);
  if (!out.combat_magic_0c_raw_u32) return fail("dated_append_combat_magic_unavailable");
  if (*out.combat_magic_0c_raw_u32 == 0x436F6D62U) {
    if (!out.combat_resolution.selected_full_id_u32) return fail("dated_append_combat_full_id_unavailable");
    if (*out.combat_resolution.selected_full_id_u32 != 0xFFFFFFFFU) { Finish(out, true); return out; }
  }
  out.army_date_count_5c_raw_i32 = Read<std::int32_t>(b.common, army.object, 0x5C);
  if (!out.army_date_count_5c_raw_i32) return fail("dated_append_army_date_count_unavailable");
  if (*out.army_date_count_5c_raw_i32 <= 0) { Finish(out, true); return out; }
  if (!tomorrow) return fail("dated_append_tomorrow_operand_unavailable");
  const auto data = Read<const void *>(b.common, army.object, 0x50);
  if (data) { out.date_array_identity = Identity(*data); out.date_array_present = *data != nullptr; }
  if (!data || !*data) return fail("dated_append_date_array_unavailable");
  for (std::int32_t i = 0; i < *out.army_date_count_5c_raw_i32; ++i) {
    game::ArmyPreDateDatedEntryV1 entry{}; entry.native_index = i;
    const auto pointer = Read<const void *>(b.common, *data, static_cast<std::size_t>(i) * 8);
    if (pointer) { entry.pointer_identity = Identity(*pointer); entry.pointer_present = *pointer != nullptr; }
    if (pointer && *pointer) entry.date_low_raw_i32 = Read<std::int32_t>(b.common, *pointer);
    out.date_entries.push_back(entry);
    if (!entry.date_low_raw_i32) return fail("dated_append_required_date_entry_unavailable");
    if (*entry.date_low_raw_i32 <= *tomorrow) {
      out.date_scan_ready = true; Finish(out, true); return out;
    }
  }
  out.date_scan_ready = true; Finish(out, true); return out;
}
} // namespace pre_date_dated_append_detail

// One global same-query observation; callers attach the same value to scoped
// Strength rows. Reuse the already captured globals and exact native raw clock.
inline game::ArmyPreDateDatedAppendInputsV1 ReadPreDateDatedAppend12003(
    const PreDateDatedAppendBindings12003 &b,
    const game::ArmyFirstRemovalCleanupInputsV1 *existing_globals = nullptr,
    const game::ArmySupplyTimingSnapshot *existing_clock = nullptr) {
  using namespace pre_date_dated_append_detail;
  game::ArmyPreDateDatedAppendInputsV1 out{};
  if (!b.common.enabled) { out.unavailable_reason = "dated_append_exact_build_bindings_unavailable"; return out; }
  const auto state = Read<const void *>(b.common, b.common.game_state_slot);
  if (existing_clock && existing_clock->current_date_raw) {
    out.current_date_raw_i32 = existing_clock->current_date_raw;
    out.clock_source = "same_query_army_update_clock_v1";
  } else if (state && *state) {
    out.current_date_raw_i32 = Read<std::int32_t>(b.common, *state, 0x08);
    if (out.current_date_raw_i32) out.clock_source = "same_query_game_state_08";
  }
  if (out.current_date_raw_i32) {
    out.tomorrow_date_low_i32 = PreDateTomorrowLow12003(*out.current_date_raw_i32);
    out.clock_ready = true;
  }
  const auto data = state && *state ? Read<const void *>(b.common, *state, 0xA0) : std::nullopt;
  if (!data || !*data) { out.unavailable_reason = "dated_append_manager_unavailable"; return out; }
  const auto manager = daily_assault_roster_detail::At(*data, 0x2A540);
  out.manager_loaded = true; out.manager_identity = Identity(manager);
  out.source_c8 = IdList(b.common, manager, 0xC8, "c8", existing_globals, true);
  out.initial_158 = IdList(b.common, manager, 0x158, "158", existing_globals, false);
  if (out.source_c8.count_raw_i32 && *out.source_c8.count_raw_i32 > 0) {
    for (std::int32_t i = 0; i < *out.source_c8.count_raw_i32; ++i) {
      const auto requested = out.source_c8.ordered_ids_u32 &&
          static_cast<std::size_t>(i) < out.source_c8.ordered_ids_u32->size()
          ? out.source_c8.ordered_ids_u32->at(static_cast<std::size_t>(i)) : std::nullopt;
      out.occurrences.push_back(Occurrence(b, i, requested, out.tomorrow_date_low_i32));
    }
  }
  const bool complete = out.source_c8.ready &&
      std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &row) { return row.ready; });
  if (!complete) out.unavailable_reason = "dated_append_request_operands_incomplete";
  Finish(out, complete); return out;
}
} // namespace xar::ck3_12003

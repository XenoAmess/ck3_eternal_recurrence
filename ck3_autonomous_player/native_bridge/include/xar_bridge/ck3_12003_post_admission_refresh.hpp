#pragma once

#include "xar_bridge/ck3_12003_pre_date_pending_update.hpp"

#include <algorithm>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace xar::ck3_12003 {
struct CurrentPostAdmissionRefreshBindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  const void *arrg_registry_slot = nullptr, *arrg_fallback_slot = nullptr;
};
inline CurrentPostAdmissionRefreshBindings12003 BindCurrentPostAdmissionRefresh12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentPostAdmissionRefreshBindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (!out.common.enabled) return out;
  out.arrg_registry_slot = reinterpret_cast<const void *>(base + 0x5D1F340);
  out.arrg_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1F338);
  return out;
}
namespace post_admission_refresh_detail {
using namespace daily_assault_roster_detail;
template <typename T> inline void FinishInputs(T &out, bool complete) {
  out.ready = complete; out.status = complete ? "available" : "partial";
  if (complete) out.unavailable_reason.clear();
  else if (out.unavailable_reason.empty() || out.unavailable_reason == "not_demanded")
    out.unavailable_reason = "post_admission_refresh_source_operands_incomplete";
}
inline bool Covered(const game::ArmyDailyAssaultRawReferencesV1 &refs, std::size_t size) {
  return refs.references_ready && refs.count_raw_i32 && *refs.count_raw_i32 >= 0 &&
      size == static_cast<std::size_t>(*refs.count_raw_i32);
}
struct ResolutionCacheRow {
  std::uint32_t requested = 0;
  Resolved resolved{};
};
inline Resolved Selected(const CurrentPostAdmissionRefreshBindings12003 &b,
    const std::optional<std::uint32_t> &requested, bool army,
    std::vector<ResolutionCacheRow> &cache) {
  if (requested) {
    const auto found = std::find_if(cache.begin(), cache.end(),
        [&](const auto &row) { return row.requested == *requested; });
    if (found != cache.end()) return found->resolved;
  }
  auto result = Resolve(b.common, army ? b.common.army_registry_slot : b.arrg_registry_slot,
      army ? b.common.army_fallback_slot : b.arrg_fallback_slot, requested, 0x10);
  if (requested) cache.push_back({*requested, result});
  return result;
}
inline bool SameSelected(const game::ArmyDailyAssaultOperandResolutionV1 &resolution,
    const Resolved &actual, const std::optional<std::uint32_t> &requested) {
  return resolution.selected_object_ready && actual.observation.selected_object_ready &&
      resolution.requested_full_id_u32 == requested &&
      resolution.object_identity == actual.observation.object_identity;
}
inline const game::ArmyDailyAssaultArRgOccurrenceV1 *TableArRg(
    const game::ArmyCurrentDailyAssaultTableV1 *table, const Resolved &actual,
    const std::optional<std::uint32_t> &requested) {
  if (!table || !actual.observation.selected_object_ready) return nullptr;
  for (const auto &group : table->groups)
    for (const auto &row : group.arrgs.occurrences)
      if (row.raw_full_id_u32 == requested && row.resolution.object_identity == actual.observation.object_identity)
        return &row;
  return nullptr;
}
inline const game::ArmyPreDatePendingArRgV1 *PendingArRg(
    const game::ArmyPreDatePendingOccurrenceV1 *pending, const Resolved &actual,
    const std::optional<std::uint32_t> &requested) {
  if (!pending) return nullptr;
  for (const auto &row : pending->arrg_occurrences)
    if (row.raw_full_id_u32 == requested && SameSelected(row.arrg_resolution, actual, requested)) return &row;
  return nullptr;
}
inline game::ArmyPostAdmissionRefreshArRgV1 ArRg(const CurrentPostAdmissionRefreshBindings12003 &b,
    const game::ArmyDailyAssaultRawReferenceOccurrenceV1 &raw,
    const game::ArmyPreDatePendingOccurrenceV1 *pending,
    const game::ArmyCurrentDailyAssaultTableV1 *table,
    std::vector<ResolutionCacheRow> &cache) {
  game::ArmyPostAdmissionRefreshArRgV1 out{};
  out.native_index = raw.native_index; out.raw_full_id_u32 = raw.raw_full_id_u32;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; FinishInputs(out, false); return out; };
  const auto actual = Selected(b, raw.raw_full_id_u32, false, cache);
  out.arrg_resolution = actual.observation;
  if (!actual.observation.selected_object_ready) return fail("post_admission_refresh_arrg_selection_unavailable");
  const auto *table_row = TableArRg(table, actual, raw.raw_full_id_u32);
  out.magic_14_raw_u32 = table_row && table_row->magic_raw_u32
      ? table_row->magic_raw_u32 : Read<std::uint32_t>(b.common, actual.object, 0x14);
  if (!out.magic_14_raw_u32) return fail("post_admission_refresh_arrg_magic_unavailable");
  // A wrong magic rejects the actual selected object without demanding its full ID.
  if (*out.magic_14_raw_u32 != 0x41725267U) {
    out.identity_valid = false; out.numeric_24_inputs_ready = true; out.numeric_28_inputs_ready = true;
    FinishInputs(out, true); return out;
  }
  if (!out.arrg_resolution.selected_full_id_u32) return fail("post_admission_refresh_arrg_full_id_unavailable");
  out.identity_valid = *out.arrg_resolution.selected_full_id_u32 != 0xFFFFFFFFU;
  if (!*out.identity_valid) {
    out.numeric_24_inputs_ready = true; out.numeric_28_inputs_ready = true;
    FinishInputs(out, true); return out;
  }
  const auto *pending_row = PendingArRg(pending, actual, raw.raw_full_id_u32);
  if (pending_row && pending_row->current_38_raw_i32) out.current_38_raw_i32 = pending_row->current_38_raw_i32;
  else if (table_row && table_row->current_raw_i32) out.current_38_raw_i32 = table_row->current_raw_i32;
  else out.current_38_raw_i32 = Read<std::int32_t>(b.common, actual.object, 0x38);
  // Both source passes admit the same identities. The QWORD is unconditional for every admitted row.
  out.value_40_raw_i64 = Read<std::int64_t>(b.common, actual.object, 0x40);
  out.numeric_24_inputs_ready = out.current_38_raw_i32.has_value();
  out.numeric_28_inputs_ready = out.value_40_raw_i64.has_value();
  if (!out.numeric_24_inputs_ready && !out.numeric_28_inputs_ready)
    out.unavailable_reason = "post_admission_refresh_arrg_numbers_unavailable";
  else if (!out.numeric_24_inputs_ready) out.unavailable_reason = "post_admission_refresh_arrg_38_unavailable";
  else if (!out.numeric_28_inputs_ready) out.unavailable_reason = "post_admission_refresh_arrg_40_unavailable";
  FinishInputs(out, out.numeric_24_inputs_ready && out.numeric_28_inputs_ready); return out;
}
inline game::ArmyPostAdmissionRefreshOccurrenceV1 Occurrence(
    const CurrentPostAdmissionRefreshBindings12003 &b,
    const game::ArmyDailyAssaultRawReferenceOccurrenceV1 &raw,
    const game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 *roster,
    const game::ArmyPreDatePendingOccurrenceV1 *pending,
    const game::ArmyCurrentDailyAssaultTableV1 *table,
    std::vector<ResolutionCacheRow> &army_cache, std::vector<ResolutionCacheRow> &arrg_cache) {
  game::ArmyPostAdmissionRefreshOccurrenceV1 out{};
  out.native_index = raw.native_index; out.raw_full_id_u32 = raw.raw_full_id_u32;
  const auto actual = Selected(b, raw.raw_full_id_u32, true, army_cache);
  out.original_army_resolution = actual.observation;
  if (!actual.observation.selected_object_ready) {
    out.unavailable_reason = "post_admission_refresh_army_selection_unavailable"; FinishInputs(out, false); return out;
  }
  // These are observed caches, never asserted to be this callback's outputs.
  out.actual_army_24_raw_i32 = Read<std::int32_t>(b.common, actual.object, 0x24);
  out.actual_army_28_raw_i64 = Read<std::int64_t>(b.common, actual.object, 0x28);
  out.actual_army_20_raw_u8 = Read<std::uint8_t>(b.common, actual.object, 0x20);
  out.actual_army_21_raw_u8 = Read<std::uint8_t>(b.common, actual.object, 0x21);
  out.actual_army_30_raw_u8 = Read<std::uint8_t>(b.common, actual.object, 0x30);
  out.actual_army_31_raw_u8 = Read<std::uint8_t>(b.common, actual.object, 0x31);
  if (roster && SameSelected(roster->original_army_resolution, actual, raw.raw_full_id_u32) &&
      roster->original_arrg_references.references_ready)
    out.original_arrg_references = roster->original_arrg_references;
  else if (pending && SameSelected(pending->original_army_resolution, actual, raw.raw_full_id_u32) &&
      pending->original_arrg_references.references_ready)
    out.original_arrg_references = pending->original_arrg_references;
  else out.original_arrg_references = References(b.common, At(actual.object, 0x38));
  const auto *same_pending = pending && SameSelected(pending->original_army_resolution, actual, raw.raw_full_id_u32)
      ? pending : nullptr;
  for (const auto &reference : out.original_arrg_references.occurrences)
    out.arrg_occurrences.push_back(ArRg(b, reference, same_pending, table, arrg_cache));
  const bool covered = Covered(out.original_arrg_references, out.arrg_occurrences.size());
  out.arrg_rows_ready = covered && std::all_of(out.arrg_occurrences.begin(), out.arrg_occurrences.end(),
      [](const auto &row) { return row.identity_valid.has_value(); });
  out.numeric_24_inputs_ready = covered && std::all_of(out.arrg_occurrences.begin(), out.arrg_occurrences.end(),
      [](const auto &row) { return row.numeric_24_inputs_ready; });
  out.numeric_28_inputs_ready = covered && std::all_of(out.arrg_occurrences.begin(), out.arrg_occurrences.end(),
      [](const auto &row) { return row.numeric_28_inputs_ready; });
  if (!out.numeric_24_inputs_ready || !out.numeric_28_inputs_ready)
    out.unavailable_reason = "post_admission_refresh_arrg_operands_incomplete";
  FinishInputs(out, out.numeric_24_inputs_ready && out.numeric_28_inputs_ready); return out;
}
} // namespace post_admission_refresh_detail
inline game::ArmyCurrentPostAdmissionRefreshInputsV1 ReadCurrentPostAdmissionRefreshInputs12003(
    const CurrentPostAdmissionRefreshBindings12003 &bindings,
    const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &same_query_roster,
    const game::ArmyCurrentPreDatePendingUpdateInputsV1 *same_query_pending = nullptr,
    const game::ArmyCurrentDailyAssaultTableV1 *same_query_table = nullptr) noexcept {
  using namespace post_admission_refresh_detail;
  game::ArmyCurrentPostAdmissionRefreshInputsV1 out{};
  if (!bindings.common.enabled) { out.unavailable_reason = "post_admission_refresh_unbound"; return out; }
  // The primary roster is copied from the existing same-query capture, never resampled here.
  out.manager_loaded = same_query_roster.manager_loaded; out.manager_identity = same_query_roster.manager_identity;
  out.original_roster = same_query_roster.original_roster;
  out.raw_roster_references_ready = out.original_roster.references_ready;
  std::vector<ResolutionCacheRow> army_cache, arrg_cache;
  for (const auto &raw : out.original_roster.occurrences) {
    const auto roster_found = std::find_if(same_query_roster.occurrences.begin(), same_query_roster.occurrences.end(),
        [&](const auto &row) { return row.native_index == raw.native_index && row.raw_full_id_u32 == raw.raw_full_id_u32; });
    const auto *roster = roster_found == same_query_roster.occurrences.end() ? nullptr : &*roster_found;
    const game::ArmyPreDatePendingOccurrenceV1 *pending = nullptr;
    if (same_query_pending) {
      const auto found = std::find_if(same_query_pending->occurrences.begin(), same_query_pending->occurrences.end(),
          [&](const auto &row) { return row.native_index == raw.native_index && row.raw_full_id_u32 == raw.raw_full_id_u32; });
      if (found != same_query_pending->occurrences.end()) pending = &*found;
    }
    out.occurrences.push_back(Occurrence(bindings, raw, roster, pending, same_query_table, army_cache, arrg_cache));
  }
  const bool covered = Covered(out.original_roster, out.occurrences.size());
  out.original_army_selections_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
      [](const auto &row) { return row.original_army_resolution.selected_object_ready; });
  out.numeric_24_inputs_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
      [](const auto &row) { return row.numeric_24_inputs_ready; });
  out.numeric_28_inputs_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
      [](const auto &row) { return row.numeric_28_inputs_ready; });
  out.source_operands_ready = out.original_army_selections_ready && out.numeric_24_inputs_ready && out.numeric_28_inputs_ready;
  if (!out.source_operands_ready) out.unavailable_reason = "post_admission_refresh_source_operands_incomplete";
  FinishInputs(out, out.source_operands_ready); return out;
}
} // namespace xar::ck3_12003

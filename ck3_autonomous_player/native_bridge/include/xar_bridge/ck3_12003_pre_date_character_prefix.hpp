#pragma once
#include "xar_bridge/ck3_12003_pre_date_dated_append.hpp"
#include <unordered_map>

namespace xar::ck3_12003 {
struct CurrentPreDateCharacterPrefixBindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  bool (*membership)(void *, std::int32_t, bool) = nullptr;
  bool (*basic_rule)(bool, std::int32_t, std::int32_t, void *) = nullptr;
  bool (*availability)(void *, std::int32_t, bool, void *) = nullptr;
};
inline CurrentPreDateCharacterPrefixBindings12003 BindCurrentPreDateCharacterPrefix12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentPreDateCharacterPrefixBindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (!out.common.enabled) return out;
  out.membership = reinterpret_cast<decltype(out.membership)>(base + 0x2C12170);
  out.basic_rule = reinterpret_cast<decltype(out.basic_rule)>(base + 0x1D63180);
  out.availability = reinterpret_cast<decltype(out.availability)>(base + 0x2C129A0);
  return out;
}
namespace pre_date_character_prefix_detail {
using namespace daily_assault_roster_detail;

// This limited shortcut only folds already observed existing-key counts.
// Full insertion/probe/growth behavior remains in the peer pending projection.
inline std::optional<bool> EarlierSkip(const game::ArmyPreDatePendingOccurrenceV1 *p,
    const game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 &same,
    std::unordered_map<std::uint32_t, std::optional<std::int32_t>> &counts) {
  if (!p || p->native_index != same.native_index || p->raw_full_id_u32 != same.raw_full_id_u32 ||
      p->original_army_resolution.object_identity != same.original_army_resolution.object_identity ||
      !p->pending_mutator_selected) return std::nullopt;
  if (!*p->pending_mutator_selected) return false;
  const auto target = p->pending_setup.target_army_full_id_u32;
  if (!target) return std::nullopt;
  auto found = counts.find(*target);
  const auto unknown = [&]() -> std::optional<bool> { counts[*target] = std::nullopt; return std::nullopt; };
  if (!p->pending_setup.ready || p->pending_setup.existing_key != true ||
      !p->original_arrg_references.references_ready || !p->original_arrg_references.count_raw_i32 ||
      p->arrg_occurrences.size() != p->original_arrg_references.occurrences.size()) return unknown();
  std::optional<std::int32_t> before = found == counts.end()
      ? p->pending_setup.existing_references.count_raw_i32 : found->second;
  if (!before) return unknown();
  std::uint32_t added = 0;
  for (const auto &row : p->arrg_occurrences) {
    if (!row.append_to_pending) return unknown();
    if (*row.append_to_pending) ++added;
  }
  const auto after = std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(*before) + added);
  counts[*target] = after;
  return after == *p->original_arrg_references.count_raw_i32;
}
inline game::ArmyPreDateCharacterOccurrenceV1 Occurrence(const CurrentPreDateCharacterPrefixBindings12003 &b,
    const game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 &same, std::optional<bool> skip, std::string skip_source) {
  game::ArmyPreDateCharacterOccurrenceV1 out{};
  out.native_index = same.native_index; out.original_request_full_id_u32 = same.raw_full_id_u32;
  out.army_resolution = same.original_army_resolution; out.earlier_skip = skip; out.earlier_skip_source = std::move(skip_source);
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  if (!out.original_request_full_id_u32) return fail("character_prefix_original_request_unavailable");
  if (!out.army_resolution.selected_object_ready) return fail("character_prefix_selected_army_unavailable");
  if (skip == true) { Finish(out, true); return out; }
  const auto army = Resolve(b.common, b.common.army_registry_slot, b.common.army_fallback_slot,
      same.raw_full_id_u32, 0x10);
  if (!army.observation.selected_object_ready || army.observation.object_identity != out.army_resolution.object_identity)
    return fail("character_prefix_same_query_army_selection_unavailable");
  const auto rejected = [&]() {
    out.failure_append_army_10_raw_u32 = Read<std::uint32_t>(b.common, army.object, 0x10);
    if (!out.failure_append_army_10_raw_u32) return fail("character_prefix_failure_army_id_unavailable");
    Finish(out, true); return out;
  };
  out.army_character_120_raw_u32 = Read<std::uint32_t>(b.common, army.object, 0x120);
  if (!out.army_character_120_raw_u32) return fail("character_prefix_army120_unavailable");
  if (*out.army_character_120_raw_u32 == 0xFFFFFFFFU) { Finish(out, true); return out; }
  const auto character = Resolve(b.common, b.common.character_registry_slot, b.common.character_fallback_slot,
      out.army_character_120_raw_u32, 0x18);
  out.character_resolution = character.observation;
  if (!out.character_resolution.selected_object_ready) return fail("character_prefix_character_selection_unavailable");
  out.army_unit_124_raw_u32 = Read<std::uint32_t>(b.common, army.object, 0x124);
  if (!out.army_unit_124_raw_u32) return fail("character_prefix_army124_unavailable");
  const auto unit = Resolve(b.common, b.common.unit_registry_slot, b.common.unit_fallback_slot,
      out.army_unit_124_raw_u32, 0x10);
  out.unit_resolution = unit.observation;
  if (!out.unit_resolution.selected_object_ready) return fail("character_prefix_unit_selection_unavailable");
  out.unit_owner_174_raw_u32 = Read<std::uint32_t>(b.common, unit.object, 0x174);
  if (!out.unit_owner_174_raw_u32) return fail("character_prefix_unit174_unavailable");
  out.character_magic_1c_raw_u32 = Read<std::uint32_t>(b.common, character.object, 0x1C);
  if (!out.character_magic_1c_raw_u32) return fail("character_prefix_character_tag_unavailable");
  if (*out.character_magic_1c_raw_u32 != 0x43686172U) return rejected();
  out.character_full_id_18_raw_u32 = Read<std::uint32_t>(b.common, character.object, 0x18);
  if (!out.character_full_id_18_raw_u32) return fail("character_prefix_character18_unavailable");
  if (*out.character_full_id_18_raw_u32 == 0xFFFFFFFFU) return rejected();
  const auto death = Read<const void *>(b.common, character.object, 0x1D0);
  if (!death) return fail("character_prefix_character_death_unavailable");
  out.character_death_1d0_present = *death != nullptr;
  if (*out.character_death_1d0_present) return rejected();
  bool state_admitted = false;
  for (auto [offset, observed] : {
      std::pair<std::size_t, std::optional<bool> *>{0x1C8, &out.character_state_1c8_present},
      {0x1C0, &out.character_state_1c0_present}, {0x1B8, &out.character_state_1b8_present}}) {
    const auto value = Read<const void *>(b.common, character.object, offset);
    if (!value) return fail("character_prefix_character_state_unavailable");
    *observed = *value != nullptr;
    if (**observed) { state_admitted = true; break; }
  }
  if (!state_admitted) return rejected();
  const auto owner = std::bit_cast<std::int32_t>(*out.unit_owner_174_raw_u32);
  auto &membership = out.membership; membership.demanded = true;
  if (!b.membership) { membership.unavailable_reason = "membership_native_callback_unavailable"; return fail("membership_native_verdict_unavailable"); }
  membership.verdict = b.membership(const_cast<void *>(character.object), owner, false);
  membership.observable = true; membership.unavailable_reason.clear();
  if (!*membership.verdict) return rejected();
  auto &basic = out.basic_rule; basic.demanded = true;
  if (!b.basic_rule) { basic.unavailable_reason = "basic_rule_native_callback_unavailable"; return fail("basic_rule_native_verdict_unavailable"); }
  basic.verdict = b.basic_rule(true, std::bit_cast<std::int32_t>(*out.character_full_id_18_raw_u32), owner, nullptr);
  basic.observable = true; basic.unavailable_reason.clear();
  if (!*basic.verdict) return rejected();
  auto &availability = out.availability; availability.demanded = true;
  if (!b.availability) { availability.unavailable_reason = "availability_native_callback_unavailable"; return fail("availability_native_verdict_unavailable"); }
  availability.verdict = b.availability(const_cast<void *>(character.object), owner, false, nullptr);
  availability.observable = true; availability.unavailable_reason.clear();
  if (!*availability.verdict) return rejected();
  Finish(out, true); return out;
}
} // namespace pre_date_character_prefix_detail

// Owning-thread paused query only: branch-demanded source predicates, no mutator,
// command, assignment, callback or physical manager write.
inline game::ArmyCurrentPreDateCharacterPrefixInputsV1 ReadCurrentPreDateCharacterPrefixInputs12003(
    const CurrentPreDateCharacterPrefixBindings12003 &b,
    const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &same_query_roster,
    const game::ArmyCurrentPreDatePendingUpdateInputsV1 *same_query_pending = nullptr,
    const game::ArmyFirstRemovalCleanupInputsV1 *same_query_globals = nullptr) {
  using namespace pre_date_character_prefix_detail;
  game::ArmyCurrentPreDateCharacterPrefixInputsV1 out{};
  out.original_roster = same_query_roster.original_roster;
  const auto unavailable = [&](const char *reason) {
    out.unavailable_reason = reason;
    for (const auto &same : same_query_roster.occurrences) {
      game::ArmyPreDateCharacterOccurrenceV1 row{};
      row.native_index = same.native_index; row.original_request_full_id_u32 = same.raw_full_id_u32;
      row.army_resolution = same.original_army_resolution; row.unavailable_reason = reason; Finish(row, false);
      out.occurrences.push_back(std::move(row));
    }
    return out;
  };
  if (!b.common.enabled) return unavailable("character_prefix_exact_build_bindings_unavailable");
  const auto state = Read<const void *>(b.common, b.common.game_state_slot);
  const auto data = state && *state ? Read<const void *>(b.common, *state, 0xA0) : std::nullopt;
  if (!data || !*data) return unavailable("character_prefix_manager_unavailable");
  const auto manager = At(*data, 0x2A540);
  out.manager_loaded = true; out.manager_identity = Identity(manager);
  out.initial_80 = pre_date_dated_append_detail::IdList(b.common, manager, 0x80, "80", same_query_globals, false);
  std::unordered_map<std::uint32_t, std::optional<std::int32_t>> counts;
  for (const auto &same : same_query_roster.occurrences) {
    const game::ArmyPreDatePendingOccurrenceV1 *pending = nullptr;
    if (same_query_pending) for (const auto &row : same_query_pending->occurrences)
      if (row.native_index == same.native_index) { pending = &row; break; }
    const auto skip = EarlierSkip(pending, same, counts);
    const auto source = !skip ? "unavailable" : pending && pending->pending_mutator_selected == false
        ? "pending_dispatch_bypass" : "same_query_existing_pending_count";
    out.occurrences.push_back(Occurrence(b, same, skip, source));
  }
  const bool complete = out.original_roster.references_ready && out.original_roster.count_raw_i32 &&
      *out.original_roster.count_raw_i32 >= 0 && out.occurrences.size() == static_cast<std::size_t>(*out.original_roster.count_raw_i32) &&
      std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &row) { return row.ready; });
  if (!complete) out.unavailable_reason = "character_prefix_demanded_inputs_incomplete";
  Finish(out, complete); return out;
}
} // namespace xar::ck3_12003

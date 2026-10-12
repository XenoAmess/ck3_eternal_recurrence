#pragma once

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/prewar_owner_inventory12004.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

namespace xar::ck3_12004 {

struct PrewarCommandableRaisedRegiment12004 {
  std::int32_t army_regiment_id = -1;
  std::optional<std::int32_t> observed_full_id;
  std::optional<std::uint32_t> observed_magic;
  std::optional<std::int32_t> current_soldiers_raw;
  std::optional<std::int32_t> maximum_soldiers_raw;
  std::optional<std::int32_t> native_carmy_id_raw;
  bool identity_and_atoms_ready = false;
  bool operator==(const PrewarCommandableRaisedRegiment12004 &) const = default;
};

struct PrewarCommandableRaisedRow12004 {
  PrewarOwnerArmyRegiment12004 source;
  PrewarCommandableRaisedRegiment12004 regiment;
  std::optional<std::int32_t> observed_carmy_full_id;
  std::optional<std::uint32_t> observed_carmy_magic;
  std::optional<std::int32_t> public_unit_id;
  std::optional<bool> carmy_roster_data_present;
  std::optional<std::int32_t> carmy_roster_capacity;
  std::optional<std::int32_t> carmy_roster_count;
  std::vector<PrewarCommandableRaisedRegiment12004> ordered_carmy_roster;
  bool carmy_roster_complete = false;
  std::optional<game::ArmySnapshot> fresh_public_army;
  std::optional<std::int32_t> observed_unit_full_id;
  std::optional<std::uint32_t> observed_unit_magic;
  std::optional<std::int32_t> observed_unit_owner;
  std::optional<std::int32_t> observed_unit_carmy_id;
  std::optional<std::int32_t> native_unit_state;
  std::optional<std::int32_t> retreat_raw;
  std::optional<std::int32_t> native_route_capacity;
  std::optional<std::int32_t> native_route_count;
  std::optional<bool> current_province_pointer_matches;
  std::optional<std::int32_t> observed_current_province_id;
  std::optional<std::uint32_t> observed_current_province_magic;
  std::optional<std::int32_t> move_mode;
  std::optional<bool> character_command_allowed;
  std::optional<bool> army_move_allowed;
  bool qualified = false;
  std::string failure;
  bool operator==(const PrewarCommandableRaisedRow12004 &) const = default;
};

struct PrewarCommandableRaisedObservation12004 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t owner_character_id = -1;
  std::optional<std::int32_t> observed_actor_full_id;
  std::optional<std::uint32_t> observed_actor_magic;
  PrewarOwnerIdCollection12004 source_raised_ids;
  bool source_census_complete = false;
  bool available = false;
  // Maximum CURRENT count of one independently verified standing ArRg.
  // This is a known subset floor, never the sum or complete CArmy strength,
  // a route/delivery forecast, or a claim of command execution.
  std::optional<std::int64_t> known_lower_soldiers;
  std::string source_scope = "current_actor_standing_single_arrg_known_subset_max";
  std::vector<PrewarCommandableRaisedRow12004> rows;
  // Unique full-generation ArRg references in first qualified source order.
  std::vector<std::int32_t> qualified_raised_regiment_refs;
  bool partial = false;
  std::string failure;
  bool operator==(const PrewarCommandableRaisedObservation12004 &) const = default;
};

namespace prewar_commandable_raised_detail12004 {

inline constexpr std::int32_t kMaximumRows = 8192;
inline constexpr std::int32_t kMaximumRoster = 8192;
inline constexpr std::int32_t kMaximumRosterReads = 65536;

template <typename T>
inline bool Copy(const void *base, std::size_t offset, T &value) noexcept {
  static_assert(std::is_trivially_copyable_v<T>);
  if (base == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (1) { return false; }
#endif
}

template <typename T>
inline void Capture(const void *base, std::size_t offset,
                    std::optional<T> &value) noexcept {
  T raw{};
  if (Copy(base, offset, raw)) value = raw;
}

template <typename Result, typename Function, typename... Args>
inline bool Call(Function function, Result &result, Args... args) noexcept {
  static_assert(std::is_trivially_copyable_v<Result>);
  static_assert(std::is_trivially_copyable_v<Function> &&
                (std::is_trivially_copyable_v<Args> && ...));
  if (function == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = function(args...);
    return true;
#if defined(_MSC_VER)
  } __except (1) { return false; }
#endif
}

// Only local borrowed pointers. No fallback object or storage-index-only join.
inline void *Resolve(void **slot, std::int32_t full_id) noexcept {
  if (slot == nullptr || full_id == -1) return nullptr;
  void *registry = nullptr, *entries = nullptr, *object = nullptr;
  std::int32_t capacity = 0, observed = -1;
  const auto index = static_cast<std::uint32_t>(full_id) & 0xFFFFFFU;
  if (!Copy(slot, 0, registry) || !Copy(registry, 0x20, entries) ||
      !Copy(registry, 0x2C, capacity) || capacity < 0 || capacity > 0x1000000 ||
      index >= static_cast<std::uint32_t>(capacity) ||
      !Copy(entries, static_cast<std::size_t>(index) * 0x10 + 8, object) ||
      !Copy(object, 0x10, observed) || observed != full_id) return nullptr;
  return object;
}

inline bool Collection(const PrewarOwnerIdCollection12004 &ids) {
  if (!ids.header_read_complete || !ids.entries_copied_complete ||
      !ids.data_present || !ids.capacity || !ids.count || *ids.capacity < 0 ||
      *ids.count < 0 || *ids.count > *ids.capacity || *ids.count > kMaximumRows ||
      (*ids.count != 0 && !*ids.data_present) ||
      ids.full_ids.size() != static_cast<std::size_t>(*ids.count)) return false;
  std::set<std::int32_t> seen;
  std::vector<std::int32_t> unique;
  for (const auto id : ids.full_ids) if (seen.insert(id).second) unique.push_back(id);
  return unique == ids.unique_full_ids && ids.duplicate_full_id_occurrences >= 0 &&
      static_cast<std::size_t>(ids.duplicate_full_id_occurrences) ==
          ids.full_ids.size() - unique.size();
}

inline void SetFailure(std::string &failure, const char *reason) noexcept {
  try { failure = reason; }
  catch (...) { failure.clear(); }
}

inline bool Regiment(const ck3_12002::ArmyBindings &bindings, std::int32_t id,
                     PrewarCommandableRaisedRegiment12004 &row) noexcept {
  row.army_regiment_id = id;
  void *object = Resolve(bindings.regiment_storage_slot, id);
  if (object == nullptr) return false;
  Capture(object, 0x10, row.observed_full_id);
  Capture(object, 0x14, row.observed_magic);
  Capture(object, 0x38, row.current_soldiers_raw);
  Capture(object, 0x3C, row.maximum_soldiers_raw);
  Capture(object, 0x140, row.native_carmy_id_raw);
  row.identity_and_atoms_ready = row.observed_full_id == id &&
      row.observed_magic == 0x41725267U && row.current_soldiers_raw &&
      *row.current_soldiers_raw >= 0 && row.maximum_soldiers_raw &&
      *row.maximum_soldiers_raw >= 0 && row.native_carmy_id_raw &&
      *row.native_carmy_id_raw != -1;
  return row.identity_and_atoms_ready;
}

inline bool Qualify(const ck3_12002::ArmyBindings &armies,
                    const ck3_12002::MilitaryBindings &military,
                    const ck3_12002::MilitaryWorldAccess &world,
                    const game::Snapshot &frame, void *actor,
                    std::int32_t &remaining_roster_reads,
                    PrewarCommandableRaisedRow12004 &row) {
  const auto fail = [&](const char *reason) { row.failure = reason; return false; };
  const auto &source = row.source;
  if (source.army_regiment_id == -1 || !source.full_generation_ready ||
      !source.atoms_read_complete || source.observed_full_id != source.army_regiment_id ||
      source.observed_magic != 0x41725267U ||
      !Regiment(armies, source.army_regiment_id, row.regiment) ||
      row.regiment.current_soldiers_raw != source.current_soldiers_raw ||
      row.regiment.maximum_soldiers_raw != source.maximum_soldiers_raw ||
      row.regiment.native_carmy_id_raw != source.native_carmy_id_raw)
    return fail("source_or_native_arrg_identity_atoms_unqualified");
  const auto carmy_id = *row.regiment.native_carmy_id_raw;
  void *army = Resolve(armies.internal_army_storage_slot, carmy_id);
  if (army == nullptr) return fail("carmy_full_generation_unavailable");
  Capture(army, 0x10, row.observed_carmy_full_id);
  Capture(army, 0x14, row.observed_carmy_magic);
  Capture(army, 0x124, row.public_unit_id);
  if (row.observed_carmy_full_id != carmy_id || row.observed_carmy_magic != 0x41726D79U ||
      !row.public_unit_id || *row.public_unit_id == -1)
    return fail("carmy_identity_or_public_unit_backlink_invalid");
  const auto selected = std::find_if(frame.player_armies.begin(), frame.player_armies.end(),
      [&](const auto &value) { return value.army_id == *row.public_unit_id; });
  if (selected == frame.player_armies.end() ||
      std::count_if(frame.player_armies.begin(), frame.player_armies.end(),
          [&](const auto &value) { return value.army_id == *row.public_unit_id; }) != 1)
    return fail("fresh_public_unit_join_missing_or_ambiguous");
  row.fresh_public_army = *selected;
  if (!selected->controllable || selected->owner_character_id != frame.played_character_id ||
      selected->in_combat || selected->retreating || selected->army_state_code != 1 ||
      selected->army_state != "regular" || !selected->has_current_province ||
      selected->current_province_id <= 0 ||
      selected->route_read_status != game::ArmyRouteReadStatus::complete_empty ||
      selected->route_source_count != 0 || !selected->route_province_ids.empty() ||
      selected->move_target_observable)
    return fail("fresh_public_unit_not_proven_standing_controllable");
  void *unit = nullptr;
  if (!Call(world.resolve_unit, unit, world.context, *row.public_unit_id) || unit == nullptr)
    return fail("unit_resolution_unavailable");
  Capture(unit, 0x10, row.observed_unit_full_id);
  Capture(unit, 0x14, row.observed_unit_magic);
  Capture(unit, 0x174, row.observed_unit_owner);
  Capture(unit, 0x178, row.observed_unit_carmy_id);
  Capture(unit, 0x170, row.retreat_raw);
  Capture(unit, 0x40, row.native_route_capacity);
  Capture(unit, 0x44, row.native_route_count);
  std::int32_t state = 0;
  if (Call(armies.get_unit_state, state, unit)) row.native_unit_state = state;
  if (row.observed_unit_full_id != row.public_unit_id || row.observed_unit_magic != 0x556E6974U ||
      row.observed_unit_owner != frame.played_character_id ||
      row.observed_unit_carmy_id != carmy_id || row.native_unit_state != 1 ||
      row.retreat_raw != 0 || !row.native_route_capacity || *row.native_route_capacity < 0 ||
      row.native_route_count != 0)
    return fail("native_unit_identity_owner_or_standing_state_invalid");
  void *province = nullptr, *native_province = nullptr;
  if (!Call(world.resolve_province, province, world.context, selected->current_province_id) ||
      province == nullptr || !Copy(unit, 0x20, native_province))
    return fail("current_province_unavailable");
  row.current_province_pointer_matches = province == native_province;
  Capture(province, 0x10, row.observed_current_province_id);
  Capture(province, 0x85C, row.observed_current_province_magic);
  if (!*row.current_province_pointer_matches ||
      row.observed_current_province_id != selected->current_province_id ||
      row.observed_current_province_magic != 0x50726F76U)
    return fail("current_province_identity_or_unit_echo_invalid");
  void *roster = nullptr;
  if (Copy(army, 0x38, roster)) row.carmy_roster_data_present = roster != nullptr;
  Capture(army, 0x40, row.carmy_roster_capacity);
  Capture(army, 0x44, row.carmy_roster_count);
  if (!row.carmy_roster_data_present || !*row.carmy_roster_data_present ||
      !row.carmy_roster_capacity || *row.carmy_roster_capacity < 0 ||
      *row.carmy_roster_capacity > kMaximumRoster || !row.carmy_roster_count ||
      *row.carmy_roster_count <= 0 || *row.carmy_roster_count > *row.carmy_roster_capacity ||
      *row.carmy_roster_count > remaining_roster_reads)
    return fail("carmy_roster_header_or_read_budget_invalid");
  remaining_roster_reads -= *row.carmy_roster_count;
  std::set<std::int32_t> seen;
  bool roster_ready = true;
  bool target_found = false;
  for (std::int32_t i = 0; i < *row.carmy_roster_count; ++i) {
    std::int32_t id = -1;
    PrewarCommandableRaisedRegiment12004 member{};
    if (!Copy(roster, static_cast<std::size_t>(i) * 4, id))
      return fail("carmy_roster_entry_unreadable");
    const bool member_ready = Regiment(armies, id, member);
    if (!seen.insert(id).second || !member_ready || member.native_carmy_id_raw != carmy_id)
      roster_ready = false;
    if (id == source.army_regiment_id) {
      target_found = true;
      if (member != row.regiment) roster_ready = false;
    }
    row.ordered_carmy_roster.push_back(std::move(member));
  }
  row.carmy_roster_complete = roster_ready && target_found;
  if (!row.carmy_roster_complete) return fail("carmy_roster_duplicate_identity_or_backlink_invalid");
  std::int32_t mode = 2;
  if (!Call(military.move_mode, mode, unit, province, std::int32_t{1}))
    return fail("move_mode_unreadable");
  row.move_mode = mode;
  if (mode != 0 && mode != 1) return fail("move_mode_unqualified");
  bool allowed = false;
  // Existing actual4 preview passes command kind 1, not the returned move mode.
  if (Call(military.character_command_allowed, allowed, actor, std::int32_t{1}))
    row.character_command_allowed = allowed;
  allowed = false;
  if (Call(military.army_move_allowed, allowed, unit, mode)) row.army_move_allowed = allowed;
  if (row.character_command_allowed != true || row.army_move_allowed != true)
    return fail("native_current_command_predicate_unqualified");
  row.qualified = true;
  return true;
}

} // namespace prewar_commandable_raised_detail12004

// Called only with actual4 bindings inside one fresh paused main-thread ticket.
// The caller compares complete frame/owner/observation DTOs in both rounds and
// withdraws readiness on any frame drift. No borrowed pointer leaves this call.
// True means a safe observation was produced; available separately qualifies
// the known subset floor. No native command, path or route is constructed.
inline bool ReadPrewarCommandableRaised12004(
    const ck3_12002::ArmyBindings &armies,
    const ck3_12002::MilitaryBindings &military,
    const ck3_12002::MilitaryWorldAccess &world,
    const game::Snapshot &freshFrame,
    const PrewarOwnerInventory12004 &owner,
    PrewarCommandableRaisedObservation12004 &output) noexcept {
  namespace detail = prewar_commandable_raised_detail12004;
  try {
    output = {};
    output.snapshot_revision = owner.snapshot_revision;
    output.date_raw = owner.date_raw;
    output.actor_character_id = owner.actor_character_id;
    output.owner_character_id = owner.owner_character_id;
    output.source_raised_ids = owner.raised_army_regiment_ids;
    if (!freshFrame.map_ready || !freshFrame.paused || !freshFrame.has_played_character ||
        !freshFrame.played_character_alive || freshFrame.played_character_id == -1 ||
        owner.actor_character_id != freshFrame.played_character_id ||
        owner.owner_character_id != freshFrame.played_character_id ||
        owner.date_raw != freshFrame.date_raw || !owner.snapshot_revision ||
        !owner.exact_build_ready || !owner.owner_identity_ready || !owner.owner_echo_ready ||
        owner.observed_owner_full_id != owner.owner_character_id ||
        owner.observed_owner_magic != 0x43686172U ||
        owner.composition_owner_echo_90 != owner.owner_character_id ||
        !owner.source_frame_ready || !owner.native_lifetime_ready || !owner.cleanup_succeeded ||
        !armies.enabled || !military.enabled || armies.internal_army_storage_slot == nullptr ||
        armies.regiment_storage_slot == nullptr || armies.get_unit_state == nullptr ||
        world.resolve_character == nullptr || world.resolve_unit == nullptr ||
        world.resolve_province == nullptr || military.move_mode == nullptr ||
        military.character_command_allowed == nullptr || military.army_move_allowed == nullptr) {
      output.failure = "fresh_actor_frame_or_bindings_unqualified";
      return false;
    }
    void *actor = nullptr;
    if (!detail::Call(world.resolve_character, actor, world.context, owner.actor_character_id) ||
        actor == nullptr) {
      output.failure = "actor_resolution_unavailable";
      return false;
    }
    detail::Capture(actor, 0x18, output.observed_actor_full_id);
    detail::Capture(actor, 0x1C, output.observed_actor_magic);
    if (output.observed_actor_full_id != owner.actor_character_id ||
        output.observed_actor_magic != 0x43686172U) {
      output.failure = "actor_full_generation_or_magic_invalid";
      return false;
    }
    output.source_census_complete = detail::Collection(output.source_raised_ids) &&
        owner.raised_army_regiments.size() == output.source_raised_ids.full_ids.size();
    output.partial = !output.source_census_complete;
    auto remaining_reads = detail::kMaximumRosterReads;
    const auto count = (std::min)(owner.raised_army_regiments.size(),
                                static_cast<std::size_t>(detail::kMaximumRows));
    if (count != owner.raised_army_regiments.size()) output.partial = true;
    for (std::size_t i = 0; i < count; ++i) {
      PrewarCommandableRaisedRow12004 row{};
      row.source = owner.raised_army_regiments[i];
      if (i >= output.source_raised_ids.full_ids.size() ||
          row.source.occurrence_index != static_cast<std::int32_t>(i) ||
          row.source.army_regiment_id != output.source_raised_ids.full_ids[i]) {
        row.failure = "owner_arrg_occurrence_join_invalid";
      } else {
        detail::Qualify(armies, military, world, freshFrame, actor, remaining_reads, row);
      }
      if (!row.qualified) output.partial = true;
      output.rows.push_back(std::move(row));
    }
    std::map<std::int32_t, PrewarCommandableRaisedRegiment12004> observed;
    std::set<std::int32_t> conflicts;
    for (const auto &row : output.rows) if (row.regiment.identity_and_atoms_ready) {
      const auto [at, inserted] = observed.emplace(row.regiment.army_regiment_id, row.regiment);
      if (!inserted && at->second != row.regiment) conflicts.insert(row.regiment.army_regiment_id);
    }
    std::set<std::int32_t> credited;
    std::int64_t lower = 0;
    for (auto &row : output.rows) {
      if (conflicts.contains(row.source.army_regiment_id)) {
        row.qualified = false;
        row.failure = "selected_arrg_raw_conflict";
        output.partial = true;
      }
      if (!row.qualified || !credited.insert(row.source.army_regiment_id).second) continue;
      output.qualified_raised_regiment_refs.push_back(row.source.army_regiment_id);
      lower = (std::max)(lower, static_cast<std::int64_t>(*row.regiment.current_soldiers_raw));
    }
    const bool observed_empty = output.source_census_complete && output.source_raised_ids.full_ids.empty();
    if (!output.qualified_raised_regiment_refs.empty() || observed_empty) {
      output.known_lower_soldiers = lower;
      output.available = true;
    }
    if (output.partial) output.failure = "standing_commandable_raised_subset_partial";
    else if (!output.available) output.failure = "no_qualified_standing_arrg";
    return true;
  } catch (...) {
    output.available = false;
    output.known_lower_soldiers.reset();
    output.source_census_complete = false;
    output.partial = true;
    output.qualified_raised_regiment_refs.clear();
    for (auto &row : output.rows) row.qualified = false;
    detail::SetFailure(output.failure, "commandable_raised_cpp_exception");
    return false;
  }
}

} // namespace xar::ck3_12004

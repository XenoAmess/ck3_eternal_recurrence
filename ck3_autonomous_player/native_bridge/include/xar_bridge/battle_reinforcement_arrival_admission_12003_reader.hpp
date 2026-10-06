#pragma once

#include "battle_reinforcement_arrival_admission_12003.hpp"
#include "xar_bridge/ck3_12002_routes.hpp"

#include <algorithm>
#include <cstddef>
#include <cstring>
#include <utility>

namespace xar::ck3_12002 {
namespace arrival_admission_12003_detail {

using Output = game::BattleReinforcementArrivalAdmission12003Snapshot;
using Status = game::ArrivalAdmission12003Status;

// Extracted read-only mirror of the reviewed routes adapter. The parent binds
// RouteBindings to exact 1.20.0.3; this leaf neither binds nor calls the mutable
// contact resolver. Full identities are checked after low-24-bit slot lookup.
template <class T> inline T At(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
  return value;
}

inline void *Resolve(void **slot, std::int32_t id, std::size_t id_offset) noexcept {
  if (slot == nullptr || *slot == nullptr || id < 0) return nullptr;
  void *const storage = *slot;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  const auto count = At<std::int32_t>(storage, 0x2C);
  void *const rows = At<void *>(storage, 0x20);
  if (rows == nullptr || count <= 0 || index >= static_cast<std::uint32_t>(count))
    return nullptr;
  void *const object = At<void *>(rows, static_cast<std::size_t>(index) * 0x10 + 8);
  return object != nullptr && At<std::int32_t>(object, id_offset) == id
             ? object : nullptr;
}

inline void *Province(void *game_state, std::int32_t id) noexcept {
  if (game_state == nullptr || id <= 0) return nullptr;
  void *const data = At<void *>(game_state, 0xA0);
  if (data == nullptr || id >= At<std::int32_t>(data, 0x14C)) return nullptr;
  void *const rows = At<void *>(data, 0x140);
  if (rows == nullptr) return nullptr;
  void *const p = At<void *>(rows, static_cast<std::size_t>(id) * 8);
  return p != nullptr && At<std::uint32_t>(p, 0x85C) == 0x50726F76U &&
                 At<std::int32_t>(p, 0x10) == id ? p : nullptr;
}

inline void *Character(const RouteBindings &b, std::int32_t id) noexcept {
  void *const p = Resolve(b.character_storage_slot, id, 0x18);
  return p != nullptr && At<std::uint32_t>(p, 0x1C) == 0x43686172U ? p : nullptr;
}

inline bool ClockMatches(const RouteBindings &b, const game::Snapshot &s) noexcept {
  return b.enabled && b.game_state_slot != nullptr && *b.game_state_slot != nullptr &&
         b.jomini_state_slot != nullptr && *b.jomini_state_slot != nullptr &&
         At<std::int32_t>(*b.game_state_slot, 8) == s.date_raw &&
         (At<std::uint8_t>(*b.jomini_state_slot, 0x20) != 0) == s.paused;
}

inline bool Ids(const void *owner, std::size_t data_offset, std::size_t count_offset,
                std::int32_t maximum, std::vector<std::int32_t> &out) {
  out.clear();
  void *const data = At<void *>(owner, data_offset);
  const auto count = At<std::int32_t>(owner, count_offset);
  if (count < 0 || count > maximum || (count > 0 && data == nullptr)) return false;
  out.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i) {
    const auto id = At<std::int32_t>(data, static_cast<std::size_t>(i) * 4);
    if (id < 0) { out.clear(); return false; }
    out.push_back(id);
  }
  return true;
}

inline Status Fail(Output &out, Status status, std::string_view reason) {
  out.status = status;
  out.unavailable_reason = reason;
  out.eligibility_now = "unavailable";
  return status;
}

inline void Init(Output &out, std::int32_t subject_id, std::int32_t target_id,
                 std::string_view provenance) {
  out = {};
  out.subject.public_cunit_id = subject_id;
  if (target_id > 0) out.target.province_id = target_id;
  out.target.provenance = provenance;
}

// Unlike a projected roster, this reads only members already stored in the
// current combat and checks the same CArmy -> combat/CUnit backlinks used by
// the existing actual-contact reader. Its order is the native side order.
inline bool Side(const RouteBindings &b, const void *combat, std::size_t side_offset,
                 std::int32_t combat_id, std::vector<std::int32_t> &out) {
  out.clear();
  const auto *const side = static_cast<const std::byte *>(combat) + side_offset;
  std::vector<std::int32_t> native_ids;
  if (At<const void *>(side, 0xB8) != combat ||
      !Ids(side, 0x10, 0x1C, 4'096, native_ids) || native_ids.empty()) return false;
  out.reserve(native_ids.size());
  for (const auto id : native_ids) {
    void *const army = Resolve(b.army_internal_storage_slot, id, 0x10);
    if (army == nullptr || At<std::int32_t>(army, 0x128) != combat_id) return false;
    const auto unit_id = At<std::int32_t>(army, 0x124);
    void *const unit = Resolve(b.army_storage_slot, unit_id, 0x10);
    if (unit == nullptr || At<std::int32_t>(unit, 0x178) != id ||
        std::find(out.begin(), out.end(), unit_id) != out.end()) return false;
    out.push_back(unit_id);
  }
  return true;
}

inline bool Rosters(const RouteBindings &b, void *combat, std::int32_t combat_id,
                    Output &out) {
  if (!Side(b, combat, 0x20, combat_id,
            out.current_attacker_public_cunit_ids_in_stored_order) ||
      !Side(b, combat, 0x368, combat_id,
            out.current_defender_public_cunit_ids_in_stored_order)) return false;
  for (const auto id : out.current_attacker_public_cunit_ids_in_stored_order) {
    if (std::find(out.current_defender_public_cunit_ids_in_stored_order.begin(),
                  out.current_defender_public_cunit_ids_in_stored_order.end(), id) !=
        out.current_defender_public_cunit_ids_in_stored_order.end()) return false;
  }
  return true;
}

inline Status Sample(const RouteBindings &b, std::int32_t subject_id,
                     std::int32_t target_id, std::string_view provenance, Output &out) {
  Init(out, subject_id, target_id, provenance);
  void *const game_state = *b.game_state_slot;
  void *const unit = Resolve(b.army_storage_slot, subject_id, 0x10);
  if (unit == nullptr)
    return Fail(out, Status::subject_cunit_not_found, "subject_cunit_not_found");
  const auto native_id = At<std::int32_t>(unit, 0x178);
  void *const army = Resolve(b.army_internal_storage_slot, native_id, 0x10);
  if (army == nullptr || At<std::int32_t>(army, 0x124) != subject_id)
    return Fail(out, Status::state_changed, "army_backlink_mismatch");
  out.subject.native_carmy_id = native_id;
  const auto owner_id = At<std::int32_t>(unit, 0x174);
  void *const owner = Character(b, owner_id);
  if (owner == nullptr)
    return Fail(out, Status::unavailable, "subject_owner_unavailable");
  out.subject.owner_character_id = owner_id;
  void *const current = At<void *>(unit, 0x20);
  if (current == nullptr || Province(game_state, At<std::int32_t>(current, 0x10)) != current)
    return Fail(out, Status::state_changed, "subject_current_province_unavailable");
  out.subject.current_province_id = At<std::int32_t>(current, 0x10);
  if (target_id == -1 && provenance == "none") {
    out.eligibility_now = "not_applicable";
    out.status = Status::not_applicable;
    return out.status;
  }
  void *const target = Province(game_state, target_id);
  if (target == nullptr)
    return Fail(out, Status::target_province_not_found, "target_province_not_found");

  const bool active = b.is_army_in_combat(army);
  void *active_combat = nullptr;
  if (active) {
    const auto combat_id = At<std::int32_t>(army, 0x128);
    active_combat = Resolve(b.combat_storage_slot, combat_id, 8);
    if (active_combat == nullptr || At<std::uint8_t>(active_combat, 0x704) != 0 ||
        At<void *>(active_combat, 0x6B8) != current || current != target)
      return Fail(out, Status::state_changed, "active_combat_identity_mismatch");
    out.subject.active_combat_id = combat_id;
  } else {
    game::BattleReinforcementArrivalAdmissionRawGates12003 gates;
    void *const gate = At<void *>(target, 0x20);
    gates.province_contact_gate_enabled = gate != nullptr && At<std::uint8_t>(gate, 0x1B) != 0;
    void *const mode_root = *b.contact_game_mode_slot;
    void *const mode = mode_root == nullptr ? nullptr : At<void *>(mode_root, 0x1C0);
    gates.contact_game_mode_allows_contact = mode != nullptr && At<std::uint8_t>(mode, 0x28) == 0;
    gates.unit_contact_state_raw = At<std::int32_t>(unit, 0x18);
    gates.unit_retreat_state_raw = At<std::int32_t>(unit, 0x170);
    gates.army_empty_for_contact = b.is_army_empty_for_contact(army);
    out.raw_gates = gates;
    out.eligibility_now = gates.province_contact_gate_enabled &&
        gates.contact_game_mode_allows_contact && gates.unit_contact_state_raw == 0 &&
        gates.unit_retreat_state_raw <= 0 && !gates.army_empty_for_contact
            ? "eligible" : "ineligible";
  }

  if (!Ids(target, 0x758, 0x764, 1'024, out.current_target_combat_ids_in_stored_order))
    return Fail(out, Status::state_changed, "target_combat_array_unavailable");
  void *selected = nullptr;
  // Same forward owner -> representative XOR and last stored compatible
  // selection as ck3_12002_routes.cpp:1419-1471. No loser/opponent builder.
  for (std::size_t i = 0; i < out.current_target_combat_ids_in_stored_order.size(); ++i) {
    const auto id = out.current_target_combat_ids_in_stored_order[i];
    void *const combat = Resolve(b.combat_storage_slot, id, 8);
    if (combat == nullptr || At<void *>(combat, 0x6B8) != target)
      return Fail(out, Status::state_changed, "target_combat_identity_mismatch");
    if (At<std::uint8_t>(combat, 0x704) != 0) continue;
    void *const attacker = Character(b, At<std::int32_t>(combat, 0x90));
    void *const defender = Character(b, At<std::int32_t>(combat, 0x3D8));
    if (attacker == nullptr || defender == nullptr)
      return Fail(out, Status::unavailable, "combat_representative_unavailable");
    if (b.is_character_hostile(owner, attacker, false) !=
        b.is_character_hostile(owner, defender, false)) {
      out.current_target_compatible_combat_ids_in_stored_order.push_back(id);
      selected = combat;
      out.contact_if_now_selected_combat_id = id;
      out.selected_combat_stored_index = static_cast<std::int32_t>(i);
    }
  }

  if (active) {
    const auto active_id = *out.subject.active_combat_id;
    const auto found = std::find(out.current_target_combat_ids_in_stored_order.begin(),
                                 out.current_target_combat_ids_in_stored_order.end(), active_id);
    std::vector<std::int32_t> province_units;
    if (found == out.current_target_combat_ids_in_stored_order.end() ||
        !Ids(current, 0x740, 0x74C, 4'096, province_units) ||
        std::find(province_units.begin(), province_units.end(), subject_id) == province_units.end() ||
        !Rosters(b, active_combat, active_id, out))
      return Fail(out, Status::state_changed, "active_combat_roster_unavailable");
    const auto a_count = std::count(out.current_attacker_public_cunit_ids_in_stored_order.begin(),
                                    out.current_attacker_public_cunit_ids_in_stored_order.end(), subject_id);
    const auto d_count = std::count(out.current_defender_public_cunit_ids_in_stored_order.begin(),
                                    out.current_defender_public_cunit_ids_in_stored_order.end(), subject_id);
    if (a_count + d_count != 1)
      return Fail(out, Status::state_changed, "subject_active_participation_unverified");
    // Active observation is the only selection exception: publish the actual
    // backlink combat and actual side, rather than a new-contact selection.
    out.contact_if_now_selected_combat_id = active_id;
    out.selected_combat_stored_index = static_cast<std::int32_t>(
        std::distance(out.current_target_combat_ids_in_stored_order.begin(), found));
    out.join_side = a_count == 1 ? "attacker" : "defender";
    out.subject_current_participation_verified = true;
    out.eligibility_now = "already_in_active_combat";
  } else if (selected != nullptr) {
    void *const attacker = Character(b, At<std::int32_t>(selected, 0x90));
    void *const defender = Character(b, At<std::int32_t>(selected, 0x3D8));
    if (attacker == nullptr || defender == nullptr)
      return Fail(out, Status::unavailable, "combat_representative_unavailable");
    // Reverse representative -> owner calls deliberately retain native
    // asymmetry; forward compatibility does not establish the joining side.
    const bool joins_defender = b.is_character_hostile(attacker, owner, false);
    const bool joins_attacker = b.is_character_hostile(defender, owner, false);
    if (joins_defender == joins_attacker)
      return Fail(out, Status::unavailable, "reverse_join_side_unavailable");
    if (!Rosters(b, selected, *out.contact_if_now_selected_combat_id, out))
      return Fail(out, Status::state_changed, "selected_combat_roster_unavailable");
    out.join_side = joins_defender ? "defender" : "attacker";
  }
  out.status = Status::available;
  return out.status;
}

} // namespace arrival_admission_12003_detail

// Existing owning-thread paused snapshot, foreign or player full CUnitID, and
// an explicitly sourced target. This observation has no controllability gate,
// route planner, ETA calculator, native AI assignment writer, or game action.
inline game::ArrivalAdmission12003Status ReadBattleReinforcementArrivalAdmission12003(
    const RouteBindings &b, const game::Snapshot &paused_scope,
    std::int32_t subject_public_cunit_id, std::int32_t target_province_id,
    std::string_view target_provenance,
    game::BattleReinforcementArrivalAdmission12003Snapshot &out) noexcept {
  using namespace arrival_admission_12003_detail;
  try {
    Init(out, subject_public_cunit_id, target_province_id, target_provenance);
    out.observed_date_raw = paused_scope.date_raw;
    if (!b.enabled || b.game_state_slot == nullptr || b.jomini_state_slot == nullptr ||
        b.army_storage_slot == nullptr || b.army_internal_storage_slot == nullptr ||
        b.character_storage_slot == nullptr || b.combat_storage_slot == nullptr ||
        b.contact_game_mode_slot == nullptr || b.is_character_hostile == nullptr ||
        b.is_army_empty_for_contact == nullptr || b.is_army_in_combat == nullptr ||
        subject_public_cunit_id < 0)
      return Fail(out, Status::unavailable, "arrival_bindings_unavailable");
    if (!ClockMatches(b, paused_scope))
      return Fail(out, Status::unavailable, "snapshot_clock_mismatch");
    if (!paused_scope.paused)
      return Fail(out, Status::requires_paused, "requires_paused");
    Output first, second;
    const auto first_status = Sample(b, subject_public_cunit_id, target_province_id,
                                     target_provenance, first);
    const auto second_status = Sample(b, subject_public_cunit_id, target_province_id,
                                      target_provenance, second);
    if (first_status != second_status || first != second || !ClockMatches(b, paused_scope))
      return Fail(out, Status::state_changed, "arrival_observation_changed");
    out = std::move(second);
    out.observed_date_raw = paused_scope.date_raw;
    return out.status;
  } catch (...) {
    out.status = game::ArrivalAdmission12003Status::unavailable;
    out.eligibility_now = "unavailable";
    out.unavailable_reason = "arrival_read_failed";
    return out.status;
  }
}

} // namespace xar::ck3_12002

#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/ck3_12002_battle_journal.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

namespace xar::ck3_12002 {
namespace {

template <typename T> T At(const void *p, std::size_t o) noexcept {
  T v{};
  std::memcpy(&v, static_cast<const std::byte *>(p) + o, sizeof(v));
  return v;
}
void *Resolve(void **slot, std::int32_t id, std::size_t identity) noexcept {
  if (!slot || !*slot || id <= 0)
    return nullptr;
  auto *storage = *slot;
  auto *rows = At<void *>(storage, 0x20);
  auto cap = At<std::int32_t>(storage, 0x2C);
  auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (!rows || cap <= 0 || cap > 1'000'000 ||
      index >= static_cast<std::uint32_t>(cap))
    return nullptr;
  auto *p = At<void *>(rows, index * 0x10ULL + 8);
  return p && At<std::int32_t>(p, identity) == id ? p : nullptr;
}
bool Header(const void *p, std::size_t data_off, std::size_t cap_off,
            std::size_t count_off, const void *&data, std::int32_t &count,
            std::int32_t maximum = 4096) noexcept {
  data = At<const void *>(p, data_off);
  count = At<std::int32_t>(p, count_off);
  auto cap = At<std::int32_t>(p, cap_off);
  return count >= 0 && cap >= count && cap >= 0 && count <= maximum &&
         (!count || data);
}
bool Scope(const BattleBindings &b, const game::Snapshot &s) noexcept {
  return b.enabled && s.paused && s.map_ready && b.game_state_slot &&
         *b.game_state_slot && b.jomini_state_slot && *b.jomini_state_slot &&
         At<std::int32_t>(*b.game_state_slot, 8) == s.date_raw &&
         At<std::uint8_t>(*b.jomini_state_slot, 0x20) != 0;
}
void *Province(const BattleBindings &b, void *p) noexcept {
  if (!p || !b.resolve_province)
    return nullptr;
  const auto id = At<std::int32_t>(p, 0x10);
  return id > 0 && b.resolve_province(b.province_context, id) == p ? p
                                                                   : nullptr;
}
void *NativeProvince(void *context, std::int32_t id) noexcept {
  auto **slot = static_cast<void **>(context);
  if (!slot || !*slot || id <= 0)
    return nullptr;
  auto *data = At<void *>(*slot, 0xA0);
  if (!data || id >= At<std::int32_t>(data, 0x14C))
    return nullptr;
  auto *rows = At<void *>(data, 0x140);
  if (!rows)
    return nullptr;
  auto *p = At<void *>(rows, static_cast<std::size_t>(id) * 8);
  return p && At<std::uint32_t>(p, 0x85C) == 0x50726F76U &&
                 At<std::int32_t>(p, 0x10) == id
             ? p
             : nullptr;
}
std::string Phase(std::int32_t v) {
  const char *names[]{"maneuver", "main", "pursuit", "done"};
  return v >= 0 && v <= 3 ? names[v] : "";
}
std::string Winner(std::int32_t v) {
  return v == -1 ? "none" : v == 0 ? "attacker" : v == 1 ? "defender" : "";
}
bool Add(std::int64_t &v, std::int64_t n) noexcept {
  if ((n > 0 && v > (std::numeric_limits<std::int64_t>::max)() - n) ||
      (n < 0 && v < (std::numeric_limits<std::int64_t>::min)() - n))
    return false;
  v += n;
  return true;
}
bool ArmyIds(const BattleBindings &b, const void *combat, std::size_t side_off,
             std::int32_t combat_id,
             std::vector<game::BattleControlArmyIdentitySnapshot> &out) {
  auto *side = static_cast<const std::byte *>(combat) + side_off;
  const void *data{};
  std::int32_t count{};
  if (At<const void *>(side, 0xB8) != combat ||
      !Header(side, 0x10, 0x18, 0x1C, data, count))
    return false;
  for (std::int32_t i = 0; i < count; ++i) {
    auto id = At<std::int32_t>(data, i * 4ULL);
    auto *army = Resolve(b.army_internal_storage_slot, id, 0x10);
    if (!army || At<std::int32_t>(army, 0x128) != combat_id)
      return false;
    auto unit_id = At<std::int32_t>(army, 0x124);
    auto *unit = Resolve(b.army_storage_slot, unit_id, 0x10);
    if (!unit || At<std::int32_t>(unit, 0x178) != id)
      return false;
    auto owner = At<std::int32_t>(unit, 0x174);
    if (!Resolve(b.character_storage_slot, owner, 0x18) ||
        std::any_of(out.begin(), out.end(), [&](auto &r) {
          return r.native_carmy_id == id || r.public_cunit_id == unit_id;
        }))
      return false;
    out.push_back({id, unit_id, owner, combat_id});
  }
  return true;
}
bool TransitionSample(const BattleBindings &b,
                      const game::BattleTransitionRequest &req,
                      game::BattleTransitionSnapshot &out) {
  out = {};
  out.combat_id = req.combat_id;
  auto *combat = Resolve(b.combat_storage_slot, req.combat_id, 8);
  if (!combat) {
    out.status = game::BattleTransitionSnapshotStatus::combat_not_found;
    out.battle_transition_ready = true;
    return true;
  }
  if (At<std::uint8_t>(combat, kBattleDailyGuardOffset))
    return false;
  auto *province = Province(b, At<void *>(combat, 0x6B8));
  if (!province)
    return false;
  out.province_id = At<std::int32_t>(province, 0x10);
  out.phase_raw = At<std::int32_t>(combat, kBattlePhaseOffset);
  out.phase = Phase(out.phase_raw);
  out.phase_day = At<std::int32_t>(combat, kBattlePhaseDayOffset);
  out.winner_raw = At<std::int32_t>(combat, 0x6E0);
  out.winner_side = Winner(out.winner_raw);
  out.forced_winner_raw = At<std::int32_t>(combat, 0x700);
  out.forced_winner_side = Winner(out.forced_winner_raw);
  auto flag = At<std::uint8_t>(combat, kBattleFinalizedOffset);
  out.finalized = flag != 0;
  out.battle_result_id = At<std::int32_t>(combat, 0x708);
  if (out.phase.empty() || out.winner_side.empty() ||
      out.forced_winner_side.empty() || out.phase_day < 0 || flag > 1 ||
      (out.battle_result_id != -1 &&
       !Resolve(b.battle_result_storage_slot, out.battle_result_id, 8)))
    return false;
  std::vector<game::BattleControlArmyIdentitySnapshot> a, d;
  if (!ArmyIds(b, combat, 0x20, req.combat_id, a) ||
      !ArmyIds(b, combat, 0x368, req.combat_id, d))
    return false;
  for (auto &r : a)
    out.attacker_public_cunit_ids_in_stored_order.push_back(r.public_cunit_id);
  for (auto &r : d) {
    if (std::find(out.attacker_public_cunit_ids_in_stored_order.begin(),
                  out.attacker_public_cunit_ids_in_stored_order.end(),
                  r.public_cunit_id) !=
        out.attacker_public_cunit_ids_in_stored_order.end())
      return false;
    out.defender_public_cunit_ids_in_stored_order.push_back(r.public_cunit_id);
  }
  out.status = game::BattleTransitionSnapshotStatus::available;
  out.battle_transition_ready = true;
  return Resolve(b.combat_storage_slot, req.combat_id, 8) == combat &&
         !At<std::uint8_t>(combat, kBattleDailyGuardOffset);
}
bool Bucket(const BattleBindings &b, const void *side, std::size_t offset,
            const char *name, game::BattleControlSideSnapshot &out,
            std::vector<game::BattleControlRegimentEntrySnapshot> &rows,
            std::int64_t &current) {
  const void *data{};
  std::int32_t count{};
  if (!Header(side, offset, offset + 8, offset + 12, data, count))
    return false;
  for (std::int32_t i = 0; i < count; ++i) {
    auto *entry = static_cast<const std::byte *>(data) + i * 0x60ULL;
    game::BattleControlRegimentEntrySnapshot r{};
    r.bucket = name;
    r.bucket_index = i;
    r.regiment_id = At<std::int32_t>(entry, 8);
    auto *regiment = Resolve(b.regiment_storage_slot, r.regiment_id, 0x10);
    if (!regiment)
      return false;
    r.native_carmy_id =
        At<std::int32_t>(regiment, kBattleArmyRegimentArmyOffset);
    auto army = std::find_if(
        out.ordered_armies.begin(), out.ordered_armies.end(),
        [&](auto &a) { return a.native_carmy_id == r.native_carmy_id; });
    if (army == out.ordered_armies.end())
      return false;
    r.public_cunit_id = army->public_cunit_id;
    r.owner_character_id = army->owner_character_id;
    auto *type = At<void *>(regiment, kBattleArmyRegimentTypeOffset);
    if (!type)
      return false;
    auto fights = At<std::uint8_t>(type, kBattleMainPhaseTypeFlag);
    if (fights > 1)
      return false;
    r.fights_in_main_phase = fights != 0;
    r.hard_casualties_available = r.fights_in_main_phase;
    r.starting_raw = At<std::int64_t>(entry, 0x10);
    r.current_fighting_raw = At<std::int64_t>(entry, 0x18);
    r.soft_casualties_raw = At<std::int64_t>(entry, 0x20);
    if (r.starting_raw < 0 || r.current_fighting_raw < 0 ||
        r.soft_casualties_raw < 0 || r.current_fighting_raw > r.starting_raw ||
        r.soft_casualties_raw > r.starting_raw - r.current_fighting_raw)
      return false;
    auto remainder =
        r.starting_raw - r.current_fighting_raw - r.soft_casualties_raw;
    if (r.fights_in_main_phase) {
      r.hard_casualties_raw = remainder;
      if (!Add(out.derived_main_fighting_entry_hard_casualties_raw, remainder))
        return false;
    } else if (!Add(out.non_main_start_minus_current_minus_soft_raw, remainder))
      return false;
    r.effective_max_size = At<std::int32_t>(entry, 0x30);
    r.effective_siege_raw = At<std::int64_t>(entry, 0x38);
    r.effective_damage_raw = At<std::int64_t>(entry, 0x40);
    r.effective_toughness_raw = At<std::int64_t>(entry, 0x48);
    r.effective_pursuit_raw = At<std::int64_t>(entry, 0x50);
    r.effective_screen_raw = At<std::int64_t>(entry, 0x58);
    r.entry_strength_raw =
        b.get_combat_regiment_strength(const_cast<std::byte *>(entry));
    if (!Add(current, r.current_fighting_raw) ||
        !Add(out.derived_current_fighting_raw, r.current_fighting_raw) ||
        !Add(out.derived_soft_casualties_raw, r.soft_casualties_raw))
      return false;
    rows.push_back(std::move(r));
  }
  return true;
}
bool Side(const BattleBindings &b, const void *combat, std::size_t off,
          std::int32_t id, std::int32_t index,
          game::BattleControlSideSnapshot &out) {
  auto *p = static_cast<const std::byte *>(combat) + off;
  out.side_index = index;
  out.role = index ? "defender" : "attacker";
  out.current_roll_points = At<std::int32_t>(combat, index ? 0x6D4 : 0x6D0);
  if (!ArmyIds(b, combat, off, id, out.ordered_armies))
    return false;
  out.primary_participant_character_id = At<std::int32_t>(p, 0x70);
  out.selected_commander_character_id = At<std::int32_t>(p, 0x74);
  if (!Resolve(b.character_storage_slot, out.primary_participant_character_id,
               0x18) ||
      (out.selected_commander_character_id != -1 &&
       !Resolve(b.character_storage_slot, out.selected_commander_character_id,
                0x18)))
    return false;
  std::int64_t levy{}, maa{};
  if (!Bucket(b, p, 0x28, "levy", out, out.levy_entries, levy) ||
      !Bucket(b, p, 0x40, "men_at_arms", out, out.men_at_arms_entries, maa))
    return false;
  const void *data{};
  std::int32_t count{};
  if (!Header(p, 0x58, 0x60, 0x64, data, count))
    return false;
  for (std::int32_t i = 0; i < count; ++i) {
    game::BattleControlParticipantHardSnapshot r{
        i, At<std::int32_t>(data, i * 0x18ULL + 8),
        At<std::int64_t>(data, i * 0x18ULL + 0x10)};
    if (!Resolve(b.character_storage_slot, r.participant_character_id, 0x18) ||
        r.hard_casualties_raw < 0 ||
        !Add(out.participant_hard_total_raw, r.hard_casualties_raw))
      return false;
    out.participant_hard_ledger.push_back(r);
  }
  out.stored_current_fighting_raw = At<std::int64_t>(p, 0x98);
  out.stored_levy_current_fighting_raw = At<std::int64_t>(p, 0xA0);
  out.stored_current_matches_derived =
      out.stored_current_fighting_raw == out.derived_current_fighting_raw;
  out.stored_levy_current_matches_derived =
      out.stored_levy_current_fighting_raw == levy;
  out.side_strength_raw =
      b.get_combat_side_strength(const_cast<std::byte *>(p));
  return true;
}
bool Retreat(const BattleBindings &b, const game::Snapshot &scope, void *combat,
             void *army, game::BattleControlSnapshot &out) {
  auto selected = out.selected_native_carmy_id;
  auto contains = [&](const auto &side) {
    return std::any_of(side.ordered_armies.begin(), side.ordered_armies.end(),
                       [&](auto &r) { return r.native_carmy_id == selected; });
  };
  bool a = contains(out.attacker), d = contains(out.defender);
  if (a == d)
    return false;
  out.side_index = d ? 1 : 0;
  const auto &side = d ? out.defender : out.attacker;
  auto *p = static_cast<std::byte *>(combat) + (d ? 0x368 : 0x20);
  auto f0 = At<std::uint8_t>(p, 0xC0), f1 = At<std::uint8_t>(p, 0xC1),
       f2 = At<std::uint8_t>(p, 0xC2);
  if (f0 > 1 || f1 > 1 || f2 > 1)
    return false;
  out.side_flags = {f0 != 0, f1 != 0, f2 != 0};
  auto owns = std::count_if(
      side.ordered_armies.begin(), side.ordered_armies.end(), [&](auto &r) {
        return r.owner_character_id == out.selected_owner_character_id;
      });
  out.side_scope =
      owns == static_cast<std::ptrdiff_t>(side.ordered_armies.size())
          ? "full_side"
          : "owner_subset";
  for (auto &r : side.ordered_armies)
    (r.owner_character_id == out.selected_owner_character_id
         ? out.affected_public_cunit_ids_in_stored_order
         : out.unaffected_same_side_public_cunit_ids_in_stored_order)
        .push_back(r.public_cunit_id);
  auto *result =
      out.battle_result_id == -1
          ? (b.battle_result_fallback_slot ? *b.battle_result_fallback_slot
                                           : nullptr)
          : Resolve(b.battle_result_storage_slot, out.battle_result_id, 8);
  auto *owner =
      Resolve(b.character_storage_slot, out.selected_owner_character_id, 0x18);
  if (!result || !owner || !b.get_combat_retreat_rule_state ||
      !b.can_order_combat_retreat || !b.minimum_days_before_manual_retreat)
    return false;
  auto *land = At<void *>(owner, kBattleLandStatusOffset);
  void *rules = nullptr;
  if (land && At<std::int32_t>(land, 0x1F8) == -1) {
    rules = b.get_combat_retreat_rule_state(owner);
    if (!rules)
      return false;
  }
  auto &l = out.legality;
  l.status = "available";
  l.phase_raw = out.phase_raw;
  l.phase = out.phase;
  l.retreat_elapsed_baseline_date_raw = At<std::int32_t>(result, 0x2C);
  auto day = [](std::int32_t v) {
    return (static_cast<std::int64_t>(v) - 0x029C55C0) / 24;
  };
  l.elapsed_whole_days =
      day(scope.date_raw) - day(l.retreat_elapsed_baseline_date_raw);
  l.minimum_elapsed_whole_days_exclusive =
      *b.minimum_days_before_manual_retreat;
  l.landless_gate_allows_retreat =
      !land || At<std::int32_t>(land, 0x1F8) != -1 ||
      (rules &&
       (At<std::uint32_t>(rules, kBattleRuleFlagsOffset) & (1U << 10)));
  auto reason = [&](const char *code, const char *key) {
    l.reason_codes_in_native_order.emplace_back(code);
    l.native_reason_keys_in_native_order.emplace_back(key);
  };
  if (f0)
    reason("disallowed", "COMBAT_NO_RETREAT_DISALLOWED");
  if (!f1 && l.elapsed_whole_days <= l.minimum_elapsed_whole_days_exclusive)
    reason("too_early", "COMBAT_NO_RETREAT_TOO_EARLY");
  if (out.phase_raw >= 2)
    reason("pursuit_or_done", "COMBAT_NO_RETREAT_PURSUIT");
  if (!l.landless_gate_allows_retreat)
    reason("landless", "COMBAT_NO_RETREAT_LANDLESS");
  l.native_boolean = b.can_order_combat_retreat(combat, army, nullptr);
  l.legal_now = l.reason_codes_in_native_order.empty();
  l.earliest_day_gate_date_raw =
      0x029C55C0 + (day(l.retreat_elapsed_baseline_date_raw) +
                    l.minimum_elapsed_whole_days_exclusive + 1) *
                       24;
  return l.legal_now == l.native_boolean;
}
bool ControlSample(const BattleBindings &b, const game::Snapshot &scope,
                   const game::BattleControlRequest &req,
                   game::BattleControlSnapshot &out) {
  auto *unit = Resolve(b.army_storage_slot, req.subject_public_cunit_id, 0x10);
  if (!unit)
    return false;
  auto aid = At<std::int32_t>(unit, 0x178);
  auto *army = Resolve(b.army_internal_storage_slot, aid, 0x10);
  if (!army || At<std::int32_t>(army, 0x124) != req.subject_public_cunit_id)
    return false;
  auto cid = At<std::int32_t>(army, 0x128);
  auto *combat = Resolve(b.combat_storage_slot, cid, 8);
  if (!combat)
    return false;
  game::BattleTransitionSnapshot t{};
  if (!TransitionSample(b, {cid}, t) ||
      t.status != game::BattleTransitionSnapshotStatus::available)
    return false;
  out = {};
  out.subject_public_cunit_id = req.subject_public_cunit_id;
  out.subject_native_carmy_id = aid;
  out.combat_id = cid;
  out.selected_public_cunit_id = req.subject_public_cunit_id;
  out.selected_native_carmy_id = aid;
  out.selected_owner_character_id = At<std::int32_t>(unit, 0x174);
  out.province_id = t.province_id;
  out.combat_province_id = t.province_id;
  out.phase = t.phase;
  out.phase_raw = t.phase_raw;
  out.phase_day = t.phase_day;
  out.winner_side = t.winner_side;
  out.winner_raw = t.winner_raw;
  out.forced_winner_side = t.forced_winner_side;
  out.forced_winner_raw = t.forced_winner_raw;
  out.finalized = t.finalized;
  out.battle_result_id = t.battle_result_id;
  out.base_combat_width = At<std::int32_t>(combat, 0x6C0);
  out.final_combat_width = At<std::int32_t>(combat, 0x6C4);
  out.roll_cadence_counter = At<std::int32_t>(combat, 0x6E4);
  out.base_advantage_raw = At<std::int64_t>(combat, 0x6C8);
  out.resolved_advantage_raw = At<std::int64_t>(combat, 0x710);
  return Side(b, combat, 0x20, cid, 0, out.attacker) &&
         Side(b, combat, 0x368, cid, 1, out.defender) &&
         Retreat(b, scope, combat, army, out) &&
         !At<std::uint8_t>(combat, kBattleDailyGuardOffset);
}
bool Route(const BattleBindings &b, const void *unit,
           game::BattleReinforcementRouteSnapshot &out) {
  auto *current = Province(b, At<void *>(unit, 0x20));
  if (!current)
    return false;
  out.current_province_id = At<std::int32_t>(current, 0x10);
  const void *data{};
  std::int32_t count{};
  if (!Header(unit, 0x38, 0x40, 0x44, data, count, 2048))
    return false;
  for (std::int32_t i = 0; i < count; ++i) {
    auto *info = At<void *>(data, i * 8ULL);
    if (!info)
      return false;
    auto id = At<std::int32_t>(info, 0);
    if (!b.resolve_province || !b.resolve_province(b.province_context, id))
      return false;
    out.route_province_ids.push_back(id);
  }
  // Native destination getter 0x24AA820 reads the last committed path entry;
  // an empty path returns the null Province. +0x30 is contact adjacency state.
  if (!out.route_province_ids.empty())
    out.move_target_province_id = out.route_province_ids.back();
  return true;
}
bool ReinforcementSample(const BattleBindings &b, const game::Snapshot &scope,
                         const game::BattleReinforcementAssignmentRequest &req,
                         game::BattleReinforcementAssignmentSnapshot &out) {
  out = {};
  out.selected_public_cunit_id = req.selected_public_cunit_id;
  auto *unit = Resolve(b.army_storage_slot, req.selected_public_cunit_id, 0x10);
  if (!unit) {
    out.unavailable_reason = "subject_cunit_not_found";
    return false;
  }
  auto aid = At<std::int32_t>(unit, 0x178);
  auto *army = Resolve(b.army_internal_storage_slot, aid, 0x10);
  if (!army || At<std::int32_t>(army, 0x124) != req.selected_public_cunit_id) {
    out.unavailable_reason = "army_backlink_mismatch";
    return false;
  }
  out.selected_native_carmy_id = aid;
  auto coordinator_id = At<std::int32_t>(unit, 0x1C4);
  auto *coordinator =
      Resolve(b.ai_war_coordinator_storage_slot, coordinator_id, 0x10);
  auto *subunit = At<void *>(unit, 0x1D0);
  if (!coordinator ||
      At<std::uintptr_t>(coordinator, 0) != b.ai_war_coordinator_vtable ||
      !subunit || At<std::uintptr_t>(subunit, 0) != b.ai_subunit_stack_vtable) {
    out.unavailable_reason = "ai_assignment_not_bound";
    return false;
  }
  auto *parent = At<void *>(subunit, kBattleSubunitParentOffset);
  if (!parent || At<std::uintptr_t>(parent, 0) != b.ai_unit_stack_vtable ||
      At<void *>(parent, 0x58) != coordinator) {
    out.unavailable_reason = "parent_coordinator_mismatch";
    return false;
  }
  const void *ids{};
  std::int32_t id_count{};
  if (!Header(subunit, 0x10, 0x18, 0x1C, ids, id_count, 128))
    return false;
  bool found = false;
  for (std::int32_t i = 0; i < id_count; ++i) {
    auto id = At<std::int32_t>(ids, i * 4ULL);
    if (!Resolve(b.army_storage_slot, id, 0x10))
      return false;
    found |= id == req.selected_public_cunit_id;
  }
  if (!found) {
    out.unavailable_reason = "subunit_backlink_mismatch";
    return false;
  }
  const void *stacks{};
  std::int32_t stack_count{};
  if (!Header(coordinator, 0x50, 0x58, 0x5C, stacks, stack_count, 2048))
    return false;
  for (std::int32_t i = 0; i < stack_count; ++i)
    if (At<void *>(stacks, i * 8ULL) == parent)
      out.unit_stack_stored_index = i;
  if (!out.unit_stack_stored_index) {
    out.unavailable_reason = "parent_membership_mismatch";
    return false;
  }
  const void *subunits{};
  std::int32_t count{};
  if (!Header(parent, 0x40, 0x48, 0x4C, subunits, count, 2048))
    return false;
  game::BattleReinforcementNativeOrderSnapshot order{};
  for (std::int32_t i = 0; i < count; ++i) {
    auto *s = At<void *>(subunits, i * 8ULL);
    if (!s || At<std::uintptr_t>(s, 0) != b.ai_subunit_stack_vtable ||
        At<void *>(s, 0x38) != parent)
      return false;
    if (s == subunit)
      out.subunit_stored_index = i;
    game::BattleReinforcementParentSubunitSnapshot row{};
    const void *u{};
    std::int32_t n{};
    if (!Header(s, 0x10, 0x18, 0x1C, u, n, 128))
      return false;
    for (std::int32_t j = 0; j < n; ++j) {
      auto id = At<std::int32_t>(u, j * 4ULL);
      if (!Resolve(b.army_storage_slot, id, 0x10))
        return false;
      row.public_cunit_ids_in_stored_order.push_back(id);
    }
    auto flags = At<std::uint8_t>(s, 0x48);
    row.asking_for_help = flags & 1;
    row.assigned_to_help = flags & 2;
    auto *target = At<void *>(s, 0x40);
    if (row.assigned_to_help) {
      if (!Province(b, target))
        return false;
      row.assignment_target_province_id = At<std::int32_t>(target, 0x10);
    }
    order.parent_subunits_in_stored_order.push_back(std::move(row));
  }
  if (!out.subunit_stored_index) {
    out.unavailable_reason = "subunit_membership_mismatch";
    return false;
  }
  const void *provinces{};
  std::int32_t province_count{};
  if (!Header(parent, 0x08, 0x10, 0x14, provinces, province_count, 2048))
    return false;
  for (std::int32_t i = 0; i < province_count; ++i) {
    auto *p = Province(b, At<void *>(provinces, i * 8ULL));
    if (!p)
      return false;
    order.support_search_province_ids_in_stored_order.push_back(
        At<std::int32_t>(p, 0x10));
  }
  game::BattleReinforcementSignalSnapshot signal{};
  auto flags = At<std::uint8_t>(subunit, kBattleSubunitFlagsOffset);
  signal.asking_for_help = flags & 1;
  signal.assigned_to_help = flags & 2;
  signal.asking_changed_last_evaluation = flags & 0x10;
  if (signal.asking_for_help)
    signal.request_power_basis_raw = At<std::int64_t>(subunit, 0x28);
  signal.cross_coordinator_request_valid_raw =
      At<std::uint8_t>(subunit, kBattleSubunitCrossValidityOffset);
  if (signal.cross_coordinator_request_valid_raw)
    signal.cross_coordinator_request_power_raw =
        At<std::int64_t>(subunit, kBattleSubunitCrossPowerOffset);
  game::BattleReinforcementAssignmentStateSnapshot assignment{};
  auto *target = At<void *>(subunit, kBattleSubunitTargetOffset);
  if (signal.assigned_to_help) {
    if (!Province(b, target))
      return false;
    assignment.assignment_target_province_id = At<std::int32_t>(target, 0x10);
    assignment.target_provenance = "native_help_override";
  }
  auto cid = At<std::int32_t>(army, 0x128);
  if (auto *combat = Resolve(b.combat_storage_slot, cid, 8);
      combat && !At<std::uint8_t>(combat, kBattleFinalizedOffset)) {
    assignment.active_combat_id = cid;
    assignment.combat_binding_status = "already_in_active_combat";
  }
  game::BattleReinforcementRouteSnapshot route{};
  if (!Route(b, unit, route))
    return false;
  std::vector<std::int32_t> projected, arrivals;
  bool timeline_available =
      ReadCommittedRouteTimeline(b.route_bindings, scope,
                                 req.selected_public_cunit_id, projected,
                                 arrivals) &&
      projected == route.route_province_ids;
  if (timeline_available)
    route.arrival_date_raws = arrivals;
  bool aligned = assignment.assignment_target_province_id &&
                 (route.route_province_ids.empty()
                      ? route.current_province_id ==
                            *assignment.assignment_target_province_id
                      : route.route_province_ids.back() ==
                            *assignment.assignment_target_province_id);
  route.route_alignment = !assignment.assignment_target_province_id
                              ? "no_assignment"
                          : !aligned            ? "not_aligned"
                          : !timeline_available ? "timeline_unavailable"
                                                : "aligned_to_assignment";
  if (aligned && timeline_available)
    route.assignment_eta_date_raw =
        arrivals.empty() ? scope.date_raw : arrivals.back();
  if (!route.route_province_ids.empty() && b.read_route_edge_duration) {
    std::int64_t raw{};
    if (b.read_route_edge_duration(unit, &raw, 0) == &raw)
      signal.first_route_edge_remaining_duration_q100000 = raw;
  }
  game::BattleReinforcementContactProjectionSnapshot projection{};
  if (assignment.assignment_target_province_id) {
    projection.status = "unavailable";
    auto *p =
        b.resolve_province
            ? b.resolve_province(b.province_context,
                                 *assignment.assignment_target_province_id)
            : nullptr;
    auto *owner =
        Resolve(b.character_storage_slot, At<std::int32_t>(unit, 0x174), 0x18);
    const void *combat_data{};
    std::int32_t combat_count{};
    bool valid =
        p && owner && b.route_bindings.is_character_hostile &&
        Header(p, 0x758, 0x760, 0x764, combat_data, combat_count, 1024);
    if (valid) {
      for (std::int32_t i = 0; i < combat_count; ++i) {
        auto candidate_id = At<std::int32_t>(combat_data, i * 4ULL);
        auto *c = Resolve(b.combat_storage_slot, candidate_id, 8);
        if (!c || At<void *>(c, 0x6B8) != p) {
          valid = false;
          break;
        }
        if (At<std::uint8_t>(c, 0x704))
          continue;
        auto *a = Resolve(b.character_storage_slot, At<std::int32_t>(c, 0x90),
                          0x18),
             *d = Resolve(b.character_storage_slot, At<std::int32_t>(c, 0x3D8),
                          0x18);
        if (!a || !d) {
          valid = false;
          break;
        }
        if (b.route_bindings.is_character_hostile(owner, a, false) !=
            b.route_bindings.is_character_hostile(owner, d, false))
          projection.current_target_compatible_combat_ids_in_stored_order
              .push_back(candidate_id);
      }
      if (valid) {
        projection.status = "available";
        if (!projection.current_target_compatible_combat_ids_in_stored_order
                 .empty())
          projection.contact_if_now_selected_combat_id =
              projection.current_target_compatible_combat_ids_in_stored_order
                  .back();
      } else
        projection.current_target_compatible_combat_ids_in_stored_order.clear();
    }
  }
  out.coordinator_id = coordinator_id;
  out.signal = std::move(signal);
  out.assignment = std::move(assignment);
  out.route = std::move(route);
  out.native_order = std::move(order);
  out.contact_projection = std::move(projection);
  out.status = game::BattleReinforcementAssignmentStatus::available;
  out.battle_reinforcement_assignment_ready = true;
  return true;
}
bool TerminalSample(const BattleBindings &b, const game::Snapshot &scope,
                    const game::BattleTerminalTransitionRequestV1 &r,
                    game::BattleTerminalTransitionSnapshotV1 &o) {
  o = {};
  o.prior_combat_id = r.prior_combat_id;
  o.subject_public_cunit_id = r.subject_public_cunit_id;
  o.prior.combat_id = r.prior_combat_id;
  auto j = LookupBattleTerminalJournalV1(r.prior_combat_id,
                                         r.after_terminal_sequence.value_or(0));
  o.terminal_journal.requested_after_sequence = r.after_terminal_sequence;
  o.terminal_journal.oldest_available_sequence = j.oldest_available_sequence;
  o.terminal_journal.latest_sequence = j.latest_sequence;
  auto fail = [&](const char *reason) {
    o.unavailable_reason = reason;
    return true;
  };
  if (j.status == BattleTerminalJournalLookupStatusV1::invalid_cursor)
    return fail("invalid_request");
  if (j.status == BattleTerminalJournalLookupStatusV1::journal_gap)
    return fail("journal_gap");
  if (j.status == BattleTerminalJournalLookupStatusV1::unavailable)
    return fail("journal_unavailable");
  auto *prior = Resolve(b.combat_storage_slot, r.prior_combat_id, 8);
  o.removal.prior_combat_strictly_resolves = prior != nullptr;
  if (j.status == BattleTerminalJournalLookupStatusV1::observed) {
    auto &e = j.event;
    if (e.capture_failure_flags)
      return fail("journal_capture_incomplete");
    o.terminal_journal.event_sequence = e.sequence;
    o.terminal_journal.event_status =
        game::BattleTerminalJournalEventStatusV1::observed;
    auto &p = o.prior;
    p.terminal_kind = e.suppress_normal_result_envelopes
                          ? game::BattleTerminalKindV1::no_normal_result
                          : game::BattleTerminalKindV1::normal_result;
    p.suppress_normal_result_envelopes = e.suppress_normal_result_envelopes;
    p.phase_raw = e.phase_raw;
    p.winner_raw = e.winner_raw;
    p.finalized_before = e.finalized_before;
    p.daily_guard_raw = e.daily_guard_raw;
    p.province_id = e.province_id;
    p.battle_result_id = e.battle_result_id;
    if (e.wipe_raw_observable)
      p.wipe_raw = e.wipe_raw;
    p.attacker_primary_participant_character_id =
        e.attacker_primary_participant_character_id;
    p.defender_primary_participant_character_id =
        e.defender_primary_participant_character_id;
    p.attacker_public_cunit_ids_in_stored_order = std::vector<std::int32_t>(
        e.attacker_public_cunit_ids_in_stored_order.begin(),
        e.attacker_public_cunit_ids_in_stored_order.begin() +
            e.attacker_public_cunit_count);
    p.defender_public_cunit_ids_in_stored_order = std::vector<std::int32_t>(
        e.defender_public_cunit_ids_in_stored_order.begin(),
        e.defender_public_cunit_ids_in_stored_order.begin() +
            e.defender_public_cunit_count);
    auto w = LookupBattleWarscoreJournalV1(r.prior_combat_id);
    auto &ws = p.battle_warscore;
    if (e.suppress_normal_result_envelopes)
      ws.status = game::BattleTerminalWarscoreStatusV1::not_recorded_by_native;
    else if (w.status == BattleWarscoreJournalLookupStatusV1::observed &&
             !w.event.capture_failure_flags) {
      ws.status = game::BattleTerminalWarscoreStatusV1::recorded;
      ws.war_id = w.event.war_id;
      ws.war_battle_row_index = w.event.war_battle_row_index;
      ws.value_raw_q100000 = w.event.battle_warscore_value_raw;
      ws.winner_is_war_attacker = w.event.winner_is_war_attacker;
      ws.combat_side0_is_war_attacker = w.event.combat_side0_is_war_attacker;
      ws.attacker_relative_delta_raw_q100000 =
          w.event.winner_is_war_attacker ? w.event.battle_warscore_value_raw
                                         : -w.event.battle_warscore_value_raw;
    } else if (w.status == BattleWarscoreJournalLookupStatusV1::not_observed)
      ws.status = game::BattleTerminalWarscoreStatusV1::not_recorded_by_native;
  } else if (prior) {
    game::BattleTransitionSnapshot t{};
    if (!TransitionSample(b, {r.prior_combat_id}, t) ||
        t.status != game::BattleTransitionSnapshotStatus::available)
      return false;
    if (t.finalized)
      return fail("terminal_event_not_observed");
    auto &p = o.prior;
    p.terminal_kind = game::BattleTerminalKindV1::active_not_terminal;
    p.phase_raw = t.phase_raw;
    p.winner_raw = t.winner_raw;
    p.finalized_before = t.finalized;
    p.daily_guard_raw = At<std::uint8_t>(prior, 0x705);
    p.province_id = t.province_id;
    p.battle_result_id = t.battle_result_id;
    p.attacker_primary_participant_character_id = At<std::int32_t>(prior, 0x90);
    p.defender_primary_participant_character_id =
        At<std::int32_t>(prior, 0x3D8);
    p.attacker_public_cunit_ids_in_stored_order =
        std::move(t.attacker_public_cunit_ids_in_stored_order);
    p.defender_public_cunit_ids_in_stored_order =
        std::move(t.defender_public_cunit_ids_in_stored_order);
  }
  void *province = nullptr;
  std::vector<std::int32_t> province_combats;
  if (o.prior.province_id && b.resolve_province) {
    province = b.resolve_province(b.province_context, *o.prior.province_id);
    o.removal.prior_province_strictly_resolves = province != nullptr;
    if (province) {
      const void *data{};
      std::int32_t n{};
      if (!Header(province, 0x758, 0x760, 0x764, data, n, 1024))
        return false;
      for (std::int32_t i = 0; i < n; ++i)
        province_combats.push_back(At<std::int32_t>(data, i * 4ULL));
      o.removal.prior_province_contains_prior_combat_id =
          std::find(province_combats.begin(), province_combats.end(),
                    r.prior_combat_id) != province_combats.end();
    }
  }
  if (o.prior.battle_result_id) {
    auto *result =
        Resolve(b.battle_result_storage_slot, *o.prior.battle_result_id, 8);
    o.removal.result_strictly_resolves = result != nullptr;
    if (result) {
      auto n = At<std::int32_t>(result, 0xC4);
      if (n < 0 || n > 1'000'000)
        return false;
      o.removal.result_relevant_player_count = n;
    }
  }
  auto *unit = Resolve(b.army_storage_slot, r.subject_public_cunit_id, 0x10);
  o.subject.exists = unit != nullptr;
  if (!unit) {
    o.successor.state = game::BattleTerminalSuccessorStateV1::subject_missing;
  } else {
    game::BattleReinforcementRouteSnapshot route{};
    if (!Route(b, unit, route))
      return false;
    o.subject.current_province_id = route.current_province_id;
    o.subject.move_target_province_id = route.move_target_province_id;
    o.subject.route_province_ids_in_stored_order =
        std::move(route.route_province_ids);
    o.subject.movement_or_retreat_state_raw = At<std::int32_t>(unit, 0x170);
    auto aid = At<std::int32_t>(unit, 0x178);
    if (aid > 0) {
      auto *army = Resolve(b.army_internal_storage_slot, aid, 0x10);
      if (!army || At<std::int32_t>(army, 0x124) != r.subject_public_cunit_id)
        return false;
      o.subject.native_carmy_id = aid;
      auto cid = At<std::int32_t>(army, 0x128);
      if (cid > 0) {
        o.subject.combat_backlink_id = cid;
        auto *c = Resolve(b.combat_storage_slot, cid, 8);
        if (c && !At<std::uint8_t>(c, 0x704))
          o.subject.active_combat_id = cid;
      }
    }
    o.subject.blocked_by_active_combat = o.subject.active_combat_id.has_value();
    game::BattleReinforcementAssignmentSnapshot reinforcement{};
    if (ReinforcementSample(b, scope, {r.subject_public_cunit_id},
                            reinforcement)) {
      o.subject.ai_membership_status =
          game::BattleTerminalAiMembershipStatusV1::observed;
      o.subject.coordinator_id = reinforcement.coordinator_id;
      o.subject.unit_stack_stored_index = reinforcement.unit_stack_stored_index;
      o.subject.subunit_stored_index = reinforcement.subunit_stored_index;
    } else if (At<std::int32_t>(unit, 0x1C4) == -1)
      o.subject.ai_membership_status =
          game::BattleTerminalAiMembershipStatusV1::none;
    if (o.prior.terminal_kind !=
            game::BattleTerminalKindV1::active_not_terminal &&
        province && o.prior.attacker_public_cunit_ids_in_stored_order &&
        o.prior.defender_public_cunit_ids_in_stored_order) {
      auto overlaps = [&](const auto &candidate, std::int32_t id) {
        return std::find(
                   candidate.attacker_public_cunit_ids_in_stored_order.begin(),
                   candidate.attacker_public_cunit_ids_in_stored_order.end(),
                   id) !=
                   candidate.attacker_public_cunit_ids_in_stored_order.end() ||
               std::find(
                   candidate.defender_public_cunit_ids_in_stored_order.begin(),
                   candidate.defender_public_cunit_ids_in_stored_order.end(),
                   id) !=
                   candidate.defender_public_cunit_ids_in_stored_order.end();
      };
      for (auto cid : province_combats) {
        if (cid == r.prior_combat_id)
          continue;
        game::BattleTransitionSnapshot t{};
        if (!TransitionSample(b, {cid}, t) ||
            t.status != game::BattleTransitionSnapshotStatus::available)
          return false;
        if (t.finalized)
          continue;
        bool match =
            std::any_of(
                o.prior.attacker_public_cunit_ids_in_stored_order->begin(),
                o.prior.attacker_public_cunit_ids_in_stored_order->end(),
                [&](auto id) { return overlaps(t, id); }) ||
            std::any_of(
                o.prior.defender_public_cunit_ids_in_stored_order->begin(),
                o.prior.defender_public_cunit_ids_in_stored_order->end(),
                [&](auto id) { return overlaps(t, id); });
        if (match) {
          o.successor.matching_combat_ids_in_native_order.push_back(cid);
          if (o.subject.active_combat_id == cid) {
            o.successor.selected_successor_combat_id = cid;
            for (auto id : *o.prior.attacker_public_cunit_ids_in_stored_order)
              if (overlaps(t, id))
                o.successor.participant_overlap_public_cunit_ids_in_prior_order
                    .push_back(id);
            for (auto id : *o.prior.defender_public_cunit_ids_in_stored_order)
              if (overlaps(t, id))
                o.successor.participant_overlap_public_cunit_ids_in_prior_order
                    .push_back(id);
          }
        }
      }
      if (o.successor.selected_successor_combat_id)
        o.successor.state =
            game::BattleTerminalSuccessorStateV1::residual_new_combat;
      else if (o.subject.movement_or_retreat_state_raw.value_or(0) > 0)
        o.successor.state =
            game::BattleTerminalSuccessorStateV1::subject_retreating;
      else if (!o.subject.active_combat_id &&
               o.successor.matching_combat_ids_in_native_order.empty()) {
        if (o.subject.ai_membership_status ==
            game::BattleTerminalAiMembershipStatusV1::observed)
          o.successor.state =
              game::BattleTerminalSuccessorStateV1::subject_assignment_reopened;
        else if (o.subject.ai_membership_status ==
                 game::BattleTerminalAiMembershipStatusV1::none)
          o.successor.state =
              game::BattleTerminalSuccessorStateV1::no_successor;
      }
    }
  }
  o.status = game::BattleTerminalTransitionStatusV1::available;
  o.battle_terminal_transition_ready = true;
  return true;
}
} // namespace

BattleBindings BindBattleImage(std::uintptr_t base,
                               std::string_view sha) noexcept {
  BattleBindings b{};
  if (!base || sha != kExecutableSha256)
    return b;
  b.enabled = true;
  b.game_state_slot = reinterpret_cast<void **>(base + kGameStateSlotRva);
  b.jomini_state_slot = reinterpret_cast<void **>(base + kJominiStateSlotRva);
  b.army_storage_slot = reinterpret_cast<void **>(base + 0x5D1E380);
  b.army_internal_storage_slot = reinterpret_cast<void **>(base + 0x5D1DE48);
  b.regiment_storage_slot = reinterpret_cast<void **>(base + 0x5D1F340);
  b.character_storage_slot =
      reinterpret_cast<void **>(base + kCharacterStorageSlotRva);
  b.combat_storage_slot =
      reinterpret_cast<void **>(base + kBattleCombatStorageRva);
  b.battle_result_storage_slot =
      reinterpret_cast<void **>(base + kBattleResultStorageRva);
  b.battle_result_fallback_slot =
      reinterpret_cast<void **>(base + kBattleResultFallbackRva);
  b.ai_war_coordinator_storage_slot =
      reinterpret_cast<void **>(base + 0x5D204F0);
  b.ai_unit_stack_vtable = base + 0x45AA608;
  b.ai_subunit_stack_vtable = base + 0x45AB4B0;
  b.ai_war_coordinator_vtable = base + 0x45AB0B8;
  b.minimum_days_before_manual_retreat = reinterpret_cast<const std::int32_t *>(
      base + kBattleMinimumRetreatDaysRva);
  b.get_combat_side_strength =
      reinterpret_cast<decltype(b.get_combat_side_strength)>(
          base + kBattleSideStrengthRva);
  b.get_combat_regiment_strength =
      reinterpret_cast<decltype(b.get_combat_regiment_strength)>(
          base + kBattleEntryStrengthRva);
  b.can_order_combat_retreat =
      reinterpret_cast<decltype(b.can_order_combat_retreat)>(
          base + kBattleCanRetreatRva);
  b.get_combat_retreat_rule_state =
      reinterpret_cast<decltype(b.get_combat_retreat_rule_state)>(
          base + kBattleRetreatRuleRva);
  b.read_route_edge_duration =
      reinterpret_cast<decltype(b.read_route_edge_duration)>(base + 0x24AB060);
  b.route_bindings = BindRouteImage(base, sha);
  b.province_context = b.game_state_slot;
  b.resolve_province = NativeProvince;
  return b;
}
game::BattleTransitionSnapshotStatus
ReadBattleTransitionSnapshot(const BattleBindings &b, const game::Snapshot &s,
                             const game::BattleTransitionRequest &r,
                             game::BattleTransitionSnapshot &o) noexcept {
  o = {};
  o.combat_id = r.combat_id;
  if (!Scope(b, s) || r.combat_id <= 0)
    return o.status;
  game::BattleTransitionSnapshot a{}, c{};
  if (!TransitionSample(b, r, a) || !TransitionSample(b, r, c) || a != c ||
      !Scope(b, s)) {
    o.status = game::BattleTransitionSnapshotStatus::state_changed;
    return o.status;
  }
  o = std::move(c);
  o.observed_date_raw = s.date_raw;
  return o.status;
}
game::BattleControlSnapshotStatus
ReadBattleControlSnapshot(const BattleBindings &b, const game::Snapshot &s,
                          const game::BattleControlRequest &r,
                          game::BattleControlSnapshot &o) noexcept {
  o = {};
  o.subject_public_cunit_id = r.subject_public_cunit_id;
  if (!s.paused) {
    o.status = game::BattleControlSnapshotStatus::requires_paused;
    return o.status;
  }
  if (!Scope(b, s) || !b.get_combat_side_strength ||
      !b.get_combat_regiment_strength || r.subject_public_cunit_id < 0)
    return o.status;
  auto army = std::find_if(
      s.player_armies.begin(), s.player_armies.end(),
      [&](auto &a) { return a.army_id == r.subject_public_cunit_id; });
  if (army == s.player_armies.end()) {
    o.status = game::BattleControlSnapshotStatus::subject_cunit_not_found;
    return o.status;
  }
  if (!army->controllable) {
    o.status = game::BattleControlSnapshotStatus::subject_not_controllable;
    return o.status;
  }
  if (army->retreating) {
    o.status = game::BattleControlSnapshotStatus::subject_retreating;
    return o.status;
  }
  if (!army->in_combat) {
    o.status = game::BattleControlSnapshotStatus::subject_not_in_combat;
    return o.status;
  }
  game::BattleControlSnapshot a{}, c{};
  if (!ControlSample(b, s, r, a) || !ControlSample(b, s, r, c) || a != c ||
      !Scope(b, s)) {
    o.status = game::BattleControlSnapshotStatus::state_changed;
    return o.status;
  }
  o = std::move(c);
  o.status = game::BattleControlSnapshotStatus::available;
  o.observed_date_raw = s.date_raw;
  o.battle_control_ready = true;
  return o.status;
}
game::BattleReinforcementAssignmentStatus ReadBattleReinforcementAssignmentV1(
    const BattleBindings &b, const game::Snapshot &s,
    const game::BattleReinforcementAssignmentRequest &r,
    game::BattleReinforcementAssignmentSnapshot &o) noexcept {
  o = {};
  o.selected_public_cunit_id = r.selected_public_cunit_id;
  o.observed_date_raw = s.date_raw;
  if (!Scope(b, s) || r.selected_public_cunit_id < 0) {
    o.unavailable_reason =
        s.paused ? "unsupported_build_or_state_changed" : "requires_paused";
    return o.status;
  }
  game::BattleReinforcementAssignmentSnapshot a{}, c{};
  auto ar = ReinforcementSample(b, s, r, a),
       cr = ReinforcementSample(b, s, r, c);
  if (ar != cr || a != c || !Scope(b, s)) {
    o.unavailable_reason = "state_changed";
    return o.status;
  }
  o = std::move(c);
  o.observed_date_raw = s.date_raw;
  if (!cr && o.unavailable_reason.empty())
    o.unavailable_reason = "state_changed";
  return o.status;
}
game::BattleTerminalTransitionStatusV1 ReadBattleTerminalTransitionV1(
    const BattleBindings &b, const game::Snapshot &s,
    const game::BattleTerminalTransitionRequestV1 &r,
    game::BattleTerminalTransitionSnapshotV1 &o) noexcept {
  o = {};
  o.prior_combat_id = r.prior_combat_id;
  o.subject_public_cunit_id = r.subject_public_cunit_id;
  o.observed_date_raw = s.date_raw;
  if (!Scope(b, s) || r.prior_combat_id <= 0 ||
      r.subject_public_cunit_id < 0) {
    o.unavailable_reason =
        s.paused ? "invalid_request_or_state_changed" : "requires_paused";
    return o.status;
  }
  game::BattleTerminalTransitionSnapshotV1 a{}, c{};
  if (!TerminalSample(b, s, r, a) || !TerminalSample(b, s, r, c) || a != c ||
      !Scope(b, s)) {
    o.unavailable_reason = "state_changed";
    return o.status;
  }
  o = std::move(c);
  o.observed_date_raw = s.date_raw;
  return o.status;
}
} // namespace xar::ck3_12002

#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_battle_journal.hpp"
#include "xar_bridge/ck3_12002_phase.hpp"

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
    if (b.current_battle_knight_identity_enabled && r.bucket == "men_at_arms") {
      // Existing v2 ReadCombatKnights membership source and full-ID/backlink
      // semantics. -1 alone is native none; invalid identities fail this bucket.
      const auto knight_id = At<std::int32_t>(regiment, 0x148);
      if (knight_id != -1) {
        auto *knight = Resolve(b.character_storage_slot, knight_id, 0x18);
        if (knight_id <= 0 || !knight ||
            At<std::uint32_t>(knight, 0x1C) != 0x43686172U)
          return false;
        auto *link = At<void *>(knight, phase_character::kCharacterKnightLinkOffset);
        if (!link || At<std::int32_t>(link,
                phase_character::kKnightLinkRegimentIdOffset) != r.regiment_id)
          return false;
      }
      r.knight_character_id_raw = knight_id;
    }
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
          std::int32_t province_id, void *terrain, bool roll_applicable,
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
  if (roll_applicable) {
    out.selected_commander_next_roll_bounds =
        ReadSelectedCommanderNextRollBounds(
            b.commander_roll_context, province_id, terrain,
            out.selected_commander_character_id);
  } else {
    out.selected_commander_next_roll_bounds.unavailable_reason =
        "next_main_roll_not_applicable_in_phase";
  }
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
std::optional<bool> FirstArmyOwnerLandRuleAllows(
    const BattleBindings &b, const void *army) {
  if (!army)
    return std::nullopt;
  auto *unit = Resolve(b.army_storage_slot,
                       At<std::int32_t>(army, 0x124), 0x10);
  if (!unit)
    return std::nullopt;
  auto *owner = Resolve(b.character_storage_slot,
                        At<std::int32_t>(unit, 0x174), 0x18);
  if (!owner)
    return std::nullopt;
  auto *land = At<void *>(owner, kBattleLandStatusOffset);
  if (!land || At<std::int32_t>(land, 0x1F8) != -1)
    return true;
  if (!b.get_combat_retreat_rule_state)
    return std::nullopt;
  auto *rules = b.get_combat_retreat_rule_state(owner);
  if (!rules)
    return std::nullopt;
  return (At<std::uint32_t>(rules, kBattleRuleFlagsOffset) & (1U << 10)) != 0;
}

std::optional<game::BattleControlCurrentPhaseTransitionInputsV1>
CurrentPhaseTransitionInputs(const BattleBindings &b, void *combat,
                             const game::BattleControlSnapshot &snapshot) {
  if (!b.minimum_days_before_manual_retreat)
    return std::nullopt;

  game::BattleControlCurrentPhaseTransitionInputsV1 out{};
  out.forced_winner_raw = snapshot.forced_winner_raw;
  out.result_start_date_raw =
      snapshot.legality.retreat_elapsed_baseline_date_raw;
  out.minimum_elapsed_days =
      snapshot.legality.minimum_elapsed_whole_days_exclusive;
  const std::array<const game::BattleControlSideSnapshot *, 2> snapshots{
      &snapshot.attacker, &snapshot.defender};
  const std::array<const void *, 2> sides{
      static_cast<std::byte *>(combat) + kBattleAttackerSideOffset,
      static_cast<std::byte *>(combat) + kBattleDefenderSideOffset};
  for (std::size_t index = 0; index < sides.size(); ++index) {
    auto &row = out.sides[index];
    row.side_index = static_cast<std::int32_t>(index);
    row.stored_current_fighting_raw = At<std::int64_t>(sides[index], 0x98);
    row.disallowed = At<std::uint8_t>(sides[index], 0xC0) != 0;
    row.allow_early = At<std::uint8_t>(sides[index], 0xC1) != 0;
    row.skip_pursuit = At<std::uint8_t>(sides[index], 0xC2) != 0;
    // This is the first stored native Army, independently of the selected Army.
    // Native empty-side resolution uses its actual canonical receiver.
    const auto &armies = snapshots[index]->ordered_armies;
    auto *first = armies.empty()
        ? (b.army_internal_fallback_slot ? *b.army_internal_fallback_slot
                                        : nullptr)
        : Resolve(b.army_internal_storage_slot,
                  armies.front().native_carmy_id, 0x10);
    if (!first)
      continue;
    row.first_native_carmy_id = At<std::int32_t>(first, 0x10);
    if (b.can_order_combat_retreat)
      row.native_can_retreat =
          b.can_order_combat_retreat(combat, first, nullptr);
    // A native fallback may lack an owner representable by the strict reader.
    // Its direct native Boolean remains observed independently of this leaf.
    row.owner_land_rule_allows = FirstArmyOwnerLandRuleAllows(b, first);
  }
  return out;
}

std::optional<game::BattleControlCurrentPursuitInputsV1> CurrentPursuitInputs(
    const BattleBindings &b, const void *combat,
    const game::BattleControlSnapshot &snapshot) {
  if (!b.pursuit_phase_days || !b.base_toughness_multiplier ||
      !b.minimum_pursuit_multiplier || !b.pursuit_stat_multiplier)
    return std::nullopt;

  game::BattleControlCurrentPursuitInputsV1 out{};
  out.source_combat_id = snapshot.combat_id;
  out.pursuit_phase_days = *b.pursuit_phase_days;
  out.base_toughness_multiplier_raw = *b.base_toughness_multiplier;
  out.minimum_pursuit_multiplier_raw = *b.minimum_pursuit_multiplier;
  out.pursuit_stat_multiplier_raw = *b.pursuit_stat_multiplier;
  // Pools are frozen only on entry into an active pursuit. Main-phase storage
  // can contain zero or prior data and is not an observed initialized pool.
  if (snapshot.phase_raw == 2 && !snapshot.finalized &&
      (snapshot.winner_raw == 0 || snapshot.winner_raw == 1)) {
    out.losing_side_index = 1 - snapshot.winner_raw;
    const auto losing_side_offset = *out.losing_side_index == 0
        ? kBattleAttackerSideOffset : kBattleDefenderSideOffset;
    out.losing_side_skip_pursuit =
        At<std::uint8_t>(combat, losing_side_offset + 0xC2) != 0;
    out.initial_loser_levy_soft_raw = At<std::int64_t>(combat, 0x6E8);
    out.initial_loser_maa_soft_raw = At<std::int64_t>(combat, 0x6F0);
  }
  return out;
}
std::optional<game::BattleControlCurrentLossInputsV1> CurrentLossInputs(
    const BattleBindings &b, void *combat, void *province,
    const game::BattleControlSnapshot &snapshot) {
  if (!b.damage_scaling || !b.main_hard_conversion ||
      !b.pursuit_hard_conversion || !b.read_loss_side_modifier ||
      !b.province_has_holding || !b.read_loss_province_modifier)
    return std::nullopt;

  game::BattleControlCurrentLossInputsV1 out{};
  out.source_combat_id = snapshot.combat_id;
  out.source_target_province_id = snapshot.province_id;
  out.stored_advantage_damage_factor_raw =
      At<std::int64_t>(combat, kBattleStoredAdvantageDamageFactorOffset);
  out.runtime_damage_scaling_raw = *b.damage_scaling;
  out.runtime_main_hard_conversion_raw = *b.main_hard_conversion;
  out.runtime_pursuit_hard_conversion_raw = *b.pursuit_hard_conversion;
  out.province_has_holding =
      At<std::uint32_t>(province, 0x85C) == 0x50726F76U &&
      b.province_has_holding(province);
  if (out.province_has_holding &&
      b.read_loss_province_modifier(
          &out.province_winter_hard_conversion_modifier_raw,
          static_cast<std::byte *>(province) + 0x30, 0x1AC, nullptr,
          100'000, 0) != &out.province_winter_hard_conversion_modifier_raw)
    return std::nullopt;

  const std::array<void *, 2> sides{
      static_cast<std::byte *>(combat) + kBattleAttackerSideOffset,
      static_cast<std::byte *>(combat) + kBattleDefenderSideOffset};
  const std::size_t advantaged_side = snapshot.resolved_advantage_raw > 0 ? 0 : 1;
  for (std::size_t index = 0; index < sides.size(); ++index) {
    auto &row = out.sides[index];
    row.side_index = static_cast<std::int32_t>(index);
    row.primary_participant_character_id =
        At<std::int32_t>(sides[index], 0x70);
    if (b.read_primary_levy_damage != nullptr) {
      auto *primary = Resolve(b.character_storage_slot,
                              row.primary_participant_character_id, 0x18);
      if (primary != nullptr) {
        std::int64_t scratch{};
        const auto *value = b.read_primary_levy_damage(&scratch, primary);
        if (value != nullptr)
          row.levy_damage_raw = At<std::int64_t>(value, 0);
      }
    }
    row.outgoing_advantage_factor_raw = index == advantaged_side
        ? out.stored_advantage_damage_factor_raw : 100'000;
    if (b.read_loss_side_modifier(&row.own_hard_conversion_modifier_raw,
                                 sides[index], 0x199) !=
            &row.own_hard_conversion_modifier_raw ||
        b.read_loss_side_modifier(&row.opposing_hard_conversion_modifier_raw,
                                 sides[1 - index], 0x19A) !=
            &row.opposing_hard_conversion_modifier_raw)
      return std::nullopt;
  }
  return out;
}

std::optional<game::BattleControlFullBackingInputsV1> FullBackingInputs(
    const BattleBindings &b, const game::BattleControlSnapshot &snapshot) {
  if (!b.full_backing_inputs_enabled)
    return std::nullopt;

  game::BattleControlFullBackingInputsV1 out{};
  out.source_combat_id = snapshot.combat_id;
  out.source_target_province_id = snapshot.province_id;
  const std::array<const game::BattleControlSideSnapshot *, 2> sides{
      &snapshot.attacker, &snapshot.defender};
  for (std::size_t side_index = 0; side_index < sides.size(); ++side_index) {
    auto &side = out.sides[side_index];
    side.side_index = static_cast<std::int32_t>(side_index);
    for (const auto &identity : sides[side_index]->ordered_armies) {
      auto *army = Resolve(b.army_internal_storage_slot,
                           identity.native_carmy_id, 0x10);
      if (!army)
        return std::nullopt;
      const void *data{};
      std::int32_t count{};
      if (!Header(army, 0x38, 0x40, 0x44, data, count))
        return std::nullopt;
      game::BattleControlFullBackingArmyV1 row{};
      row.native_carmy_id = identity.native_carmy_id;
      row.public_cunit_id = identity.public_cunit_id;
      row.owner_character_id = identity.owner_character_id;
      for (std::int32_t regiment_index = 0; regiment_index < count;
           ++regiment_index) {
        const auto id = At<std::int32_t>(data, regiment_index * 4ULL);
        auto *regiment = Resolve(b.regiment_storage_slot, id, 0x10);
        if (!regiment)
          return std::nullopt;
        const auto current = At<std::int32_t>(regiment, 0x38);
        if (current < 0)
          return std::nullopt;
        // 2667E90 counts these physical backing rows, including legitimate zero.
        // Combat fighting entries are a separate view and do not filter this list.
        row.ordered_regiments.push_back({id, current});
      }
      side.ordered_armies.push_back(std::move(row));
    }
  }
  out.enumeration_complete = true;
  return out;
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
  if (b.roll_cadence_interval != nullptr)
    out.roll_cadence_interval = *b.roll_cadence_interval;
  out.base_advantage_raw = At<std::int64_t>(combat, 0x6C8);
  out.resolved_advantage_raw = At<std::int64_t>(combat, 0x710);
  const bool roll_applicable = out.phase_raw == 1 && !out.finalized;
  auto *province = Province(b, At<void *>(combat, 0x6B8));
  if (province == nullptr || At<std::int32_t>(province, 0x10) != out.province_id)
    return false;
  const auto get_terrain = b.commander_roll_context.get_province_terrain;
  void *terrain = roll_applicable && get_terrain != nullptr
      ? get_terrain(province) : nullptr;
  if (!Side(b, combat, 0x20, cid, 0, out.province_id, terrain,
            roll_applicable, out.attacker) ||
      !Side(b, combat, 0x368, cid, 1, out.province_id, terrain,
            roll_applicable, out.defender) ||
      !Retreat(b, scope, combat, army, out) ||
      At<std::uint8_t>(combat, kBattleDailyGuardOffset))
    return false;
  out.active_counter_inputs_v1 =
      ReadActiveBattleCounterInputsV1(b.commander_roll_context, combat, out);
  out.current_loss_inputs_v1 = CurrentLossInputs(b, combat, province, out);
  out.full_backing_inputs_v1 = FullBackingInputs(b, out);
  out.current_pursuit_inputs_v1 = CurrentPursuitInputs(b, combat, out);
  out.current_phase_transition_inputs_v1 =
      CurrentPhaseTransitionInputs(b, combat, out);
  if (Province(b, At<void *>(combat, 0x6B8)) != province)
    return false;
  if (roll_applicable && get_terrain != nullptr &&
      get_terrain(province) != terrain) {
    out.attacker.selected_commander_next_roll_bounds = {};
    out.defender.selected_commander_next_roll_bounds = {};
    out.attacker.selected_commander_next_roll_bounds.unavailable_reason =
        "combat_terrain_changed";
    out.defender.selected_commander_next_roll_bounds.unavailable_reason =
        "combat_terrain_changed";
  }
  return true;
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
    out.unavailable_reason = "subject_not_ai_managed";
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
game::BattleCurrentPersonStateSnapshotV1 CurrentPersonSample(
    const BattleBindings &b, void *character) noexcept {
  game::BattleCurrentPersonStateSnapshotV1 observed{};
  auto &prowess = observed.effective_prowess;
  if (character && b.current_person_effective_prowess_enabled) {
    // Same signed int32 effective value used by v2 ReadCombatKnights.
    prowess.available = true;
    prowess.points = At<std::int32_t>(
        character, phase_character::kCharacterProwessOffset);
  } else {
    prowess.unavailable_reason = character ? "effective_prowess_reader_unbound"
                                          : "character_unresolved";
  }
  auto &injury = observed.injury_traits;
  constexpr std::array<std::string_view, 8> keys{
      "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
      "one_eyed", "disfigured", "incapable"};
  const auto &traits = b.current_person_traits;
  const void *database = character && traits.enabled &&
      traits.get_trait_database && traits.character_has_trait
      ? traits.get_trait_database() : nullptr;
  std::size_t observed_flags = 0;
  if (database) {
    for (std::size_t index = 0; index < keys.size(); ++index) {
      void *definition = phase_character::FindUniqueTraitDefinition(database,
                                                                  keys[index]);
      bool present = false;
      if (phase_character::ReadTraitPresence(traits, character,
              std::span<void *const>(&definition, 1), present)) {
        injury.flags[index] = present;
        ++observed_flags;
      }
    }
  }
  injury.status = observed_flags == keys.size()
      ? game::BattleCurrentPersonInjuryTraitsStatusV1::available
      : observed_flags != 0 ? game::BattleCurrentPersonInjuryTraitsStatusV1::partial
                            : game::BattleCurrentPersonInjuryTraitsStatusV1::unavailable;
  if (observed_flags != keys.size()) {
    injury.unavailable_reason = !character ? "character_unresolved"
        : !traits.enabled || !traits.get_trait_database || !traits.character_has_trait
            ? "injury_trait_reader_unbound"
            : !database ? "trait_database_unavailable"
                        : "trait_definition_or_presence_unavailable";
  }
  if (!injury.flags[0] || !injury.flags[1] || !injury.flags[2]) {
    injury.wounded_rank_unavailable_reason = "wounded_trait_unavailable";
  } else {
    std::int32_t rank = 0;
    std::int32_t present_count = 0;
    for (std::int32_t index = 0; index < 3; ++index) {
      if (*injury.flags[static_cast<std::size_t>(index)]) {
        rank = index + 1;
        ++present_count;
      }
    }
    if (present_count <= 1) injury.wounded_rank = rank;
    else injury.wounded_rank_unavailable_reason = "wounded_traits_multiple_present";
  }
  return observed;
}

game::BattleTerminalCharacterCustodySnapshotV1 CharacterObservationSample(
    const BattleBindings &b, std::int32_t id,
    bool include_current_person = false) noexcept {
  game::BattleTerminalCharacterCustodySnapshotV1 observed{};
  observed.character_id = id;
  void *const character = Resolve(b.character_storage_slot, id, 0x18);
  if (include_current_person && b.current_person_state_enabled)
    observed.current_person_state = CurrentPersonSample(b, character);
  if (!character) return observed;
  // Exact .3 native 0x28EE9BA compares this eight-byte death-data pointer.
  // Missing strict identity remains null; nonnull is an observed dead object.
  observed.alive = At<void *>(character, kCharacterDeathDataOffset) == nullptr;
  void *const extension = At<void *>(character, 0x1B0);
  void *const relation = extension ? At<void *>(extension, 0x288) : nullptr;
  const auto jailer = relation ? At<std::int32_t>(relation, 0) : -1;
  if (jailer == -1) {
    observed.status = game::BattleTerminalCustodyStatusV1::none;
    observed.actual_jailer_character_id = -1;
  } else if (jailer > 0 && Resolve(b.character_storage_slot, jailer, 0x18)) {
    observed.status = game::BattleTerminalCustodyStatusV1::observed;
    observed.actual_jailer_character_id = jailer;
  }
  return observed;
}

bool TerminalSample(const BattleBindings &b, const game::Snapshot &scope,
                    const game::BattleTerminalTransitionRequestV1 &r,
                    game::BattleTerminalTransitionSnapshotV1 &o) {
  o = {};
  o.prior_combat_id = r.prior_combat_id;
  o.subject_public_cunit_id = r.subject_public_cunit_id;
  o.prior.combat_id = r.prior_combat_id;
  if (!r.character_ids.empty()) {
    o.character_observations.emplace();
    for (const auto id : r.character_ids) {
      if (std::any_of(o.character_observations->begin(),
                      o.character_observations->end(),
                      [id](const auto &row) { return row.character_id == id; }))
        continue;
      o.character_observations->push_back(CharacterObservationSample(b, id, true));
    }
  }
  // A character-only request explicitly has no historical Combat or CUnit.
  if (r.prior_combat_id == -1 && r.subject_public_cunit_id == -1 &&
      !r.character_ids.empty()) {
    o.status = game::BattleTerminalTransitionStatusV1::available;
    return true;
  }
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
    p.terminal_date_raw = e.observed_date_raw;
    p.suppress_normal_result_envelopes = e.suppress_normal_result_envelopes;
    p.phase_raw = e.phase_raw;
    p.phase_day = e.phase_day;
    p.winner_raw = e.winner_raw;
    p.finalized_before = e.finalized_before;
    if (e.side_loss_inputs_observable) {
      p.side_loss_inputs_in_native_order = e.side_loss_inputs_in_native_order;
      if (e.winner_raw == 0 || e.winner_raw == 1) {
        const auto losing_side_index = 1 - e.winner_raw;
        const auto &loss = e.side_loss_inputs_in_native_order[
            static_cast<std::size_t>(losing_side_index)];
        p.hard_loss_inputs = game::BattleTerminalHardLossInputsSnapshotV1{
            losing_side_index, loss.baseline_raw_q100000,
            loss.stored_current_fighting_raw_q100000,
            loss.levy_soft_raw_q100000, loss.men_at_arms_soft_raw_q100000,
            loss.hard_loss_raw_q100000};
      }
    }
    if (e.side_final_result_observed[0] && e.side_final_result_observed[1])
      p.side_final_results_in_native_order = e.side_final_results_in_native_order;
    if (e.character_result_rows_observable) {
      p.character_result_rows_in_native_order.emplace();
      for (std::uint32_t i = 0; i < e.character_result_row_count; ++i) {
        const auto &row = e.character_result_rows[i];
        std::optional<std::string> key;
        if (row.key_observable) key.emplace(row.key.data(), row.key_size);
        p.character_result_rows_in_native_order->push_back({
            row.native_row_index, row.left_character_id, row.right_character_id,
            std::move(key), row.type_raw,
            row.side0, row.target_right});
      }
      std::vector<std::int32_t> ids;
      const auto add_id = [&](std::int32_t id) {
        if (id > 0 && std::find(ids.begin(), ids.end(), id) == ids.end()) ids.push_back(id);
      };
      add_id(e.attacker_primary_participant_character_id);
      add_id(e.defender_primary_participant_character_id);
      for (const auto id : e.selected_commander_character_ids) add_id(id);
      for (const auto &row : *p.character_result_rows_in_native_order) {
        add_id(row.left_character_id);
        add_id(row.right_character_id);
      }
      p.character_custody_in_observed_order.emplace();
      for (const auto id : ids)
        p.character_custody_in_observed_order->push_back(
            CharacterObservationSample(b, id));
    }
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
    p.phase_day = t.phase_day;
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

void EnableBattleFullBacking12003(BattleBindings &b, std::uintptr_t base,
                                  std::string_view sha) noexcept {
  b.full_backing_inputs_enabled =
      b.enabled && base != 0 && sha == ck3_12003::kExecutableSha256;
}

void EnableBattleCurrentPerson12003(BattleBindings &b, std::uintptr_t base,
                                    std::string_view sha) noexcept {
  if (!b.enabled || !base || sha != ck3_12003::kExecutableSha256) return;
  b.current_battle_knight_identity_enabled = true;
  b.current_person_state_enabled = true;
  b.current_person_effective_prowess_enabled = true;
  b.current_person_traits.enabled = true;
  b.current_person_traits.get_trait_database =
      reinterpret_cast<phase_character::GetTraitDatabase>(
          base + phase_character::kTraitDatabaseRva);
  b.current_person_traits.character_has_trait =
      reinterpret_cast<phase_character::CharacterHasTrait>(
          base + phase_character::kCharacterHasTraitRva);
}

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
  b.army_internal_fallback_slot =
      reinterpret_cast<void **>(base + kBattleArmyInternalFallbackRva);
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
      reinterpret_cast<void **>(base + 0x5D20550);
  b.ai_unit_stack_vtable = base + 0x45AA608;
  b.ai_subunit_stack_vtable = base + 0x45AB4B0;
  b.ai_war_coordinator_vtable = base + 0x45AB0B8;
  b.minimum_days_before_manual_retreat = reinterpret_cast<const std::int32_t *>(
      base + kBattleMinimumRetreatDaysRva);
  b.roll_cadence_interval = reinterpret_cast<const std::int32_t *>(
      base + kBattleRollCadenceIntervalRva);
  b.pursuit_phase_days = reinterpret_cast<const std::int32_t *>(
      base + kBattlePursuitPhaseDaysRva);
  b.base_toughness_multiplier = reinterpret_cast<const std::int64_t *>(
      base + kBattleBaseToughnessMultiplierRva);
  b.minimum_pursuit_multiplier = reinterpret_cast<const std::int64_t *>(
      base + kBattleMinimumPursuitMultiplierRva);
  b.pursuit_stat_multiplier = reinterpret_cast<const std::int64_t *>(
      base + kBattlePursuitStatMultiplierRva);
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
  b.commander_roll_context = BindCombatImage(base, sha);
  b.damage_scaling = reinterpret_cast<const std::int64_t *>(
      base + kBattleDamageScalingRva);
  b.main_hard_conversion = reinterpret_cast<const std::int64_t *>(
      base + kBattleMainHardConversionRva);
  b.pursuit_hard_conversion = reinterpret_cast<const std::int64_t *>(
      base + kBattlePursuitHardConversionRva);
  b.read_loss_side_modifier = reinterpret_cast<ReadBattleSideModifier>(
      base + kBattleLossSideModifierRva);
  b.read_primary_levy_damage =
      reinterpret_cast<decltype(b.read_primary_levy_damage)>(
          base + kBattlePrimaryLevyDamageRva);
  b.province_has_holding = reinterpret_cast<PhaseProvincePredicate>(
      base + kPhaseProvinceHasHoldingRva);
  b.read_loss_province_modifier = reinterpret_cast<ReadAdvantageModifierValue>(
      base + kAdvantageModifierValueRva);
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
  const bool sampled = ControlSample(b, s, r, a) && ControlSample(b, s, r, c);
  if (sampled && a.full_backing_inputs_v1 != c.full_backing_inputs_v1) {
    // A changing optional census cannot invalidate the existing control frame.
    a.full_backing_inputs_v1.reset();
    c.full_backing_inputs_v1.reset();
  }
  if (sampled && a.current_phase_transition_inputs_v1 !=
                     c.current_phase_transition_inputs_v1) {
    // A changing optional leaf does not invalidate the existing control frame.
    a.current_phase_transition_inputs_v1.reset();
    c.current_phase_transition_inputs_v1.reset();
  }
  if (!sampled || a != c || !Scope(b, s)) {
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
  if (!cr) {
    // A stable negative must obey the shared unavailable DTO contract. The
    // sample can have read identity and membership fields before failing.
    o.unavailable_reason = c.unavailable_reason.empty()
                               ? "state_changed" : c.unavailable_reason;
    return o.status;
  }
  o = std::move(c);
  o.observed_date_raw = s.date_raw;
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
  const bool character_only = r.prior_combat_id == -1 &&
      r.subject_public_cunit_id == -1 && !r.character_ids.empty();
  if (!Scope(b, s) || (!character_only &&
      (r.prior_combat_id <= 0 || r.subject_public_cunit_id < 0))) {
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

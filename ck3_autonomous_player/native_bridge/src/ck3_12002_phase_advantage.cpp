#include "xar_bridge/ck3_12002_phase_advantage.hpp"
#include "xar_bridge/ck3_12002_phase.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_12002 {
namespace {
constexpr std::int64_t kScale = 100'000;
constexpr std::uint32_t kEffectMagic = 0x4744624F;
constexpr std::array<std::size_t, 3> kSupplyOffsets{0xF20, 0xF30, 0xF40};
constexpr std::array<std::string_view, 3> kSupplyKeys{
    "supply_state_supplied_advantage", "supply_state_running_low_advantage",
    "supply_state_starving_advantage"};

template<class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}
bool Add(std::int64_t a, std::int64_t b, std::int64_t &out) noexcept {
  if ((b > 0 && a > std::numeric_limits<std::int64_t>::max() - b) ||
      (b < 0 && a < std::numeric_limits<std::int64_t>::min() - b)) return false;
  out = a + b;
  return true;
}
void *Resolve(void **slot, std::int32_t id) noexcept {
  if (slot == nullptr || *slot == nullptr || id <= 0) return nullptr;
  auto *storage = *slot;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  const auto capacity = Load<std::uint32_t>(storage, 0x2C);
  if (index >= capacity || capacity > 4'194'304) return nullptr;
  auto *data = Load<void *>(storage, 0x20);
  if (data == nullptr) return nullptr;
  auto *result = Load<void *>(data, static_cast<std::size_t>(index) * 16 + 8);
  return result != nullptr && Load<std::int32_t>(result, 0x10) == id
      ? result : nullptr;
}
bool ReadKey(void *object, std::string &key) {
  if (object == nullptr) return false;
  const auto length = Load<std::size_t>(object, 0x28);
  const auto capacity = Load<std::size_t>(object, 0x30);
  if (length == 0 || length > 512 || capacity < length) return false;
  const auto *data = capacity < 16
      ? static_cast<const char *>(object) + 0x18
      : Load<const char *>(object, 0x18);
  if (data == nullptr) return false;
  key.assign(data, length);
  return true;
}
bool ValidEffect(void *effect) noexcept {
  return effect != nullptr && Load<std::uint32_t>(effect, 0x38) == kEffectMagic;
}
bool RequireKey(void *effect, std::string_view expected) {
  std::string key;
  return ValidEffect(effect) && ReadKey(effect, key) && key == expected;
}
bool Append(NonReligiousAdvantagePlan &plan, std::size_t side,
    std::string_view stage, void *effect, bool selected, bool applied,
    std::int64_t scale, std::string key, std::string reason,
    std::int32_t &append_order, std::int64_t &accumulator) {
  if (side > 1 || (selected && (!ValidEffect(effect) || key.empty())) ||
      (applied && (!selected || scale == 0))) return false;
  game::CombatAdvantageConstructorSourceV3TestOnly row;
  row.stage_order = static_cast<std::int32_t>(plan.model.constructor_sources.size());
  row.stage = stage;
  row.side = side == 0 ? "attacker" : "defender";
  row.selected = selected;
  row.applied = applied;
  row.scale_raw = scale;
  row.accumulator_before_raw = accumulator;
  row.effect_advantage_points = selected ? Load<std::int32_t>(effect, 0x40) : 0;
  if (selected) row.source_key = std::move(key);
  if (applied) {
    const auto points = static_cast<std::int64_t>(row.effect_advantage_points);
    if (scale < 0 ||
        (points > 0 && scale > std::numeric_limits<std::int64_t>::max() / points) ||
        (points < 0 && points < std::numeric_limits<std::int64_t>::min() /
            std::max<std::int64_t>(scale, 1))) return false;
    const auto contribution = points * scale;
    if (side == 1 && contribution == std::numeric_limits<std::int64_t>::min())
      return false;
    row.signed_contribution_raw = side == 0 ? contribution : -contribution;
    std::int64_t next = 0;
    if (!Add(accumulator, row.signed_contribution_raw, next)) return false;
    accumulator = std::clamp<std::int64_t>(next, -10'000'000, 10'000'000);
    row.append_order = append_order++;
    plan.ledgers[side].push_back({effect, contribution});
  } else {
    row.append_order = -1;
    row.skip_reason = std::move(reason);
    if (row.skip_reason.empty()) return false;
  }
  row.accumulator_after_raw = accumulator;
  plan.model.constructor_sources.push_back(std::move(row));
  return true;
}

struct ArmyContext {
  const game::CombatArmyInputsSnapshot *snapshot = nullptr;
  void *army = nullptr;
  void *owner = nullptr;
};
bool Contexts(const PhaseEnvironment &env,
    const game::CombatSimulationInputsSnapshot &base,
    std::array<std::vector<ArmyContext>, 2> &out) {
  const std::array<const std::vector<std::int32_t> *, 2> ids{
      &base.scenario.attacker_army_ids, &base.scenario.defender_army_ids};
  for (std::size_t side = 0; side < 2; ++side) {
    if (ids[side]->empty() || ids[side]->size() > 65'536) return false;
    for (auto id : *ids[side]) {
      const auto row = std::find_if(base.armies.begin(), base.armies.end(),
          [id](const auto &army) { return army.army_id == id; });
      if (row == base.armies.end() || !row->available ||
          row->owner.status != game::CombatObservationStatus::available ||
          !row->regiments_observable) return false;
      void *army = env.resolve_internal_army(env.context, row->native_carmy_id);
      void *owner = env.resolve_character(env.context, row->owner.character_id);
      if (army == nullptr || owner == nullptr ||
          Load<std::int32_t>(army, 0x10) != row->native_carmy_id ||
          Load<std::int32_t>(owner, 0x18) != row->owner.character_id) return false;
      out[side].push_back({&*row, army, owner});
    }
  }
  return true;
}

bool Supply(const AdvantageBindings &bindings, void *rules,
    const std::vector<ArmyContext> &armies,
    game::CombatAdvantageSupplyInputV3TestOnly &out, void *&effect) {
  if (bindings.supply_thresholds == nullptr ||
      bindings.supply_threshold_count == nullptr) return false;
  const auto *thresholds = *bindings.supply_thresholds;
  const auto count = *bindings.supply_threshold_count;
  if (thresholds == nullptr || count < 3 || count > 64) return false;
  std::array<std::int64_t, 3> totals{};
  std::vector<std::int32_t> native_ids;
  for (const auto &army : armies) {
    native_ids.push_back(army.snapshot->native_carmy_id);
    const auto supply = Load<std::int64_t>(army.army, 0x180) / kScale;
    std::int32_t state = count - 1;
    for (std::int32_t index = 0; index < count; ++index)
      if (supply >= thresholds[index]) { state = index; break; }
    const auto bucket = static_cast<std::size_t>(std::min(state, 2));
    for (const auto &row : army.snapshot->regiments) {
      auto *regiment = Resolve(bindings.regiment_storage_slot, row.regiment_id);
      if (regiment == nullptr || Load<std::uint32_t>(regiment, 0x14) != 0x41725267 ||
          Load<std::int32_t>(regiment, 0x140) != army.snapshot->native_carmy_id ||
          Load<std::int32_t>(regiment, 0x38) != row.current_soldiers ||
          row.current_soldiers < 0 || !row.identity_valid) return false;
      bool eligible = Load<std::int32_t>(regiment, 0x14C) != 1;
      if (!eligible) {
        auto *data = Load<void *>(regiment, 0x20);
        const auto membership_count = Load<std::int32_t>(regiment, 0x2C);
        if (membership_count < 0 || membership_count > 65'536 ||
            (membership_count > 0 && data == nullptr)) return false;
        if (membership_count > 0) {
          auto *unit = Resolve(bindings.supply_unit_storage_slot,
              Load<std::int32_t>(data, 8));
          if (unit == nullptr) return false;
          eligible = Load<std::uint8_t>(unit, 0x141) != 0;
        }
      }
      if (eligible && !Add(totals[bucket], row.current_soldiers, totals[bucket]))
        return false;
    }
  }
  std::int64_t total = 0, supplied_and_low = 0;
  if (!Add(totals[0], totals[1], supplied_and_low) ||
      !Add(supplied_and_low, totals[2], total)) return false;
  const auto bucket = total <= 0 || totals[0] > total - totals[0] ? 0U
      : supplied_and_low > total - supplied_and_low ? 1U : 2U;
  effect = Load<void *>(rules, kSupplyOffsets[bucket]);
  if (!RequireKey(effect, kSupplyKeys[bucket])) return false;
  AdvantageNativeIdArray array{native_ids.data(),
      static_cast<std::int32_t>(native_ids.size()),
      static_cast<std::int32_t>(native_ids.size())};
  if (bindings.select_supply(&array) != effect) return false;
  out.selected_key = kSupplyKeys[bucket];
  constexpr std::array<std::string_view, 3> identities{
      "loaded_combat_rule_database:+0xF20", "loaded_combat_rule_database:+0xF30",
      "loaded_combat_rule_database:+0xF40"};
  out.selected_effect_identity = identities[bucket];
  out.selected_effect_points = Load<std::int32_t>(effect, 0x40);
  out.eligible_soldiers_total = total;
  out.eligible_soldiers_supplied = totals[0];
  out.eligible_soldiers_running_low = totals[1];
  out.eligible_soldiers_starving = totals[2];
  return true;
}

bool DebtEffect(void *rules, std::int32_t selector, bool treasury,
    void *&effect, std::string &key) {
  effect = nullptr;
  key.clear();
  const auto count = Load<std::int32_t>(rules, treasury ? 0x1084 : 0xFDC);
  if (count < 0 || count > 1'024 || selector < -1 || selector > count)
    return false;
  if (selector == -1) return true;
  if (selector == count) {
    effect = Load<void *>(rules, 0xF60);
    key = "combat_debt_level_no_income";
  } else {
    auto *data = Load<void *>(rules, treasury ? 0x1078 : 0xFD0);
    if (data == nullptr) return false;
    effect = Load<void *>(data, static_cast<std::size_t>(selector) * 8);
    key = treasury ? "treasury_combat_debt_level_" : "combat_debt_level_";
    key += std::to_string(selector);
  }
  // A native fallback is a legitimate unselected debt effect.
  return !ValidEffect(effect) || RequireKey(effect, key);
}

bool TreasuryDebt(const AdvantageBindings &bindings, void *owner,
    std::int32_t &selector, bool &observable) {
  selector = 0;
  observable = false;
  auto *government = bindings.get_government(owner);
  if (government == nullptr) return false;
  if ((Load<std::uint32_t>(government, 0x40) & (1U << 29U)) == 0 ||
      Load<void *>(owner, 0x1B0) == nullptr) return true;
  std::int32_t realm = -1;
  auto *container = Load<void *>(owner, 0x1C0);
  const auto data_offset = container != nullptr ? 0x1E0U : 0x68U;
  const auto count_offset = container != nullptr ? 0x1ECU : 0x74U;
  if (container == nullptr) container = Load<void *>(owner, 0x1D0);
  if (container != nullptr) {
    const auto count = Load<std::int32_t>(container, count_offset);
    auto *data = Load<void *>(container, data_offset);
    if (count < 0 || count > 65'536 || (count > 0 && data == nullptr)) return false;
    if (count > 0) realm = Load<std::int32_t>(data, 0);
  }
  auto *treasury = bindings.resolve_treasury(&realm);
  if (treasury == nullptr || Load<std::uint32_t>(treasury, 0x14) != 0x4C616E64 ||
      Load<std::int32_t>(treasury, 0x10) == -1 ||
      Load<std::int64_t>(treasury, 0x318) >= 0) return true;
  selector = bindings.select_debt(owner, 3);
  observable = true;
  return true;
}
} // namespace

AdvantageBindings BindAdvantageImage(std::uintptr_t base,
    std::string_view sha, const CombatBindings &combat) noexcept {
  AdvantageBindings b;
  if (base == 0 || sha != kExecutableSha256 || !combat.enabled) return b;
  b.enabled = true;
  b.get_rules = reinterpret_cast<GetCombatRules>(base + kAdvantageRuleDatabaseRva);
  b.select_supply = reinterpret_cast<SelectAdvantageSupply>(base + kAdvantageSupplySelectorRva);
  b.select_debt = reinterpret_cast<SelectAdvantageDebt>(base + kAdvantageDebtSelectorRva);
  b.resolve_treasury = reinterpret_cast<ResolveAdvantageTreasury>(base + kAdvantageResolveTreasuryRva);
  b.get_government = reinterpret_cast<decltype(b.get_government)>(base + kAdvantageCharacterGovernmentRva);
  b.has_modifier_flag = reinterpret_cast<AdvantageModifierFlag>(base + kAdvantageModifierFlagRva);
  b.read_province_modifier = reinterpret_cast<ReadAdvantageProvinceModifier>(base + kAdvantageProvinceModifierRva);
  b.read_modifier_value = reinterpret_cast<ReadAdvantageModifierValue>(base + kAdvantageModifierValueRva);
  b.province_has_holding = reinterpret_cast<PhaseProvincePredicate>(base + kPhaseProvinceHasHoldingRva);
  b.supply_unit_storage_slot = reinterpret_cast<void **>(base + kAdvantageSupplyUnitStorageRva);
  b.supply_thresholds = reinterpret_cast<const std::int32_t *const *>(base + kAdvantageSupplyThresholdsRva);
  b.supply_threshold_count = reinterpret_cast<const std::int32_t *>(base + kAdvantageSupplyThresholdCountRva);
  b.get_modifier_aggregator = combat.get_character_modifier_aggregator;
  b.get_terrain = combat.get_province_terrain;
  b.is_holding_defender = combat.is_holding_defender;
  b.regiment_storage_slot = combat.regiment_storage_slot;
  return b;
}

bool BuildNonReligiousAdvantagePlan(const AdvantageBindings &b,
    const PhaseEnvironment &env, const game::CombatSimulationInputsSnapshot &base,
    const std::array<void *, 2> &commanders, NonReligiousAdvantagePlan &out) noexcept {
  out = {};
  out.unavailable_reason = "native_nonreligious_advantage_preconditions_unavailable";
  out.model.observation_origin = "native_exact_build_production";
  try {
    if (!b.enabled || b.get_rules == nullptr || b.get_terrain == nullptr ||
        b.select_supply == nullptr || b.select_debt == nullptr ||
        b.resolve_treasury == nullptr || b.get_government == nullptr ||
        b.has_modifier_flag == nullptr || b.get_modifier_aggregator == nullptr ||
        b.is_holding_defender == nullptr || b.province_has_holding == nullptr ||
        b.read_province_modifier == nullptr || b.read_modifier_value == nullptr ||
        env.resolve_internal_army == nullptr || env.resolve_character == nullptr ||
        env.resolve_province == nullptr || commanders[0] == nullptr ||
        commanders[1] == nullptr || !base.target_province.available ||
        !base.target_province.terrain.available || !base.target_province.crossing.available)
      return false;
    auto *target = env.resolve_province(env.context, base.target_province_id);
    auto *terrain = target == nullptr ? nullptr : b.get_terrain(target);
    auto *rules = b.get_rules();
    std::string terrain_key;
    if (rules == nullptr || !ReadKey(terrain, terrain_key) ||
        terrain_key != base.target_province.terrain.key) return false;
    std::array<std::vector<ArmyContext>, 2> armies;
    if (!Contexts(env, base, armies)) return false;
    const std::array<std::string_view, 4> crossing_keys{"none", "strait", "river", "large_river"};
    const auto crossing = std::find(crossing_keys.begin(), crossing_keys.end(),
        base.target_province.crossing.kind);
    if (crossing == crossing_keys.end()) return false;
    const auto crossing_index = static_cast<std::size_t>(crossing - crossing_keys.begin());
    std::int32_t append_order = 0;
    std::int64_t accumulator = 0;
    for (std::size_t side = 0; side < 2; ++side) {
      auto *effect = Load<void *>(rules, (side == 0 ? 0xF70 : 0xFA0) + crossing_index * 8);
      const bool valid = ValidEffect(effect);
      std::string key;
      if (valid && !ReadKey(effect, key)) return false;
      bool ignored = false;
      if (side == 1 && valid) {
        auto *aggregator = b.get_modifier_aggregator(commanders[0]);
        if (aggregator == nullptr) return false;
        ignored = b.has_modifier_flag(static_cast<std::byte *>(aggregator) + 0x68, 0x1A4);
      }
      if (!Append(out, side, side == 0 ? "attacker_adjacency" : "defender_adjacency",
          effect, valid, valid && !ignored, kScale, std::move(key),
          ignored ? "attacker_no_water_crossing_penalty" : "loaded_adjacency_effect_not_selected",
          append_order, accumulator)) return false;
    }
    for (std::size_t side = 0; side < 2; ++side) {
      auto *effect = Load<void *>(terrain, side == 0 ? 0x48 : 0x50);
      const bool valid = ValidEffect(effect);
      const auto key = "terrain:" + terrain_key + (side == 0 ? ":attacker" : ":defender");
      if (!Append(out, side, side == 0 ? "attacker_terrain" : "defender_terrain",
          effect, valid, valid, kScale, valid ? key : std::string{},
          "terrain_effect_not_selected", append_order, accumulator)) return false;
    }
    out.model.side_inputs.resize(2);
    for (std::size_t side = 0; side < 2; ++side) {
      auto &input = out.model.side_inputs[side];
      input.side = side == 0 ? "attacker" : "defender";
      input.primary_army_id = armies[side].front().snapshot->army_id;
      input.owner_character_id = armies[side].front().snapshot->owner.character_id;
      for (const auto &army : armies[side]) input.ordered_army_ids.push_back(army.snapshot->army_id);
      void *effect = nullptr;
      if (!Supply(b, rules, armies[side], input.supply, effect)) return false;
      if (!Append(out, side, side == 0 ? "supply_0" : "supply_1", effect, true,
          input.supply.selected_effect_points != 0, kScale, input.supply.selected_key,
          "zero_effect_not_appended", append_order, accumulator)) return false;
      input.primary_army_gathering_raw = Load<std::int32_t>(armies[side].front().army, 0x5C);
    }
    out.holding_defender = b.is_holding_defender(armies[1].front().owner, target);
    if (!base.target_province.defender_context.available ||
        base.target_province.defender_context.holding_defender_status != game::CombatObservationStatus::available ||
        out.holding_defender != base.target_province.defender_context.holding_defender) return false;
    std::int64_t holding_scale = kScale;
    if (out.holding_defender) {
      if (b.read_province_modifier(&holding_scale, target, 0x1EB, 0, nullptr) != &holding_scale)
        return false;
      if (b.province_has_holding(target)) {
        std::int64_t holding_modifier = 0;
        if (b.read_modifier_value(&holding_modifier, static_cast<std::byte *>(target) + 0x30,
            0x1D6, nullptr, kScale, 0) != &holding_modifier ||
            !Add(holding_scale, holding_modifier, holding_scale)) return false;
      }
    }
    auto *holding_effect = Load<void *>(rules, 0xF10);
    if (!RequireKey(holding_effect, "holding_defender_advantage") ||
        !Append(out, 1, "holding_defender_1", holding_effect, out.holding_defender,
          out.holding_defender && holding_scale > 0,
          out.holding_defender ? holding_scale : kScale,
          out.holding_defender ? "holding_defender_advantage" : "",
          out.holding_defender ? "holding_scale_not_positive" : "holding_defender_predicate_false",
          append_order, accumulator)) return false;
    auto *gathering_effect = Load<void *>(rules, 0xF00);
    if (!RequireKey(gathering_effect, "gathering_army_advantage")) return false;
    for (std::size_t side = 0; side < 2; ++side) {
      const bool gathering = out.model.side_inputs[side].primary_army_gathering_raw != 0;
      if (!Append(out, side, side == 0 ? "gathering_army_0" : "gathering_army_1",
          gathering_effect, gathering, gathering, kScale,
          gathering ? "gathering_army_advantage" : "", "primary_army_not_gathering",
          append_order, accumulator)) return false;
    }
    for (std::size_t side = 0; side < 2; ++side) {
      auto &input = out.model.side_inputs[side];
      input.owner_debt_selector_raw = b.select_debt(armies[side].front().owner, 0);
      if (!TreasuryDebt(b, armies[side].front().owner, input.treasury_debt_selector_raw,
          input.treasury_debt_selector_observable)) return false;
      for (std::size_t treasury = 0; treasury < 2; ++treasury) {
        void *effect = nullptr;
        std::string key;
        const bool observable = treasury == 0 || input.treasury_debt_selector_observable;
        if (observable && !DebtEffect(rules, treasury == 0 ? input.owner_debt_selector_raw :
            input.treasury_debt_selector_raw, treasury != 0, effect, key)) return false;
        const bool selected = observable && ValidEffect(effect);
        const auto stage = std::string("debt_") + std::to_string(side) +
            (treasury == 0 ? "_owner" : "_treasury");
        if (!Append(out, side, stage, effect, selected, selected, kScale,
            selected ? key : std::string{}, !observable ? "treasury_debt_gate_false" :
            treasury == 0 ? "owner_debt_effect_not_selected" : "treasury_debt_effect_not_selected",
            append_order, accumulator)) return false;
      }
    }
    for (std::size_t side = 0; side < 2; ++side)
      if (!Append(out, side, side == 0 ? "unreformed_faith_0" : "unreformed_faith_1",
          nullptr, false, false, kScale, {}, "religion_constructor_operand_implementation_pending",
          append_order, accumulator)) return false;
    out.model.base_static_accumulator_raw = accumulator;
    out.model.unavailable_reason = "religion_constructor_sources_implementation_pending";
    out.unavailable_reason = out.model.unavailable_reason;
    out.nonreligious_available = true;
    return true;
  } catch (...) {
    out = {};
    out.unavailable_reason = "native_nonreligious_advantage_exception";
    return false;
  }
}
} // namespace xar::ck3_12002

#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar::ck3_12002;
using namespace xar::game;
void Require(bool value, std::string_view message) {
  if (!value) throw std::runtime_error(std::string(message));
}
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename T, std::size_t N>
void Put(Bytes<N> &object, std::size_t offset, T value) {
  Require(offset + sizeof(value) <= object.size(), "fixture write range");
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
struct Store {
  Bytes<0x38> header{};
  std::vector<std::byte> rows;
  void *root = header.data();
  void Set(std::int32_t id, void *object) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    const auto offset = static_cast<std::size_t>(index) * 16U + 8U;
    if (rows.size() < offset + 8U) rows.resize(offset + 8U);
    std::memcpy(rows.data() + offset, &object, sizeof(object));
    Put(header, 0x20, rows.data());
    Put(header, 0x2C, static_cast<std::int32_t>((rows.size() + 15U) / 16U));
  }
};
constexpr std::int32_t kCombat = 0x01000003;
constexpr std::int32_t kResult = 0x01000004;
constexpr std::int32_t kProvince = 2640;
constexpr std::array<std::int32_t, 2> kUnits{0x01000011, 0x01000012};
constexpr std::array<std::int32_t, 2> kArmies{0x01000001, 0x01000002};
constexpr std::array<std::int32_t, 2> kOwners{0x01000021, 0x01000022};
constexpr std::array<std::size_t, 2> kSides{0x20, 0x368};

// Bounded synthetic RVA storage, never a loaded executable or game process.
struct Fixture {
  static constexpr std::uintptr_t kWindowBegin = 0x5C67000;
  static constexpr std::uintptr_t kWindowEnd = 0x5D21000;
  std::vector<std::byte> globals =
      std::vector<std::byte>(kWindowEnd - kWindowBegin);
  std::uintptr_t image_base =
      reinterpret_cast<std::uintptr_t>(globals.data()) - kWindowBegin;
  Bytes<0xA8> game_state{};
  Bytes<0x28> jomini_state{};
  Bytes<0x158> game_data{};
  std::array<void *, 2641> province_rows{};
  Bytes<0x860> province{};
  Bytes<0x730> combat{};
  Bytes<0xD8> result{};
  std::array<Bytes<0x200>, 2> units{};
  std::array<Bytes<0x148>, 2> armies{};
  std::array<Bytes<0x220>, 2> characters{};
  Store unit_store, army_store, character_store, combat_store, result_store;
  BattleBindings bindings{};
  Snapshot scope{};
  template <typename T> void Global(std::uintptr_t rva, T value) {
    Require(rva >= kWindowBegin && rva + sizeof(value) <= kWindowEnd,
            "fixture global range");
    std::memcpy(globals.data() + rva - kWindowBegin, &value, sizeof(value));
  }
  static std::int32_t Strength(void *) { return 0; }
  static void *RuleState(void *) { return nullptr; }
  static bool Retreat(void *combat_object, void *, void *) {
    std::int32_t phase{};
    std::memcpy(&phase, static_cast<std::byte *>(combat_object) + 0x6B0,
                sizeof(phase));
    return phase < 2;
  }
  Fixture() {
    scope.paused = true;
    scope.map_ready = true;
    scope.has_played_character = true;
    scope.played_character_id = kOwners[0];
    scope.date_raw = 0x029C55C0 + 15 * 24;
    Put(game_state, 8, scope.date_raw);
    Put<std::uint8_t>(jomini_state, 0x20, 1);
    Put(game_state, 0xA0, game_data.data());
    province_rows[kProvince] = province.data();
    Put(game_data, 0x140, province_rows.data());
    Put<std::int32_t>(game_data, 0x14C, 2641);
    Put(province, 0x10, kProvince);
    Put<std::uint32_t>(province, 0x85C, 0x50726F76U);
    Put(combat, 8, kCombat);
    Put(combat, 0x6B8, province.data());
    Put<std::int32_t>(combat, 0x6B0, 1);
    Put<std::int32_t>(combat, 0x6B4, 12);
    Put<std::int32_t>(combat, 0x6E4, 2);
    Put<std::int32_t>(combat, 0x6E0, -1);
    Put<std::int32_t>(combat, 0x700, -1);
    Put(combat, 0x708, kResult);
    Put(result, 8, kResult);
    Put<std::int32_t>(result, 0x2C, 0x029C55C0);
    combat_store.Set(kCombat, combat.data());
    result_store.Set(kResult, result.data());
    for (std::size_t side = 0; side != 2; ++side) {
      Put(characters[side], 0x18, kOwners[side]);
      character_store.Set(kOwners[side], characters[side].data());
      Put(units[side], 0x10, kUnits[side]);
      Put(units[side], 0x174, kOwners[side]);
      Put(units[side], 0x178, kArmies[side]);
      Put(armies[side], 0x10, kArmies[side]);
      Put(armies[side], 0x124, kUnits[side]);
      Put(armies[side], 0x128, kCombat);
      unit_store.Set(kUnits[side], units[side].data());
      army_store.Set(kArmies[side], armies[side].data());
      Put(combat, kSides[side] + 0x10, &kArmies[side]);
      Put<std::int32_t>(combat, kSides[side] + 0x18, 1);
      Put<std::int32_t>(combat, kSides[side] + 0x1C, 1);
      Put(combat, kSides[side] + 0xB8, combat.data());
      Put(combat, kSides[side] + 0x70, kOwners[side]);
      Put<std::int32_t>(combat, kSides[side] + 0x74, -1);
    }
    ArmySnapshot player_army{};
    player_army.army_id = kUnits[0];
    player_army.controllable = true;
    player_army.in_combat = true;
    scope.player_armies.push_back(player_army);
    Global(kGameStateSlotRva, game_state.data());
    Global(kJominiStateSlotRva, jomini_state.data());
    Global(0x5D1E380, unit_store.root);
    Global(0x5D1DE48, army_store.root);
    Global(kCharacterStorageSlotRva, character_store.root);
    Global(kBattleCombatStorageRva, combat_store.root);
    Global(kBattleResultStorageRva, result_store.root);
    Global(kBattleResultFallbackRva, result.data());
    Global<std::int32_t>(kBattleMinimumRetreatDaysRva, 14);
    Global<std::int32_t>(0x5C69B74, 11);
    Global<std::int32_t>(0x5C69B78, 0x23456789);
    Global<std::int64_t>(0x5C699C0, 5'000'000'003);
    Global<std::int64_t>(0x5C699A0, 0);
    Global<std::int64_t>(0x5C699D0, -7'000'000'011);
    // Current .3 admission already reuses this .2 ABI binder.
    bindings = BindBattleImage(image_base, kExecutableSha256);
    Require(bindings.enabled, "production ABI binder unavailable");
    Require(kBattleRollCadenceIntervalRva == 0x5C69B48 &&
      reinterpret_cast<std::uintptr_t>(bindings.roll_cadence_interval) ==
          image_base + 0x5C69B48, "cadence readonly binding RVA changed");
    Require(reinterpret_cast<std::uintptr_t>(bindings.pursuit_phase_days) ==
              image_base + 0x5C69B74 &&
            reinterpret_cast<std::uintptr_t>(bindings.base_toughness_multiplier) ==
              image_base + 0x5C699C0 &&
            reinterpret_cast<std::uintptr_t>(bindings.minimum_pursuit_multiplier) ==
              image_base + 0x5C699A0 &&
            reinterpret_cast<std::uintptr_t>(bindings.pursuit_stat_multiplier) ==
              image_base + 0x5C699D0, "pursuit readonly binding RVAs changed");
    bindings.get_combat_side_strength = Strength;
    bindings.get_combat_regiment_strength = Strength;
    bindings.get_combat_retreat_rule_state = RuleState;
    bindings.can_order_combat_retreat = Retreat;
    bindings.commander_roll_context = {};
    bindings.damage_scaling = nullptr;
  }
};

constexpr std::array<std::int32_t, 2> kPrimaries{0x01000031, 0x01000032};
constexpr std::array<std::int32_t, 3> kRegiments{0x01000041, 0x01000042, 0x01000043};
constexpr std::array<std::int64_t, 2> kEfficiency{5'000'000'007, 700'007};
constexpr std::array<std::int64_t, 2> kResistance{0, 6'000'000'009};
constexpr std::array<std::int64_t, 2> kContext{123'457, 765'433};
constexpr std::array<std::int64_t, 3> kCurrent{1'200'001, 400'007, 2'300'007};
template <typename T> T Read(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
struct CounterFixture : Fixture {
  static inline CounterFixture *active = nullptr;
  Bytes<0xF10> rules{};
  std::array<Bytes<0x220>, 2> primary_characters{};
  std::array<Bytes<0x20>, 2> aggregators{};
  std::array<Bytes<0x150>, 3> regiments{};
  std::array<Bytes<0x990>, 3> types{};
  std::array<Bytes<0x10>, 2> targets0{};
  std::array<Bytes<0x10>, 1> targets1{};
  std::array<Bytes<0x60>, 2> entries0{};
  std::array<Bytes<0x60>, 1> entries1{};
  Store regiment_store;
  std::vector<std::array<std::int64_t, 2>> chunk_calls;
  std::vector<std::array<std::int32_t, 2>> modifier_calls;
  std::vector<std::array<std::int32_t, 2>> context_calls;
  bool fail_current_getter = false;
  bool resolver_called = false;
  static void *Rules() { return active->rules.data(); }
  static void *Aggregator(void *character) {
    const auto id = Read<std::int32_t>(character, 0x18);
    for (std::size_t side = 0; side < kPrimaries.size(); ++side)
      if (id == kPrimaries[side] && character == active->primary_characters[side].data())
        return active->aggregators[side].data();
    return nullptr;
  }
  static std::int64_t *Modifier(void *aggregator, std::int64_t *output,
                                std::int32_t modifier) {
    const auto id = Read<std::int32_t>(aggregator, 0);
    active->modifier_calls.push_back({id, modifier});
    if (modifier == 0x113) *output = Read<std::int64_t>(aggregator, 8);
    else if (modifier == 0x114) *output = Read<std::int64_t>(aggregator, 0x10);
    else return nullptr;
    return output;
  }
  static std::int64_t *Chunk(const void *entry, std::int64_t *output) {
    const auto id = Read<std::int32_t>(entry, 8);
    const auto current = Read<std::int64_t>(entry, 0x18);
    active->chunk_calls.push_back({id, current});
    if (active->fail_current_getter) return nullptr;
    for (std::size_t index = 0; index < kRegiments.size(); ++index) {
      if (id != kRegiments[index]) continue;
      const auto stack = Read<std::int32_t>(active->types[index].data(), 0x70);
      if (stack <= 0) return nullptr;
      *output = current / stack;
      return output;
    }
    return nullptr;
  }
  static std::int64_t *Context(std::int64_t *output, void *countered, void *countering) {
    const auto own = Read<std::int32_t>(countered, 0);
    const auto opposite = Read<std::int32_t>(countering, 0);
    active->context_calls.push_back({own, opposite});
    if (own == kPrimaries[0] && opposite == kPrimaries[1]) *output = kContext[0];
    else if (own == kPrimaries[1] && opposite == kPrimaries[0]) *output = kContext[1];
    else return nullptr;
    return output;
  }
  static void Resolve(void *, void *, void *, std::int64_t) {
    active->resolver_called = true;
  }
  CounterFixture(bool fail) : fail_current_getter(fail) {
    active = this;
    Put<std::int32_t>(rules, 0xEFC, 3);
    for (std::size_t side = 0; side < kPrimaries.size(); ++side) {
      Put(primary_characters[side], 0x18, kPrimaries[side]);
      Put<std::uint32_t>(primary_characters[side], 0x1C, 0x43686172U);
      character_store.Set(kPrimaries[side], primary_characters[side].data());
      Put(aggregators[side], 0, kPrimaries[side]);
      Put(aggregators[side], 8, kEfficiency[side]);
      Put(aggregators[side], 0x10, kResistance[side]);
      Put(combat, kSides[side] + 0x70, kPrimaries[side]);
      // The selected commander and first Army owner are deliberately not primary.
      Put(combat, kSides[side] + 0x74, kOwners[side]);
    }
    for (std::size_t index = 0; index < kRegiments.size(); ++index) {
      const std::size_t side = index == 2 ? 1 : 0;
      Put(regiments[index], 0x10, kRegiments[index]);
      Put(regiments[index], 0x18, types[index].data());
      Put(regiments[index], 0x140, kArmies[side]);
      Put<std::int32_t>(regiments[index], 0x148, -1);
      regiment_store.Set(kRegiments[index], regiments[index].data());
      Put<std::uint8_t>(types[index], kBattleMainPhaseTypeFlag, 1);
      Put<std::int32_t>(types[index], 0x260, index == 0 ? 0 : index == 1 ? -1 : 1);
      Put<std::int32_t>(types[index], 0x70, index == 0 ? 1 : index == 1 ? 0 : 10);
      auto &entry = index == 2 ? entries1[0] : entries0[index];
      Put(entry, 8, kRegiments[index]);
      Put(entry, 0x10, kCurrent[index] + 100'003);
      Put(entry, 0x18, kCurrent[index]);
      Put<std::int64_t>(entry, 0x20, 30'001);
      Put<std::int32_t>(entry, 0x30, 100);
      Put<std::int64_t>(entry, 0x40, index == 1 ? 500'003 : 300'007);
      Put<std::int64_t>(entry, 0x48, 400'009);
      Put<std::int64_t>(entry, 0x50, 200'011);
      Put<std::int64_t>(entry, 0x58, 100'013);
    }
    Put<std::int32_t>(targets0[0], 0, 1);
    Put<std::int64_t>(targets0[0], 8, 1'750'003);
    Put<std::int32_t>(targets0[1], 0, 2);
    Put<std::int64_t>(targets0[1], 8, 0);
    Put<std::int32_t>(targets1[0], 0, 0);
    Put<std::int64_t>(targets1[0], 8, 250'003);
    Put(types[0], 0x2A8, targets0.data());
    Put<std::int32_t>(types[0], 0x2B4, 2);
    // Legal class -1 is an absent counter row; its stack/targets are not operands.
    Put<std::int32_t>(types[1], 0x2B4, -17);
    Put(types[2], 0x2A8, targets1.data());
    Put<std::int32_t>(types[2], 0x2B4, 1);
    Put(combat, kSides[0] + 0x40, entries0.data());
    Put<std::int32_t>(combat, kSides[0] + 0x48, 2);
    Put<std::int32_t>(combat, kSides[0] + 0x4C, 2);
    Put<std::int64_t>(combat, kSides[0] + 0x98, kCurrent[0] + kCurrent[1]);
    Put(combat, kSides[1] + 0x40, entries1.data());
    Put<std::int32_t>(combat, kSides[1] + 0x48, 1);
    Put<std::int32_t>(combat, kSides[1] + 0x4C, 1);
    Put<std::int64_t>(combat, kSides[1] + 0x98, kCurrent[2]);
    Global(0x5D1F340, regiment_store.root);
    auto &counter = bindings.commander_roll_context;
    counter.enabled = true;
    counter.character_storage_slot = &character_store.root;
    counter.regiment_storage_slot = &regiment_store.root;
    counter.get_combat_rules = Rules;
    counter.get_character_modifier_aggregator = Aggregator;
    counter.read_character_modifier = Modifier;
    counter.read_counter_current_chunk = Chunk;
    counter.get_counter_context_scale = Context;
    counter.resolve_counter_classes = Resolve;
    // The independent roll-bounds leaf is explicitly unbound in this fixture.
    counter.commander_min_roll = nullptr;
    counter.commander_max_roll = nullptr;
  }
};
std::string CounterCase(std::string_view name, bool fail) {
  CounterFixture f(fail);
  BattleControlSnapshot snapshot{};
  Require(ReadBattleControlSnapshot(f.bindings, f.scope, {kUnits[0]}, snapshot) ==
              BattleControlSnapshotStatus::available && snapshot.battle_control_ready,
          "production control availability changed by counter leaf");
  const auto &counter = snapshot.active_counter_inputs_v1;
  Require(counter.attempted && counter.source_combat_id == kCombat &&
              counter.source_target_province_id == kProvince,
          "counter producer did not bind actual control identity");
  Require(!f.chunk_calls.empty(), "native current chunk getter was not called");
  for (const auto &call : f.chunk_calls) {
    Require(call[0] == kRegiments[0] || call[0] == kRegiments[2],
            "absent counter row was passed to chunk getter");
    Require(call[1] == (call[0] == kRegiments[0] ? kCurrent[0] : kCurrent[2]),
            "production rawQ helper floored actual fractional Entry+18");
  }
  Require(!f.resolver_called, "readonly producer called the mutating counter resolver");
  if (fail) {
    Require(!counter.available && counter.class_count == 0 && counter.sides.empty() &&
                counter.contexts.empty() && counter.unavailable_reason == "counter_current_chunk_unavailable",
            "required getter failure did not retain isolated unavailable leaf");
  } else {
    Require(counter.available && counter.class_count == 3 && counter.sides.size() == 2 &&
                counter.contexts.size() == 2 && counter.unavailable_reason.empty(),
            "complete actual counter census was not published");
    for (std::size_t side = 0; side < 2; ++side) {
      const auto &row = counter.sides[side];
      Require(row.side_index == static_cast<std::int32_t>(side) &&
                  row.primary_owner_character_id == kPrimaries[side] &&
                  row.counter_efficiency_raw == kEfficiency[side] &&
                  row.counter_resistance_raw == kResistance[side],
              "primary identity or genuine modifier DB values changed");
      const auto &context = counter.contexts[side];
      Require(context.countered_side_index == static_cast<std::int32_t>(side) &&
                  context.countering_side_index == static_cast<std::int32_t>(1 - side) &&
                  context.countered_primary_owner_character_id == kPrimaries[side] &&
                  context.countering_primary_owner_character_id == kPrimaries[1 - side] &&
                  context.context_scale_raw == kContext[side],
              "directional primary context identity/order changed");
    }
    const auto &first = counter.sides[0].men_at_arms_entries[0];
    const auto &absent = counter.sides[0].men_at_arms_entries[1];
    const auto &opposite = counter.sides[1].men_at_arms_entries[0];
    Require(first.current_fighting_raw == 1'200'001 && first.current_chunk_raw == 1'200'001 &&
                first.stack_size_soldiers == 1 && first.targets.size() == 2 &&
                first.targets[0].class_index == 1 && first.targets[0].effectiveness_raw == 1'750'003 &&
                first.targets[1].class_index == 2 && first.targets[1].effectiveness_raw == 0 &&
                absent.status == CombatObservationStatus::absent && absent.class_index == -1 &&
                absent.current_fighting_raw == kCurrent[1] && absent.stack_size_soldiers == 0 &&
                absent.targets.empty() && opposite.current_chunk_raw == 230'000,
            "entry order/rawQ/targets/legal-negative absent row changed");
    Require(f.context_calls.size() >= 2 && f.context_calls.size() % 2 == 0,
            "directional context getter calls incomplete");
    for (std::size_t index = 0; index < f.context_calls.size(); ++index) {
      const auto side = index % 2;
      Require(f.context_calls[index][0] == kPrimaries[side] &&
                  f.context_calls[index][1] == kPrimaries[1 - side],
              "native directional callback order changed");
    }
    Require(!f.modifier_calls.empty(), "native primary modifiers were not read");
    for (const auto &call : f.modifier_calls)
      Require((call[0] == kPrimaries[0] || call[0] == kPrimaries[1]) &&
                  (call[1] == 0x113 || call[1] == 0x114),
              "modifier reader received a commander/first Army owner or wrong modifier");
  }
  snapshot.snapshot_revision = 77;
  const auto wire = xar::ck3_11906::SerializeBattleControlSnapshotV1(snapshot);
  const auto resume = xar::ck3_11906::SerializeActiveCombatResumeInputsV1(snapshot);
  Require(!wire.empty() && !resume.empty(), "production serializer rejected control counter leaf");
  Require(resume.find("\"input_observation_ready\":false") != std::string::npos,
          "current counter census changed existing resume readiness");
  return "{\"name\":\"" + std::string(name) +
      "\",\"expected_counter_available\":" + (fail ? "false" : "true") +
      ",\"getter_received_first_current_raw\":" + std::to_string(f.chunk_calls[0][1]) +
      ",\"chunk_getter_calls\":" + std::to_string(f.chunk_calls.size()) +
      ",\"modifier_getter_calls\":" + std::to_string(f.modifier_calls.size()) +
      ",\"context_getter_calls\":" + std::to_string(f.context_calls.size()) +
      ",\"battle_control_snapshot\":" + wire +
      ",\"active_combat_resume_inputs_v1\":" + resume + "}";
}
} // namespace

// Unused legacy mailbox leaves in the serializer TU are not game reads.
namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &, game::Snapshot &) noexcept { return false; }
game::BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const Bindings &, const game::BattleControlRequest &,
    game::BattleControlSnapshot &output) noexcept { return output.status; }
bool ReadCurrentBattleKnightV1(const Bindings &, const game::Snapshot &,
    const game::BattleControlSnapshot &, const game::CurrentBattleKnightRequestV1 &,
    game::CurrentBattleKnightSnapshotV1 &) noexcept { return false; }
} // namespace xar::ck3_11906


int main(int argc, char **argv) {
  try {
    Require(argc == 2, "output directory required");
    const std::string payload = "{\"schema_version\":1,\"actual\":0,\"cases\":[" +
        CounterCase("fractional_current_q_and_primary_directional_census", false) + "," +
        CounterCase("chunk_read_failure_keeps_control_available", true) + "]}";
    std::ofstream file(std::string(argv[1]) + "/active_counter_control_cases.json", std::ios::binary);
    file << payload;
    Require(static_cast<bool>(file), "production wire output failed");
    std::cout << "GREEN: 2 actual production Control+counter+serializer fixture cases; actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE-RED: " << error.what() << '\n';
    return 1;
  }
}

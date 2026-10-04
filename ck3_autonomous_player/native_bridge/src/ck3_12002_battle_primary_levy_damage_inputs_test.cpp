// Current primary getter and observed side+A0 operands; no outgoing damage routine is invoked.
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
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
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
constexpr std::array<std::int32_t, 4> kRegiments{
    0x01000005, 0x01000006, 0x01000007, 0x01000008};
constexpr std::array<std::size_t, 2> kSides{0x20, 0x368};
constexpr std::array<std::size_t, 2> kBuckets{0x28, 0x40};

// This is a bounded fake global-RVA window, not a loaded game or executable.
// Native binder addresses are checked before only callable leaves are stubbed.
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
  std::array<void *, 2642> province_rows{};
  Bytes<0x860> province{}, army_province{};
  Bytes<0x730> combat{};
  Bytes<0xD8> result{};
  std::array<Bytes<0x200>, 2> units{};
  std::array<Bytes<0x148>, 2> armies{};
  std::array<Bytes<0x220>, 2> characters{};
  std::array<Bytes<0x150>, 4> regiments{};
  std::array<Bytes<0xA20>, 4> types{};
  std::array<Bytes<0x60>, 4> entries{};
  Store unit_store, army_store, character_store, regiment_store, combat_store,
      result_store;
  BattleBindings bindings{};
  Snapshot scope{};
  std::int64_t factor = 175003;
  std::array<std::int64_t, 3> runtime{-3007, 0, 100019};
  std::array<std::int64_t, 2> own{-101007, 211009};
  std::array<std::int64_t, 2> opposing{404013, -303011};
  std::int64_t winter = -4003;
  bool has_holding = true;
  std::array<std::int64_t, 2> levy_damage{0, 125007};
  std::array<unsigned, 2> levy_damage_reads{};
  bool wrong_leaf_argument = false;
  std::array<int, 2> own_reads{}, opposing_reads{};
  int winter_reads = 0, holding_reads = 0;
  static Fixture *current;

  template <typename T> void Global(std::uintptr_t rva, T value) {
    Require(rva >= kWindowBegin && rva + sizeof(value) <= kWindowEnd,
            "fixture global range");
    std::memcpy(globals.data() + rva - kWindowBegin, &value, sizeof(value));
  }
  template <std::size_t N>
  static void Array(Bytes<N> &object, std::size_t offset, void *data,
                    std::int32_t count) {
    Put(object, offset, data);
    Put(object, offset + 8U, count);
    Put(object, offset + 12U, count);
  }
  static std::int64_t Attribute(std::size_t side, std::size_t bucket,
                                std::size_t field) {
    return static_cast<std::int64_t>((side + 1U) * 1000000U +
           (bucket + 1U) * 10000U + (field + 1U) * 100U + 7U);
  }
  static std::int32_t Strength(void *) { return 12345; }
  static void *RuleState(void *) { return nullptr; }
  static bool Retreat(void *actual_combat, void *actual_army, void *sink) {
    auto &f = *current;
    if (actual_combat != f.combat.data() || actual_army != f.armies[0].data() ||
        sink != nullptr) {
      f.wrong_leaf_argument = true;
      return false;
    }
    return Get<std::int32_t>(actual_combat, 0x6B0) < 2;
  }
  static std::int64_t *SideModifier(std::int64_t *output, void *actual_side,
                                    std::uint16_t modifier) {
    auto &f = *current;
    std::size_t side = 2;
    for (std::size_t i = 0; i != 2; ++i) {
      if (actual_side == f.combat.data() + kSides[i]) side = i;
    }
    if (side == 2 || output == nullptr ||
        (modifier != 0x199 && modifier != 0x19A)) {
      f.wrong_leaf_argument = true;
      return nullptr;
    }
    if (modifier == 0x199) {
      ++f.own_reads[side];
      *output = f.own[side];
    } else {
      ++f.opposing_reads[side];
      *output = f.opposing[side];
    }
    return output;
  }
  static std::int64_t *PrimaryLevyDamage(std::int64_t *output,
                                         void *actual_primary) {
    auto &f = *current;
    if (!output) { f.wrong_leaf_argument = true; return nullptr; }
    std::size_t side = 0;
    while (side != 2 && actual_primary != f.characters[side].data()) ++side;
    if (side == 2) { f.wrong_leaf_argument = true; return nullptr; }
    ++f.levy_damage_reads[side];
    *output = f.levy_damage[side];
    return output; // Exact .3 native callee returns saved RCX.
  }
  static bool HasHolding(void *actual_province) {
    auto &f = *current;
    ++f.holding_reads;
    if (actual_province != f.province.data()) {
      f.wrong_leaf_argument = true;
      return false;
    }
    return f.has_holding;
  }
  static std::int64_t *ProvinceModifier(std::int64_t *output, void *container,
      std::int32_t modifier, void *context, std::int64_t multiplier,
      std::int32_t mode) {
    auto &f = *current;
    ++f.winter_reads;
    if (!output || container != f.province.data() + 0x30 || modifier != 0x1AC ||
        context != nullptr || multiplier != 100000 || mode != 0) {
      f.wrong_leaf_argument = true;
      return nullptr;
    }
    *output = f.winter;
    return output;
  }
  Fixture() {
    current = this;
    scope.paused = true;
    scope.map_ready = true;
    scope.has_played_character = true;
    scope.played_character_id = kOwners[0];
    scope.date_raw = 0x029C55C0 + 15 * 24;
    Put(game_state, 8, scope.date_raw);
    Put<std::uint8_t>(jomini_state, 0x20, 1);
    Put(game_state, 0xA0, game_data.data());
    province_rows[kProvince] = province.data();
    province_rows[2641] = army_province.data();
    Put(game_data, 0x140, province_rows.data());
    Put<std::int32_t>(game_data, 0x14C, 2642);
    Put(province, 0x10, kProvince);
    Put<std::uint32_t>(province, 0x85C, 0x50726F76U);
    Put<std::int32_t>(army_province, 0x10, 2641);
    Put<std::uint32_t>(army_province, 0x85C, 0x50726F76U);
    Put(combat, 8, kCombat);
    Put(combat, 0x6B8, province.data());
    Put<std::int32_t>(combat, 0x6B0, 1);
    Put<std::int32_t>(combat, 0x6B4, 12);
    Put<std::int32_t>(combat, 0x6C0, 1200);
    Put<std::int32_t>(combat, 0x6C4, 1200);
    Put<std::int64_t>(combat, 0x6C8, -170001);
    Put<std::int64_t>(combat, 0x710, 220011);
    Put<std::int32_t>(combat, 0x6E0, -1);
    Put<std::int32_t>(combat, 0x700, -1);
    Put(combat, 0x708, kResult);
    Put(result, 8, kResult);
    Put<std::int32_t>(result, 0x2C, 0x029C55C0);
    combat_store.Set(kCombat, combat.data());
    result_store.Set(kResult, result.data());
    for (std::size_t side = 0; side != 2; ++side) {
      Put(characters[side], 0x18, kOwners[side]);
      Put<std::uint32_t>(characters[side], 0x1C, 0x43686172U);
      character_store.Set(kOwners[side], characters[side].data());
      Put(units[side], 0x10, kUnits[side]);
      Put(units[side], 0x174, kOwners[side]);
      Put(units[side], 0x178, kArmies[side]);
      Put(units[side], 0x20, army_province.data());
      Put(armies[side], 0x10, kArmies[side]);
      Put(armies[side], 0x124, kUnits[side]);
      Put(armies[side], 0x128, kCombat);
      unit_store.Set(kUnits[side], units[side].data());
      army_store.Set(kArmies[side], armies[side].data());
      Array(combat, kSides[side] + 0x10,
            const_cast<std::int32_t *>(&kArmies[side]), 1);
      Put(combat, kSides[side] + 0xB8, combat.data());
      Put(combat, kSides[side] + 0x70, kOwners[side]);
      Put<std::int32_t>(combat, kSides[side] + 0x74, -1);
      Put<std::int64_t>(combat, kSides[side] + 0x98, 4200000);
      Put<std::int64_t>(combat, kSides[side] + 0xA0, 2100000);
      for (std::size_t bucket = 0; bucket != 2; ++bucket) {
        const auto index = side * 2U + bucket;
        Put(regiments[index], 0x10, kRegiments[index]);
        Put(regiments[index], 0x18, types[index].data());
        Put(regiments[index], 0x140, kArmies[side]);
        Put<std::uint8_t>(types[index], 0x98A, 1);
        regiment_store.Set(kRegiments[index], regiments[index].data());
        Put(entries[index], 8, kRegiments[index]);
        Put<std::int64_t>(entries[index], 0x10, 3000000);
        Put<std::int64_t>(entries[index], 0x18, 2000000);
        Put<std::int64_t>(entries[index], 0x20, 500000);
        Put<std::int32_t>(entries[index], 0x30, 30);
        for (std::size_t field = 0; field != 4; ++field) {
          Put(entries[index], 0x40 + field * 8U, Attribute(side,bucket,field));
        }
        Array(combat, kSides[side] + kBuckets[bucket],
              entries[index].data(), 1);
      }
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
    Global(0x5D1F340, regiment_store.root);
    Global(kCharacterStorageSlotRva, character_store.root);
    Global(kBattleCombatStorageRva, combat_store.root);
    Global(kBattleResultStorageRva, result_store.root);
    Global(kBattleResultFallbackRva, result.data());
    Global<std::int32_t>(kBattleMinimumRetreatDaysRva, 14);
    // The admitted .3 production adapter reuses this .2 ABI binder; its outer
    // exact-build check is not altered or re-tested by this focused fixture.
    bindings = BindBattleImage(image_base, kExecutableSha256);
    Require(bindings.enabled, "production ABI binder did not admit fixture");
    Require(reinterpret_cast<std::uintptr_t>(bindings.damage_scaling) ==
                image_base + 0x5C69B90 &&
            reinterpret_cast<std::uintptr_t>(bindings.main_hard_conversion) ==
                image_base + 0x5C69BA0 &&
            reinterpret_cast<std::uintptr_t>(bindings.pursuit_hard_conversion) ==
                image_base + 0x5C69BB0,
            "production runtime slot RVAs changed");
    Require(reinterpret_cast<std::uintptr_t>(bindings.read_loss_side_modifier) ==
                image_base + 0x264DD20 &&
            reinterpret_cast<std::uintptr_t>(bindings.province_has_holding) ==
                image_base + 0xC6AF20 &&
            reinterpret_cast<std::uintptr_t>(bindings.read_loss_province_modifier) ==
                image_base + 0x2C4D550,
            "production modifier leaf RVAs changed");
    Require(reinterpret_cast<std::uintptr_t>(bindings.read_primary_levy_damage) ==
                image_base + kBattlePrimaryLevyDamageRva &&
            kBattlePrimaryLevyDamageRva == 0x2C15610,
            "production primary levy getter RVA changed");
    bindings.read_primary_levy_damage = PrimaryLevyDamage;
    bindings.get_combat_side_strength = Strength;
    bindings.get_combat_regiment_strength = Strength;
    bindings.get_combat_retreat_rule_state = RuleState;
    bindings.can_order_combat_retreat = Retreat;
    bindings.commander_roll_context = {};
    bindings.read_loss_side_modifier = SideModifier;
    bindings.province_has_holding = HasHolding;
    bindings.read_loss_province_modifier = ProvinceModifier;
  }
  void RefreshInputs() {
    Put(combat, 0x6D8, factor);
    Global(0x5C69B90, runtime[0]);
    Global(0x5C69BA0, runtime[1]);
    Global(0x5C69BB0, runtime[2]);
  }
};
Fixture *Fixture::current = nullptr;

std::string Expected(Fixture &f, bool available) {
  const auto advantage=Get<std::int64_t>(f.combat.data(),0x710);
  std::string result="{\"scale\":100000,\"source_combat_id\":"+
      std::to_string(kCombat)+",\"source_target_province_id\":"+
      std::to_string(kProvince)+",\"stored_advantage_damage_factor_raw\":"+
      std::to_string(f.factor)+",\"runtime_damage_scaling_raw\":"+
      std::to_string(f.runtime[0])+",\"runtime_main_hard_conversion_raw\":"+
      std::to_string(f.runtime[1])+",\"runtime_pursuit_hard_conversion_raw\":"+
      std::to_string(f.runtime[2])+",\"province_has_holding\":"+
      (f.has_holding ? "true" : "false")+
      ",\"province_winter_hard_conversion_modifier_raw\":"+
      std::to_string(f.has_holding ? f.winter : 0)+",\"sides\":[";
  for (std::size_t side=0;side!=2;++side) {
    if (side) result+=',';
    const auto applied=(side==0 ? advantage>0 : advantage<=0);
    result+="{\"side_index\":"+std::to_string(side)+
      ",\"outgoing_advantage_factor_raw\":"+
      std::to_string(applied ? f.factor : 100000)+
      ",\"own_hard_conversion_modifier_raw\":"+std::to_string(f.own[side])+
      ",\"opposing_hard_conversion_modifier_raw\":"+
      std::to_string(f.opposing[1U-side])+
      ",\"primary_participant_character_id\":"+std::to_string(kOwners[side])+
      ",\"levy_damage_raw\":"+
      (available ? std::to_string(f.levy_damage[side]) : "null")+"}";
  }
  return result+"]}";
}

std::string Case(std::string_view name, int index) {
  Fixture f;
  const bool bound = index == 0;
  if (!bound) f.bindings.read_primary_levy_damage = nullptr;
  f.RefreshInputs();
  const auto original_characters = f.characters;
  BattleControlSnapshot snapshot{};
  const auto status = ReadBattleControlSnapshot(f.bindings, f.scope,
                                               {kUnits[0]}, snapshot);
  Require(status == BattleControlSnapshotStatus::available &&
          snapshot.battle_control_ready, "production control reader failed");
  Require(snapshot.current_loss_inputs_v1.has_value(),
          "optional primary getter removed existing current-loss inputs");
  Require(!f.wrong_leaf_argument, "readonly getter received wrong native arguments");
  Require(f.characters == original_characters,
          "readonly primary observer changed Character backing memory");
  const std::array<const BattleControlSideSnapshot *, 2> sides{
      &snapshot.attacker, &snapshot.defender};
  const auto &input = *snapshot.current_loss_inputs_v1;
  for (std::size_t side = 0; side != 2; ++side) {
    const auto &row = input.sides[side];
    Require(row.primary_participant_character_id == kOwners[side] &&
            row.primary_participant_character_id ==
              sides[side]->primary_participant_character_id,
            "primary full-ID provenance differs from actual CCombatSide+70");
    Require(sides[side]->stored_levy_current_fighting_raw ==
              Get<std::int64_t>(f.combat.data(), kSides[side] + 0xA0) &&
            sides[side]->stored_levy_current_fighting_raw == 2100000,
            "observed side+A0 levy operand changed");
    Require(row.levy_damage_raw.has_value() == bound,
            "unbound getter differs from native observed zero");
    if (bound) {
      Require(*row.levy_damage_raw == f.levy_damage[side] &&
              f.levy_damage_reads[side] == 2,
              "production reader bypassed exact primary readonly getter");
    } else {
      Require(f.levy_damage_reads[side] == 0,
              "unbound getter was called instead of preserving null");
    }
  }
  snapshot.snapshot_revision = static_cast<std::uint64_t>(100 + index);
  const auto wire = xar::ck3_11906::SerializeBattleControlSnapshotV1(snapshot);
  Require(!wire.empty(), "production control serializer rejected new fixture");
  return "{\"name\":\"" + std::string(name) +
      "\",\"battle_control_snapshot\":" + wire +
      ",\"expected_loss_inputs_v1\":" + Expected(f, bound) + "}";
}
} // namespace

// The same serializer TU also carries unused legacy mailbox leaves. Only the
// ck3_12002 production reader above and serializer are invoked by this fixture.
namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &,game::Snapshot &) noexcept { return false; }
game::BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const Bindings &,const game::BattleControlRequest &,
    game::BattleControlSnapshot &output) noexcept { return output.status; }
bool ReadCurrentBattleKnightV1(const Bindings &,const game::Snapshot &,
    const game::BattleControlSnapshot &,const game::CurrentBattleKnightRequestV1 &,
    game::CurrentBattleKnightSnapshotV1 &) noexcept { return false; }
} // namespace xar::ck3_11906

int main(int argc,char **argv) {
  try {
    Require(argc==2,"output directory required");
    const std::array<const char *,2> names{
        "resolved_primary_getter_zero_and_nonzero",
        "unbound_primary_getter_preserves_existing_inputs"};
    std::string payload="{\"schema_version\":1,\"actual\":0,\"cases\":[";
    for (std::size_t i=0;i!=names.size();++i) {
      if (i) payload+=',';
      payload+=Case(names[i],static_cast<int>(i));
    }
    payload+="]}";
    std::ofstream output(std::string(argv[1])+"/primary_levy_damage_input_cases.json",
                         std::ios::binary);
    Require(output.good(),"could not open focused wire output");
    output<<payload<<'\n';
    Require(output.good(),"could not write focused wire output");
    std::cout<<"Primary-levy-damage production focused fixture GREEN: "
             <<names.size()<<" bounded cases; actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr<<"Primary-levy-damage production focused fixture RED: "
             <<error.what()<<'\n';
    return 1;
  }
}

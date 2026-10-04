// Current phase operands: production reader/serializer, synthetic current frames.
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
constexpr std::array<std::int32_t, 6> kRegiments{
    0x01000005, 0x01000006, 0x01000007, 0x01000008,
    0x01000009, 0x0100000A};
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
  std::array<Bytes<0x150>, 6> regiments{};
  std::array<std::array<std::int32_t,3>,2> ordered_regiments{};
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
    for (std::size_t i=0; i!=regiments.size(); ++i) {
      Put(regiments[i],0x10,kRegiments[i]);
      Put<std::int32_t>(regiments[i],0x38,
                       static_cast<std::int32_t>((i+1U)*1019U));
    }
    ordered_regiments[0]={kRegiments[4],kRegiments[1],kRegiments[0]};
    ordered_regiments[1]={kRegiments[3],kRegiments[5],kRegiments[2]};
    for (std::size_t side=0; side!=2; ++side) {
      Array(armies[side],0x38,ordered_regiments[side].data(),3);
      regiment_store.Set(kRegiments[4U+side],regiments[4U+side].data());
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



constexpr std::int32_t kExtraArmy=0x01000003;
constexpr std::int32_t kExtraUnit=0x01000013;
constexpr std::int32_t kExtraOwner=0x01000023;
struct PhaseFixture : Fixture {
  Bytes<0x148> extra_army{}, fallback_army{};
  Bytes<0x200> extra_unit{}, land{};
  Bytes<0x220> extra_owner{};
  Bytes<0x48> rules{};
  std::array<std::int32_t,2> attacker_armies{kExtraArmy,kArmies[0]};
  std::array<unsigned,4> receiver_reads{};
  bool wrong_current_receiver=false;
  static PhaseFixture *active;
  static void *OwnerRules(void *owner) {
    auto &f=*active;
    if (owner!=f.extra_owner.data()) { f.wrong_current_receiver=true; return nullptr; }
    return f.rules.data();
  }
  static bool CurrentRetreat(void *combat_receiver,void *army,void *sink) {
    auto &f=*active;
    if (combat_receiver!=f.combat.data() || sink!=nullptr) {
      f.wrong_current_receiver=true; return false;
    }
    std::size_t receiver=4;
    if (army==f.armies[0].data()) receiver=0;
    if (army==f.armies[1].data()) receiver=1;
    if (army==f.extra_army.data()) receiver=2;
    if (army==f.fallback_army.data()) receiver=3;
    if (receiver==4) { f.wrong_current_receiver=true; return false; }
    ++f.receiver_reads[receiver];
    if (receiver==3) return false; // Actual synthetic canonical receiver Boolean.
    const auto side=receiver==1 ? 1U : 0U;
    const auto offset=kSides[side];
    if (Get<std::uint8_t>(f.combat.data(),offset+0xC0)!=0) return false;
    const auto day=[](std::int32_t raw) {
      return (static_cast<std::int64_t>(raw)-0x029C55C0)/24;
    };
    if (!Get<std::uint8_t>(f.combat.data(),offset+0xC1) &&
        day(Get<std::int32_t>(f.game_state.data(),8))-
        day(Get<std::int32_t>(f.result.data(),0x2C))<=
        *f.bindings.minimum_days_before_manual_retreat) return false;
    return Get<std::int32_t>(f.combat.data(),0x6B0)<2 && receiver!=2;
  }
  PhaseFixture() {
    active=this;
    Require(reinterpret_cast<std::uintptr_t>(bindings.army_internal_fallback_slot)==
      image_base+kBattleArmyInternalFallbackRva &&
      kBattleArmyInternalFallbackRva==0x5D1DE50,
      "production canonical Army fallback binding changed");
    Put(extra_owner,0x18,kExtraOwner);
    Put<std::uint32_t>(extra_owner,0x1C,0x43686172U);
    Put(extra_owner,kBattleLandStatusOffset,land.data());
    Put<std::int32_t>(land,0x1F8,-1);
    Put<std::uint32_t>(rules,kBattleRuleFlagsOffset,0);
    character_store.Set(kExtraOwner,extra_owner.data());
    Put(extra_unit,0x10,kExtraUnit); Put(extra_unit,0x174,kExtraOwner);
    Put(extra_unit,0x178,kExtraArmy); Put(extra_unit,0x20,army_province.data());
    unit_store.Set(kExtraUnit,extra_unit.data());
    Put(extra_army,0x10,kExtraArmy); Put(extra_army,0x124,kExtraUnit);
    Put(extra_army,0x128,kCombat); army_store.Set(kExtraArmy,extra_army.data());
    Put<std::int32_t>(fallback_army,0x10,-1);
    Put<std::int32_t>(fallback_army,0x124,-1);
    Global(kBattleArmyInternalFallbackRva,fallback_army.data());
    bindings.get_combat_retreat_rule_state=OwnerRules;
    bindings.can_order_combat_retreat=CurrentRetreat;
    RefreshInputs();
  }
  void Date(std::int32_t date) {
    scope.date_raw=date; Put(game_state,8,date);
  }
};
PhaseFixture *PhaseFixture::active=nullptr;

std::string Bool(bool value) { return value ? "true" : "false"; }
std::string OptionalBool(std::optional<bool> value) {
  return value ? Bool(*value) : "null";
}
std::string OptionalId(std::optional<std::int32_t> value) {
  return value ? std::to_string(*value) : "null";
}
std::string Expected(std::size_t scenario,bool fallback_bound) {
  std::string result="{\"forced_winner_raw\":-1,\"result_start_date_raw\":"+
    std::to_string(scenario==0 ? 0x029C55C0+23 : 0)+
    ",\"minimum_elapsed_days\":"+std::to_string(scenario==0 ? 2 : 0)+",\"sides\":[";
  for (std::size_t side=0;side!=2;++side) {
    if (side) result+=',';
    (void)fallback_bound;
    const auto id=std::optional<std::int32_t>{scenario==0 ?
      (side==0 ? kExtraArmy : kArmies[1]) : kArmies[side]};
    const auto native=std::optional<bool>{scenario==1};
    const auto owner=std::optional<bool>{scenario==0 ? side==1 : true};
    result+="{\"side_index\":"+std::to_string(side)+
      ",\"stored_current_fighting_raw\":"+std::to_string(scenario==0 ? 4200000 : 0)+
      ",\"disallowed\":"+Bool(scenario==0 && side==1)+
      ",\"allow_early\":"+Bool(scenario==0 && side==1)+
      ",\"skip_pursuit\":"+Bool(scenario==0 && side==1)+
      ",\"first_native_carmy_id\":"+OptionalId(id)+
      ",\"native_can_retreat\":"+OptionalBool(native)+
      ",\"owner_land_rule_allows\":"+OptionalBool(owner)+"}";
  }
  return result+"]}";
}
std::string Observe(PhaseFixture &f,std::size_t scenario,bool fallback_bound,
                    std::string_view name,std::uint64_t revision) {
  const auto original=f.combat;
  BattleControlSnapshot out{};
  Require(ReadBattleControlSnapshot(f.bindings,f.scope,{kUnits[0]},out)==
    BattleControlSnapshotStatus::available && out.battle_control_ready,
    "existing production control reader failed");
  Require(out.current_phase_transition_inputs_v1.has_value(),
    "production phase input leaf absent");
  const auto &block=*out.current_phase_transition_inputs_v1;
  Require(block.forced_winner_raw==-1 && block.result_start_date_raw==
    (scenario==0 ? 0x029C55C0+23 : 0) && block.minimum_elapsed_days==
    (scenario==0 ? 2 : 0),"native sentinel/date/runtime operands changed");
  for (std::size_t side=0;side!=2;++side) {
    const auto &row=block.sides[side];
    Require(row.side_index==static_cast<std::int32_t>(side) &&
      row.stored_current_fighting_raw==(scenario==0 ? 4200000 : 0),
      "native ordered cached current was refreshed or lost");
    Require(row.disallowed==(scenario==0 && side==1) &&
      row.allow_early==(scenario==0 && side==1) &&
      row.skip_pursuit==(scenario==0 && side==1),"native flag values changed");
  }
  if (scenario==0) {
    Require(block.sides[0].first_native_carmy_id==kExtraArmy &&
      block.sides[0].native_can_retreat==false &&
      block.sides[0].owner_land_rule_allows==false &&
      block.sides[1].first_native_carmy_id==kArmies[1] &&
      block.sides[1].native_can_retreat==false &&
      block.sides[1].owner_land_rule_allows==true,
      "production observer substituted the selected Army/owner");
    Require(out.selected_native_carmy_id==kArmies[0] &&
      out.legality.landless_gate_allows_retreat && out.legality.elapsed_whole_days==2,
      "current timer or selected-owner context changed");
    Require(f.receiver_reads[0]==2 && f.receiver_reads[1]==2 &&
      f.receiver_reads[2]==2,"real double-sample callbacks did not visit distinct first Armies");
  } else {
    Require(block.sides[0].first_native_carmy_id==kArmies[0] &&
      block.sides[0].native_can_retreat==true &&
      block.sides[0].owner_land_rule_allows==true,"legal first receiver values lost");
    const auto &row=block.sides[1];
    Require(row.first_native_carmy_id==kArmies[1] && row.native_can_retreat==true &&
      row.owner_land_rule_allows==true,"genuine opposite-side receiver values lost");
    Require(!out.attacker.levy_entries.empty() &&
      out.attacker.levy_entries.front().current_fighting_raw>0,
      "cache-lag scenario lost positive actual Entry current");
  }
  Require(f.combat==original && !f.wrong_leaf_argument && !f.wrong_current_receiver,
    "current observer changed native data or used a wrong callback receiver");
  out.snapshot_revision=revision;
  const auto wire=xar::ck3_11906::SerializeBattleControlSnapshotV1(out);
  const auto resume=xar::ck3_11906::SerializeActiveCombatResumeInputsV1(out);
  Require(!wire.empty() && !resume.empty(),
    "existing serializer rejected current native scenario");
  return "{\"name\":\""+std::string(name)+"\",\"battle_control_snapshot\":"+
    wire+",\"active_resume_inputs\":"+resume+
    ",\"expected_phase_transition_inputs\":"+Expected(scenario,fallback_bound)+"}";
}
std::string Case(std::size_t scenario) {
  PhaseFixture f;
  if (scenario==0) {
    f.Date(0x029C55C0+48); Put<std::int32_t>(f.result,0x2C,0x029C55C0+23);
    f.Global<std::int32_t>(kBattleMinimumRetreatDaysRva,2);
    Fixture::Array(f.combat,kSides[0]+0x10,f.attacker_armies.data(),2);
    Put<std::uint8_t>(f.combat,kSides[1]+0xC0,1);
    Put<std::uint8_t>(f.combat,kSides[1]+0xC1,1);
    Put<std::uint8_t>(f.combat,kSides[1]+0xC2,1);
    return "{\"name\":\"actual_first_army_and_current_timer\",\"observations\":["+
      Observe(f,0,true,"actual_first_army",201)+"]}";
  }
  Put<std::int32_t>(f.result,0x2C,0);
  f.Global<std::int32_t>(kBattleMinimumRetreatDaysRva,0);
  for (const auto offset:kSides) Put<std::int64_t>(f.combat,offset+0x98,0);
  return "{\"name\":\"legal_zero_and_cache_lag\",\"observations\":["+
    Observe(f,1,true,"genuine_nonempty_zero",202)+"]}";
}
} // namespace
namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &,game::Snapshot &) noexcept { return false; }
game::BattleControlSnapshotStatus ReadBattleControlSnapshot(
  const Bindings &,const game::BattleControlRequest &,game::BattleControlSnapshot &out) noexcept {
  return out.status;
}
bool ReadCurrentBattleKnightV1(const Bindings &,const game::Snapshot &,
  const game::BattleControlSnapshot &,const game::CurrentBattleKnightRequestV1 &,
  game::CurrentBattleKnightSnapshotV1 &) noexcept { return false; }
}
int main(int argc,char **argv) {
  try {
    Require(argc==2,"output directory required");
    std::ofstream stream(std::string(argv[1])+"/phase_transition_input_cases.json",std::ios::binary);
    Require(stream.good(),"could not open focused wire output");
    stream<<"{\"schema_version\":1,\"actual\":0,\"cases\":["<<Case(0)<<','<<Case(1)<<"]}\n";
    Require(stream.good(),"could not write focused wire output");
    std::cout<<"Current-phase input production fixture GREEN: 2 cases, actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr<<"Current-phase input production fixture RED: "<<error.what()<<'\n';
    return 1;
  }
}

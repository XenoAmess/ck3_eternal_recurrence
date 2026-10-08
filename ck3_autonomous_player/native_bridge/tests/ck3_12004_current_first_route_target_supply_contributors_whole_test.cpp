#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar;
namespace current = ck3_12004;
constexpr std::int32_t kUnit=0x01000001, kArmy=0x02000001, kRegiment=0x03000001;
constexpr std::int32_t kCommander=0x05000001, kForeignUnit=0x01000002;
constexpr std::int32_t kForeignOwner=0x06000002, kInvalidUnit=0x07000005;
struct Scene { std::string_view stem; std::int32_t count, usage; bool duplicate; };
constexpr std::array<Scene,3> kScenes{{
    {"01-target-subject-absent",0,0,false},
    {"02-target-subject-duplicate",2,200,true},
    {"03-target-excluded-and-unresolved",2,0,false}}};
void Check(bool ok,const std::string &message) { if(!ok) throw std::runtime_error(message); }
template<class T,std::size_t N>
void Store(std::array<std::byte,N> &object,std::size_t offset,T value) {
  Check(offset<=N && sizeof(T)<=N-offset,"fixture Store out of bounds");
  std::memcpy(object.data()+offset,&value,sizeof value);
}
template<class T> T Load(const void *object,std::size_t offset) {
  T value{}; std::memcpy(&value,static_cast<const std::byte *>(object)+offset,sizeof value); return value;
}
void AppendString(std::string &out,std::string_view value) {
  out+='"';
  for(char ch:value) {
    if(ch=='"' || ch=='\\') out+='\\';
    if(ch=='\n') out+="\\n"; else if(ch=='\r') out+="\\r";
    else if(ch=='\t') out+="\\t"; else out+=ch;
  }
  out+='"';
}
void AppendIds(std::string &out,const std::vector<std::int32_t> &values) {
  out+='[';
  for(std::size_t i=0;i<values.size();++i) { if(i) out+=','; out+=std::to_string(values[i]); }
  out+=']';
}
// Fixture-owned original memory only. The actual reader constructs every DTO.
// Large inputs and their readonly before-copy are allocated directly on the heap.
struct Inputs {
  std::array<std::byte,0xA8> game_state{};
  std::array<std::byte,0x160> game_data{};
  std::array<std::byte,0x30> unit_storage{},army_storage{},regiment_storage{},unit_slots{};
  std::array<std::byte,0x20> army_slots{},regiment_slots{};
  std::array<std::byte,0x1C0> unit{},foreign_unit{};
  std::array<std::byte,0x200> army{};
  std::array<std::byte,0x180> regiment{};
  std::array<std::byte,0x900> province{},target{};
  std::array<std::byte,0xC0> province_definition{},target_definition{};
  std::array<void *,3> provinces{};
  std::array<std::byte,0x30> character_storage{};
  std::array<std::byte,16*29830> character_slots{};
  std::array<std::byte,0x400> owner{},foreign_owner{},commander{};
  std::array<std::byte,0x20> fallback{};
  std::array<std::byte,0x100> modifier_aggregator{};
  std::array<std::uint16_t,1> modifier_keys{0x1A9};
  std::array<std::int64_t,1> modifier_values{0};
  std::array<std::int32_t,1> current_ids{kUnit},route_ids{2};
  std::array<void *,1> route_pointers{};
  std::array<std::int32_t,2> target_ids{},regiment_ids{kRegiment,kRegiment};
  std::int64_t gain=2000000,slope=100000,min_loss=100000,max_loss=500000,floor=100000;
  friend bool operator==(const Inputs &,const Inputs &)=default;
};
struct Calls {
  std::map<std::string,std::size_t> counts;
  std::vector<std::string> events,abi_failures;
  std::array<std::size_t,4> soldier_flags{};
  std::vector<std::int32_t> eligible_ids,modifier_ordinals;
};
struct Fixture;
Fixture *active=nullptr;
std::int32_t CurrentSoldiers(void *,std::uint8_t);
std::int32_t MaximumSoldiers(void *);
std::int64_t *Capacity(std::int64_t *,void *,void *);
std::int64_t *Attrition(void *,std::int64_t *,void *);
std::int64_t *MonthlySupply(void *,std::int64_t *,void *,void *);
std::int32_t ProvinceLimit(void *,void *,void *,void *);
std::int32_t ProvinceUsage(void *,void *,std::int32_t,std::int64_t *);
bool RegimentEligible(void *);
bool SharesWarSide(void *,void *,void *);
bool FleetActive(void *);
bool Resupply(void *,void *);
bool ProvinceCondition(void *);
std::int64_t *ProvinceComponent(std::int64_t *,void *,std::int32_t,void *,std::int64_t,std::int32_t);
void *ModifierAggregator(void *);
std::int64_t *ReadModifier(void *,std::int64_t *,std::int32_t);
struct Fixture {
  Inputs input{};
  Scene scene;
  current::ArmyBindings bindings{};
  Calls calls{};
  void *game_slot=input.game_state.data(),*unit_slot=input.unit_storage.data();
  void *army_slot=input.army_storage.data(),*regiment_slot=input.regiment_storage.data();
  void *character_slot=input.character_storage.data(),*fallback_slot=input.fallback.data();
  explicit Fixture(Scene value):scene(value) {
    Store(input.game_state,0x08,std::int64_t{53288448});
    Store(input.game_state,0xA0,static_cast<void *>(input.game_data.data()));
    input.provinces={nullptr,input.province.data(),input.target.data()};
    Store(input.game_data,0x140,static_cast<void *>(input.provinces.data()));
    Store(input.game_data,0x14C,std::int32_t{3});
    Store(input.province,0x10,std::int32_t{1});
    Store(input.province,0x20,static_cast<void *>(input.province_definition.data()));
    Store(input.province,0x740,static_cast<void *>(input.current_ids.data()));
    Store(input.province,0x74C,std::int32_t{1});
    Store(input.province,0x85C,std::uint32_t{0x50726F76});
    Store(input.target,0x10,std::int32_t{2});
    Store(input.target,0x20,static_cast<void *>(input.target_definition.data()));
    input.target_ids=scene.duplicate ? std::array<std::int32_t,2>{kUnit,kUnit}
        : std::array<std::int32_t,2>{kForeignUnit,kInvalidUnit};
    Store(input.target,0x740,scene.count==0 ? static_cast<void *>(nullptr)
        : static_cast<void *>(input.target_ids.data()));
    Store(input.target,0x74C,scene.count);
    Store(input.target,0x85C,std::uint32_t{0x50726F76});
    Store(input.unit_storage,0x20,static_cast<void *>(input.unit_slots.data()));
    Store(input.unit_storage,0x2C,std::int32_t{3});
    Store(input.unit_slots,0x18,static_cast<void *>(input.unit.data()));
    Store(input.unit_slots,0x28,static_cast<void *>(input.foreign_unit.data()));
    Store(input.army_storage,0x20,static_cast<void *>(input.army_slots.data()));
    Store(input.army_storage,0x2C,std::int32_t{2});
    Store(input.army_slots,0x18,static_cast<void *>(input.army.data()));
    Store(input.regiment_storage,0x20,static_cast<void *>(input.regiment_slots.data()));
    Store(input.regiment_storage,0x2C,std::int32_t{2});
    Store(input.regiment_slots,0x18,static_cast<void *>(input.regiment.data()));
    Store(input.unit,0x10,kUnit);
    Store(input.unit,0x20,static_cast<void *>(input.province.data()));
    input.route_pointers[0]=input.route_ids.data();
    Store(input.unit,0x38,static_cast<void *>(input.route_pointers.data()));
    Store(input.unit,0x40,std::int32_t{1});
    Store(input.unit,0x44,std::int32_t{1});
    Store(input.unit,0x174,std::int32_t{29829});
    Store(input.unit,0x178,kArmy);
    Store(input.foreign_unit,0x10,kForeignUnit);
    Store(input.foreign_unit,0x20,static_cast<void *>(input.target.data()));
    Store(input.foreign_unit,0x174,kForeignOwner);
    Store(input.foreign_unit,0x178,std::int32_t{-1});
    Store(input.army,0x10,kArmy);
    Store(input.army,0x14,std::uint32_t{0x41726D79});
    Store(input.army,0x120,kCommander);
    Store(input.army,0x124,kUnit);
    Store(input.army,0x12C,std::int32_t{-1});
    Store(input.army,0x38,static_cast<void *>(input.regiment_ids.data()));
    Store(input.army,0x40,std::int32_t{2});
    Store(input.army,0x44,std::int32_t{2});
    Store(input.army,0x180,std::int64_t{100000000});
    Store(input.regiment,0x10,kRegiment);
    Store(input.regiment,0x14,std::uint32_t{0x41725267});
    Store(input.regiment,0x38,std::int32_t{50});
    Store(input.regiment,0x3C,std::int32_t{100});
    Store(input.regiment,0x40,std::int64_t{25000000});
    Store(input.character_storage,0x20,static_cast<void *>(input.character_slots.data()));
    Store(input.character_storage,0x2C,std::int32_t{29830});
    Store(input.character_slots,16*29829+8,static_cast<void *>(input.owner.data()));
    Store(input.character_slots,16+8,static_cast<void *>(input.commander.data()));
    Store(input.character_slots,32+8,static_cast<void *>(input.foreign_owner.data()));
    Store(input.owner,0x18,std::int32_t{29829});
    Store(input.owner,0x1C,std::uint32_t{0x43686172});
    Store(input.commander,0x18,kCommander);
    Store(input.commander,0x1C,std::uint32_t{0x43686172});
    Store(input.foreign_owner,0x18,kForeignOwner);
    Store(input.foreign_owner,0x1C,std::uint32_t{0x43686172});
    Store(input.fallback,0x18,std::int32_t{-1});
    Store(input.modifier_aggregator,0x68,static_cast<void *>(input.modifier_keys.data()));
    Store(input.modifier_aggregator,0x74,std::int32_t{1});
    Store(input.modifier_aggregator,0xD0,static_cast<void *>(input.modifier_values.data()));
    bindings.enabled=true;
    bindings.game_state_slot=&game_slot;
    bindings.unit_storage_slot=&unit_slot;
    bindings.internal_army_storage_slot=&army_slot;
    bindings.regiment_storage_slot=&regiment_slot;
    bindings.get_army_current_soldiers=CurrentSoldiers;
    bindings.get_army_maximum_soldiers=MaximumSoldiers;
    bindings.get_army_supply_capacity=Capacity;
    bindings.get_army_attrition_fraction=Attrition;
    bindings.get_army_monthly_supply_change=MonthlySupply;
    bindings.get_province_supply_limit=ProvinceLimit;
    bindings.get_province_supply_usage=ProvinceUsage;
    bindings.is_regiment_supply_loss_eligible=RegimentEligible;
    bindings.current_province_supply_contributor_bindings={true,SharesWarSide};
    bindings.current_movement_progress_enabled=true;
    // Reuse this existing registry without enabling the monthly-budget family.
    bindings.monthly_loss_budget_bindings.character_storage_slot=&character_slot;
    bindings.province_supply_character_fallback_slot=&fallback_slot;
    auto &resupply=bindings.current_land_resupply_bindings;
    resupply.enabled=true;
    resupply.is_army_fleet_supply_active=FleetActive;
    resupply.is_resupply_eligible=Resupply;
    resupply.character_storage_slot=&character_slot;
    resupply.loaded_gain_raw=&input.gain;
    auto &land=bindings.current_land_supply_rate_bindings;
    land.enabled=true;
    land.province_component_condition=ProvinceCondition;
    land.read_province_component=ProvinceComponent;
    land.character_storage_slot=&character_slot;
    land.character_fallback_slot=&fallback_slot;
    land.get_character_modifier_aggregator=ModifierAggregator;
    land.read_character_modifier=ReadModifier;
    land.loaded_excess_slope_raw=&input.slope;
    land.loaded_min_loss_raw=&input.min_loss;
    land.loaded_max_loss_raw=&input.max_loss;
    land.loaded_divisor_floor_raw=&input.floor;
  }
};
std::string PointerText(const void *value) { return std::to_string(reinterpret_cast<std::uintptr_t>(value)); }
void Record(std::string name,bool matches,std::string arguments) {
  ++active->calls.counts[name];
  active->calls.events.push_back(std::move(name));
  if(!matches) active->calls.abi_failures.push_back(std::move(arguments));
}
std::int32_t CurrentSoldiers(void *receiver,std::uint8_t flags) {
  Record("current_soldiers_flags_"+std::to_string(flags),
      receiver==active->input.army.data()+0x38 && (flags==0 || flags==2),
      "CurrentSoldiers receiver="+PointerText(receiver)+" flags="+std::to_string(flags));
  if(flags<active->calls.soldier_flags.size()) ++active->calls.soldier_flags[flags];
  return 100;
}
std::int32_t MaximumSoldiers(void *receiver) {
  Record("maximum_soldiers",receiver==active->input.army.data(),"MaximumSoldiers receiver="+PointerText(receiver));
  return 200;
}
std::int64_t *Capacity(std::int64_t *out,void *receiver,void *details) {
  Record("capacity",out && receiver==active->input.army.data() && !details,
      "Capacity receiver="+PointerText(receiver)+" details="+PointerText(details));
  if(out) *out=200000000; return out;
}
std::int64_t *Attrition(void *receiver,std::int64_t *out,void *details) {
  Record("attrition",out && receiver==active->input.army.data() && !details,
      "Attrition receiver="+PointerText(receiver)+" details="+PointerText(details));
  if(out) *out=0; return out;
}
std::int64_t *MonthlySupply(void *receiver,std::int64_t *out,void *province,void *details) {
  Record("monthly_supply",out && receiver==active->input.army.data() &&
      province==active->input.province.data() && !details,
      "MonthlySupply receiver="+PointerText(receiver)+" province="+PointerText(province));
  if(out) *out=2000000; return out;
}
std::int32_t ProvinceLimit(void *province,void *owner,void *commander,void *details) {
  const bool target=province==active->input.target.data();
  Record(target?"target_limit":"current_limit",(target || province==active->input.province.data()) &&
      owner==active->input.owner.data() && commander==active->input.commander.data() && !details,
      "ProvinceLimit province="+PointerText(province)+" owner="+PointerText(owner)+
      " commander="+PointerText(commander)+" details="+PointerText(details));
  return 100;
}
std::int32_t ProvinceUsage(void *province,void *owner,std::int32_t mode,std::int64_t *details) {
  const bool target=province==active->input.target.data();
  Record(target?"target_usage":"current_usage",(target || province==active->input.province.data()) &&
      owner==active->input.owner.data() && mode==0 && !details,
      "ProvinceUsage province="+PointerText(province)+" owner="+PointerText(owner)+
      " mode="+std::to_string(mode)+" details="+PointerText(details));
  return target?active->scene.usage:100;
}
bool RegimentEligible(void *regiment) {
  Record("regiment_eligible",regiment==active->input.regiment.data(),"RegimentEligible receiver="+PointerText(regiment));
  if(regiment) active->calls.eligible_ids.push_back(Load<std::int32_t>(regiment,0x10));
  return true;
}
bool SharesWarSide(void *left,void *right,void *details) {
  Record("target_foreign_common_war_side",left==active->input.owner.data() &&
      right==active->input.foreign_owner.data() && !details,
      "SharesWarSide left="+PointerText(left)+" right="+PointerText(right)+" details="+PointerText(details));
  return false;
}
bool FleetActive(void *army) {
  Record("current_fleet_active",army==active->input.army.data(),"FleetActive receiver="+PointerText(army)); return false;
}
bool Resupply(void *owner,void *province) {
  Record("current_resupply",owner==active->input.owner.data() && province==active->input.province.data(),
      "Resupply owner="+PointerText(owner)+" province="+PointerText(province)); return true;
}
bool ProvinceCondition(void *province) {
  Record("current_component_condition",province==active->input.province.data(),"ProvinceCondition receiver="+PointerText(province));
  return true;
}
std::int64_t *ProvinceComponent(std::int64_t *out,void *receiver,std::int32_t ordinal,
    void *details,std::int64_t multiplier,std::int32_t mode) {
  Record("current_component",out && receiver==active->input.province.data()+0x30 &&
      ordinal==0x1AB && !details && multiplier==100000 && mode==0,
      "ProvinceComponent receiver="+PointerText(receiver)+" ordinal="+std::to_string(ordinal)+
      " multiplier="+std::to_string(multiplier)+" mode="+std::to_string(mode));
  if(out) *out=0; return out;
}
void *ModifierAggregator(void *commander) {
  Record("current_commander_aggregator",commander==active->input.commander.data(),
      "ModifierAggregator receiver="+PointerText(commander)); return active->input.modifier_aggregator.data();
}
std::int64_t *ReadModifier(void *receiver,std::int64_t *out,std::int32_t ordinal) {
  Record("current_commander_modifier",out && receiver==active->input.modifier_aggregator.data()+0x68 && ordinal==0x1A9,
      "ReadModifier receiver="+PointerText(receiver)+" ordinal="+std::to_string(ordinal));
  active->calls.modifier_ordinals.push_back(ordinal);
  if(out) *out=active->input.modifier_values[0]; return out;
}
std::string Diagnostics(const Fixture &f) {
  std::string out="{\"counts\":{"; bool first=true;
  for(const auto &[name,value]:f.calls.counts) {
    if(!first) out+=','; first=false; AppendString(out,name); out+=':'+std::to_string(value);
  }
  out+="},\"soldier_flags\":[";
  for(std::size_t i=0;i<f.calls.soldier_flags.size();++i) {
    if(i) out+=','; out+=std::to_string(f.calls.soldier_flags[i]);
  }
  out+="],\"eligible_regiment_ids\":"; AppendIds(out,f.calls.eligible_ids);
  out+=",\"modifier_ordinals\":"; AppendIds(out,f.calls.modifier_ordinals);
  out+=",\"abi_failures\":[";
  for(std::size_t i=0;i<f.calls.abi_failures.size();++i) {
    if(i) out+=','; AppendString(out,f.calls.abi_failures[i]);
  }
  out+="],\"ordered_events\":[";
  for(std::size_t i=0;i<f.calls.events.size();++i) {
    if(i) out+=','; AppendString(out,f.calls.events[i]);
  }
  return out+"]}";
}
void AssertCount(const Fixture &f,const char *name,std::size_t expected) {
  const auto found=f.calls.counts.find(name);
  const auto actual=found==f.calls.counts.end()?0:found->second;
  Check(actual==expected,"callback "+std::string(name)+" expected="+std::to_string(expected)+
      " actual="+std::to_string(actual)+" "+Diagnostics(f));
}
void AssertScene(const Fixture &f,const Inputs &before,const game::ArmyStrengthSnapshot &row) {
  Check(row.available && row.army_id==kUnit && row.native_carmy_id==kArmy &&
      row.native_carmy_id_observable,"whole subject identities changed");
  Check(row.current_soldiers==100 && row.maximum_soldiers==200 && row.regiment_count==2 &&
      row.regiment_strengths && row.regiment_strengths->size()==2 &&
      (*row.regiment_strengths)[0].army_regiment_id==kRegiment &&
      (*row.regiment_strengths)[1].army_regiment_id==kRegiment,
      "original whole subject duplicate regiment roster/totals changed");
  Check(row.current_supply_raw==100000000 && row.current_supply_capacity_raw==200000000 &&
      row.current_supply_change_monthly_raw==2000000 && row.current_attrition_fraction_raw==0,
      "original current stock/capacity/LAND rate changed");
  Check(row.current_movement_progress &&
      row.current_movement_progress->unavailable_reason=="movement_getters_unavailable",
      "NULL movement getters must remain an independent unavailable observation");
  Check(row.current_province_supply_contributors_v1.has_value(),"current contributor sibling omitted");
  const auto &original=*row.current_province_supply_contributors_v1;
  Check(original.status=="available" && original.current_usage_ready && original.contributors_ready &&
      original.province_id==1 && original.native_province_unit_count==1 &&
      original.native_supply_usage_soldiers==100 && original.native_supply_limit_soldiers==100 &&
      original.occurrences.size()==1 && original.occurrences[0].army_id==kUnit &&
      original.occurrences[0].native_eligible_current_soldiers==100 &&
      original.occurrences[0].included==true && original.occurrences[0].regiments.size()==2,
      "current contributor context was replaced by target context");
  Check(row.current_land_resupply_v1 && row.current_land_resupply_v1->current_observation_ready &&
      row.current_land_resupply_v1->province_id==1 &&
      row.current_land_resupply_v1->native_resupply_eligible==true &&
      row.current_land_supply_rate_inputs_v1 && row.current_land_supply_rate_inputs_v1->current_observation_ready &&
      row.current_land_supply_rate_inputs_v1->province_id==1 &&
      row.current_land_supply_rate_inputs_v1->province_component_raw==0 &&
      row.current_land_supply_rate_inputs_v1->commander_modifier_1a9_raw==0,
      "original current LAND/resupply observers changed");
  Check(row.current_first_route_target_supply_contributors_v1.has_value(),"production target contributor hook omitted");
  const auto &target=*row.current_first_route_target_supply_contributors_v1;
  Check(target.subject_army_id==kUnit && target.subject_carmy_id==kArmy &&
      target.current_province_id==1 && target.first_route_target_province_id==2 &&
      target.route_source_count==1 && target.target_contributors_v1,"original first target/subject join changed");
  const auto &inputs=*target.target_contributors_v1;
  Check(inputs.current_usage_ready && inputs.province_id==2 && inputs.subject_army_id==kUnit &&
      inputs.subject_carmy_id==kArmy && inputs.native_supply_limit_soldiers==100 &&
      inputs.native_supply_usage_soldiers==f.scene.usage && inputs.native_province_unit_count==f.scene.count &&
      inputs.occurrences.size()==static_cast<std::size_t>(f.scene.count),
      "target scalar/roster did not use the genuine target pointer");
  if(f.scene.count==0) {
    Check(target.status=="available" && target.current_target_inputs_ready && inputs.contributors_ready &&
        target.subject_matching_occurrence_indices.empty() && target.subject_included_occurrence_count==0 &&
        inputs.occurrences.empty(),"legitimate empty target roster/absence changed");
  } else if(f.scene.duplicate) {
    Check(target.status=="available" && target.current_target_inputs_ready && inputs.contributors_ready &&
        target.subject_matching_occurrence_indices==std::vector<std::int32_t>({0,1}) &&
        target.subject_included_occurrence_count==2,"subject duplicate matches were deduplicated");
    for(std::int32_t i=0;i<2;++i) {
      const auto &occ=inputs.occurrences[static_cast<std::size_t>(i)];
      Check(occ.available && occ.stored_index==i && occ.army_id==kUnit && occ.included==true &&
          occ.native_eligible_current_soldiers==100 && occ.native_carmy_id==kArmy && occ.regiments.size()==2 &&
          occ.regiments[0].army_regiment_id==kRegiment && occ.regiments[1].army_regiment_id==kRegiment,
          "target duplicate flags2 count/Reg duplicate evidence changed");
    }
  } else {
    Check(target.status=="partial" && !target.current_target_inputs_ready &&
        target.unavailable_reason=="current_province_contributors_partial" && !inputs.contributors_ready &&
        target.subject_matching_occurrence_indices.empty() && !target.subject_included_occurrence_count,
        "partial target roster was erased or completed");
    const auto &foreign=inputs.occurrences[0]; const auto &invalid=inputs.occurrences[1];
    Check(foreign.available && foreign.army_id==kForeignUnit && foreign.owner_character_id==kForeignOwner &&
        foreign.included==false && foreign.inclusion_basis=="native_not_common_war_side" &&
        !foreign.native_carmy_id && !foreign.native_eligible_current_soldiers && foreign.regiments.empty() &&
        !invalid.available && invalid.army_id==kInvalidUnit &&
        invalid.unavailable_reason=="province_contributor_unit_unresolved" && !invalid.included,
        "native exclusion/unresolved source order changed");
  }
  const auto extra=f.scene.duplicate?std::size_t{2}:std::size_t{0};
  AssertCount(f,"current_soldiers_flags_0",1); AssertCount(f,"current_soldiers_flags_2",1+extra);
  AssertCount(f,"regiment_eligible",4+2*extra);
  for(const auto name:{"current_limit","current_usage","target_limit","target_usage","maximum_soldiers",
                      "capacity","attrition","monthly_supply","current_fleet_active","current_resupply",
                      "current_component_condition","current_component","current_commander_aggregator",
                      "current_commander_modifier"}) AssertCount(f,name,1);
  AssertCount(f,"target_foreign_common_war_side",f.scene.count>0 && !f.scene.duplicate?1:0);
  Check(f.calls.abi_failures.empty(),"callback actual ABI failures: "+Diagnostics(f));
  std::vector<std::string> expected{
      "regiment_eligible","regiment_eligible","current_soldiers_flags_0","maximum_soldiers",
      "capacity","attrition","monthly_supply","current_limit","current_usage","current_soldiers_flags_2",
      "regiment_eligible","regiment_eligible","target_limit","target_usage"};
  for(std::size_t i=0;i<extra;++i) {
    expected.emplace_back("current_soldiers_flags_2");
    expected.emplace_back("regiment_eligible"); expected.emplace_back("regiment_eligible");
  }
  if(f.scene.count>0 && !f.scene.duplicate) expected.emplace_back("target_foreign_common_war_side");
  for(const auto name:{"current_fleet_active","current_resupply","current_component_condition","current_component",
                      "current_commander_aggregator","current_commander_modifier"}) expected.emplace_back(name);
  Check(f.calls.events==expected,"actual callback order differs: "+Diagnostics(f));
  Check(f.calls.modifier_ordinals==std::vector<std::int32_t>({0x1A9}) &&
      f.calls.eligible_ids==std::vector<std::int32_t>(4+2*extra,kRegiment),
      "actual callback operand IDs/ordinals differ: "+Diagnostics(f));
  Check(f.input==before,"readonly whole reader changed original route/registries/target/current inputs");
}
std::string Whole(const Fixture &f,const game::ArmyStrengthSnapshot &row) {
  std::string out="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(out,f.scene.stem);
  out+=",\"ok\":true,\"result\":{\"step\":\"query-army-strengths-v1\",\"accepted\":true,"
      "\"status\":\"available\",\"query_sequence\":1,\"army_strengths\":[";
  game::AppendArmyStrengthV1(out,row,[](auto raw){return std::to_string(raw);},AppendIds,AppendString);
  out+="]}}";
  return game::Render12004BuildIdentity(std::move(out),game::Ck3_12004AdapterDescriptor());
}
std::string Context(const Fixture &f) {
  std::string out="{\"schema\":\"xar.current-first-route-target-supply-contributors-native-context.v1\",\"scene\":";
  AppendString(out,f.scene.stem);
  out+=",\"producer\":\"ReadArmyStrengthsForScope12004 -> AppendArmyStrengthV1 -> Render12004BuildIdentity\","
      "\"synthetic_context\":{\"actor_character_id\":29829,\"public_revision\":1,\"native_revision\":1,"
      "\"snapshot_id\":\"native:1\",\"date_raw\":53288448,\"paused\":true,\"map_ready\":true,"
      "\"bridge_host_pid\":1200401,\"current_province_id\":1,\"scope_role\":\"player\","
      "\"scope_army_ids\":[16777217],\"war_ids\":[],\"route_province_ids\":[2],"
      "\"transport_connection_id\":\"current-first-route-target-contributors-12004\","
      "\"episode_id\":\"current-first-route-target-contributors-12004\"},"
      "\"synthetic_army_context\":{\"army_id\":16777217,\"owner_character_id\":29829,"
      "\"current_province_id\":1,\"route_province_ids\":[2],\"move_target_province_id\":2},"
      "\"heartbeat_published\":false,\"native_fixture_inputs\":{\"subject_army_id\":16777217,"
      "\"subject_carmy_id\":33554433,\"current_province_id\":1,\"first_route_target_province_id\":2,"
      "\"route_source_count\":1,\"current_native_usage_soldiers\":100,\"target_native_limit_soldiers\":100,"
      "\"target_native_usage_soldiers\":";
  out+=std::to_string(f.scene.usage);
  out+=",\"target_native_unit_count\":"+std::to_string(f.scene.count)+",\"target_original_unit_ids\":";
  std::vector<std::int32_t> target_ids;
  for(std::int32_t i=0;i<f.scene.count;++i) target_ids.push_back(f.input.target_ids[static_cast<std::size_t>(i)]);
  AppendIds(out,target_ids);
  out+="},\"callbacks\":"+Diagnostics(f)+",\"all_fixture_input_bytes_unchanged\":true,"
      "\"native_EXE_callback_invoked\":false,\"actual_arrival_observed\":false,"
      "\"actual_after_arrival_usage_observed\":false,\"full_arrival_supply_transition_ready\":false,"
      "\"old_GREEN_replayed\":false}";
  return out;
}
void Write(const std::filesystem::path &path,const std::string &content) {
  std::ofstream out(path,std::ios::binary); out<<content<<'\n';
  Check(static_cast<bool>(out),"artifact write failed: "+path.string());
}
} // namespace
int main(int argc,char **argv) {
  std::filesystem::path output; std::unique_ptr<Fixture> fixture;
  try {
    Check(argc==3 && std::string_view(argv[1])=="--wire-dir",
        "usage: xar_ck3_12004_current_first_route_target_supply_contributors_whole_test --wire-dir <fresh-dir>");
    output=argv[2]; std::filesystem::create_directories(output);
    for(const auto scene:kScenes) {
      fixture=std::make_unique<Fixture>(scene);
      auto before=std::make_unique<Inputs>(fixture->input);
      active=fixture.get();
      const std::array<current::ArmyStrengthScope,1> scope{
          current::ArmyStrengthScope{kUnit,game::ArmyStrengthScopeRole::player,{}}};
      std::vector<game::ArmyStrengthSnapshot> rows;
      const auto status=current::ReadArmyStrengthsForScope12004(fixture->bindings,scope,rows);
      Check(status==game::ReadArmyStrengthsResult::available && rows.size()==1,
          "actual whole reader status="+std::to_string(static_cast<int>(status))+
          " row_count="+std::to_string(rows.size())+" "+Diagnostics(*fixture));
      AssertScene(*fixture,*before,rows.front());
      Write(output/(std::string(scene.stem)+".json"),Whole(*fixture,rows.front()));
      Write(output/(std::string(scene.stem)+"-native-context.json"),Context(*fixture));
      active=nullptr;
    }
    Write(output/"PRODUCER-RECEIPT.json",
        "{\"schema\":\"xar.current-first-route-target-supply-contributors-producer-receipt.v1\","
        "\"status\":\"PASS\",\"scene_count\":3,\"whole_reader_calls\":3,\"whole_serializer_calls\":3,"
        "\"fixture_owned_objects_and_callbacks\":true,\"native_EXE_callback_invoked\":false,"
        "\"actual_arrival_observed\":false,\"all_fixture_input_bytes_unchanged\":true,\"old_GREEN_replayed\":false}");
    std::cout<<"three current first route target contributor whole scenes emitted\n"; return 0;
  } catch(const std::exception &error) {
    std::string receipt="{\"schema\":\"xar.current-first-route-target-supply-contributors-producer-receipt.v1\","
        "\"status\":\"FAIL\",\"error\":";
    AppendString(receipt,error.what());
    if(fixture) {
      receipt+=",\"scene\":"; AppendString(receipt,fixture->scene.stem);
      receipt+=",\"actual_callbacks\":"+Diagnostics(*fixture);
    }
    receipt+=",\"native_EXE_callback_invoked\":false}";
    if(!output.empty()) { std::ofstream out(output/"PRODUCER-RECEIPT.json",std::ios::binary); out<<receipt<<'\n'; }
    active=nullptr; std::cerr<<receipt<<'\n'; return 1;
  }
}

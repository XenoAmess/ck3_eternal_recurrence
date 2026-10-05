#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
template<class T,class Bytes> void Put(Bytes &bytes,std::size_t offset,T value) {
  std::memcpy(bytes.data()+offset,&value,sizeof value);
}
void Check(bool value,const char *message) { if(!value) throw std::runtime_error(message); }
std::int32_t Current(void *,std::uint8_t) { return 0; }
std::int32_t Maximum(void *) { return 0; }
void Emit(const std::filesystem::path &directory,const char *label,const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire,row,
      [](auto value){return std::to_string(value);},
      [](std::string &out,const std::vector<std::int32_t> &values){
        out+='[';
        for(std::size_t i=0;i<values.size();++i) {
          if(i!=0) out+=',';
          out+=std::to_string(values[i]);
        }
        out+=']';
      },
      [](std::string &out,std::string_view value){out+='"';out+=value;out+='"';});
  std::filesystem::create_directories(directory);
  std::ofstream file(directory/(std::string(label)+".json"),std::ios::binary);
  Check(static_cast<bool>(file),"production wire output");file<<wire<<'\n';
}
void Cases(const std::filesystem::path &directory) {
  constexpr std::int32_t unit_id=0x01000001,army_id=0x02000001;
  std::array<std::byte,0x180> unit{};
  std::array<std::byte,0x208> army{},fallback_army{};
  std::array<std::byte,0xB0> state{};
  std::array<std::byte,0x30> units{},armies{},regiments{},unit_slots{},army_slots{};
  std::vector<std::byte> manager(0x2A5C0);
  std::array<std::int32_t,4> queue{0x03000001,army_id,army_id,-1};
  Put(unit,0x10,unit_id);Put(unit,0x178,army_id);
  Put(army,0x10,army_id);Put(army,0x14,std::uint32_t{0x41726D79});Put(army,0x124,unit_id);
  Put(fallback_army,0x10,std::int32_t{-1});Put(fallback_army,0x14,std::uint32_t{0x41726D79});
  Put(state,0xA0,static_cast<void *>(manager.data()));
  Put(manager,0x2A5A8,static_cast<void *>(queue.data()));
  Put(manager,0x2A5B0,std::int32_t{4});Put(manager,0x2A5B4,std::int32_t{4});
  Put(unit_slots,0x18,static_cast<void *>(unit.data()));Put(army_slots,0x18,static_cast<void *>(army.data()));
  Put(units,0x20,static_cast<void *>(unit_slots.data()));Put(units,0x2C,std::int32_t{3});
  Put(armies,0x20,static_cast<void *>(army_slots.data()));Put(armies,0x2C,std::int32_t{3});
  void *units_pointer=units.data(),*armies_pointer=armies.data(),*regiments_pointer=regiments.data();
  void *state_pointer=state.data(),*fallback_pointer=fallback_army.data();
  ArmyBindings bindings{};
  bindings.enabled=true;bindings.unit_storage_slot=&units_pointer;
  bindings.internal_army_storage_slot=&armies_pointer;bindings.regiment_storage_slot=&regiments_pointer;
  bindings.game_state_slot=&state_pointer;bindings.get_army_current_soldiers=Current;
  bindings.get_army_maximum_soldiers=Maximum;
  bindings.monthly_daily_queue_bindings={true,&fallback_pointer};
  const std::array<ArmyStrengthScope,1> scope{{{unit_id,game::ArmyStrengthScopeRole::player,{}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read=[&]() {
    Check(ReadArmyStrengthsForScope(bindings,scope,rows)==game::ReadArmyStrengthsResult::available,
          "existing parent strength remains available");return rows[0];
  };
  const auto army_before=army,fallback_before=fallback_army;
  const auto manager_before=manager;
  auto row=read();const auto first=*row.monthly_daily_queue_inputs_v1;
  const auto &resolved=*first.initial_army_resolution_rows;
  Check(first.available && *first.manager_army_id_list_2a5a8==std::vector<std::int32_t>(queue.begin(),queue.end()) &&
        resolved.size()==4 && resolved[0].used_fallback==true && resolved[0].resolved_army_id==-1 &&
        resolved[0].native_army_identity_valid==false && resolved[1].used_fallback==false &&
        resolved[1].resolved_army_id==army_id && resolved[1].native_army_identity_valid==true &&
        resolved[2].raw_army_reference_id==resolved[1].raw_army_reference_id &&
        resolved[3].used_fallback==true,"initial occurrence generation/fallback/order and predicate exact");
  Check(*read().monthly_daily_queue_inputs_v1==first,"stable repeated current frame is equal");
  Check(army==army_before && fallback_army==fallback_before && manager==manager_before,
        "observer never drains queue or calls removal");
  Emit(directory,"invalid-prefix-first-call",row);
  Put(manager,0x2A5B4,std::int32_t{0});row=read();
  Check(row.monthly_daily_queue_inputs_v1->available &&
        row.monthly_daily_queue_inputs_v1->manager_army_id_list_2a5a8->empty() &&
        row.monthly_daily_queue_inputs_v1->initial_army_resolution_rows->empty(),"empty queue is observed zero");
  Emit(directory,"empty-queue",row);
  Put(manager,0x2A5B4,std::int32_t{4});bindings.monthly_daily_queue_bindings.army_fallback_slot=nullptr;
  row=read();
  Check(!row.monthly_daily_queue_inputs_v1->available &&
        row.monthly_daily_queue_inputs_v1->manager_army_id_list_2a5a8->size()==4 &&
        !row.monthly_daily_queue_inputs_v1->initial_army_resolution_rows->at(0).available &&
        !row.monthly_daily_queue_inputs_v1->initial_army_resolution_rows->at(0).native_army_identity_valid &&
        row.monthly_daily_queue_inputs_v1->initial_army_resolution_rows->at(1).available,
        "unknown initial fallback cannot become invalid skip or hide later observed row");
  Emit(directory,"partial-prefix",row);
  bindings.monthly_daily_queue_bindings.army_fallback_slot=&fallback_pointer;
  Put(fallback_army,0x10,std::int32_t{0x07000002});row=read();
  Check(row.monthly_daily_queue_inputs_v1->available &&
        row.monthly_daily_queue_inputs_v1->initial_army_resolution_rows->at(0).used_fallback==true &&
        row.monthly_daily_queue_inputs_v1->initial_army_resolution_rows->at(0).native_army_identity_valid==true,
        "actual valid fallback is not artificially filtered");
  Emit(directory,"valid-fallback-first-call",row);
  bindings.monthly_daily_queue_bindings.enabled=false;
  Check(!read().monthly_daily_queue_inputs_v1,"older fixture/binder leaves additive family absent");
}
} // namespace
int main(int argc,char **argv) {
  try {
    Check(argc==2,"wire directory required");Cases(argv[1]);
    std::cout<<"PASS: daily queue initial operands and four new production wires\n";return 0;
  } catch(const std::exception &error){std::cerr<<"FIXTURE RED: "<<error.what()<<'\n';return 1;}
}

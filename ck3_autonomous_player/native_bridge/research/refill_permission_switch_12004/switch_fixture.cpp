#include <windows.h>
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_scoped_ordered_refill_core.hpp"
#include "xar_bridge/ck3_12004_regiment_refill_switch_readonly.hpp"
#include "xar_bridge/army_ordered_refill_persistent_v1_serializer.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
constexpr std::int32_t R=0x11000001,A=0x21000001,B=std::int32_t(0x81000002U),C=0x33000003;
constexpr std::int32_t T=0x31000001,TF=0x32000002;
template<class T>void Put(void *p,std::size_t off,T value){std::memcpy(static_cast<std::byte *>(p)+off,&value,sizeof value);}
struct World {
  std::byte *image=nullptr;
  std::array<std::byte,0x200> regi{},definition{},charA{},charB{},charC{};
  std::array<std::byte,0x500> milA{},milB{},milC{};
  std::array<std::byte,0x160> title{},titleFallback{};
  std::array<std::byte,0x40> regiRegistry{},charRegistry{},titleRegistry{};
  std::array<std::uintptr_t,4> regiTable{};
  std::array<std::uintptr_t,8> charTable{};
  std::array<std::uintptr_t,6> titleTable{};
  bool deny_switch=false,change_reference=false;
  unsigned ref_reads=0;
  World(){
    image=static_cast<std::byte *>(VirtualAlloc(nullptr,0x5E00000,MEM_RESERVE,PAGE_NOACCESS));
    if(!image)throw std::runtime_error("reserve failed");
    for(auto page:{0x5C67000,0x5D1D000,0x5D1E000})
      if(!VirtualAlloc(image+page,0x1000,MEM_COMMIT,PAGE_READWRITE))throw std::runtime_error("commit failed");
    Put(regi.data(),0x10,R);Put(regi.data(),0x14,std::uint32_t(0x52656769));
    Put(regi.data(),0x118,definition.data());Put(definition.data(),0x38,std::uint32_t(0x4744624F));
    Put(regi.data(),0x12C,A);Put(regi.data(),0x130,std::int32_t(-1));Put(regi.data(),0x148,std::int64_t(100));
    for(unsigned i=0;i<7;++i){auto off=0x18+i*0x24;
      Put(regi.data(),off,std::int32_t(100));Put(regi.data(),off+4,std::int32_t(80));
      Put(regi.data(),off+8,R);Put(regi.data(),off+0xC,std::int32_t(i));Put(regi.data(),off+0x10,std::int32_t(-1));}
    for(auto pair:{std::pair{charA.data(),A},std::pair{charB.data(),B},std::pair{charC.data(),C}}){
      Put(pair.first,0x18,pair.second);Put(pair.first,0x1C,std::uint32_t(0x43686172));}
    Put(charA.data(),0x1C0,milA.data());Put(charB.data(),0x1C0,milB.data());Put(charC.data(),0x1C0,milC.data());
    Put(milA.data(),0x4A9,std::uint8_t(2));Put(milB.data(),0x4A9,std::uint8_t(0));Put(milC.data(),0x4A9,std::uint8_t(0));
    Put(title.data(),0x10,T);Put(title.data(),0x128,B);
    Put(titleFallback.data(),0x10,TF);Put(titleFallback.data(),0x128,B);
    regiTable[3]=std::uintptr_t(regi.data());charTable[3]=std::uintptr_t(charA.data());
    charTable[5]=std::uintptr_t(charB.data());charTable[7]=std::uintptr_t(charC.data());
    titleTable[3]=std::uintptr_t(title.data());titleTable[5]=std::uintptr_t(titleFallback.data());
    Put(regiRegistry.data(),0x20,regiTable.data());Put(regiRegistry.data(),0x2C,std::int32_t(2));
    Put(charRegistry.data(),0x20,charTable.data());Put(charRegistry.data(),0x2C,std::int32_t(4));
    Put(titleRegistry.data(),0x20,titleTable.data());Put(titleRegistry.data(),0x2C,std::int32_t(3));
    Put(image,0x5D1EB68,regiRegistry.data());Put(image,0x5D1EB58,regi.data());
    Put(image,0x5C67568,charRegistry.data());Put(image,0x5C67570,charC.data());
    Put(image,0x5D1DAF8,titleRegistry.data());Put(image,0x5D1DAE0,titleFallback.data());
  }
  ~World(){if(image)VirtualFree(image,0,MEM_RELEASE);}
  static bool Read(void *context,std::uintptr_t address,void *out,std::size_t size) noexcept {
    auto &w=*static_cast<World *>(context);
    if(w.deny_switch&&address==std::uintptr_t(w.milA.data())+0x4A9)return false;
    if(w.change_reference&&address==std::uintptr_t(w.regi.data())+0x12C&&++w.ref_reads==2)
      Put(w.regi.data(),0x12C,B);
    std::memcpy(out,reinterpret_cast<const void *>(address),size);return true;
  }
  xar::ck3_12002::ArmyBindings Bind(bool exact=true){
    xar::ck3_12002::ArmyBindings b{};b.enabled=true;
    b.persistent_regiment_storage_slot=reinterpret_cast<void **>(image+0x5D1EB68);
    b.scoped_ordered_refill_bindings.enabled=true;
    b.scoped_ordered_refill_bindings.persistent_fallback_slot=reinterpret_cast<void **>(image+0x5D1EB58);
    if(exact)b.scoped_ordered_refill_bindings.refill_switch_image_base_12004=std::uintptr_t(image);
    return b;
  }
};
void Text(std::string &out,std::string_view value){out+='"';out+=value;out+='"';}
auto Number=[](auto value){return std::to_string(value);};
void Check(bool value){if(!value)throw std::runtime_error("native assertion failed");}
void Emit(const char *name,World &w,const char *expected_branch,const char *expected_status,
          std::optional<bool> enabled,std::optional<std::int32_t> character,bool legacy=false,bool pure=false){
  std::string json="{\"case\":\"";json+=name;json+="\",\"synthetic\":true,\"CK3_runtime_observed\":false,";
  if(pure){
    auto r=xar::ck3_12004::ReadRegimentRefillPermissionSwitch12004(
      {std::uintptr_t(w.image),&w,&World::Read},std::uintptr_t(w.regi.data()),R);
    Check(r.status==expected_status&&r.source_branch==expected_branch&&r.enabled==enabled&&r.resolved_character_full_id==character);
    json+="\"producer\":\"ReadRegimentRefillPermissionSwitch12004\",\"switch\":";
    xar::game::AppendArmyRefillPermissionSwitchV1(json,r,Number,&Text);
  }else{
    auto r=xar::ck3_12003::ReadOrderedRefillPersistent12003(w.Bind(!legacy),R);
    Check(r.chunks.size()==7);
    for(auto &chunk:r.chunks){
      if(legacy){Check(!chunk.refill_permission_switch_v1);continue;}
      Check(chunk.refill_permission_switch_v1.has_value());auto &s=*chunk.refill_permission_switch_v1;
      Check(s.status==expected_status&&s.source_branch==expected_branch&&s.enabled==enabled&&s.resolved_character_full_id==character);
    }
    json+="\"producer\":\"ReadOrderedRefillPersistent12003\",\"persistent\":";
    xar::game::AppendArmyOrderedRefillPersistentV1(json,r,Number,&Text);
  }
  json+='}';std::cout<<json<<'\n';
}
}
int main(){try{
  {World w;Emit("direct_nonzero",w,"direct_character","available",true,A);}
  {World w;Put(w.milA.data(),0x4A9,std::uint8_t(0));Emit("direct_disabled",w,"direct_character","available",false,A);}
  {World w;Put(w.regi.data(),0x12C,std::int32_t(-1));Put(w.regi.data(),0x130,T);Emit("title_holder_not_player",w,"title_holder","available",false,B);}
  {World w;Put(w.regi.data(),0x12C,std::int32_t(-1));Put(w.regi.data(),0x130,std::int32_t(0x35000001));Emit("title_generation_fallback",w,"title_holder","available",false,B);}
  {World w;Put(w.regi.data(),0x12C,std::int32_t(0x45000001));Emit("character_generation_fallback",w,"direct_character","available",false,C);}
  {World w;Put(w.regi.data(),0x130,T);Emit("both_references_native_fallback",w,"conflicting_references_fallback","available",false,C);}
  {World w;Put(w.regi.data(),0x12C,std::int32_t(-1));Emit("missing_references_native_fallback",w,"missing_references_fallback","available",false,C);}
  {World w;Put(w.definition.data(),0x38,std::uint32_t(0x12345678));Emit("non_special_bypass",w,"non_special_definition_bypass","not_applicable",{},{});}
  {World w;Put(w.charA.data(),0x1C0,std::uintptr_t(0));Emit("missing_military_component",w,"direct_character","unavailable",{},A);}
  {World w;Emit("legacy_leaf_absent",w,"","",{},{},true);}
  {World w;w.deny_switch=true;Emit("unreadable_switch",w,"direct_character","unavailable",{},A,false,true);}
  {World w;w.change_reference=true;Emit("source_changes_during_capture",w,"direct_character","unavailable",{},A,false,true);}
  return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}

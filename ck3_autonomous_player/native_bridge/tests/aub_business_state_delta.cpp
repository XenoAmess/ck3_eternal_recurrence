#include "xar_bridge/aub_business_state_v1.hpp"
#include <Windows.h>
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_12003;
using namespace xar::ck3_11906;
namespace {
struct Fixture {
  std::array<std::byte,0x200> actor{};
  std::array<std::byte,0x20> script{},collection{};
  std::array<std::byte,0x60> pool{};
  std::array<std::byte,5*0x20> records{};
  std::array<std::byte,4*0x20> rows{};
  std::array<bool,4> registered{true,true,true,true};
  int calls=0;bool change_between_passes=false;bool wrong_return=false;
  template<class T>void put(void *p,std::size_t off,T v){std::memcpy(static_cast<std::byte *>(p)+off,&v,sizeof(v));}
  Fixture(){
    put(actor.data(),0x18,std::int32_t{31254});put(actor.data(),0x1C,std::uint32_t{0x43686172});
    put(actor.data(),0x1B0,script.data());put(script.data(),0,std::int32_t{0});
    put(collection.data(),0x10,rows.data());put(collection.data(),0x1C,std::int32_t{0});
    put(pool.data(),0x10,rows.data());put(pool.data(),0x1C,std::int32_t{4});
    put(pool.data(),0x30,records.data());put(pool.data(),0x3C,std::uint32_t{5});
    for(std::size_t i=0;i<4;++i){auto *r=records.data()+(i+1)*0x20;const auto key=kAubBusinessFlagKeysV1[i];
      put(r,0,key.data());put(r,0x10,std::uint64_t{key.size()});put(r,0x18,std::uint64_t{key.size()});}
  }
  void keys(std::initializer_list<std::uint32_t> values){std::size_t i=0;for(auto key:values)put(rows.data(),i++*0x20+8,key);put(collection.data(),0x1C,static_cast<std::int32_t>(i));}
} *fixture;
std::uint32_t *Lookup(void *,std::uint32_t *out,const xar::ck3_12003::religion::repentance_recovery_inputs::NativeStringView *v){
  ++fixture->calls;
  if(fixture->change_between_passes&&fixture->calls==5)fixture->keys({1});
  *out=0xFFFFFFFF;
  for(std::size_t i=0;i<4;++i)if(std::string_view(v->data,static_cast<std::size_t>(v->length))==kAubBusinessFlagKeysV1[i]&&fixture->registered[i])*out=static_cast<std::uint32_t>(i+1);
  return fixture->wrong_return?nullptr:out;
}
void *Flags(void *){return fixture->collection.data();}
void require(bool actual,const char *label){if(!actual)throw std::runtime_error(label);}
bool query(Fixture &f,std::array<AubBusinessFlagV1,4> &out,bool offline=true){
 fixture=&f;ZhongguoScoreboardNativeEnvironmentV1 e{};e.exact_build_admitted=true;e.gui_abi_revision=GuiAbiRevisionV1::crozier12003;e.offline_fixture_function_overrides=offline;
 ZhongguoScoreboardAccessV1 a{};AubFlagReadBindingsV1 b{Lookup,Flags,f.pool.data()};return ReadAubBusinessFlagsV1(e,a,b,f.actor.data(),31254,out);
}
}
// These are link-only stubs for separate paused mailbox integration. The delta
// calls only ReadAubBusinessFlagsV1 and the production-source tuple comparator.
namespace xar::ck3_11906 {
std::string SerializeIngameDecisionItemV1(const IngameDecisionItemResultV1 &){return "{}";}
bool ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,void *&,void *&) noexcept{return false;}
bool ResolveNamedGuiWidgetV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,std::string_view,std::string_view,void *&,void *&) noexcept{return false;}
bool InspectNamedGuiSubtreeV1(const ZhongguoScoreboardAccessV1 &,std::uintptr_t,void *,std::string_view,NamedGuiTreeInspectionV1 &) noexcept{return false;}
}
int main(int argc,char **argv){try{
 if(argc==2&&std::strcmp(argv[1],"serialization")==0){
  Fixture f;f.keys({1});std::array<AubBusinessFlagV1,4> values{};
  require(query(f,values),"serialization reads actual fixture flags");
  AubBusinessStateResultV1 r{};r.flags=values;r.available=true;r.owner_thread_verified=true;r.frame_verified=true;
  r.source_abi_pins_verified=true;r.gui_owner_binding_verified=true;r.stable_two_pass_verified=true;
  r.detail_census_verified=true;r.detail_root_available=true;r.detail_tree_complete=true;r.detail_effectively_visible=false;
  r.native_revision=7;r.connection_generation=1;r.game_pid=12700;r.played_character_id=31254;r.date_raw=1234;
  std::cout<<SerializeAubBusinessStateV1(r)<<'\n';return 0;
 }

 std::size_t n=0;std::array<AubBusinessFlagV1,4> out{};
 {Fixture f;require(query(f,out)&&out[0].present==false&&out[3].present==false,"complete empty flag set is actual false");++n;}
 {Fixture f;f.registered={false,false,false,false};require(query(f,out)&&!out[0].atom_registered&&out[0].present==false,"existing atom absent is observed false");++n;}
 {Fixture f;f.keys({1,2,4});require(query(f,out)&&out[0].present==true&&out[1].present==true&&out[2].present==false&&out[3].present==true,"native row presence independent four values");++n;}
 {Fixture f;f.put(f.actor.data(),0x18,std::int32_t{29829});require(!query(f,out),"old historical ID rejected");++n;}
 {Fixture f;f.put(f.actor.data(),0x1A5,std::uint8_t{1});require(!query(f,out),"dummy actor rejected");++n;}
 {Fixture f;f.put(f.actor.data(),0x1D0,f.rows.data());require(!query(f,out),"dead actor rejected");++n;}
 {Fixture f;f.put(f.script.data(),0,std::int32_t{-1});require(query(f,out)&&out[0].present==false,"actual -1 empty script index");++n;}
 {Fixture f;f.put(f.collection.data(),0x1C,std::int32_t{65537});require(!query(f,out),"flag row bound rejected");++n;}
 {Fixture f;f.keys({1,1});require(!query(f,out),"duplicate target flag rejected");++n;}
 {Fixture f;f.put(f.pool.data(),0x48,std::uint32_t{1});require(!query(f,out),"odd string-pool writer lock rejected");++n;}
 {Fixture f;f.put(f.records.data()+0x20,0x10,std::uint64_t{16});require(!query(f,out),"atom name roundtrip mismatch rejected");++n;}
 {Fixture f;f.change_between_passes=true;require(!query(f,out),"actual flag set changed between passes rejected");++n;}
 {Fixture f;f.wrong_return=true;require(!query(f,out),"lookup returned wrong out pointer rejected");++n;}
 {Fixture f;require(!query(f,out,false),"function override denied in production environment");++n;}
 for(std::size_t choice=0;choice<6;++choice){Fixture f;if(choice<2){if(choice%2)f.keys({1,2});else f.keys({1,2,4});}
   else if(choice<4){if(choice%2)f.keys({1,3});else f.keys({1,3,4});}else{if(choice%2)f.keys({1});else f.keys({1,4});}
   require(query(f,out),"policy tuple actual read");AubBusinessStateResultV1 s{};s.available=true;s.flags=out;
   require(AubFlagsMatchSelectedPolicyV1(kAubPolicyValueKeysV1[choice],s),"six source-defined expected tuple");
   s.flags[0].present=false;require(!AubFlagsMatchSelectedPolicyV1(kAubPolicyValueKeysV1[choice],s),"ACK without enabled flag rejected");++n;}
 std::cout<<"{\"new_vectors\":"<<n<<",\"result\":\"PASS\",\"native_live_verified\":false}\n";return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}

#include "xar_bridge/ck3_12004_holy_site_relic_action_context.hpp"
// Reuse only the frozen owned-memory fixture's storage/input constructor. Its
// historical main is compiled under a different name and is never executed.
#define main permissions_historical_fixture_not_executed
#include "ck3_12004_holy_site_relic_permissions_test.cpp"
#undef main
namespace a=xar::ck3_12004::religion::relic_action_context;
namespace {
struct ActionFixture:Fixture {
 std::int32_t picker_result=1;bool unknown_text=false,drift=false,faith_drift=false;unsigned picker_calls=0,equipped_calls=0,text_calls=0;
 void*Object(std::uint32_t id){void*store=nullptr,*rows=nullptr,*out=nullptr;memory.Get(artifacts,0,store);memory.Get(store,0x20,rows);memory.Get(rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,out);return out;}
 ActionFixture(){
  // R6 actual role: window+98 is the outer CInGameInterfaceIdler,
  // not its separate +10 CIngameInterfaceIdlerGfx object.
  memory.Put(window,0x98,owner);
  for(const auto id:{first,second,installed,nonowned}){
   auto*old=Object(id);auto*current=memory.Make(0xC0);std::memcpy(current,old,0xB8);memory.Entry(artifacts,id,current);
   memory.Put(current,0x78,id==installed?std::uint32_t{0xFFFFFFFFU}:player);
   auto*type=memory.Make(0x50);memory.Put(type,0x40,std::uint32_t{6});memory.Put(type,0x44,std::uint32_t{7});memory.Put(current,0xB8,type);
  }
  for(unsigned i=0;i<3;++i){auto*type=memory.Make(0x220);memory.Put(type,0x209,std::uint8_t{1});memory.Put(slots,i*24+8,type);}
 }
 static ActionFixture&Self(const a::Bindings&b){return *static_cast<ActionFixture*>(b.permissions.model.read_context);}
 static bool Picker(const a::Bindings&b,const void*i,const void*artifact,std::int32_t&v)noexcept {
  auto&f=Self(b);++f.picker_calls;std::uint32_t id=0;if(i!=static_cast<unsigned char*>(f.site)+0x28||!f.memory.Get(artifact,0x10,id))return false;v=f.picker_result;return true;
 }
 static bool Equipped(const a::Bindings&b,const void*i,const void*artifact,bool&v)noexcept {
  auto&f=Self(b);++f.equipped_calls;std::uint32_t id=0;void*rows=nullptr;std::int32_t count=0;v=false;
  if(!f.memory.Get(artifact,0x10,id)||!f.memory.Get(i,0x40,rows)||!f.memory.Get(i,0x4C,count)||count<0||count>4096)return false;
  for(std::int32_t n=0;n<count;++n){std::uint32_t slot_id=0;if(!f.memory.Get(rows,static_cast<std::size_t>(n)*24+16,slot_id))return false;if(slot_id==id)v=true;}return true;
 }
 static bool Text(const a::Bindings&b,const void*w,std::uintptr_t rva,std::string&v)noexcept {
  auto&f=Self(b);++f.text_calls;if(w!=f.window)return false;
  if(rva==0x17D6990){if(f.drift)f.memory.Put(f.Object(first),0x78,std::uint32_t{0xFFFFFFFFU});if(f.unknown_text)return false;
   if(f.faith_drift)f.memory.Put(f.rite,0x4B8,faith_id+0x01000000U);
   v="Original preview: piety +100; \"replace\"\nUTF-8: 圣物";return true;}
  if(rva==0x17D5A60){v="Original enshrine tooltip";return true;}
  if(rva==0x17D5F60){v="Original remove tooltip";return true;}return false;
 }
 a::Bindings BindAction(){a::Bindings b{};b.permissions=Bind();b.slot_picker=&Picker;b.equipped=&Equipped;b.text=&Text;b.getter_backend="owned_fixture_injected_getter";return b;}
 bool ReadAction(a::Snapshot&s,std::uint32_t id=first){return a::ReadHolySiteRelicActionContext12004(BindAction(),owner,Context(),site_id,id,s);}
};
void SaveAction(const std::filesystem::path&dir,const char*name,const a::Snapshot&s){std::ofstream out(dir/name,std::ios::binary);out<<a::SerializeHolySiteRelicActionContextCommand12004(s,"g2-read-relic-action-context-fixture",701,s.date_raw)<<'\n';Check(bool(out),"new production action-context packet written");}
}
#if !defined(XAR_RELIC_ACTION_CONTEXT_FIXTURE_TYPES_ONLY)
int main(int argc,char**argv){try {
 checks=0;Check(argc==2,"one new output directory required");const std::filesystem::path dir(argv[1]);Check(std::filesystem::create_directories(dir),"existing output directory refused");
 {ActionFixture f;f.memory.Put(f.window,0x110,static_cast<void*>(nullptr));a::Snapshot s;Check(f.ReadAction(s)&&s.preview_identity_available,"empty original automatic destination observed");
  Check(s.destination.effective_slot_index==1U&&!s.destination.replacing_artifact_id&&f.picker_calls==1,"original picker dependency used, known empty distinct from unknown");
  Check(s.artifact_ownership.character_owner_matches_player==true&&s.artifact_ownership.player_owned_reference_member==true&&s.artifact_ownership.player_equipped_slot_member.value==false,"character ownership, owned refs and equipped kept distinct");SaveAction(dir,"enshrine-empty.json",s);}
 {ActionFixture f;f.memory.Put(f.window,0x110,f.slots);a::Snapshot s;Check(f.ReadAction(s)&&s.preview_identity_available&&s.destination.effective_slot_index==0U&&s.destination.replacing_artifact_id==Fixture::installed,"explicit compatible replacement preview");
  Check(s.destination.replacing_artifact.available&&s.destination.replacing_artifact.holy_site_owner_matches_requested==true&&f.picker_calls==0,"replacement full object/owner resolved without picker");SaveAction(dir,"enshrine-replace.json",s);}
 {ActionFixture f;void*type=nullptr;f.memory.Get(f.slots,32,type);f.memory.Put(type,0x209,std::uint8_t{0});f.memory.Put(type,0x40,std::uint32_t{98});a::Snapshot s;
  Check(f.ReadAction(s)&&s.destination.explicit_slot_type_compatible==false&&s.destination.original_picker_called&&f.picker_calls==1,"source-bound explicit incompatible branch falls back to original picker");SaveAction(dir,"explicit-incompatible-fallback.json",s);}
 {ActionFixture f;f.memory.Put(f.window,0x108,Fixture::installed);f.memory.Put(f.window,0x110,f.slots);a::Snapshot s;
  Check(f.ReadAction(s,Fixture::installed)&&s.preview_identity_available&&s.destination.action_kind=="remove"&&!s.destination.effective_slot_index&&!s.destination.replacing_artifact_id,"remove does not invent enshrine destination");
  Check(s.artifact_ownership.character_owner_matches_player==false&&s.artifact_ownership.player_owned_reference_member==false&&s.artifact_ownership.site_equipped_slot_member.value==true,"remove owned by holy site, not already actor owned");SaveAction(dir,"remove-installed.json",s);}
 {ActionFixture f;f.memory.Put(f.window,0x108,Fixture::second);a::Snapshot s;Check(f.ReadAction(s)&&!s.selected_artifact_matches_request&&!s.preview_identity_available&&!s.selected_action_effect_description.available&&f.text_calls==0,"wrong selected artifact never evaluates misleading preview");SaveAction(dir,"request-not-selected.json",s);}
 {ActionFixture f;f.memory.Put(f.window,0x110,static_cast<void*>(nullptr));f.picker_result=-1;a::Snapshot s;Check(f.ReadAction(s)&&!s.destination.available&&!s.destination.effective_slot_index&&!s.preview_identity_available,"no compatible slot is not index zero");SaveAction(dir,"no-compatible-slot.json",s);}
 {ActionFixture f;f.unknown_text=true;a::Snapshot s;Check(f.ReadAction(s)&&!s.selected_action_effect_description.available&&s.enshrine_disabled_tooltip.available&&!s.preview_identity_available,"unknown effect description blocks frozen preview identity");SaveAction(dir,"unknown-text.json",s);}
 {ActionFixture f;f.drift=true;a::Snapshot s;Check(!f.ReadAction(s)&&!s.available&&!s.preview_identity_available&&s.unavailable_reason=="relic_action_context_inputs_changed_during_read","ownership drift rejected after original description evaluation");SaveAction(dir,"ownership-drift.json",s);}
 {ActionFixture f;f.memory.Put(f.handler,0x5D8,static_cast<void*>(nullptr));a::Snapshot s;Check(f.ReadAction(s)&&s.artifact_ownership.available&&!s.destination.available&&!s.preview_identity_available&&f.text_calls==0,"independent ownership postread survives closed window");SaveAction(dir,"window-unavailable.json",s);}
 {ActionFixture f;f.faith_drift=true;a::Snapshot s;Check(!f.ReadAction(s)&&!s.available&&!s.preview_identity_available&&s.unavailable_reason=="relic_action_context_inputs_changed_during_read","player faith drift during original description rejects action preview");SaveAction(dir,"faith-drift.json",s);}
 Check(!a::BindHolySiteRelicActionContextImage12004(Fixture::image,"foreign-build").permissions.model.enabled,"foreign EXE identity rejects source binding");
 std::cout<<"PASS checks="<<checks<<" packets=10 production_reader=true production_serializer=true synthetic_storage=true injected_native_dependencies=true engine_code_executed=false live=false historical_fixture_main_executed=false\n";return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
#endif

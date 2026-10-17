#include "xar_bridge/ck3_12004_holy_site_relic_permissions.hpp"
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

namespace r=xar::ck3_12004::religion::relic_permissions;
namespace {
unsigned checks=0;
void Check(bool value,const char*why){++checks;if(!value)throw std::runtime_error(why);}
struct Memory {
 struct Block {std::unique_ptr<unsigned char[]>data;std::size_t size;};
 std::vector<Block>blocks;
 void* Make(std::size_t n){auto p=std::make_unique<unsigned char[]>(n);auto*raw=p.get();blocks.push_back({std::move(p),n});return raw;}
 bool Read(const void*p,void*out,std::size_t n)const noexcept {
  const auto a=reinterpret_cast<std::uintptr_t>(p);
  for(const auto&b:blocks){const auto start=reinterpret_cast<std::uintptr_t>(b.data.get());
   if(a>=start&&a-start<=b.size&&n<=b.size-static_cast<std::size_t>(a-start)){std::memcpy(out,p,n);return true;}}
  return false;
 }
 template<class T>void Put(void*p,std::size_t offset,const T&v){
  auto*dest=static_cast<unsigned char*>(p)+offset;
  T old{};if(!Read(dest,&old,sizeof(old)))throw std::runtime_error("fixture write outside owned memory");
  std::memcpy(dest,&v,sizeof(v));
 }
 template<class T>bool Get(const void*p,std::size_t offset,T&v)const noexcept {
  return Read(static_cast<const unsigned char*>(p)+offset,&v,sizeof(v));
 }
 void** Storage(std::uint32_t count){auto*store=Make(0x40);auto*rows=Make(static_cast<std::size_t>(count)*16);
  Put(store,0x20,rows);Put(store,0x2C,count);auto**global=static_cast<void**>(Make(sizeof(void*)));Put(global,0,store);return global;}
 void Entry(void**global,std::uint32_t id,void*object){void*store=nullptr,*rows=nullptr;
  if(!Get(global,0,store)||!Get(store,0x20,rows))throw std::runtime_error("fixture storage missing");
  Put(rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object);}
 void Header(void*p,std::size_t offset,void*data,std::int32_t count){Put(p,offset,data);Put(p,offset+8,count);Put(p,offset+12,count);Put(p,offset+16,std::uint64_t{0});}
};
struct Fixture {
 static constexpr std::uintptr_t image=0x10000000;
 static constexpr std::uint32_t player=15893,site_id=0x84000002,rite_id=0x83000001,faith_id=0x81000001;
 static constexpr std::uint32_t first=0x85000004,second=0x86000005,installed=0x87000006,nonowned=0x89000007;
 Memory memory;
 void *actor=nullptr,*site=nullptr,*rite=nullptr,*data=nullptr,*inv=nullptr,*owner=nullptr,*gfx=nullptr,*handler=nullptr,*window=nullptr,*slots=nullptr;
 void **characters=nullptr,**sites=nullptr,**rites=nullptr,**artifacts=nullptr;
 std::uint32_t*current_actor=nullptr;
 bool predicate_failure=false;
 unsigned inventory_calls=0,candidate_calls=0,artifact_permission_calls=0,button_calls=0;
 Fixture(){
  characters=memory.Storage(player+1);sites=memory.Storage(3);rites=memory.Storage(2);artifacts=memory.Storage(8);
  actor=memory.Make(0x200);site=memory.Make(0xC0);rite=memory.Make(0x500);data=memory.Make(0x600);
  inv=static_cast<unsigned char*>(data)+0x458;
  memory.Put(actor,0x18,player);memory.Put(actor,0x1C,std::uint32_t{0x43686172});memory.Put(actor,0xB4,rite_id);memory.Put(actor,0x1B0,data);
  memory.Put(site,0x10,site_id);memory.Put(site,0x14,std::uint32_t{0x486F5374});memory.Put(rite,8,rite_id);memory.Put(rite,0x4B8,faith_id);
  memory.Entry(characters,player,actor);memory.Entry(sites,site_id,site);memory.Entry(rites,rite_id,rite);
  for(const auto id:{first,second,installed,nonowned}){auto*a=memory.Make(0xB8);memory.Put(a,0x10,id);
   memory.Put(a,0x14,std::uint32_t{0x41727469});memory.Put(a,0xB0,std::int32_t{id==first?3:2});
   memory.Put(a,0x7C,id==installed?site_id:id==nonowned?std::uint32_t{14}:std::uint32_t{0xFFFFFFFFU});memory.Entry(artifacts,id,a);}
  auto*ids=memory.Make(12);memory.Put(ids,0,first);memory.Put(ids,4,second);memory.Put(ids,8,first);
  memory.Put(inv,0x38,player);memory.Put(inv,0x3C,std::uint32_t{0xFFFFFFFFU});memory.Header(inv,0x58,ids,3);
  slots=memory.Make(72);for(unsigned i=0;i<3;++i){memory.Put(slots,i*24,std::uintptr_t{0x20000000});memory.Put(slots,i*24+8,std::uintptr_t{0x30000000});
   memory.Put(slots,i*24+16,i==0?installed:std::uint32_t{0xFFFFFFFFU});memory.Put(slots,i*24+20,std::uint32_t{0x496E7653});}
  memory.Header(site,0x68,slots,3);
  owner=memory.Make(0x20);gfx=memory.Make(0x100);handler=memory.Make(0x600);window=memory.Make(0x160);auto*root=memory.Make(8);
  memory.Put(owner,0x10,gfx);memory.Put(gfx,0x88,handler);memory.Put(handler,0x5D8,window);
  memory.Put(window,0,image+0x4592338);memory.Put(window,0x10,image+0x4592310);memory.Put(window,0x98,gfx);
  memory.Put(window,0xA0,handler);memory.Put(window,0x60,root);memory.Put(window,0xC8,site_id);memory.Put(window,0x108,first);
  const void*selected_slot=static_cast<unsigned char*>(slots)+24;memory.Put(window,0x110,selected_slot);
  auto*cached=memory.Make(4);memory.Put(cached,0,second);memory.Header(window,0x130,cached,1);
  current_actor=static_cast<std::uint32_t*>(memory.Make(4));memory.Put(current_actor,0,player);
 }
 static Fixture& Self(const r::Bindings&b){return *static_cast<Fixture*>(b.model.read_context);}
 static bool Read(void*context,const void*p,void*out,std::size_t n)noexcept{return static_cast<Fixture*>(context)->memory.Read(p,out,n);}
 static bool Inventory(const r::Bindings&b,const void*a,const void*&out)noexcept{auto&f=Self(b);++f.inventory_calls;if(a!=f.actor)return false;out=f.inv;return true;}
 static bool Candidate(const r::Bindings&b,const void*a,const void*s,bool&out)noexcept{auto&f=Self(b);++f.candidate_calls;
  std::uint32_t id=0;if(s!=f.site||!f.memory.Get(a,0x10,id)||(f.predicate_failure&&id==second))return false;out=id==first;return true;}
 static bool Enshrine(const r::Bindings&b,const void*w,const void*a,bool&out)noexcept{auto&f=Self(b);++f.artifact_permission_calls;
  std::uint32_t id=0;if(w!=f.window||!f.memory.Get(a,0x10,id))return false;out=id==first||id==nonowned;return true;}
 static bool Remove(const r::Bindings&b,const void*w,const void*a,bool&out)noexcept{auto&f=Self(b);++f.artifact_permission_calls;
  std::uint32_t id=0;if(w!=f.window||!f.memory.Get(a,0x10,id))return false;out=id==installed;return true;}
 static bool EnshrineButton(const r::Bindings&b,const void*w,bool&out)noexcept{auto&f=Self(b);++f.button_calls;
  std::uint32_t id=0;if(w!=f.window||!f.memory.Get(w,0x108,id))return false;out=id==first;return true;}
 static bool RemoveButton(const r::Bindings&b,const void*w,bool&out)noexcept{auto&f=Self(b);++f.button_calls;
  std::uint32_t id=0;if(w!=f.window||!f.memory.Get(w,0x108,id))return false;out=id==installed;return true;}
 r::Bindings Bind(){r::Bindings b{};b.model.enabled=true;b.model.image_base=image;b.model.read_memory=&Read;b.model.read_context=this;
  b.model.character_storage=characters;b.model.holy_site_storage=sites;b.model.rite_storage=rites;b.model.artifact_storage=artifacts;
  b.current_actor_reference=current_actor;b.player_inventory=&Inventory;b.candidate_predicate=&Candidate;
  b.can_enshrine=&Enshrine;b.can_remove=&Remove;b.enshrine_button=&EnshrineButton;b.remove_button=&RemoveButton;
  b.getter_backend="owned_fixture_injected_getter";return b;}
 xar::ck3_12002::religion::Context Context(){xar::ck3_12002::religion::Context c{};c.available=true;c.capture_epoch=17;c.date_raw=51394920;
  c.played_character_id=player;c.rite_id=rite_id;c.faith_id=faith_id;return c;}
 bool ReadSnapshot(r::Snapshot&s,std::optional<std::uint32_t>a=first,std::uint32_t id=site_id){return r::ReadHolySiteRelicPermissions12004(Bind(),owner,Context(),id,a,s);}
};
void Save(const std::filesystem::path&dir,const char*name,const r::Snapshot&s){std::ofstream out(dir/name,std::ios::binary);
 out<<r::SerializeHolySiteRelicPermissionsCommand12004(s,"g2-read-holy-site-relic-permissions-fixture",701,s.date_raw)<<'\n';Check(bool(out),"production serializer packet written");}
}
int main(int argc,char**argv){try{
 Check(argc==2,"one new output directory required");const std::filesystem::path dir(argv[1]);Check(std::filesystem::create_directories(dir),"existing output directory refused");
 {Fixture f;r::Snapshot s;Check(f.ReadSnapshot(s),"normal production reader");
  Check(s.current_candidates.artifact_ids==std::vector<std::uint32_t>{Fixture::first,Fixture::first},"current predicate preserves duplicates/order");
  Check(s.window_context.cached_candidates.artifact_ids==std::vector<std::uint32_t>{Fixture::second},"cached GUI list independent from current predicate");
  Check(s.artifact_permissions.can_enshrine.value==true&&s.artifact_permissions.can_remove.value==false,"native true and false preserved");
  Check(s.window_context.selected_slot_index==1U&&s.current_buttons.context_matches_requested_artifact==true,"explicit real slot and selected artifact bound");
  Check(s.native_getter_calls==8&&f.inventory_calls==1&&f.candidate_calls==3&&f.artifact_permission_calls==2&&f.button_calls==2,"actual dependency routes and top-level call count");Save(dir,"normal.json",s);}
 {Fixture f;f.memory.Put(f.window,0x108,Fixture::second);r::Snapshot s;Check(f.ReadSnapshot(s)&&s.artifact_permissions.can_enshrine.value==true&&
  s.current_buttons.can_enshrine.value==false&&s.current_buttons.context_matches_requested_artifact==false,"explicit target is distinct from current button");Save(dir,"selected-different.json",s);}
 {Fixture f;r::Snapshot s;Check(f.ReadSnapshot(s,Fixture::nonowned)&&s.artifact_permissions.player_inventory_contains_reference==false&&
  s.artifact_permissions.can_enshrine.value==true,"raw command permission does not establish actor ownership");Save(dir,"nonowned-permission.json",s);}
 {Fixture f;f.memory.Put(f.handler,0x5D8,static_cast<void*>(nullptr));r::Snapshot s;Check(f.ReadSnapshot(s)&&!s.window_context.available&&s.current_candidates.available&&
  !s.artifact_permissions.can_enshrine.value,"absent window does not erase current player candidates or invent permission false");Save(dir,"window-unavailable.json",s);}
 {Fixture f;auto*foreign=f.memory.Make(24);f.memory.Put(f.window,0x110,foreign);r::Snapshot s;Check(f.ReadSnapshot(s)&&!s.window_context.available&&
  f.artifact_permission_calls==0&&f.button_calls==0,"foreign slot pointer rejected before original permission dependencies");Save(dir,"foreign-slot.json",s);}
 {Fixture f;r::Snapshot s;Check(f.ReadSnapshot(s,Fixture::first+0x01000000U)&&!s.artifact_permissions.object_resolved&&s.current_buttons.available,
  "stale requested artifact refused independently of valid current selected artifact");Save(dir,"stale-artifact.json",s);}
 {Fixture f;r::Snapshot s;Check(!f.ReadSnapshot(s,Fixture::first,Fixture::site_id+0x01000000U)&&!s.holy_site_id&&s.native_getter_calls==0,
  "stale holy site generation rejected before getters");Save(dir,"stale-site-generation.json",s);}
 {Fixture f;f.predicate_failure=true;r::Snapshot s;Check(f.ReadSnapshot(s)&&!s.current_candidates.available&&s.current_candidates.evaluations.size()==3&&
  s.current_candidates.evaluations[0].can_be_candidate==true&&!s.current_candidates.evaluations[1].can_be_candidate,
  "partial predicate failure preserves known rows and unknown row, no final candidate list claim");Save(dir,"predicate-unavailable.json",s);}
 {Fixture f;r::Snapshot s;Check(f.ReadSnapshot(s,std::nullopt)&&!s.artifact_permissions.available&&s.current_buttons.available&&
  !s.current_buttons.context_matches_requested_artifact,"no explicit target does not silently adopt current selection");Save(dir,"no-artifact-request.json",s);}
 {Fixture f;f.memory.Put(f.inv,0x64,std::int32_t{0});f.memory.Put(f.window,0x108,Fixture::installed);r::Snapshot s;
  Check(f.ReadSnapshot(s,Fixture::installed)&&s.current_candidates.available&&s.current_candidates.artifact_ids.empty()&&s.current_candidates.evaluations.empty()&&
   s.artifact_permissions.can_remove.value==true,"actual empty player inventory remains empty while installed artifact removal permission is independent");Save(dir,"empty-player-inventory.json",s);}
 {Fixture f;f.memory.Put(f.window,0x138,std::int32_t{-1});r::Snapshot s;Check(f.ReadSnapshot(s)&&s.window_context.available&&
  !s.window_context.cached_candidates.available&&s.artifact_permissions.available&&s.current_candidates.available,
  "unavailable GUI candidate cache is not empty and does not erase independent permissions");Save(dir,"cache-unavailable.json",s);}
 {Fixture f;f.memory.Put(f.window,0x110,static_cast<void*>(nullptr));r::Snapshot s;Check(f.ReadSnapshot(s)&&s.window_context.slot_mode=="native_automatic"&&
  !s.window_context.selected_slot_index&&s.artifact_permissions.available,"null selected slot is original automatic context, effective replacement still unobserved");Save(dir,"automatic-slot.json",s);}
 Check(!r::BindHolySiteRelicPermissionsImage12004(Fixture::image,"foreign-build").model.enabled,"foreign executable identity fails closed");
 std::cout<<"PASS checks="<<checks<<" packets=12 production_reader=true production_serializer=true synthetic_storage=true injected_native_dependencies=true engine_code_executed=false live=false\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}

#include "xar_bridge/ck3_12004_holy_site_relic_context.hpp"
#include "xar_bridge/ck3_12004_holy_site_relic_action_context.hpp"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <vector>

namespace h = xar::ck3_12004::religion::holy_site_relic;
namespace {
constexpr std::uint32_t absent=0xFFFFFFFFU, site_id=7, player=13;
constexpr std::uint32_t faith_a=0x01000001,faith_b=0x02000002;
constexpr std::uint32_t artifact_a=0x01000004,artifact_b=0x02000005,artifact_c=0x03000006;
std::size_t checks=0;
void Check(bool value,const char *message){++checks;if(!value)throw std::runtime_error(message);}
struct Header{const void *data=nullptr;std::uint32_t capacity=0,count=0;std::uintptr_t allocator=0;};
struct Slot{std::uintptr_t vtable=0,type=0;std::uint32_t artifact=absent,magic=0x496E7653;};
static_assert(sizeof(Header)==24 && sizeof(Slot)==24);
struct Block {
 std::vector<std::byte> bytes;
 explicit Block(std::size_t size):bytes(size){}
 const void *ptr()const{return bytes.data();}
 template<class T>void Put(std::size_t offset,const T &v){
  if(offset+sizeof(T)>bytes.size())throw std::runtime_error("fixture block write");
  std::memcpy(bytes.data()+offset,&v,sizeof(v));
 }
 template<class T>T Get(std::size_t offset)const{T value{};std::memcpy(&value,bytes.data()+offset,sizeof(value));return value;}
};
struct Storage {
 Block header{0x40},rows{128*16};
 void *slot=nullptr;
 Storage(){slot=header.bytes.data();header.Put(0x20,rows.ptr());header.Put(0x2C,std::uint32_t{128});}
 void Add(std::uint32_t id,const void *p){rows.Put(static_cast<std::size_t>(id&0xFFFFFFU)*16+8,p);}
};
struct Fixture {
 h::Bindings b{};
 xar::ck3_12002::religion::Context context{};
 Storage sites,artifacts,titles,characters,rites,faiths;
 Block site{0xC0},barony{0x130},county{0x130},actor{0x1C0},rite{0x4C0},holder{0x1C0},holder_rite{0x4C0};
 Block type{0x430},actor_data{0x520},holder_data{0x270},actor_model{0x110},holder_model{0x110};
 std::uint32_t actor_reference=player;
 std::array<std::uint32_t,3> owned_artifacts{artifact_a,artifact_b,artifact_c};
 std::array<std::uint16_t,2> faith_keys{0x1234,0xFFFF},local_keys{0x2345,0x1234},aggregate_keys{0x1234,0x2345};
 std::array<std::int64_t,2> faith_values{500000,900000},local_values{200000,100000};
 std::array<std::int64_t,2> actor_values{700000,400000},holder_values{900000,600000};
 bool mutate_aggregate_during_copy=false,aggregate_mutated=false;
 Block owner{0x20},gfx{0x90},handler{0x600},window{0x150},root{8};
 std::array<Block,3> artifact_objects{Block{0x4C0},Block{0x4C0},Block{0x4C0}};
 std::array<Block,65> faith_objects;
 std::array<std::uint32_t,128> associated{},candidates{};
 std::array<Slot,65> slots{};
 std::vector<std::pair<std::uintptr_t,std::size_t>> regions;
 std::size_t calls=0;
 enum class Mutation{none,faith,slot,candidate};
 Mutation mutate=Mutation::none;
 bool getter_failure=false;
 Fixture():faith_objects(MakeFaiths(std::make_index_sequence<65>{})){
  b.enabled=true;b.image_base=0x140000000;b.read_context=this;b.read_memory=&Copy;b.recognition=&Recognition;
  b.getter_backend="owned_fixture_injected_getter";
  b.holy_site_storage=&sites.slot;b.artifact_storage=&artifacts.slot;b.title_storage=&titles.slot;
  b.character_storage=&characters.slot;b.rite_storage=&rites.slot;b.faith_storage=&faiths.slot;
  context.available=true;context.capture_epoch=77;context.date_raw=42;context.played_character_id=player;
  context.rite_id=3;context.faith_id=faith_a;
  site.Put(0x10,site_id);site.Put(0x14,std::uint32_t{0x486F5374});site.Put(0x18,std::uint8_t{0});
  site.Put(0x20,type.ptr());
  type.Put(0x58,Header{faith_keys.data(),2,2,0});type.Put(0xC0,Header{faith_values.data(),2,2,0});
  type.Put(0x218,Header{local_keys.data(),2,2,0});type.Put(0x280,Header{local_values.data(),2,2,0});
  site.Put(0xB0,std::uint32_t{8});sites.Add(site_id,site.ptr());
  barony.Put(0x10,std::uint32_t{8});barony.Put(0x108,std::uint32_t{9});titles.Add(8,barony.ptr());
  county.Put(0x10,std::uint32_t{9});county.Put(0x128,std::uint32_t{14});titles.Add(9,county.ptr());
  actor.Put(0x18,player);actor.Put(0x1C,std::uint32_t{0x43686172});actor.Put(0xB4,std::uint32_t{3});characters.Add(player,actor.ptr());
  rite.Put(8,std::uint32_t{3});rite.Put(0x4B8,faith_a);rites.Add(3,rite.ptr());
  holder.Put(0x18,std::uint32_t{14});holder.Put(0x1C,std::uint32_t{0x43686172});holder.Put(0xB4,std::uint32_t{4});characters.Add(14,holder.ptr());
  holder_rite.Put(8,std::uint32_t{4});holder_rite.Put(0x4B8,faith_b);rites.Add(4,holder_rite.ptr());
  actor.Put(0x1B0,actor_data.ptr());actor_data.Put(0x258,actor_model.ptr());actor_model.Put(8,actor.ptr());
  actor_data.Put(0x490,player);actor_data.Put(0x494,absent);actor_data.Put(0x4B0,Header{owned_artifacts.data(),3,3,0});
  holder.Put(0x1B0,holder_data.ptr());holder_data.Put(0x258,holder_model.ptr());holder_model.Put(8,holder.ptr());
  actor_model.Put(0x78,Header{aggregate_keys.data(),2,2,0});actor_model.Put(0xE0,Header{actor_values.data(),2,2,0});
  holder_model.Put(0x78,Header{aggregate_keys.data(),2,2,0});holder_model.Put(0xE0,Header{holder_values.data(),2,2,0});
  for(std::size_t i=0;i<faith_objects.size();++i){
   const auto id=i==0?faith_a:i==1?faith_b:static_cast<std::uint32_t>(0x01000000+i+1);
   faith_objects[i].Put(8,id);faiths.Add(id,faith_objects[i].ptr());
  }
  const std::array ids{artifact_a,artifact_b,artifact_c};
  for(std::size_t i=0;i<ids.size();++i){auto &a=artifact_objects[i];
   a.Put(0x10,ids[i]);a.Put(0x14,std::uint32_t{0x41727469});a.Put(0x78,player);a.Put(0x7C,absent);
   a.Put(0xB0,static_cast<std::int32_t>(i+1));artifacts.Add(ids[i],a.ptr());
  }
  associated[0]=faith_a;associated[1]=faith_b;associated[2]=faith_a;
  candidates[0]=artifact_b;candidates[1]=artifact_a;
  slots[0].artifact=artifact_a;slots[1].artifact=artifact_a;
  site.Put(0x98,Header{associated.data(),128,3,0});site.Put(0x68,Header{slots.data(),65,3,0});
  owner.Put(0x10,gfx.ptr());gfx.Put(0x88,handler.ptr());handler.Put(0x5D8,window.ptr());
  window.Put(0,b.image_base+0x4592338);window.Put(0x10,b.image_base+0x4592310);
  window.Put(0xA0,handler.ptr());window.Put(0x98,owner.ptr());window.Put(0x60,root.ptr());
  window.Put(0xC8,site_id);window.Put(0x130,Header{candidates.data(),128,2,0});
  for(auto *s:{&sites,&artifacts,&titles,&characters,&rites,&faiths}){
   Add(s->header);Add(s->rows);Region(&s->slot,sizeof(s->slot));
  }
  for(auto *o:{&site,&barony,&county,&actor,&rite,&holder,&holder_rite,&owner,&gfx,&handler,&window,&root})Add(*o);
  for(auto *o:{&type,&actor_data,&holder_data,&actor_model,&holder_model})Add(*o);
  for(auto &o:artifact_objects)Add(o);for(auto &o:faith_objects)Add(o);
  Region(associated.data(),sizeof(associated));Region(candidates.data(),sizeof(candidates));Region(slots.data(),sizeof(slots));
  Region(faith_keys.data(),sizeof(faith_keys));Region(local_keys.data(),sizeof(local_keys));Region(aggregate_keys.data(),sizeof(aggregate_keys));
  Region(faith_values.data(),sizeof(faith_values));Region(local_values.data(),sizeof(local_values));
  Region(actor_values.data(),sizeof(actor_values));Region(holder_values.data(),sizeof(holder_values));
  Region(&actor_reference,sizeof(actor_reference));Region(owned_artifacts.data(),sizeof(owned_artifacts));
 }
 template<std::size_t... I>static std::array<Block,65> MakeFaiths(std::index_sequence<I...>){return {((void)I,Block{0x20})...};}
 void Region(const void *p,std::size_t size){regions.emplace_back(reinterpret_cast<std::uintptr_t>(p),size);}
 void Add(const Block &v){Region(v.ptr(),v.bytes.size());}
 static bool Copy(void *opaque,const void *source,void *destination,std::size_t size)noexcept{
  auto &f=*static_cast<Fixture*>(opaque);const auto p=reinterpret_cast<std::uintptr_t>(source);
  for(const auto &[base,length]:f.regions)if(p>=base && p-base<=length && size<=length-(p-base)){
   std::memcpy(destination,source,size);
   if(f.mutate_aggregate_during_copy&&!f.aggregate_mutated&&source==f.actor_values.data()&&size==sizeof(std::int64_t)){
    f.actor_values[0]+=100000;f.aggregate_mutated=true;
   }
   return true;
  }return false;
 }
 static bool Recognition(const h::Bindings &b,const void *object,std::uint32_t faith,bool &out)noexcept{
  auto &f=*static_cast<Fixture*>(b.read_context);++f.calls;
  std::uint32_t id=0;if(!Copy(&f,static_cast<const std::byte*>(object)+0x10,&id,sizeof(id)))return false;
  if(f.calls==1){
   if(f.mutate==Mutation::faith)f.associated[1]=faith_a;
   if(f.mutate==Mutation::slot)f.slots[0].artifact=artifact_b;
   if(f.mutate==Mutation::candidate)f.candidates[0]=artifact_c;
  }
  if(f.getter_failure)return false;
  out=(id==artifact_a && faith==faith_a)||(id==artifact_b && faith==faith_b);return true;
 }
 h::RecognitionMatrix Read(std::optional<std::uint32_t> request=std::nullopt,const void *selected_owner=nullptr){
  h::RecognitionMatrix result{};(void)h::ReadHolySiteRelicRecognitionMatrix12004(b,
   selected_owner?selected_owner:owner.ptr(),context,site_id,request,nullptr,result);return result;
 }
 static bool Inventory(const xar::ck3_12004::religion::relic_permissions::Bindings &b,const void *,const void *&out)noexcept{
  const auto &f=*static_cast<const Fixture*>(b.model.read_context);out=f.actor_data.bytes.data()+0x458;return true;
 }
};
void Write(const std::filesystem::path &directory,const char *name,const Fixture &f,h::RecognitionMatrix matrix){
 h::Snapshot parent{};parent.available=true;parent.capture_epoch=f.context.capture_epoch;parent.date_raw=f.context.date_raw;
 parent.played_character_id=player;parent.player_rite_id=f.context.rite_id;parent.player_faith_id=f.context.faith_id;
 parent.requested_holy_site_id=site_id;parent.holy_site_id=site_id;
 parent.getter_backend="owned_fixture_injected_getter";parent.unavailable_reason.clear();
 parent.recognition_matrix=std::move(matrix);
 std::ofstream stream(directory/(std::string(name)+".json"),std::ios::binary);
 stream<<h::SerializeHolySiteRelicContextCommand12004(parent,std::string("g2-read-")+name,9,f.context.date_raw);
 if(!stream)throw std::runtime_error("fixture packet write failed");
}
void Unknown(const h::RecognitionMatrix &m){
 Check(!m.available&&!m.complete&&!m.source_arrays_stable,"drift must invalidate matrix");
 Check(std::all_of(m.cells.begin(),m.cells.end(),[](const auto &c){return !c.available&&!c.value;}),"unknown must never turn false");
}
void WriteModifiers(const std::filesystem::path &directory,const char *name,const Fixture &f,h::ModifierAggregateObservation observation){
 h::Snapshot parent{};parent.available=true;parent.capture_epoch=f.context.capture_epoch;parent.date_raw=f.context.date_raw;
 parent.played_character_id=player;parent.player_rite_id=f.context.rite_id;parent.player_faith_id=f.context.faith_id;
 parent.requested_holy_site_id=site_id;parent.holy_site_id=site_id;parent.getter_backend="owned_fixture_injected_getter";
 parent.unavailable_reason.clear();parent.modifier_aggregate_observation=std::move(observation);
 std::ofstream stream(directory/(std::string(name)+".json"),std::ios::binary);
 stream<<h::SerializeHolySiteRelicContextCommand12004(parent,std::string("g2-read-")+name,9,42);Check(static_cast<bool>(stream),"modifier packet write");
}
}
int main(int argc,char **argv){
 try{
  if(argc!=2)throw std::runtime_error("expected one new packet directory");
  const std::filesystem::path directory=argv[1];
  if(std::filesystem::exists(directory)||!std::filesystem::create_directories(directory))throw std::runtime_error("new packet directory required");
  {
   Fixture f;auto m=f.Read();Check(m.available&&m.complete&&m.source_arrays_stable,"complete matrix");
   Check(m.faiths.size()==2&&m.artifacts.size()==2&&m.cells.size()==4&&m.native_getter_calls==4&&f.calls==4,"deduplicated grid and getter count");
   Check(m.faiths[0].source_player&&m.faiths[0].source_associated&&!m.faiths[0].source_county_holder,"player provenance");
   Check(m.faiths[1].source_county_holder&&m.faiths[1].source_associated,"holder provenance");
   Check(m.artifacts[0].slot_indices==std::vector<std::uint32_t>{0,1}&&m.artifacts[0].candidate_indices==std::vector<std::uint32_t>{1},"duplicate source indices");
   Check(m.cells[0].value==true&&m.cells[1].value==false&&m.cells[2].value==false&&m.cells[3].value==true,"separate observed true and false");
   Write(directory,"complete",f,std::move(m));
  }
  {
   Fixture f;auto m=f.Read(artifact_c);Check(m.complete&&m.artifacts.size()==3&&m.cells.size()==6&&m.artifacts[2].source_action_request,"action request union");
   // The following independent production action reader emits the full packet;
   // do not mix an inner DTO into the command_result packet directory.
  }
  {
   Fixture f;f.window.Put(0x108,artifact_c);
   namespace a=xar::ck3_12004::religion::relic_action_context;
   a::Bindings bindings{};bindings.permissions.model=f.b;bindings.permissions.current_actor_reference=&f.actor_reference;
   bindings.permissions.player_inventory=&Fixture::Inventory;bindings.permissions.getter_backend="owned_fixture_injected_getter";
   bindings.getter_backend="owned_fixture_injected_getter";a::Snapshot observed{};
   Check(a::ReadHolySiteRelicActionContext12004(bindings,f.owner.ptr(),f.context,site_id,artifact_c,observed),"actual action-context reader integration");
   Check(observed.recognition_matrix&&observed.recognition_matrix->complete&&observed.recognition_matrix->artifacts.size()==3,"action-context attaches exact request matrix");
   Check(!observed.preview_identity_available,"partial injected permissions do not invent an action preview");
   std::ofstream stream(directory/"action-context-integration.json",std::ios::binary);
   stream<<a::SerializeHolySiteRelicActionContextCommand12004(observed,"g2-read-action-context-integration",9,42);
   Check(static_cast<bool>(stream),"full action-context packet write");
  }
  {
   Fixture f;f.window.Put(0xC8,site_id+1);auto m=f.Read();Check(m.available&&!m.complete&&!m.window_candidates_available,"missing window remains partial");
   Check(m.artifacts.size()==1&&m.native_getter_calls==2,"no invented candidates");Write(directory,"window-unavailable",f,std::move(m));
  }
  {
   Fixture f;f.faith_objects[1].Put(8,std::uint32_t{2});auto m=f.Read();Check(m.available&&!m.complete&&!m.county_holder_faith_id,"stale generation is unresolved");
   Check(!m.faiths[1].object_resolved&&!m.cells[1].available&&!m.cells[1].value,"stale faith stays unknown");Write(directory,"stale-faith",f,std::move(m));
  }
  {
   Fixture f;f.getter_failure=true;auto m=f.Read();Check(m.available&&!m.complete&&m.native_getter_calls==4,"failed getter is counted");
   Check(std::all_of(m.cells.begin(),m.cells.end(),[](const auto &c){return !c.available&&!c.value;}),"failed getter stays unknown");Write(directory,"getter-unavailable",f,std::move(m));
  }
  for(const auto [mutation,name]:{std::pair{Fixture::Mutation::faith,"faith-drift"},std::pair{Fixture::Mutation::slot,"slot-drift"},std::pair{Fixture::Mutation::candidate,"candidate-drift"}}){
   Fixture f;f.mutate=mutation;auto m=f.Read();Unknown(m);Write(directory,name,f,std::move(m));
  }
  {
   Fixture f;for(std::size_t i=0;i<65;++i)f.associated[i]=i==0?faith_a:i==1?faith_b:static_cast<std::uint32_t>(0x01000000+i+1);
   f.site.Put(0x98,Header{f.associated.data(),128,65,0});auto m=f.Read();Unknown(m);
   Check(m.native_getter_calls==0&&f.calls==0&&m.faiths.empty()&&m.artifacts.empty()&&m.cells.empty()&&m.associated_faith_ids.size()==65,"faith overflow before getter without truncation");
   Write(directory,"faith-overflow",f,std::move(m));
  }
  {
   Fixture f;f.site.Put(0x68,Header{f.slots.data(),65,65,0});auto m=f.Read();Unknown(m);
   Check(m.slot_artifact_ids.size()==65&&m.cells.empty()&&m.native_getter_calls==0&&f.calls==0,"slot overflow before getter");Write(directory,"slot-overflow",f,std::move(m));
  }
  {
   Fixture f;for(std::size_t i=0;i<64;++i)f.associated[i]=i==0?faith_a:i==1?faith_b:static_cast<std::uint32_t>(0x01000000+i+1);
   f.site.Put(0x98,Header{f.associated.data(),128,64,0});
   f.candidates[0]=artifact_a;f.candidates[1]=artifact_b;f.candidates[2]=artifact_c;f.candidates[3]=7;f.candidates[4]=8;
   f.window.Put(0x130,Header{f.candidates.data(),128,5,0});auto m=f.Read();Unknown(m);
   Check(m.native_getter_calls==0&&f.calls==0&&m.faiths.empty()&&m.artifacts.empty()&&m.cells.empty(),"Cartesian limit checked before resolving/calling");
   Write(directory,"cartesian-overflow",f,std::move(m));
  }
  {
   Fixture f;h::ModifierAggregateObservation o{};Check(h::ReadHolySiteModifierAggregate12004(f.b,f.context,site_id,o)&&o.complete,"actual modifier fixed-source observation");
   Check(o.definition_blocks[0].entries[0].definition_raw_q64==500000&&o.definition_blocks[1].entries[0].definition_raw_q64==200000,"two independent definition PCs");
   Check(o.recipients.size()==2&&o.recipients[0].source_player&&o.recipients[1].source_county_holder,"recipient full-ID provenance");
   Check(o.recipients[0].values.size()==2&&o.recipients[0].values[0].key_raw_u16==0x1234&&o.recipients[0].values[1].key_raw_u16==0x2345,"union order, duplicate dedup and sentinel skip");
   Check(o.recipients[0].values[0].aggregate_raw_q64==700000&&o.recipients[1].values[0].aggregate_raw_q64==900000,"actual totals need not equal definition");
   WriteModifiers(directory,"modifier-owned-aggregates",f,std::move(o));
  }
  {
   Fixture f;f.actor.Put(0x1B0,static_cast<const void*>(nullptr));h::ModifierAggregateObservation o{};
   Check(h::ReadHolySiteModifierAggregate12004(f.b,f.context,site_id,o)&&!o.complete,"missing cache permits honest partial");
   Check(!o.recipients[0].available&&!o.recipients[0].owned_aggregate_observed&&
    std::all_of(o.recipients[0].values.begin(),o.recipients[0].values.end(),[](const auto &v){return !v.available&&!v.aggregate_raw_q64;}),"fallback never invented as zero");
   Check(o.recipients[1].available,"independent holder aggregate stays known");WriteModifiers(directory,"modifier-cache-unavailable",f,std::move(o));
  }
  {
   Fixture f;f.type.Put(0x64,std::int32_t{33});h::ModifierAggregateObservation o{};
   Check(!h::ReadHolySiteModifierAggregate12004(f.b,f.context,site_id,o)&&!o.source_arrays_stable&&o.definition_blocks[0].count_raw==33,"fixed PC cap");
   Check(o.definition_blocks[0].entries.empty()&&o.definition_blocks[1].entries.empty()&&o.recipients.empty(),"PC cap precedes aggregate read");WriteModifiers(directory,"modifier-definition-overflow",f,std::move(o));
  }
  {
   Fixture f;f.mutate_aggregate_during_copy=true;h::ModifierAggregateObservation o{};
   Check(!h::ReadHolySiteModifierAggregate12004(f.b,f.context,site_id,o)&&f.aggregate_mutated,"in-place aggregate drift detected");
   Check(!o.available&&!o.complete&&!o.source_arrays_stable&&
    std::all_of(o.recipients.begin(),o.recipients.end(),[](const auto &r){return !r.available&&r.values.empty();}),"drift clears observed totals");
   WriteModifiers(directory,"modifier-aggregate-drift",f,std::move(o));
  }
  {
   Fixture f;h::Snapshot observed{};Check(h::ReadHolySiteRelicContext12004(f.b,f.context,site_id,observed,f.owner.ptr()),"existing context integration");
   Check(observed.recognition_matrix&&observed.recognition_matrix->complete,"production reader attaches matrix");
   Check(observed.modifier_aggregate_observation&&observed.modifier_aggregate_observation->complete,"production reader attaches actual aggregates");
   Check(observed.native_getter_calls==2&&observed.recognition_matrix->native_getter_calls==4&&f.calls==6,"old counter retains original scope");
   std::ofstream stream(directory/"context-integration.json",std::ios::binary);stream<<h::SerializeHolySiteRelicContextCommand12004(observed,"g2-read-context-integration",9,42);
   Check(static_cast<bool>(stream),"integration packet write");
  }
  std::cout<<"PASS checks="<<checks<<" owned_memory=true injected_recognition=true live=false\n";return 0;
 }catch(const std::exception &e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}
}

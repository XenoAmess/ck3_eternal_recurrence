// Owned memory -> production reader -> production full command_result JSON.
// Recognition/current-rarity callbacks are explicit native dependency fixtures;
// no CK3 code, TLS or template trigger executes in this portable executable.
#include "xar_bridge/ck3_12004_holy_site_relic_context.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <utility>
#include <vector>

namespace r=xar::ck3_12004::religion::holy_site_relic;
namespace {
unsigned checks=0;
void Check(bool ok,const char *why) {++checks;if(!ok)throw std::runtime_error(why);}
struct Memory {
  struct Region {std::unique_ptr<std::byte[]> data;std::size_t size;};
  struct Block {const void *address;std::size_t size;};
  std::vector<Region> regions;
  std::vector<Block> blocks;
  void *fixture=nullptr;
  void *Allocate(std::size_t size) {
    auto data=std::make_unique<std::byte[]>(size);auto *p=data.get();
    regions.push_back({std::move(data),size});return p;
  }
  template<class T> void Put(void *p,std::size_t offset,T value) {
    std::memcpy(static_cast<std::byte *>(p)+offset,&value,sizeof(value));
  }
  static bool Read(void *opaque,const void *p,void *out,std::size_t size) noexcept {
    auto &m=*static_cast<Memory *>(opaque);
    const auto begin=reinterpret_cast<std::uintptr_t>(p);
    for (const auto &block:m.blocks) {
      const auto blocked=reinterpret_cast<std::uintptr_t>(block.address);
      if(begin<blocked+block.size&&blocked<begin+size)return false;
    }
    for (const auto &region:m.regions) {
      const auto base=reinterpret_cast<std::uintptr_t>(region.data.get());
      if(begin>=base&&begin-base<=region.size&&size<=region.size-static_cast<std::size_t>(begin-base)) {
        std::memcpy(out,p,size);return true;
      }
    }
    return false;
  }
  void Ids(void *p,std::size_t offset,const std::vector<std::uint32_t> &ids) {
    auto *data=ids.empty()?nullptr:Allocate(ids.size()*4);
    if(data)std::memcpy(data,ids.data(),ids.size()*4);
    Put(p,offset,data);Put(p,offset+8,static_cast<std::uint32_t>(ids.size()));
    Put(p,offset+12,static_cast<std::uint32_t>(ids.size()));Put(p,offset+16,static_cast<void *>(nullptr));
  }
};
struct Storage {
  void *header=nullptr,*rows=nullptr,*global=nullptr;
  Memory &m;
  explicit Storage(Memory &memory):m(memory) {
    header=m.Allocate(0x30);rows=m.Allocate(8*16);global=m.Allocate(8);
    m.Put(header,0x20,rows);m.Put(header,0x2C,std::uint32_t{8});m.Put(global,0,header);
  }
  void Put(std::uint32_t id,void *object,std::size_t id_offset) {
    m.Put(rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object);m.Put(object,id_offset,id);
  }
  void **Slot() const {return static_cast<void **>(global);}
};
struct Fixture {
  static constexpr std::uint32_t site_id=0x84000002U,player_faith=0x81000001U,holder_faith=0x82000002U;
  static constexpr std::uint32_t rite_id=0x83000001U,barony_id=0x87000001U,county_id=0x88000002U;
  static constexpr std::uint32_t holder_id=0x89000003U,first_id=0x85000004U,second_id=0x86000005U;
  Memory memory;
  Storage sites{memory},artifacts{memory},titles{memory},characters{memory},rites{memory},faiths{memory};
  void *site=memory.Allocate(0xB8),*first=memory.Allocate(0x4B0),*second=memory.Allocate(0x4B0);
  void *barony=memory.Allocate(0x130),*county=memory.Allocate(0x130),*holder=memory.Allocate(0xC0);
  void *rite=memory.Allocate(0x4C0),*player_faith_object=memory.Allocate(0x20),*holder_faith_object=memory.Allocate(0x20);
  std::uint32_t recognition_calls=0,current_calls=0;
  std::int32_t current_value=4;
  bool fail_recognition=false;
  Fixture() {
    memory.fixture=this;
    sites.Put(site_id,site,0x10);memory.Put(site,0x14,std::uint32_t{0x486F5374});
    artifacts.Put(first_id,first,0x10);artifacts.Put(second_id,second,0x10);
    for(auto *a:{first,second}) {
      memory.Put(a,0x14,std::uint32_t{0x41727469});memory.Put(a,0x7C,site_id);
    }
    memory.Put(first,0xB0,std::int32_t{3});memory.Put(second,0xB0,std::int32_t{1});
    memory.Ids(first,0x498,{player_faith});memory.Ids(second,0x498,{holder_faith});
    titles.Put(barony_id,barony,0x10);titles.Put(county_id,county,0x10);
    characters.Put(holder_id,holder,0x18);rites.Put(rite_id,rite,8);
    faiths.Put(player_faith,player_faith_object,8);faiths.Put(holder_faith,holder_faith_object,8);
    memory.Put(site,0xB0,barony_id);memory.Put(barony,0x108,county_id);memory.Put(county,0x128,holder_id);
    memory.Put(holder,0xB4,rite_id);memory.Put(rite,0x4B8,holder_faith);
    memory.Ids(site,0x98,{holder_faith,player_faith});
    memory.Ids(site,0x80,{first_id,second_id,first_id});
    SetSlots({first_id,second_id,0xFFFFFFFFU});SetCache(true,4);
  }
  void SetCache(bool active,std::int32_t sum) {memory.Put(site,0x18,static_cast<std::uint8_t>(active));memory.Put(site,0x1C,sum);}
  void SetSlots(const std::vector<std::uint32_t> &ids) {
    void *rows=ids.empty()?nullptr:memory.Allocate(ids.size()*24);
    for(std::size_t i=0;i<ids.size();++i)memory.Put(rows,i*24+0x10,ids[i]);
    memory.Put(site,0x68,rows);memory.Put(site,0x70,static_cast<std::uint32_t>(ids.size()));
    memory.Put(site,0x74,static_cast<std::uint32_t>(ids.size()));memory.Put(site,0x78,static_cast<void *>(nullptr));
  }
  static bool Recognition(const r::Bindings &b,const void *artifact,std::uint32_t faith,bool &value) noexcept {
    auto &f=*static_cast<Fixture *>(static_cast<Memory *>(b.read_context)->fixture);++f.recognition_calls;
    if(f.fail_recognition)return false;
    // Two labelled fixture arms. This is not a replacement implementation of
    // the real template trigger, nor proof of 1.20.0.4 engine OR semantics.
    if(artifact==f.first)value=faith==player_faith||faith==holder_faith;
    else if(artifact==f.second)value=faith==holder_faith;
    else return false;
    return true;
  }
  static bool CurrentRarity(const r::Bindings &b,const void *site,std::int32_t &value) noexcept {
    auto &f=*static_cast<Fixture *>(static_cast<Memory *>(b.read_context)->fixture);++f.current_calls;
    if(site!=f.site)return false;
    value=f.current_value;return true;
  }
  r::Bindings Bind() {
    r::Bindings b{};b.enabled=true;b.image_base=0x140000000ULL;
    b.holy_site_storage=sites.Slot();b.artifact_storage=artifacts.Slot();b.title_storage=titles.Slot();
    b.character_storage=characters.Slot();b.rite_storage=rites.Slot();b.faith_storage=faiths.Slot();
    b.read_memory=&Memory::Read;b.read_context=&memory;b.recognition=&Recognition;b.current_rarity=&CurrentRarity;
    b.getter_backend="owned_fixture_injected_getter";return b;
  }
  xar::ck3_12002::religion::Context Context() const {
    xar::ck3_12002::religion::Context c{};c.available=true;c.capture_epoch=17;c.date_raw=51394920;
    c.played_character_id=15893;c.rite_id=0;c.faith_id=player_faith;return c;
  }
};
void Save(const std::filesystem::path &dir,const char *name,const r::Snapshot &s) {
  std::ofstream f(dir/name,std::ios::binary);
  f<<r::SerializeHolySiteRelicContextCommand12004(s,"g2-read-holy-site-relic-fixture",701,s.date_raw)<<'\n';
  Check(bool(f),"full production command_result written");
}
}
int main(int argc,char **argv) {
 try {
  Check(argc==2,"one output directory required");const std::filesystem::path output(argv[1]);
  Check(std::filesystem::create_directories(output),"exclusive new output directory required");
  {
    Fixture f;auto b=f.Bind();auto c=f.Context();r::Snapshot s;
    Check(r::ReadHolySiteRelicContext12004(b,c,Fixture::site_id,s),"production reader normal input");
    Check(s.inventory.artifact_ids==std::vector<std::uint32_t>({Fixture::first_id,Fixture::second_id,Fixture::first_id}),"raw inventory preserves duplicates/order");
    Check(s.inventory.slots.size()==3&&!s.inventory.slots[2].artifact_id,"empty slot is not an invented artifact");
    Check(s.inventory.artifact_objects.size()==2&&s.inventory.artifact_objects[0].artifact_id==Fixture::first_id,"object union first appearance order");
    Check(s.inventory.artifact_objects[0].sanctified_faith_ids==std::vector<std::uint32_t>{Fixture::player_faith},"dynamic sanctified list read independently");
    Check(s.inventory.artifact_objects[0].recognition_for_county_holder_faith.value==true&&
          s.inventory.artifact_objects[1].recognition_for_player_faith.value==false,"actual target faith passed to fixture callbacks");
    Check(s.current_relic_evaluation.active_artifact_rarity_sum==4&&s.current_relic_evaluation.cache_evaluation_disagreement==false,"current native dependency result and cache differ from inventory length");
    Check(f.recognition_calls==4&&f.current_calls==1&&s.native_getter_calls==5,"getter invocation disclosure counts only top-level callbacks");
    Save(output,"normal.json",s);
  }
  {
    Fixture f;f.SetCache(false,0);r::Snapshot s;
    Check(r::ReadHolySiteRelicContext12004(f.Bind(),f.Context(),Fixture::site_id,s)&&
          s.current_relic_evaluation.cache_evaluation_disagreement==true&&s.cached_world_state.is_active==false,
          "cache disagreement preserves both values without writing cache");Save(output,"cache-disagreement.json",s);
  }
  {
    Fixture f;r::Snapshot s;
    Check(!r::ReadHolySiteRelicContext12004(f.Bind(),f.Context(),Fixture::site_id+0x01000000U,s)&&
          s.unavailable_reason=="holy_site_full_reference_unavailable"&&s.native_getter_calls==0,
          "same low24 stale generation refused before callbacks");Save(output,"stale-generation.json",s);
  }
  {
    Fixture f;f.memory.Put(f.rite,0x4B8,std::uint32_t{0x99000007});r::Snapshot s;
    Check(r::ReadHolySiteRelicContext12004(f.Bind(),f.Context(),Fixture::site_id,s)&&!s.county_context.available&&
          s.current_relic_evaluation.available&&!s.current_relic_evaluation.county_holder_faith_associated,
          "partial county identity does not invent holder faith or override successful dependency getter");
    Save(output,"holder-faith-unavailable.json",s);
  }
  {
    Fixture f;auto b=f.Bind();b.recognition=nullptr;b.current_rarity=nullptr;r::Snapshot s;
    Check(r::ReadHolySiteRelicContext12004(b,f.Context(),Fixture::site_id,s)&&s.inventory.artifact_objects[0].available&&
          !s.inventory.artifact_objects[0].recognition_for_player_faith.value&&!s.current_relic_evaluation.available&&
          s.current_relic_evaluation.inventory_artifact_count_raw==3,
          "missing getter leaves unknown result while preserving observed count and object");Save(output,"getters-unavailable.json",s);
  }
  {
    Fixture f;f.memory.Ids(f.site,0x80,{});f.SetSlots({0xFFFFFFFFU,0xFFFFFFFFU,0xFFFFFFFFU});
    f.current_value=0;f.SetCache(false,0);r::Snapshot s;
    Check(r::ReadHolySiteRelicContext12004(f.Bind(),f.Context(),Fixture::site_id,s)&&s.inventory.artifact_ids.empty()&&
          s.inventory.artifact_objects.empty()&&s.current_relic_evaluation.active_artifact_rarity_sum==0&&s.native_getter_calls==1,
          "observed empty inventory remains distinct from unavailable");Save(output,"empty-inventory.json",s);
  }
  {
    Fixture f;f.memory.Ids(f.site,0x80,{Fixture::first_id,Fixture::first_id+0x01000000U,Fixture::second_id});r::Snapshot s;
    Check(r::ReadHolySiteRelicContext12004(f.Bind(),f.Context(),Fixture::site_id,s)&&s.inventory.artifact_objects.size()==3&&
          !s.inventory.artifact_objects[1].available&&s.current_relic_evaluation.available,
          "unresolved unused reference retained without fabricating zero or blocking independent producer");
    Save(output,"bad-unused-reference.json",s);
  }
  {
    Fixture f;f.SetSlots({Fixture::first_id,Fixture::first_id,0xFFFFFFFFU});f.current_value=6;f.SetCache(true,6);r::Snapshot s;
    Check(r::ReadHolySiteRelicContext12004(f.Bind(),f.Context(),Fixture::site_id,s)&&s.inventory.slots[0].artifact_id==s.inventory.slots[1].artifact_id&&
          s.inventory.artifact_objects.size()==2&&s.current_relic_evaluation.active_artifact_rarity_sum==6,
          "real slot duplicates retained and original producer output is not reconstructed from reference union");
    Save(output,"duplicate-slots.json",s);
  }
  {
    Fixture f;f.memory.blocks.push_back({static_cast<std::byte *>(f.site)+0x18,1});r::Snapshot s;
    Check(r::ReadHolySiteRelicContext12004(f.Bind(),f.Context(),Fixture::site_id,s)&&!s.cached_world_state.available&&
          s.current_relic_evaluation.available&&!s.current_relic_evaluation.cache_evaluation_disagreement,
          "cache unreadable leaves current producer value and null comparison");Save(output,"cache-unavailable.json",s);
  }
  Check(!r::BindHolySiteRelicContextImage12004(0x140000000ULL,"wrong-image").enabled,"foreign image binder refused");
  std::cout<<"PASS checks="<<checks<<" actual_reader=true actual_serializer=true synthetic_storage=true injected_native_dependencies=true engine_code_executed=false live=false\n";
  return 0;
 }catch(const std::exception &e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}
}

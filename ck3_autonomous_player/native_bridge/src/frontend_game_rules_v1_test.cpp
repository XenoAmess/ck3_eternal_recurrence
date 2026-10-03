#include "xar_bridge/frontend_game_rules_v1.hpp"
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
constexpr std::uintptr_t base = 0x140000000, slot = base + 0x5CB87F8;
constexpr std::uintptr_t app = 0x100000, owner = 0x200000, root = 0x300000;
constexpr std::uintptr_t records = 0x400000;
struct Region { std::uintptr_t at; std::vector<std::byte> bytes; };
struct Fixture {
  std::vector<Region> regions;
  int record_reads = 0;
  bool change_second = false;
  void Add(std::uintptr_t at, std::size_t count) {
    regions.push_back({at, std::vector<std::byte>(count)});
  }
  void PutBytes(std::uintptr_t at, const void *data, std::size_t size) {
    for (auto &r : regions) if (at >= r.at && size <= r.bytes.size() &&
        at-r.at <= r.bytes.size()-size) {
      std::memcpy(r.bytes.data()+at-r.at, data, size); return;
    }
    throw std::runtime_error("fixture write outside registered region");
  }
  template <typename T> void Put(std::uintptr_t at, T value) {
    PutBytes(at,&value,sizeof(value));
  }
  void Key(std::uintptr_t object, std::string_view value) {
    if (value.size() < 16) {
      PutBytes(object+0x18,value.data(),value.size());
      Put(object+0x18+value.size(),char{0});
      Put(object+0x30,std::uint64_t{15});
    } else {
      const auto heap = object+0x100;
      Add(heap,value.size()+1);
      PutBytes(heap,value.data(),value.size());
      Put(object+0x18,heap); Put(object+0x30,std::uint64_t{value.size()});
    }
    Put(object+0x28,std::uint64_t{value.size()});
  }
  void Rtti(std::uintptr_t vt, std::uintptr_t col, std::uint32_t type) {
    Add(base+vt-8,8); Put(base+vt-8,base+col); Add(base+col,24);
    const std::array<std::uint32_t,6> values{1,0,0,type,0,static_cast<std::uint32_t>(col)};
    PutBytes(base+col,values.data(),sizeof(values));
  }
};
bool Read(void *opaque,const void *address,void *out,std::size_t size) noexcept {
  auto &f=*static_cast<Fixture *>(opaque);
  const auto at=reinterpret_cast<std::uintptr_t>(address);
  if (at==records && size==16 && ++f.record_reads==2 && f.change_second) {
    const std::array<std::uintptr_t,2> changed{0x500000,0x700000};
    std::memcpy(out,changed.data(),size); return true;
  }
  for (auto &r:f.regions) if (at>=r.at && size<=r.bytes.size() &&
      at-r.at<=r.bytes.size()-size) {
    std::memcpy(out,r.bytes.data()+at-r.at,size);return true;
  }
  return false;
}
Fixture Make() {
  Fixture f;
  f.Add(slot,8); f.Put(slot,app);
  f.Add(app,0xA40); f.Put(app,base+0x449BDA8); f.Put(app+0xA38,owner);
  f.Add(owner,0x230); f.Put(owner,base+0x46B79B0); f.Put(owner+0x60,root);
  f.Put(owner+0x98,records); f.Put(owner+0xA0,std::uint32_t{3});
  f.Put(owner+0xA4,std::uint32_t{3}); f.Add(records,3*16);
  f.Rtti(0x46B79B0,0x4D89C30,0x59929F8);
  f.Rtti(0x491BE58,0x4FFF4A8,0x560C140);
  f.Rtti(0x491C3D8,0x4FFF7A8,0x55C96F8);
  const std::array<std::pair<std::string_view,std::string_view>,3> keys{{
      {"zg361_enabled","zg361_on"},
      {"zg361_frequency","zg361_freq_yearly"},
      {"zg361_bottom_ratio","zg361_ratio_strict"}}};
  for (std::size_t i=0;i<3;++i) {
    const auto rule=0x500000+i*0x1000,setting=0x600000+i*0x1000;
    f.Add(rule,0xC0);f.Add(setting,0x80);
    f.Put(rule,base+0x491BE58);f.Put(setting,base+0x491C3D8);
    f.Put(rule+0x38,std::uint32_t{0x4744624F});
    f.Put(setting+0x38,std::uint32_t{0x4744624F});f.Put(setting+0x40,rule);
    f.Key(rule,keys[i].first);f.Key(setting,keys[i].second);
    f.Put(records+i*16,rule);f.Put(records+i*16+8,setting);
  }
  // Alternate actual selection for a change-between-passes test.
  f.Add(0x700000,0x80);f.Put(0x700000,base+0x491C3D8);
  f.Put(0x700038,std::uint32_t{0x4744624F});f.Put(0x700040,std::uintptr_t{0x500000});
  f.Key(0x700000,"zg361_off");
  return f;
}
xar::ck3_11906::FrontendGameRulesObservationV1 Query(Fixture &f, bool admitted=true,
    const void *expected_root=reinterpret_cast<void *>(root)) {
  xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 env{};
  env.module_base=base;env.exact_build_admitted=admitted;
  env.gui_abi_revision=xar::ck3_11906::GuiAbiRevisionV1::crozier12003;
  env.gui_global_slot=reinterpret_cast<void **>(slot);
  xar::ck3_11906::ZhongguoScoreboardAccessV1 access{};
  access.context=&f;access.read_memory=&Read;
  xar::ck3_11906::FrontendGameRulesObservationV1 out;
  assert(xar::ck3_11906::ProbeFrontendGameRulesV1(env,access,expected_root,out));
  return out;
}
void Unavailable(const auto &out,std::string_view reason) {
  assert(!out.ready && out.selections.empty() && out.unavailable_reason==reason);
}
}
int main() {
  {auto f=Make();auto out=Query(f);assert(out.ready && out.selections.size()==3);
   const auto json=xar::ck3_11906::SerializeFrontendGameRulesV1(out);
   assert(json.find("zg361_on")!=std::string::npos && json.find("zg361_ratio_strict")!=std::string::npos);}
  {auto f=Make();f.Put(records+8,std::uintptr_t{0x700000});auto out=Query(f);
   assert(out.ready);bool found=false;for(const auto &p:out.selections)
   if(p.rule_key=="zg361_enabled")found=p.selected_setting_key=="zg361_off";assert(found);}
  {auto f=Make();Unavailable(Query(f,false),"exact_12003_game_rules_environment_unverified");}
  {auto f=Make();f.Put(owner,base+0x46B8148);Unavailable(Query(f),"current_game_rules_owner_unverified");}
  {auto f=Make();Unavailable(Query(f,true,reinterpret_cast<void *>(0xBAD000)),"game_rules_owner_root_mismatch");}
  {auto f=Make();f.Put(owner+0xA4,std::uint32_t{4097});Unavailable(Query(f),"game_rules_selection_collection_unverified");}
  {auto f=Make();f.Put(0x600040,std::uintptr_t{0x501000});Unavailable(Query(f),"game_rules_selected_pair_unverified");}
  {auto f=Make();f.Put(0x600030,std::uint64_t{3});Unavailable(Query(f),"game_rules_selected_pair_unverified");}
  {auto f=Make();f.Key(0x501000,"zg361_enabled");Unavailable(Query(f),"game_rules_duplicate_rule_key");}
  {auto f=Make();f.change_second=true;Unavailable(Query(f),"game_rules_selection_changed_during_observation");}
  std::puts("PASS: 10 focused cases; derived .3 layouts, synthetic memory; no live validation");
}

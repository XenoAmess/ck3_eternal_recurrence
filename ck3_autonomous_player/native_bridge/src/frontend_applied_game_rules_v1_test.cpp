#include "xar_bridge/frontend_game_rules_v1.hpp"
#include <array>
#include <algorithm>
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
  int applied_reads = 0;
  bool change_applied = false;
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
  if (at==0xC00000 && size==8 && ++f.applied_reads==2 && f.change_applied) {
    const std::uintptr_t setting=0x700000;std::memcpy(out,&setting,8);return true;
  }
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
Fixture AppliedFixture() {
  auto f=Make();f.Add(base+0x5CB3D78,8);f.Put(base+0x5CB3D78,std::uintptr_t{0xB00000});
  f.Add(0xB00000,16);f.Put(0xB00000,base+0x46BF988);f.Put(0xB00008,base+0x27F82F0);
  f.Rtti(0x46BF988,0x4D9A870,0x59A4770);f.Rtti(0x491BFF8,0x4FFF0B8,0x5B964B0);
  f.Add(base+0x5C68C50,8);f.Put(base+0x5C68C50,std::uintptr_t{0});
  f.Put(app+0x268,std::uintptr_t{0xA00000});f.Add(0xA00000,0x18);
  f.Put(0xA00000,base+0x491BFF8);f.Put(0xA00008,std::uintptr_t{0xC00000});
  f.Put(0xA00010,std::uint32_t{3});f.Put(0xA00014,std::uint32_t{3});f.Add(0xC00000,24);
  for(std::uintptr_t i=0;i<3;++i)f.Put(0xC00000+i*8,std::uintptr_t{0x600000+i*0x1000});
  return f;
}
xar::ck3_11906::FrontendAppliedGameRulesV1 QueryApplied(Fixture &f) {
  xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 env{};
  env.module_base=base;env.exact_build_admitted=true;
  env.gui_abi_revision=xar::ck3_11906::GuiAbiRevisionV1::crozier12003;
  env.gui_global_slot=reinterpret_cast<void **>(slot);
  xar::ck3_11906::ZhongguoScoreboardAccessV1 access{};access.context=&f;access.read_memory=&Read;
  xar::ck3_11906::FrontendAppliedGameRulesV1 o;
  assert(xar::ck3_11906::ProbeFrontendAppliedGameRulesV1(env,access,o));return o;
}
}
int main() {
  using namespace xar::ck3_11906;
  {auto f=AppliedFixture();auto o=QueryApplied(f);assert(o.ready&&o.selections.size()==3);assert(SerializeFrontendAppliedGameRulesV1(o).find("\"applied_settings_proven\":true")!=std::string::npos);}
  {auto f=AppliedFixture();f.Put(0xC00000,std::uintptr_t{0x700000});auto o=QueryApplied(f);assert(o.ready);auto p=std::find_if(o.selections.begin(),o.selections.end(),[](const auto &v){return v.rule_key=="zg361_enabled";});assert(p!=o.selections.end()&&p->selected_setting_key=="zg361_off");}
  {auto f=AppliedFixture();f.Add(0xD00000,0xF8);f.Put(base+0x5C68C50,std::uintptr_t{0xD00000});f.Put(0xD000F0,std::uintptr_t{0xA01000});f.Add(0xA01000,0x18);f.Put(0xA01000,base+0x491BFF8);f.Put(0xA01008,std::uintptr_t{0xC01000});f.Put(0xA01010,std::uint32_t{1});f.Put(0xA01014,std::uint32_t{1});f.Add(0xC01000,8);f.Put(0xC01000,std::uintptr_t{0x700000});auto o=QueryApplied(f);assert(o.ready&&o.selections.size()==1&&o.selections[0].selected_setting_key=="zg361_off");}
  {auto f=AppliedFixture();f.Put(0xB00000,base+0x46BF998);auto o=QueryApplied(f);assert(!o.ready&&o.unavailable_reason=="applied_game_rules_selection_service_unverified");}
  {auto f=AppliedFixture();f.Put(0xB00008,base+0x27F8320);auto o=QueryApplied(f);assert(!o.ready&&o.unavailable_reason=="applied_game_rules_selection_service_unverified");}
  {auto f=AppliedFixture();f.Put(0xA00000,base+0x491BFE8);auto o=QueryApplied(f);assert(!o.ready&&o.unavailable_reason=="applied_game_rule_instance_unverified");}
  {auto f=AppliedFixture();f.Put(0xA00010,std::uint32_t{4097});f.Put(0xA00014,std::uint32_t{4097});auto o=QueryApplied(f);assert(!o.ready&&o.unavailable_reason=="applied_game_rule_setting_collection_unverified");}
  {auto f=AppliedFixture();f.Put(0x600040,std::uintptr_t{0xBAD000});auto o=QueryApplied(f);assert(!o.ready&&o.unavailable_reason=="applied_game_rule_selected_setting_unverified");}
  {auto f=AppliedFixture();f.Put(0xC00008,std::uintptr_t{0x600000});auto o=QueryApplied(f);assert(!o.ready&&o.unavailable_reason=="applied_game_rule_duplicate_rule_key");}
  {auto f=AppliedFixture();f.change_applied=true;auto o=QueryApplied(f);assert(!o.ready&&o.unavailable_reason=="applied_game_rules_changed_during_observation");}
  std::puts("PASS: 10 focused actual-instance cases; synthetic .3 std::function/getter/instance layouts, no native calls or live validation");
}

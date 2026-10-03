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
  bool change_host = false;
  int host_reads = 0;
  int calls = 0;
  bool ignore_next = false;
  bool change_other = false;
  bool change_owner_on_apply = false;
  std::string call_order;
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
  if (at==base+0x5CC14D0 && size==1 && ++f.host_reads==2 && f.change_host) {
    *static_cast<std::uint8_t *>(out)=1; return true;
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
Fixture ControlFixture() {
  auto f=Make(); f.Add(root,0xD1); f.Put(root+0xD0,std::uint8_t{0});
  f.Add(base+0x5CC14D0,1); f.Put(base+0x5CC14D0,std::uint8_t{0});
  f.Add(base+0x5C68C50,8); f.Put(base+0x5C68C50,std::uintptr_t{0});
  f.Add(0x800000,16);
  f.Put(0x800000,std::uintptr_t{0x700000});f.Put(0x800008,std::uintptr_t{0x600000});
  f.Put(0x500040,std::uintptr_t{0x800000});
  f.Put(0x500048,std::uint32_t{2});f.Put(0x50004C,std::uint32_t{2});
  return f;
}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 Env(bool fixture=false) {
  xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 env{};
  env.module_base=base;env.exact_build_admitted=true;
  env.gui_abi_revision=xar::ck3_11906::GuiAbiRevisionV1::crozier12003;
  env.gui_global_slot=reinterpret_cast<void **>(slot);
  env.offline_fixture_function_overrides=fixture;return env;
}
xar::ck3_11906::ZhongguoScoreboardAccessV1 Access(Fixture &f) {
  xar::ck3_11906::ZhongguoScoreboardAccessV1 a{};a.context=&f;a.read_memory=&Read;return a;
}
xar::ck3_11906::FrontendGameRulesControlV1 Control(Fixture &f) {
  xar::ck3_11906::FrontendGameRulesControlV1 o;
  assert(xar::ck3_11906::ProbeFrontendGameRulesControlV1(Env(),Access(f),reinterpret_cast<void *>(root),o));
  return o;
}
xar::ck3_11906::FrontendGameRuleChoiceV1 Choice(Fixture &f,
    std::string_view expected="zg361_on",std::string_view target="zg361_off") {
  xar::ck3_11906::FrontendGameRuleChoiceV1 o;
  assert(xar::ck3_11906::ProbeFrontendGameRuleChoiceV1(Env(),Access(f),reinterpret_cast<void *>(root),
      "zg361_enabled",expected,target,o));return o;
}
bool Next(void *context,void *target) noexcept {
  auto &f=*static_cast<Fixture *>(context);++f.calls;f.call_order+='N';
  assert(reinterpret_cast<std::uintptr_t>(target)==records);
  if (!f.ignore_next) f.Put(records+8,std::uintptr_t{0x700000});
  if (f.change_other) f.Put(records+16+8,std::uintptr_t{0x700000});
  return true;
}
bool Apply(void *context,void *target) noexcept {
  auto &f=*static_cast<Fixture *>(context);++f.calls;f.call_order+='A';
  assert(reinterpret_cast<std::uintptr_t>(target)==owner);
  if (f.change_owner_on_apply) f.Put(app+0xA38,std::uintptr_t{0xBAD000});
  return true;
}
bool Hide(void *context,void *target) noexcept {
  auto &f=*static_cast<Fixture *>(context);++f.calls;f.call_order+='H';
  assert(reinterpret_cast<std::uintptr_t>(target)==owner);
  f.Put(root+0xD0,std::uint8_t{8});return true;
}
xar::ck3_11906::FrontendGameRulesCallsV1 Calls(Fixture &f) { return {&f,&Next,&Apply,&Hide}; }
xar::ck3_11906::FrontendGameRulesMutationV1 Select(Fixture &f,bool fixture=true,
    std::string_view expected="zg361_on",std::string_view desired="zg361_off") {
  xar::ck3_11906::FrontendGameRulesMutationV1 o;
  assert(xar::ck3_11906::SelectFrontendGameRuleV1(Env(fixture),Access(f),reinterpret_cast<void *>(root),
      "zg361_enabled",expected,desired,Calls(f),o));return o;
}
xar::ck3_11906::FrontendGameRulesMutationV1 Commit(Fixture &f,bool apply=true) {
  xar::ck3_11906::FrontendGameRulesMutationV1 o;
  assert(xar::ck3_11906::ApplyAndHideFrontendGameRulesV1(Env(true),Access(f),reinterpret_cast<void *>(root),
      apply,Calls(f),o));return o;
}
}
int main() {
  using namespace xar::ck3_11906;
  {auto f=ControlFixture();auto o=Control(f);assert(o.ready&&o.window_visible&&o.is_host&&!o.game_has_started&&o.may_edit);}
  {auto f=ControlFixture();f.Put(base+0x5CC14D0,std::uint8_t{2});assert(Control(f).is_host);}
  {auto f=ControlFixture();f.Put(base+0x5CC14D0,std::uint8_t{1});auto o=Control(f);assert(o.ready&&!o.is_host&&!o.may_edit);}
  {auto f=ControlFixture();f.Add(0x900000,0xC4);f.Put(base+0x5C68C50,std::uintptr_t{0x900000});auto o=Control(f);assert(o.game_has_started&&!o.may_edit);}
  {auto f=ControlFixture();f.Add(0x900000,0xC4);f.Put(base+0x5C68C50,std::uintptr_t{0x900000});f.Put(0x9000C3,std::uint8_t{1});assert(Control(f).may_edit);}
  {auto f=ControlFixture();f.Put(root+0xD0,std::uint8_t{8});auto o=Control(f);assert(o.ready&&!o.window_visible&&!o.may_edit);assert(SerializeFrontendGameRulesControlV1(o).find("\"window_closed_proven\":true")!=std::string::npos);}
  {auto f=ControlFixture();f.Put(root+0xD0,std::uint8_t{2});auto o=Control(f);assert(o.ready&&!o.window_enabled&&!o.may_edit);}
  {auto f=ControlFixture();f.Put(base+0x5C68C50,std::uintptr_t{0});auto o=Control(f);assert(o.ready&&!o.game_has_started);}
  {auto f=ControlFixture();f.regions.erase(f.regions.begin()+static_cast<std::ptrdiff_t>(f.regions.size()-3));auto o=Control(f);assert(!o.ready&&o.unavailable_reason=="game_rules_native_control_predicates_unverified");}
  {auto f=ControlFixture();f.change_host=true;auto o=Control(f);assert(!o.ready&&o.unavailable_reason=="game_rules_control_changed_during_observation");}
  {auto f=ControlFixture();auto o=Choice(f);assert(o.ready&&o.next_count==1&&o.option_keys.size()==2&&o.option_keys[0]=="zg361_off");}
  {auto f=ControlFixture();auto o=Select(f,true,"zg361_on","zg361_on");assert(o.ready&&o.selection_verified&&!o.native_invoked&&f.calls==0);}
  {auto f=ControlFixture();auto o=Choice(f,"zg361_off");assert(!o.ready&&o.unavailable_reason=="game_rule_expected_current_setting_changed");}
  {auto f=ControlFixture();auto o=Choice(f,"zg361_on","absent");assert(!o.ready&&o.unavailable_reason=="game_rule_desired_setting_absent_from_options");}
  {auto f=ControlFixture();f.Put(0x700040,std::uintptr_t{0x501000});auto o=Choice(f);assert(!o.ready&&o.unavailable_reason=="game_rule_option_setting_unverified");}
  {auto f=ControlFixture();f.Put(0x800008,std::uintptr_t{0x700000});auto o=Choice(f);assert(!o.ready&&o.unavailable_reason=="game_rule_duplicate_option");}
  {auto f=ControlFixture();f.Put(0x500048,std::uint32_t{513});f.Put(0x50004C,std::uint32_t{513});auto o=Choice(f);assert(!o.ready&&o.unavailable_reason=="game_rule_option_collection_unverified");}
  {auto f=ControlFixture();f.Put(0x50004C,std::uint32_t{1});auto o=Choice(f);assert(!o.ready&&o.unavailable_reason=="game_rule_current_setting_absent_from_options");}
  {auto f=ControlFixture();auto o=Select(f);assert(o.ready&&o.native_invoked&&o.selection_verified&&o.native_next_calls==1&&f.calls==1);assert(Choice(f,"zg361_off").ready);}
  {auto f=ControlFixture();f.ignore_next=true;auto o=Select(f);assert(!o.ready&&o.native_next_calls==1&&f.calls==1&&o.unavailable_reason=="game_rule_native_next_postcondition_failed");}
  {auto f=ControlFixture();f.change_other=true;auto o=Select(f);assert(!o.ready&&o.native_next_calls==1&&f.calls==1);}
  {auto f=ControlFixture();auto o=Commit(f);assert(o.ready&&o.apply_invoked&&o.hide_invoked&&f.call_order=="AH");assert(!Control(f).window_visible);const auto s=SerializeFrontendGameRulesMutationV1(FrontendGameRulesMutationKindV1::apply_and_hide,o);assert(s.find("\"applied_settings_proven\":false")!=std::string::npos&&s.find("\"window_closed_proven\":false")!=std::string::npos);}
  {auto f=ControlFixture();f.change_owner_on_apply=true;auto o=Commit(f);assert(!o.ready&&o.apply_invoked&&!o.hide_invoked&&f.call_order=="A");}
  {auto f=ControlFixture();f.Put(base+0x5CC14D0,std::uint8_t{1});auto o=Commit(f);assert(!o.ready&&f.calls==0);}
  {auto f=ControlFixture();f.Put(base+0x5CC14D0,std::uint8_t{1});auto o=Commit(f,false);assert(o.ready&&!o.apply_invoked&&o.hide_invoked&&f.call_order=="H");}
  {auto f=ControlFixture();auto o=Select(f,false);assert(!o.ready&&!o.native_invoked&&f.calls==0&&o.unavailable_reason=="game_rules_native_call_access_unverified");}
  std::puts("PASS: 26 focused control/choice/action cases; synthetic .3 layouts and explicit fixture-only callbacks; no live calls");
}

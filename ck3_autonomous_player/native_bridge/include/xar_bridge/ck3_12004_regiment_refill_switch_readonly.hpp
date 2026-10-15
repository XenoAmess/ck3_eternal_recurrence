#pragma once
#include "xar_bridge/army_refill_permission_switch_v1.hpp"
#include "xar_bridge/ck3_12004_military_refill_switch_readonly.hpp"
#include <array>
#include <limits>
namespace xar::ck3_12004 {
// image_base is supplied only by an exact-.4-bound production collector.
struct RegimentRefillSwitchAccess12004 {
  std::uintptr_t image_base=0;
  void *context=nullptr;
  MilitaryRefillSwitchRead12004 read=nullptr;
};
namespace regiment_refill_switch_detail_12004 {
struct Reader {
  const RegimentRefillSwitchAccess12004 &a;
  template<class T> std::optional<T> At(std::uintptr_t object,std::size_t offset) const {
    T v{};
    if(!a.read||!object||offset>(std::numeric_limits<std::uintptr_t>::max)()-object||
       !a.read(a.context,object+offset,&v,sizeof v))return std::nullopt;
    return v;
  }
  struct Resolution {std::uintptr_t object=0;std::optional<std::int32_t> id;std::optional<bool> fallback;};
  Resolution Resolve(std::uintptr_t slot,std::uintptr_t fallback,std::int32_t raw,std::size_t id_offset) const {
    Resolution r;
    auto storage=At<std::uintptr_t>(a.image_base,slot);if(!storage)return r;
    bool use_fallback=!*storage;
    if(*storage) {
      auto count=At<std::int32_t>(*storage,0x2C);
      if(!count||*count<0||*count>1000000)return r;
      const auto index=std::uint32_t(raw)&0xFFFFFFU;
      use_fallback=index>=std::uint32_t(*count);
      if(!use_fallback) {
        auto table=At<std::uintptr_t>(*storage,0x20);if(!table||!*table)return r;
        auto object=At<std::uintptr_t>(*table,std::size_t(index)*16+8);if(!object)return r;
        use_fallback=!*object;
        if(*object) {
          auto identity=At<std::int32_t>(*object,id_offset);if(!identity)return r;
          use_fallback=*identity!=raw;
          if(!use_fallback){r.object=*object;r.id=identity;}
        }
      }
    }
    r.fallback=use_fallback;
    if(use_fallback) {
      auto object=At<std::uintptr_t>(a.image_base,fallback);if(!object||!*object)return r;
      r.object=*object;r.id=At<std::int32_t>(*object,id_offset);
    }
    return r;
  }
};
struct Snapshot {game::ArmyRefillPermissionSwitchV1 value;std::array<std::uintptr_t,5> objects{};};
inline Snapshot Capture(const RegimentRefillSwitchAccess12004 &a,std::uintptr_t owner,std::int32_t expected_id) {
  Snapshot s;auto &r=s.value;Reader read{a};s.objects[0]=owner;
  const auto fail=[&](const char *why){r.status="unavailable";r.unavailable_reason=why;return s;};
  if(!a.image_base||!a.read)return fail("exact_12004_refill_source_binding_unavailable");
  r.persistent_full_id=read.At<std::int32_t>(owner,0x10);
  auto magic=read.At<std::uint32_t>(owner,0x14);
  if(!r.persistent_full_id||*r.persistent_full_id!=expected_id||expected_id==-1||!magic||*magic!=0x52656769U)
    return fail("refill_source_persistent_identity_unavailable");
  auto definition=read.At<std::uintptr_t>(owner,0x118);
  if(!definition||!*definition)return fail("refill_source_definition_unavailable");
  s.objects[1]=*definition;r.definition_magic_38_raw=read.At<std::uint32_t>(*definition,0x38);
  if(!r.definition_magic_38_raw)return fail("refill_source_definition_magic_unavailable");
  if(*r.definition_magic_38_raw!=0x4744624FU) {
    r.source_branch="non_special_definition_bypass";r.status="not_applicable";return s;
  }
  r.character_ref_12c_raw=read.At<std::int32_t>(owner,0x12C);
  r.title_ref_130_raw=read.At<std::int32_t>(owner,0x130);
  if(!r.character_ref_12c_raw||!r.title_ref_130_raw)return fail("refill_source_reference_fields_unavailable");
  auto selected=*r.character_ref_12c_raw;
  if(*r.title_ref_130_raw!=-1) {
    if(*r.character_ref_12c_raw!=-1) {
      r.source_branch="conflicting_references_fallback";selected=-1;
    } else {
      r.source_branch="title_holder";
      auto title=read.Resolve(0x5D1DAF8,0x5D1DAE0,*r.title_ref_130_raw,0x10);
      s.objects[2]=title.object;r.resolved_title_full_id=title.id;r.title_used_fallback=title.fallback;
      if(!title.object||!title.id)return fail("refill_source_title_resolution_unavailable");
      auto holder=read.At<std::int32_t>(title.object,0x128);
      if(!holder)return fail("refill_source_title_holder_unavailable");selected=*holder;
    }
  } else r.source_branch=selected==-1?"missing_references_fallback":"direct_character";
  r.selected_character_raw_full_id=selected;
  auto character=read.Resolve(0x5C67568,0x5C67570,selected,0x18);
  s.objects[3]=character.object;r.resolved_character_full_id=character.id;r.character_used_fallback=character.fallback;
  if(!character.object||!character.id)return fail("refill_source_character_resolution_unavailable");
  auto value=ReadMilitaryRefillSwitch12004(a.read,a.context,character.object,*character.id,
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
  r.character_magic_raw=value.character_magic;
  if(value.military_component){s.objects[4]=*value.military_component;r.military_component_present=*value.military_component!=0;}
  if(!value.read_complete)return fail("refill_source_military_switch_unavailable");
  r.raw_byte_4a9=*value.raw_byte_4a9;r.enabled=value.enabled;r.status="available";return s;
}
} // namespace regiment_refill_switch_detail_12004
inline game::ArmyRefillPermissionSwitchV1 ReadRegimentRefillPermissionSwitch12004(
    const RegimentRefillSwitchAccess12004 &access,std::uintptr_t owner,std::int32_t expected_full_id) {
  auto before=regiment_refill_switch_detail_12004::Capture(access,owner,expected_full_id);
  if(before.value.status=="unavailable")return before.value;
  auto after=regiment_refill_switch_detail_12004::Capture(access,owner,expected_full_id);
  if(before.value!=after.value||before.objects!=after.objects) {
    before.value.status="unavailable";before.value.unavailable_reason="refill_source_changed_during_capture";
    before.value.raw_byte_4a9.reset();before.value.enabled.reset();return before.value;
  }
  before.value.identity_consistent=true;return before.value;
}
} // namespace xar::ck3_12004

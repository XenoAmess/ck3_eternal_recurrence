#include "xar_bridge/artifact_personal_use12004.hpp"
#include <algorithm>
#include <array>
#include <limits>

namespace xar::ck3_12004::artifact_personal_use {
namespace {
const void* At(const void* p,std::size_t n) noexcept {
  const auto a=reinterpret_cast<std::uintptr_t>(p);
  return a && n<=(std::numeric_limits<std::uintptr_t>::max)()-a
      ? reinterpret_cast<const void*>(a+n) : nullptr;
}
template<class T> bool Read(const Env&e,const void*p,std::size_t n,T&v) noexcept {
  const auto*a=At(p,n);const auto&b=e.existing.model;
  return a && b.read_memory && b.read_memory(b.read_context,a,&v,sizeof(v));
}
bool Resolve(const Env&e,void**storage_slot,std::uint32_t id,std::size_t id_at,
             std::size_t magic_at,std::uint32_t expected_magic,const void*&object) noexcept {
  const void*storage=nullptr,*rows=nullptr;std::uint32_t count=0,actual=absent,magic=0;
  object=nullptr;
  return id!=absent && Read(e,storage_slot,0,storage) && storage &&
      Read(e,storage,0x20,rows) && rows && Read(e,storage,0x2C,count) &&
      count<=0x01000000 && (id&0xFFFFFFU)<count &&
      Read(e,rows,(id&0xFFFFFFU)*std::size_t{16}+8,object) && object &&
      Read(e,object,id_at,actual) && actual==id &&
      Read(e,object,magic_at,magic) && magic==expected_magic;
}
struct Header {
  const void*data=nullptr;std::int32_t capacity=0,count=0;std::uint64_t allocator=0;
  bool operator==(const Header&)const=default;
};
struct RawSlot {
  std::uintptr_t vtable=0,type=0;std::uint32_t artifact=absent,magic=0;
  bool operator==(const RawSlot&)const=default;
};
static_assert(sizeof(Header)==24 && sizeof(RawSlot)==24);
template<class T> bool Rows(const Env&e,const void*p,std::size_t offset,
                           Header&h,std::vector<T>&v,std::int32_t limit) {
  if(!Read(e,p,offset,h)||h.count<0||h.count>limit||h.capacity<h.count||
     h.capacity>8192||(h.count&&!h.data))return false;
  v.resize(static_cast<std::size_t>(h.count));
  return v.empty()||e.existing.model.read_memory(e.existing.model.read_context,
      h.data,v.data(),v.size()*sizeof(T));
}
bool Key(const Env&e,const void*type,std::string&key) {
  std::uint64_t size=0,capacity=0;const void*data=At(type,0x18);
  if(!Read(e,type,0x28,size)||!Read(e,type,0x30,capacity)||!size||size>=64||size>capacity)
    return false;
  if(capacity>15 && (!Read(e,type,0x18,data)||!data))return false;
  key.resize(static_cast<std::size_t>(size));
  return e.existing.model.read_memory(e.existing.model.read_context,data,key.data(),key.size()) &&
      std::all_of(key.begin(),key.end(),[](char c){return (c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_';});
}
bool Personal(std::string_view key) noexcept {
  constexpr std::array<std::string_view,9> allowed{
      "crown","regalia","armor","weapon","brooch","trinket_1","trinket_2","trinket_3","journal"};
  return std::find(allowed.begin(),allowed.end(),key)!=allowed.end();
}
bool Pins(const Env&e) noexcept {
  const auto&b=e.existing.model;
  if(e.admitted_executable_sha256!=kExecutableSha256 || !e.existing.source_bound || !b.image_base || !b.read_memory)return false;
  struct Pin {std::uintptr_t rva;const char*hex;};
#include "artifact_personal_use12004_pins.inc"
  for(const auto&p:pins){
    std::array<unsigned char,32>actual{};const std::string_view hex=p.hex;
    if(hex.size()>64||hex.size()%2||!b.read_memory(b.read_context,
        reinterpret_cast<const void*>(b.image_base+p.rva),actual.data(),hex.size()/2))return false;
    const auto digit=[](char c){return c<='9'?c-'0':c-'a'+10;};
    for(std::size_t i=0;i<hex.size()/2;++i)
      if(actual[i]!=(digit(hex[i*2])*16+digit(hex[i*2+1])))return false;
  }
  return true;
}
struct State {
  Witness w{};Header owned_header{},slots_header{};
  std::vector<std::uint32_t>ids;std::vector<RawSlot>raw_slots;
  std::vector<std::uintptr_t>owned_objects;
  std::vector<std::string>keys;
  std::vector<ModifierEntry>modifiers;
  const void*modifier_keys=nullptr,*modifier_values=nullptr;
  std::int32_t modifier_count=0;
  std::uint32_t type_category=absent;
  bool modifier_available=false,view_visible=false;
  bool operator==(const State&) const = default;
};
bool FrameOK(const Env&e,const Frame&f) noexcept {
  Frame actual{};
  return e.enabled && e.existing.model.enabled && f.revision && f.capture_epoch &&
      f.connection_generation && f.bridge_pid && f.actor_id && f.actor_id!=absent && f.owner &&
      f.application_main_thread && f.native_tls_ready && f.paused && f.map_ready && f.actor_alive &&
      e.frame && e.frame(e.context,actual) && actual==f;
}
bool StateRead(const Env&e,const Frame&f,std::uint32_t artifact_id,State&s) {
  const void*actor=nullptr,*artifact=nullptr,*component=nullptr,*type=nullptr;
  std::uint32_t played=absent,inventory_owner=absent,inventory_site=absent;
  if(!Read(e,e.existing.current_actor_reference,0,played)||played!=f.actor_id||
      !Resolve(e,e.existing.model.character_storage,f.actor_id,0x18,0x1C,0x43686172,actor)||
      !Resolve(e,e.existing.model.artifact_storage,artifact_id,0x10,0x14,0x41727469,artifact)||
      !Read(e,actor,0x1B0,component)||!component)return false;
  const void*inventory=At(component,0x458);auto&w=s.w;
  w.actor=reinterpret_cast<std::uintptr_t>(actor);w.component=reinterpret_cast<std::uintptr_t>(component);
  w.inventory=reinterpret_cast<std::uintptr_t>(inventory);w.artifact=reinterpret_cast<std::uintptr_t>(artifact);
  if(!Read(e,inventory,0x38,inventory_owner)||inventory_owner!=f.actor_id||
      !Read(e,inventory,0x3C,inventory_site)||inventory_site!=absent||
      !Read(e,artifact,0x78,w.character_owner)||w.character_owner!=f.actor_id||
      !Read(e,artifact,0x7C,w.site_owner)||w.site_owner!=absent||
      !Read(e,artifact,0xB8,type)||!type||!Read(e,type,0x44,s.type_category)||
      !Rows(e,inventory,0x58,s.owned_header,s.ids,64)||
      std::count(s.ids.begin(),s.ids.end(),artifact_id)!=1||
      !Rows(e,inventory,0x40,s.slots_header,s.raw_slots,64))return false;
  w.artifact_type=reinterpret_cast<std::uintptr_t>(type);
  for(std::size_t n=0;n<s.ids.size();++n){
    const auto id=s.ids[n];const void*owned=nullptr;std::uint32_t character=absent,site=absent;
    if(std::find(s.ids.begin(),s.ids.begin()+n,id)!=s.ids.begin()+n ||
        !Resolve(e,e.existing.model.artifact_storage,id,0x10,0x14,0x41727469,owned)||
        !Read(e,owned,0x78,character)||character!=f.actor_id||
        !Read(e,owned,0x7C,site)||site!=absent)return false;
    s.owned_objects.push_back(reinterpret_cast<std::uintptr_t>(owned));
  }
  for(const auto&row:s.raw_slots){
    std::string key;std::uint32_t type_magic=0;
    if(row.vtable!=e.existing.model.image_base+0x4593568||row.magic!=0x496E7653||!row.type||
        !Read(e,reinterpret_cast<const void*>(row.type),0x38,type_magic)||type_magic!=0x4744624F||
        !Key(e,reinterpret_cast<const void*>(row.type),key))return false;
    s.keys.push_back(std::move(key));
    if(row.artifact!=absent &&
        std::find(s.ids.begin(),s.ids.end(),row.artifact)==s.ids.end())return false;
  }
  // Source-bound item-local PC used by Artifact.GetModifierEffects. Availability
  // is independent of slot ownership and never asserts current actor attribution.
  const void*pc=At(artifact,0xD8);
  if(Read(e,pc,0xC,s.modifier_count)&&s.modifier_count>=0&&s.modifier_count<=128&&
      Read(e,pc,0,s.modifier_keys)&&Read(e,pc,0x68,s.modifier_values)&&
      (!s.modifier_count||(s.modifier_keys&&s.modifier_values))){
    s.modifier_available=true;
    for(std::int32_t n=0;n<s.modifier_count;++n){ModifierEntry row{};
      if(!Read(e,s.modifier_keys,n*sizeof(std::uint16_t),row.key_raw_u16)||
          !Read(e,s.modifier_values,n*sizeof(std::int64_t),row.definition_value_raw_q64)){
        s.modifier_available=false;s.modifiers.clear();break;}
      s.modifiers.push_back(row);
    }
  }
  // InventoryView is optional for the global read, mandatory for actions.
  const void*gfx=nullptr,*handler=nullptr,*view=nullptr,*back=nullptr,*owner=nullptr,*root=nullptr,*selected=nullptr;
  std::uintptr_t vtable=0,secondary=0;std::uint32_t viewed=absent;
  if(Read(e,reinterpret_cast<const void*>(f.owner),0x10,gfx)&&gfx&&Read(e,gfx,0x88,handler)&&handler&&
      Read(e,handler,0x378,view)&&view&&Read(e,view,0,vtable)&&vtable==e.existing.model.image_base+0x4577608&&
      Read(e,view,0x10,secondary)&&secondary==e.existing.model.image_base+0x45776D8&&
      Read(e,view,0x98,owner)&&owner==reinterpret_cast<const void*>(f.owner)&&
      Read(e,view,0xA0,back)&&back==handler&&Read(e,view,0x60,root)&&root&&
      Read(e,view,0xC8,viewed)&&viewed==f.actor_id&&Read(e,view,0x2D0,selected)){
    w.handler=reinterpret_cast<std::uintptr_t>(handler);w.view=reinterpret_cast<std::uintptr_t>(view);
    w.view_root=reinterpret_cast<std::uintptr_t>(root);
    w.selected_slot=reinterpret_cast<std::uintptr_t>(selected);
    if(e.visible)(void)e.visible(e,view,s.view_visible);
    const void*effective=selected;
    if(!effective && e.pick && !e.pick(e,view,artifact,effective))effective=nullptr;
    if(effective){const auto start=reinterpret_cast<std::uintptr_t>(s.slots_header.data);
      const auto at=reinterpret_cast<std::uintptr_t>(effective);
      if(at<start||(at-start)%sizeof(RawSlot)||(at-start)/sizeof(RawSlot)>=s.raw_slots.size())return false;
      w.effective_slot=at;
    }
  }
  return true;
}
}
bool ReadArtifactPersonalUse12004(const Env&e,const Frame&f,std::uint32_t id,Observation&out,Witness*w) noexcept {
  const Frame frozen=f;
  out={};out.frame=frozen;out.artifact_id=id;if(w)*w={};
  try{
    if(!FrameOK(e,frozen)||!Pins(e)){out.unavailable_reason="exact_source_or_current_owner_frame_unavailable";return false;}
    State first{};
    if(!StateRead(e,frozen,id,first)){out.unavailable_reason="personal_inventory_owner_full_reference_rows_or_limit_unavailable";return false;}
    out.loaded_source_pins_verified=true;out.personally_owned=true;out.owned_ids=first.ids;
    out.inventory_artifact=first.type_category==0;
    std::uint32_t matching=0;
    for(std::size_t n=0;n<first.raw_slots.size();++n){const auto&r=first.raw_slots[n];
      out.slots.push_back({static_cast<std::uint32_t>(n),r.artifact,first.keys[n],Personal(first.keys[n])});
      if(r.artifact==id){++matching;out.equipped_slot_index=static_cast<std::uint32_t>(n);}
    }
    if(matching>1){out.unavailable_reason="artifact_in_multiple_equipment_slots";return false;}
    out.equipped=matching==1;
    bool native_member=false;
    if(e.equipped && e.equipped(e,reinterpret_cast<const void*>(first.w.inventory),
        reinterpret_cast<const void*>(first.w.artifact),native_member)){
      out.native_equipped_observed=true;
      if(native_member!=out.equipped){out.unavailable_reason="original_equipped_getter_disagrees_with_slots";return false;}
      out.can_unequip=native_member;
    }
    out.inventory_view_available=first.w.view!=0;out.inventory_view_visible=first.view_visible;
    if(first.w.effective_slot){const auto index=static_cast<std::uint32_t>(
        (first.w.effective_slot-reinterpret_cast<std::uintptr_t>(first.slots_header.data))/sizeof(RawSlot));
      out.effective_slot_index=index;const auto&r=first.raw_slots[index];
      if(r.artifact!=absent)out.replacing_artifact_id=r.artifact;
      if(Personal(first.keys[index])&&out.inventory_artifact&&e.can_equip_in_slot){bool value=false;
        if(e.can_equip_in_slot(e,reinterpret_cast<const void*>(first.w.inventory),
            reinterpret_cast<const void*>(first.w.artifact),reinterpret_cast<const void*>(r.type),value))
          out.can_equip_in_effective_slot=value;
      }
    }
    out.item_modifier_definition_available=first.modifier_available;
    out.item_modifier_definition=first.modifiers;
    if(e.modifier_text)out.modifier_description_available=e.modifier_text(e,
        reinterpret_cast<const void*>(first.w.artifact),out.modifier_description);
    State second{};
    if(!StateRead(e,frozen,id,second)||first!=second||!FrameOK(e,frozen)){
      out={};out.frame=frozen;out.artifact_id=id;out.unavailable_reason="personal_use_source_state_changed";return false;
    }
    out.available=true;out.unavailable_reason.clear();if(w)*w=first.w;return true;
  }catch(...){out.available=false;out.unavailable_reason="personal_use_read_exception";return false;}
}
Result SubmitArtifactPersonalUse12004(const Env&e,const Frame&f,const Request&r) noexcept {
  Result out{};
#if !defined(XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1)
  (void)e;(void)f;(void)r;return out;
#else
  const Frame frozen=f;
  if(!e.actions_enabled||!e.claim_once||!e.dispatch||!r.request_sequence)return out;
  Witness witness{};
  if(!ReadArtifactPersonalUse12004(e,frozen,r.artifact_id,out.before,&witness)){
    out.status="precondition_read_unavailable";return out;}
  const auto&b=out.before;
  if(!b.inventory_artifact||!b.inventory_view_visible||!b.native_equipped_observed){out.status="current_personal_view_or_membership_unavailable";return out;}
  if(b.equipped==r.desired_equipped){out.status="desired_state_already_observed_no_dispatch";return out;}
  if(r.desired_equipped){
    if(!b.effective_slot_index||*b.effective_slot_index!=r.expected_slot_index||
        b.replacing_artifact_id.value_or(absent)!=r.expected_replacing_artifact_id||
        b.can_equip_in_effective_slot!=true){out.status="frozen_slot_replacement_or_original_permission_rejected";return out;}
  }else if(!b.equipped_slot_index||*b.equipped_slot_index!=r.expected_slot_index||b.can_unequip!=true||
      !b.slots[*b.equipped_slot_index].personal){out.status="original_unequip_membership_rejected";return out;}
  if(!FrameOK(e,frozen)||!e.claim_once(e.context,frozen,r,out.before,witness)){out.status="frame_or_central_once_ledger_rejected";return out;}
  out.once_intent_consumed=true;out.invoked=true;out.needs_recovery=true;
  out.dispatch_call_returned=e.dispatch(e,reinterpret_cast<const void*>(witness.view),
      reinterpret_cast<const void*>(witness.artifact),r.desired_equipped);
  out.status=out.dispatch_call_returned?"original_callback_invoked_post_pending":"dispatch_result_unknown_no_replay";
  return out;
#endif
}
bool DesiredStateObserved12004(const Observation&before,const Request&r,const Observation&after) noexcept {
  if(!before.available||!after.available||after.artifact_id!=r.artifact_id||
      before.artifact_id!=r.artifact_id||before.frame.actor_id!=after.frame.actor_id||
      before.frame.bridge_pid!=after.frame.bridge_pid||before.frame.connection_generation!=after.frame.connection_generation||
      before.frame.owner!=after.frame.owner||after.frame.date_raw<before.frame.date_raw||
      after.frame.capture_epoch<=before.frame.capture_epoch||!after.personally_owned||
      !after.native_equipped_observed||after.equipped!=r.desired_equipped)return false;
  if(r.desired_equipped){
    if(after.equipped_slot_index!=r.expected_slot_index)return false;
    if(r.expected_replacing_artifact_id!=absent &&
        (std::find(after.owned_ids.begin(),after.owned_ids.end(),r.expected_replacing_artifact_id)==after.owned_ids.end() ||
         std::any_of(after.slots.begin(),after.slots.end(),[&](const Slot&s){return s.artifact_id==r.expected_replacing_artifact_id;})))return false;
  }
  return true;
}
}

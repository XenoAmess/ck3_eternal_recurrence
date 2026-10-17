#include "xar_bridge/ck3_12004_holy_site_relic_action_context.hpp"
#include <algorithm>
#include <array>
#include <limits>
#include <windows.h>
#include <bcrypt.h>

namespace xar::ck3_12004::religion::relic_action_context {
namespace {
constexpr std::uint32_t absent=0xFFFFFFFFU;
const void* At(const void*p,std::size_t o) noexcept {
 const auto a=reinterpret_cast<std::uintptr_t>(p);
 return a&&o<=std::numeric_limits<std::uintptr_t>::max()-a?reinterpret_cast<const void*>(a+o):nullptr;
}
template<class T>bool Read(const Bindings&b,const void*p,std::size_t o,T&v) noexcept {
 const auto*a=At(p,o);return a&&b.permissions.model.read_memory&&b.permissions.model.read_memory(b.permissions.model.read_context,a,&v,sizeof(v));
}
struct Header {const void*data=nullptr;std::int32_t capacity=0,count=0;std::uint64_t allocator=0;bool operator==(const Header&)const=default;};
struct SlotRow {std::uintptr_t vtable=0,type=0;std::uint32_t artifact=absent,magic=0;bool operator==(const SlotRow&)const=default;};
static_assert(sizeof(Header)==24&&sizeof(SlotRow)==24);
template<class T>bool Rows(const Bindings&b,const void*p,std::size_t offset,Header&h,std::vector<T>&v) {
 if(!Read(b,p,offset,h)||h.count<0||h.count>4096||h.capacity<h.count||h.capacity>8192||(h.count&&!h.data))return false;
 v.resize(static_cast<std::size_t>(h.count));
 return v.empty()||b.permissions.model.read_memory(b.permissions.model.read_context,h.data,v.data(),v.size()*sizeof(T));
}
bool Resolve(const Bindings&b,void**storage_slot,std::uint32_t id,std::size_t id_offset,
 const void*&object,std::size_t magic_offset=0,std::uint32_t expected_magic=0) noexcept {
 object=nullptr;const void*storage=nullptr,*rows=nullptr;std::uint32_t count=0,actual=absent,magic=0;
 return id!=absent&&Read(b,storage_slot,0,storage)&&storage&&Read(b,storage,0x20,rows)&&rows&&
  Read(b,storage,0x2C,count)&&(id&0xFFFFFFU)<count&&
  Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)&&object&&
  Read(b,object,id_offset,actual)&&actual==id&&(!expected_magic||(Read(b,object,magic_offset,magic)&&magic==expected_magic));
}
bool Artifact(const Bindings&b,std::uint32_t id,const void*&a) noexcept {
 return Resolve(b,b.permissions.model.artifact_storage,id,0x10,a,0x14,0x41727469U);
}
std::optional<std::uint32_t> Id(std::uint32_t v){return v==absent?std::nullopt:std::optional<std::uint32_t>{v};}
bool Pin(const Bindings&b,std::uintptr_t rva,std::string_view hex) noexcept {
 if(hex.size()%2||hex.size()>128)return false;std::array<unsigned char,64> bytes{};
 if(!b.permissions.model.read_memory(b.permissions.model.read_context,reinterpret_cast<const void*>(b.permissions.model.image_base+rva),bytes.data(),hex.size()/2))return false;
 const auto nibble=[](char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
 for(std::size_t i=0;i<hex.size()/2;++i){const int a=nibble(hex[i*2]),v=nibble(hex[i*2+1]);if(a<0||v<0||bytes[i]!=a*16+v)return false;}return true;
}
#include "ck3_12004_holy_site_relic_action_context_pins.inc"
bool SourcePins(const Bindings&b) noexcept {for(const auto&p:kPins)if(!Pin(b,p.first,p.second))return false;return true;}
bool NativePicker(const Bindings&b,const void*i,const void*a,std::int32_t&v) noexcept {
 __try{v=reinterpret_cast<std::int32_t(__fastcall*)(const void*,const void*)>(b.permissions.model.image_base+0x2C805E0)(i,a);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool NativeEquipped(const Bindings&b,const void*i,const void*a,bool&v) noexcept {
 __try{v=reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(b.permissions.model.image_base+0x22E4420)(i,a);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
struct NativeString {std::array<std::byte,32>bytes{};};
bool CallText(const Bindings&b,const void*w,std::uintptr_t rva,NativeString&v) noexcept {
 __try{return reinterpret_cast<void*(__fastcall*)(const void*,void*)>(b.permissions.model.image_base+rva)(w,v.bytes.data())==v.bytes.data();}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool DestroyText(const Bindings&b,NativeString&v) noexcept {
 __try{reinterpret_cast<void(__fastcall*)(void*)>(b.permissions.model.image_base+0x856050)(v.bytes.data());return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool NativeText(const Bindings&b,const void*w,std::uintptr_t rva,std::string&text) noexcept {
 text.clear();NativeString v{};if(!CallText(b,w,rva,v))return false;
 bool copied=false;try {
  std::uint64_t size=0,capacity=0;const void*p=v.bytes.data();
  if(Read(b,p,16,size)&&Read(b,p,24,capacity)&&size<=65536&&size<=capacity&&
   (capacity>=16||capacity==15)&&(capacity<16||Read(b,p,0,p))&&p){
   std::vector<char>raw(static_cast<std::size_t>(size)+1);
   if(b.permissions.model.read_memory(b.permissions.model.read_context,p,raw.data(),raw.size())&&raw.back()==0){text.assign(raw.data(),static_cast<std::size_t>(size));copied=true;}
  }
 }catch(...){copied=false;}
 const bool destroyed=DestroyText(b,v);if(!copied||!destroyed)text.clear();return copied&&destroyed;
}
bool Sha256(std::string_view value,std::string&out) {
 out.clear();BCRYPT_ALG_HANDLE alg=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
 DWORD bytes=0,object_size=0;bool ok=false;std::array<unsigned char,32>digest{};
 if(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
 if(BCryptGetProperty(alg,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&object_size),sizeof(object_size),&bytes,0)>=0){
  std::vector<unsigned char>object(object_size);
  if(BCryptCreateHash(alg,&hash,object.data(),object_size,nullptr,0,0)>=0){
   ok=value.size()<=std::numeric_limits<ULONG>::max()&&BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char*>(value.data())),static_cast<ULONG>(value.size()),0)>=0&&BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0)>=0;
   (void)BCryptDestroyHash(hash);
  }
 }
 (void)BCryptCloseAlgorithmProvider(alg,0);if(!ok)return false;
 constexpr char hex[]="0123456789abcdef";for(const auto c:digest){out+=hex[c>>4];out+=hex[c&15];}return true;
}
struct Pass {
 const void*actor=nullptr,*site=nullptr,*artifact=nullptr,*data=nullptr,*inventory=nullptr,*window=nullptr,*handler=nullptr,*gfx=nullptr,*root=nullptr,*selected_slot=nullptr;
 Header slots_header{},owned_header{};std::vector<SlotRow>slots;std::vector<std::uint32_t>owned;
 const void*rite=nullptr;
 std::uint32_t actor_id=absent,site_id=absent,rite_id=absent,faith_id=absent,selected_site=absent,selected_artifact=absent;bool window_available=false;
 struct Owner {const void*object=nullptr;std::uint32_t id=absent,character=absent,site=absent;std::int32_t rarity=0;};
 std::vector<Owner>owners;
};
bool Window(const Bindings&b,const void*owner,Pass&p) noexcept {
 const void*back=nullptr,*window_owner=nullptr;std::uintptr_t primary=0,secondary=0;
 return Read(b,owner,0x10,p.gfx)&&p.gfx&&Read(b,p.gfx,0x88,p.handler)&&p.handler&&Read(b,p.handler,0x5D8,p.window)&&p.window&&
  Read(b,p.window,0,primary)&&primary==b.permissions.model.image_base+0x4592338&&Read(b,p.window,0x10,secondary)&&secondary==b.permissions.model.image_base+0x4592310&&
  Read(b,p.window,0xA0,back)&&back==p.handler&&Read(b,p.window,0x98,window_owner)&&window_owner==owner&&Read(b,p.window,0x60,p.root)&&p.root&&
  Read(b,p.window,0xC8,p.selected_site)&&Read(b,p.window,0x108,p.selected_artifact)&&Read(b,p.window,0x110,p.selected_slot);
}
bool Base(const Bindings&b,const void*owner,const ck3_12002::religion::Context&c,Snapshot&out,Pass&p) {
 p.actor_id=static_cast<std::uint32_t>(c.played_character_id);p.site_id=out.requested_holy_site_id;std::uint32_t current=absent;
 if(!Read(b,b.permissions.current_actor_reference,0,current)||current!=p.actor_id||
  !Resolve(b,b.permissions.model.character_storage,p.actor_id,0x18,p.actor,0x1C,0x43686172U)||
  !Resolve(b,b.permissions.model.holy_site_storage,out.requested_holy_site_id,0x10,p.site,0x14,0x486F5374U)||
  !Artifact(b,out.requested_artifact_id,p.artifact))return false;
 if(!Read(b,p.actor,0xB4,p.rite_id)||p.rite_id!=c.rite_id||!Resolve(b,b.permissions.model.rite_storage,p.rite_id,8,p.rite)||
  !Read(b,p.rite,0x4B8,p.faith_id)||p.faith_id!=c.faith_id)return false;
 if(!Rows(b,p.site,0x68,p.slots_header,p.slots)||std::any_of(p.slots.begin(),p.slots.end(),[](const SlotRow&r){return r.magic!=0x496E7653U;}))return false;
 if(Read(b,p.actor,0x1B0,p.data)&&p.data){p.inventory=At(p.data,0x458);(void)Rows(b,p.inventory,0x58,p.owned_header,p.owned);}
 p.window_available=Window(b,owner,p)&&p.selected_site==out.requested_holy_site_id;return true;
}
void Equipped(const Bindings&b,const void*i,const void*a,Snapshot&out,relic_permissions::ObservedBool&v) {
 if(!i||!b.equipped){v.unavailable_reason="equipped_inventory_or_getter_unavailable";return;}
 bool value=false;++out.native_getter_calls;if(!b.equipped(b,i,a,value)){v.unavailable_reason="native_equipped_membership_failed";return;}
 v.available=true;v.value=value;v.unavailable_reason.clear();
}
void OwnershipRead(const Bindings&b,Pass&p,Snapshot&out,std::uint32_t id,Ownership&v) {
 v.artifact_id=id;const void*a=nullptr;if(!Artifact(b,id,a)){v.unavailable_reason="artifact_full_reference_unavailable";return;}
 v.object_resolved=true;Pass::Owner state{};state.object=a;state.id=id;
 if(!Read(b,a,0x78,state.character)||!Read(b,a,0x7C,state.site)||!Read(b,a,0xB0,state.rarity)){v.unavailable_reason="artifact_owner_channels_or_rarity_unreadable";return;}
 p.owners.push_back(state);v.character_owner_id=Id(state.character);v.holy_site_owner_id=Id(state.site);v.rarity_level=state.rarity;
 v.character_owner_matches_player=state.character==p.actor_id;v.holy_site_owner_matches_requested=state.site==out.requested_holy_site_id;
 const void*owner=nullptr;
 if((state.character!=absent&&!Resolve(b,b.permissions.model.character_storage,state.character,0x18,owner,0x1C,0x43686172U))||
  (state.site!=absent&&!Resolve(b,b.permissions.model.holy_site_storage,state.site,0x10,owner,0x14,0x486F5374U))||
  (state.character!=absent&&state.site!=absent)){v.unavailable_reason="artifact_owner_full_reference_or_exclusive_channel_invalid";return;}
 if(out.permissions.player_inventory.available&&out.permissions.player_inventory.owner_matches_player==true){
  const auto&ids=out.permissions.player_inventory.artifact_ids;v.player_owned_reference_member=std::find(ids.begin(),ids.end(),id)!=ids.end();
 }
 Equipped(b,p.inventory,a,out,v.player_equipped_slot_member);Equipped(b,At(p.site,0x28),a,out,v.site_equipped_slot_member);
 v.available=true;v.unavailable_reason.clear();
}
bool Compatible(const Bindings&b,const SlotRow&row,const void*artifact,bool&compatible) noexcept {
 const void*type=nullptr;std::uint8_t any=0;std::uint32_t s40=0,s44=0,a40=0,a44=0;
 if(!row.type||!Read(b,reinterpret_cast<const void*>(row.type),0x209,any))return false;
 if(any){compatible=true;return true;}
 if(!Read(b,artifact,0xB8,type)||!type||!Read(b,reinterpret_cast<const void*>(row.type),0x40,s40)||!Read(b,reinterpret_cast<const void*>(row.type),0x44,s44)||!Read(b,type,0x40,a40)||!Read(b,type,0x44,a44))return false;
 compatible=s44==a40&&s40==a44;return true;
}
void DestinationRead(const Bindings&b,Pass&p,Snapshot&out) {
 auto&d=out.destination;d.selected_slot_index=out.permissions.window_context.selected_slot_index;
 if(!out.artifact_ownership.available){d.unavailable_reason="artifact_ownership_unavailable";return;}
 if(out.artifact_ownership.holy_site_owner_matches_requested==true){d.action_kind="remove";d.available=true;d.unavailable_reason.clear();return;}
 d.action_kind="enshrine";std::int32_t chosen=-1;
 if(d.selected_slot_index){
  if(*d.selected_slot_index>=p.slots.size()){d.unavailable_reason="selected_slot_out_of_site_inventory";return;}
  bool compatible=false;if(!Compatible(b,p.slots[*d.selected_slot_index],p.artifact,compatible)){d.unavailable_reason="explicit_slot_type_compatibility_unavailable";return;}
  d.explicit_slot_type_compatible=compatible;if(compatible)chosen=static_cast<std::int32_t>(*d.selected_slot_index);
 }
 if(chosen<0){
  if(!b.slot_picker){d.unavailable_reason="original_slot_picker_unavailable";return;}
  d.original_picker_called=true;++out.native_getter_calls;
  if(!b.slot_picker(b,At(p.site,0x28),p.artifact,chosen)){d.unavailable_reason="original_slot_picker_failed";return;}
 }
 if(chosen<0){d.unavailable_reason="original_effective_slot_not_found";return;}
 if(static_cast<std::size_t>(chosen)>=p.slots.size()){d.unavailable_reason="original_effective_slot_out_of_bounds";return;}
 d.effective_slot_index=static_cast<std::uint32_t>(chosen);d.replacing_artifact_id=Id(p.slots[static_cast<std::size_t>(chosen)].artifact);
 if(d.replacing_artifact_id)OwnershipRead(b,p,out,*d.replacing_artifact_id,d.replacing_artifact);
 else d.replacing_artifact.unavailable_reason="effective_slot_empty";
 d.available=true;d.unavailable_reason.clear();
}
void TextRead(const Bindings&b,Pass&p,Snapshot&out,std::uintptr_t rva,Text&v) {
 if(!out.selected_artifact_matches_request){v.unavailable_reason="current_selected_artifact_differs_from_request";return;}
 if(!b.text){v.unavailable_reason="native_selected_action_text_getter_unavailable";return;}
 ++out.native_getter_calls;if(!b.text(b,p.window,rva,v.text)){v.text.clear();v.unavailable_reason="native_selected_action_text_getter_or_string_lifetime_failed";return;}
 v.available=true;v.unavailable_reason.clear();
}
bool Stable(const Bindings&b,const void*owner,const Pass&p) {
 Pass now{};std::uint32_t current=absent,rite_id=absent,faith_id=absent;const void*actor=nullptr,*site=nullptr,*data=nullptr,*rite=nullptr;
 if(!Read(b,b.permissions.current_actor_reference,0,current)||current!=p.actor_id||
  !Resolve(b,b.permissions.model.character_storage,p.actor_id,0x18,actor,0x1C,0x43686172U)||actor!=p.actor||
  !Resolve(b,b.permissions.model.holy_site_storage,p.site_id,0x10,site,0x14,0x486F5374U)||site!=p.site||
  !Rows(b,p.site,0x68,now.slots_header,now.slots)||now.slots_header!=p.slots_header||now.slots!=p.slots)return false;
 if(!Read(b,p.actor,0xB4,rite_id)||rite_id!=p.rite_id||!Resolve(b,b.permissions.model.rite_storage,rite_id,8,rite)||rite!=p.rite||
  !Read(b,rite,0x4B8,faith_id)||faith_id!=p.faith_id)return false;
 if(p.window_available&&(!Window(b,owner,now)||now.window!=p.window||now.root!=p.root||now.handler!=p.handler||now.gfx!=p.gfx||
  now.selected_site!=p.selected_site||now.selected_artifact!=p.selected_artifact||now.selected_slot!=p.selected_slot))return false;
 if(p.inventory&&(!Read(b,p.actor,0x1B0,data)||data!=p.data||!Rows(b,p.inventory,0x58,now.owned_header,now.owned)||now.owned_header!=p.owned_header||now.owned!=p.owned))return false;
 for(const auto&v:p.owners){const void*a=nullptr;std::uint32_t character=absent,site_id=absent;std::int32_t rarity=0;
  if(!Artifact(b,v.id,a)||a!=v.object||!Read(b,a,0x78,character)||character!=v.character||!Read(b,a,0x7C,site_id)||site_id!=v.site||!Read(b,a,0xB0,rarity)||rarity!=v.rarity)return false;}
 return true;
}
}
Bindings BindHolySiteRelicActionContextImage12004(std::uintptr_t base,std::string_view sha) noexcept {
 Bindings b{};b.permissions=relic_permissions::BindHolySiteRelicPermissionsImage12004(base,sha);if(!b.permissions.model.enabled)return b;
 b.slot_picker=&NativePicker;b.equipped=&NativeEquipped;b.text=&NativeText;b.source_bound=true;b.getter_backend="source_bound_native_getter";return b;
}
bool ReadHolySiteRelicActionContext12004(const Bindings&b,const void*owner,const ck3_12002::religion::Context&c,
 std::uint32_t site_id,std::uint32_t artifact_id,Snapshot&out) noexcept {
 out={};out.capture_epoch=c.capture_epoch;out.date_raw=c.date_raw;out.played_character_id=c.played_character_id;
 out.requested_holy_site_id=site_id;out.requested_artifact_id=artifact_id;out.getter_backend=b.source_bound?"unavailable":b.getter_backend;
 out.artifact_ownership.artifact_id=artifact_id;
 out.permissions.capture_epoch=c.capture_epoch;out.permissions.date_raw=c.date_raw;out.permissions.played_character_id=c.played_character_id;
 out.permissions.player_faith_id=c.available?c.faith_id:std::nullopt;out.permissions.requested_holy_site_id=site_id;out.permissions.requested_artifact_id=artifact_id;
 out.permissions.artifact_permissions.artifact_id=artifact_id;out.permissions.artifact_permissions.unavailable_reason="artifact_permissions_not_read";
 const auto fail=[&](const char*why){out.recognition_matrix.reset();out.available=false;out.unavailable_reason=why;out.preview_identity_available=false;out.preview_identity_sha256.clear();return false;};
 try {
  if(!b.permissions.model.enabled||site_id==absent||artifact_id==absent)return fail("relic_action_context_or_full_reference_invalid");
  if(b.source_bound){if(!SourcePins(b))return fail("relic_action_context_loaded_source_pins_changed");out.loaded_source_pins_verified=true;out.getter_backend=b.getter_backend;}
  if(!relic_permissions::ReadHolySiteRelicPermissions12004(b.permissions,owner,c,site_id,artifact_id,out.permissions))return fail("base_relic_permissions_unavailable");
  Pass p{};if(!Base(b,owner,c,out,p))return fail("relic_action_context_bound_objects_or_window_unavailable");
  OwnershipRead(b,p,out,artifact_id,out.artifact_ownership);
  holy_site_relic::RecognitionMatrix matrix{};
  (void)holy_site_relic::ReadHolySiteRelicRecognitionMatrix12004(b.permissions.model,owner,c,site_id,artifact_id,nullptr,matrix);
  out.recognition_matrix=std::move(matrix);
  // Matrix recognition calls do not alter the legacy preview identity or counter.
  // Missing/mismatched window still permits independent owner/slot readback.
  if(!out.permissions.window_context.available||!p.window_available){
   if(!Stable(b,owner,p))return fail("relic_action_context_inputs_changed_during_read");
   out.available=true;out.unavailable_reason.clear();out.destination.unavailable_reason="requested_site_window_context_unavailable";return true;
  }
  out.selected_artifact_matches_request=p.selected_artifact==artifact_id;
  DestinationRead(b,p,out);
  TextRead(b,p,out,0x17D6990,out.selected_action_effect_description);
  TextRead(b,p,out,0x17D5A60,out.enshrine_disabled_tooltip);TextRead(b,p,out,0x17D5F60,out.remove_disabled_tooltip);
  if(!Stable(b,owner,p))return fail("relic_action_context_inputs_changed_during_read");
  out.available=true;out.unavailable_reason.clear();
  const auto&buttons=out.permissions.current_buttons;
  if(out.selected_artifact_matches_request&&out.artifact_ownership.available&&out.destination.available&&
   out.selected_action_effect_description.available&&out.enshrine_disabled_tooltip.available&&out.remove_disabled_tooltip.available&&buttons.available&&
   out.artifact_ownership.player_owned_reference_member.has_value()&&out.artifact_ownership.player_equipped_slot_member.available&&out.artifact_ownership.site_equipped_slot_member.available&&
   (!out.destination.replacing_artifact_id||out.destination.replacing_artifact.available))
    out.preview_identity_available=Sha256(RelicActionPreviewCanonical12004(out),out.preview_identity_sha256);
  return true;
 }catch(...){return fail("relic_action_context_reader_exception");}
}
}

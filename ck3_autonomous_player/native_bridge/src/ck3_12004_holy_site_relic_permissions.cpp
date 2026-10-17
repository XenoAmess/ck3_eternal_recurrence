#include "xar_bridge/ck3_12004_holy_site_relic_permissions.hpp"
#include <algorithm>
#include <array>
#include <limits>
#include <utility>
#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_12004::religion::relic_permissions {
namespace {
constexpr std::uint32_t absent=0xFFFFFFFFU;
constexpr std::int32_t max_rows=4096;
const void* At(const void*p,std::size_t o) noexcept {
 const auto a=reinterpret_cast<std::uintptr_t>(p);
 return a&&o<=std::numeric_limits<std::uintptr_t>::max()-a?reinterpret_cast<const void*>(a+o):nullptr;
}
template<class T>bool Read(const Bindings&b,const void*p,std::size_t o,T&v) noexcept {
 const auto*a=At(p,o);return a&&b.model.read_memory&&b.model.read_memory(b.model.read_context,a,&v,sizeof(v));
}
struct Header {
 const void*data=nullptr;std::int32_t capacity=0,count=0;std::uint64_t allocator=0;
 bool operator==(const Header&)const=default;
};
static_assert(sizeof(Header)==24);
struct SlotRow {
 std::uintptr_t vtable=0,type=0;std::uint32_t artifact=absent,magic=0;
 bool operator==(const SlotRow&)const=default;
};
static_assert(sizeof(SlotRow)==24);
bool Array(const Bindings&b,const void*p,std::size_t offset,Header&h) noexcept {
 return Read(b,p,offset,h)&&h.count>=0&&h.count<=max_rows&&h.capacity>=h.count&&h.capacity<=max_rows*2&&
  (h.count==0||h.data);
}
template<class T>bool Rows(const Bindings&b,const Header&h,std::vector<T>&out) {
 out.resize(static_cast<std::size_t>(h.count));
 return out.empty()||b.model.read_memory(b.model.read_context,h.data,out.data(),out.size()*sizeof(T));
}
std::optional<std::uint32_t> Id(std::uint32_t id) {
 return id==absent?std::nullopt:std::optional<std::uint32_t>{id};
}
bool Resolve(const Bindings&b,void**storage_slot,std::uint32_t id,std::size_t id_offset,
 const void*&object,std::size_t magic_offset=0,std::uint32_t expected_magic=0) noexcept {
 object=nullptr;const void*storage=nullptr,*rows=nullptr;std::uint32_t count=0,actual=absent,magic=0;
 return id!=absent&&Read(b,storage_slot,0,storage)&&storage&&Read(b,storage,0x20,rows)&&rows&&
  Read(b,storage,0x2C,count)&&(id&0xFFFFFFU)<count&&
  Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)&&object&&
  Read(b,object,id_offset,actual)&&actual==id&&
  (!expected_magic||(Read(b,object,magic_offset,magic)&&magic==expected_magic));
}
bool Artifact(const Bindings&b,std::uint32_t id,const void*&object) noexcept {
 return Resolve(b,b.model.artifact_storage,id,0x10,object,0x14,0x41727469U);
}
bool Pin(const Bindings&b,std::uintptr_t rva,std::string_view hex) noexcept {
 if(hex.size()%2||hex.size()>128)return false;
 std::array<unsigned char,64> bytes{};
 if(!b.model.read_memory(b.model.read_context,reinterpret_cast<const void*>(b.model.image_base+rva),bytes.data(),hex.size()/2))return false;
 const auto nibble=[](char c)->int{return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
 for(std::size_t i=0;i<hex.size()/2;++i){const int a=nibble(hex[i*2]),v=nibble(hex[i*2+1]);
  if(a<0||v<0||bytes[i]!=static_cast<unsigned char>(a*16+v))return false;}
 return true;
}
#include "ck3_12004_holy_site_relic_permissions_pins.inc"
bool SourcePins(const Bindings&b) noexcept {
 for(const auto&pin:kPins)if(!Pin(b,pin.first,pin.second))return false;
 std::uintptr_t enshrine=0,remove=0;
 return Read(b,reinterpret_cast<const void*>(b.model.image_base+0x4770930),0x30,enshrine)&&
  enshrine==b.model.image_base+0x29AB4F0&&
  Read(b,reinterpret_cast<const void*>(b.model.image_base+0x47707D0),0x30,remove)&&
  remove==b.model.image_base+0x29ABB20;
}
bool NativeInventory(const Bindings&b,const void*actor,const void*&inventory) noexcept {
 inventory=nullptr;
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {inventory=reinterpret_cast<const void*(__fastcall*)(const void*)>(b.model.image_base+0x28AA890)(actor);return inventory!=nullptr;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)actor;return false;
#endif
}
bool NativeCandidate(const Bindings&b,const void*artifact,const void*site,bool&value) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {value=reinterpret_cast<bool(__fastcall*)(const void*,const void*,void*)>(b.model.image_base+0x2531200)(artifact,site,nullptr);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)artifact;(void)site;(void)value;return false;
#endif
}
bool NativeArtifactPermission(const Bindings&b,std::uintptr_t rva,const void*window,const void*artifact,bool&value) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {value=reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(b.model.image_base+rva)(window,artifact);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)rva;(void)window;(void)artifact;(void)value;return false;
#endif
}
bool NativeEnshrine(const Bindings&b,const void*w,const void*a,bool&v) noexcept {return NativeArtifactPermission(b,0x17D53F0,w,a,v);}
bool NativeRemove(const Bindings&b,const void*w,const void*a,bool&v) noexcept {return NativeArtifactPermission(b,0x17D56F0,w,a,v);}
bool NativeButton(const Bindings&b,std::uintptr_t rva,const void*w,bool&v) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {v=reinterpret_cast<bool(__fastcall*)(const void*)>(b.model.image_base+rva)(w);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)rva;(void)w;(void)v;return false;
#endif
}
bool NativeEnshrineButton(const Bindings&b,const void*w,bool&v) noexcept {return NativeButton(b,0x17D5970,w,v);}
bool NativeRemoveButton(const Bindings&b,const void*w,bool&v) noexcept {return NativeButton(b,0x17D5E40,w,v);}
struct Pass {
 const void*actor=nullptr,*site=nullptr,*actor_data=nullptr,*inventory=nullptr;
 const void*gfx=nullptr,*handler=nullptr,*window=nullptr,*root=nullptr,*selected_slot=nullptr;
 const void*requested_artifact=nullptr;
 std::uint32_t current_actor=absent,selected_site=absent,selected_artifact=absent;
 std::uint32_t player_rite=absent,player_faith=absent,owner_character=absent,owner_site=absent;
 Header player_ids{},site_slots{},window_candidates{};
 std::vector<std::uint32_t> player_artifacts,window_artifacts;
 std::vector<SlotRow>slots;
 std::vector<std::pair<std::uint32_t,const void*>>observed_artifacts;
 std::optional<std::uint32_t>requested_owner_raw;
 std::optional<std::int32_t>requested_rarity;
 bool player_inventory_available=false,slots_available=false,window_available=false,cache_available=false;
};
bool Base(const Bindings&b,const ck3_12002::religion::Context&context,std::uint32_t site_id,Pass&p) noexcept {
 const void*rite=nullptr;
 return Resolve(b,b.model.character_storage,static_cast<std::uint32_t>(context.played_character_id),0x18,p.actor,0x1C,0x43686172U)&&
  Resolve(b,b.model.holy_site_storage,site_id,0x10,p.site,0x14,0x486F5374U)&&
  Read(b,b.current_actor_reference,0,p.current_actor)&&p.current_actor==static_cast<std::uint32_t>(context.played_character_id)&&
  Read(b,p.actor,0xB4,p.player_rite)&&p.player_rite==context.rite_id&&Resolve(b,b.model.rite_storage,p.player_rite,8,rite)&&
  Read(b,rite,0x4B8,p.player_faith)&&p.player_faith==context.faith_id;
}
void ReadSlots(const Bindings&b,Pass&p,Snapshot&out) {
 auto&s=out.site_inventory_slots;
 if(!Array(b,p.site,0x68,p.site_slots)||!Rows(b,p.site_slots,p.slots)||
  std::any_of(p.slots.begin(),p.slots.end(),[](const SlotRow&r){return r.magic!=0x496E7653U;})){
  s.unavailable_reason="site_inventory_slot_table_unavailable";return;}
 for(std::size_t i=0;i<p.slots.size();++i)s.slots.push_back({static_cast<std::uint32_t>(i),Id(p.slots[i].artifact)});
 p.slots_available=s.available=true;s.unavailable_reason.clear();
}
void ReadPlayerInventory(const Bindings&b,Pass&p,Snapshot&out) {
 auto&v=out.player_inventory;
 if(!Read(b,p.actor,0x1B0,p.actor_data)||!p.actor_data){v.unavailable_reason="player_inventory_data_unavailable";return;}
 if(!b.player_inventory){v.unavailable_reason="player_inventory_getter_unavailable";return;}
 ++out.native_getter_calls;
 if(!b.player_inventory(b,p.actor,p.inventory)||p.inventory!=At(p.actor_data,0x458)){
  v.unavailable_reason="player_inventory_getter_or_owner_data_differs";return;}
 if(!Read(b,p.inventory,0x38,p.owner_character)||!Read(b,p.inventory,0x3C,p.owner_site)||
  !Array(b,p.inventory,0x58,p.player_ids)||!Rows(b,p.player_ids,p.player_artifacts)){
  v.unavailable_reason="player_inventory_header_or_owner_unavailable";return;}
 v.native_character_owner_id=Id(p.owner_character);v.native_holy_site_owner_id=Id(p.owner_site);
 v.owner_matches_player=p.owner_character==p.current_actor;v.artifact_ids=p.player_artifacts;
 p.player_inventory_available=v.available=true;v.unavailable_reason.clear();
}
void ReadWindow(const Bindings&b,const void*owner,std::uint32_t site_id,Pass&p,Snapshot&out) {
 auto&w=out.window_context;const void*back=nullptr,*window_gfx=nullptr;std::uintptr_t primary=0,secondary=0;
 if(!Read(b,owner,0x10,p.gfx)||!p.gfx||!Read(b,p.gfx,0x88,p.handler)||!p.handler||
  !Read(b,p.handler,0x5D8,p.window)||!p.window||!Read(b,p.window,0,primary)||primary!=b.model.image_base+0x4592338||
  !Read(b,p.window,0x10,secondary)||secondary!=b.model.image_base+0x4592310||
  !Read(b,p.window,0xA0,back)||back!=p.handler||!Read(b,p.window,0x98,window_gfx)||window_gfx!=p.gfx||
  !Read(b,p.window,0x60,p.root)){
  w.unavailable_reason="holy_site_window_registered_owner_unavailable";return;}
 w.root_present=p.root!=nullptr;
 if(!Read(b,p.window,0xC8,p.selected_site)){w.unavailable_reason="holy_site_window_selection_unreadable";return;}
 w.selected_holy_site_id=Id(p.selected_site);
 if(p.selected_site!=site_id){w.unavailable_reason="holy_site_window_selected_site_differs";return;}
 if(!p.root){w.unavailable_reason="holy_site_window_root_not_created";return;}
 if(!Read(b,p.window,0x108,p.selected_artifact)||!Read(b,p.window,0x110,p.selected_slot)){
  w.unavailable_reason="holy_site_window_artifact_or_slot_unreadable";return;}
 w.selected_artifact_id=Id(p.selected_artifact);
 if(!p.slots_available){w.unavailable_reason="holy_site_window_slot_table_unavailable";return;}
 if(!p.selected_slot)w.slot_mode="native_automatic";
 else {
  bool found=false;
  for(std::size_t i=0;i<p.slots.size();++i)if(p.selected_slot==At(p.site_slots.data,i*sizeof(SlotRow))){
   found=true;w.slot_mode="explicit_inventory_slot";w.selected_slot_index=static_cast<std::uint32_t>(i);
   w.selected_slot_artifact_id=Id(p.slots[i].artifact);break;}
  if(!found){w.unavailable_reason="holy_site_window_selected_slot_is_not_site_inventory_row";return;}
 }
 p.window_available=w.available=true;w.unavailable_reason.clear();
 auto&cache=w.cached_candidates;
 if(!Array(b,p.window,0x130,p.window_candidates)||!Rows(b,p.window_candidates,p.window_artifacts)){
  cache.unavailable_reason="holy_site_window_candidate_cache_unavailable";return;}
 cache.artifact_ids=p.window_artifacts;p.cache_available=cache.available=true;cache.unavailable_reason.clear();
}
void EvaluateCandidates(const Bindings&b,Pass&p,Snapshot&out) {
 auto&c=out.current_candidates;
 if(!p.player_inventory_available){c.unavailable_reason="current_player_inventory_unavailable";return;}
 bool complete=true;
 for(const auto id:p.player_artifacts){CandidateEvaluation row{};row.artifact_id=id;const void*artifact=nullptr;
  if(!Artifact(b,id,artifact)){row.unavailable_reason="candidate_artifact_full_reference_unavailable";complete=false;}
  else {
   row.object_resolved=true;p.observed_artifacts.emplace_back(id,artifact);
   if(!b.candidate_predicate){row.unavailable_reason="native_candidate_predicate_unavailable";complete=false;}
   else {bool value=false;row.predicate_called=true;++out.native_getter_calls;
    if(!b.candidate_predicate(b,artifact,p.site,value)){row.unavailable_reason="native_candidate_predicate_failed";complete=false;}
    else {row.available=true;row.can_be_candidate=value;row.unavailable_reason.clear();if(value)c.artifact_ids.push_back(id);}}
  }
  c.evaluations.push_back(std::move(row));
 }
 c.available=complete;c.unavailable_reason=complete?"":"one_or_more_candidate_evaluations_unavailable";
}
void Permission(const Bindings&b,ArtifactPermission fn,const void*w,const void*a,Snapshot&out,ObservedBool&value) {
 if(!fn){value.unavailable_reason="native_artifact_permission_getter_unavailable";return;}
 bool result=false;++out.native_getter_calls;
 if(!fn(b,w,a,result)){value.unavailable_reason="native_artifact_permission_getter_failed";return;}
 value.available=true;value.value=result;value.unavailable_reason.clear();
}
void Button(const Bindings&b,ButtonPermission fn,const void*w,Snapshot&out,ObservedBool&value) {
 if(!fn){value.unavailable_reason="native_button_permission_getter_unavailable";return;}
 bool result=false;++out.native_getter_calls;
 if(!fn(b,w,result)){value.unavailable_reason="native_button_permission_getter_failed";return;}
 value.available=true;value.value=result;value.unavailable_reason.clear();
}
void EvaluatePermissions(const Bindings&b,Pass&p,Snapshot&out) {
 auto&a=out.artifact_permissions;a.artifact_id=out.requested_artifact_id;
 if(out.requested_artifact_id){const void*artifact=nullptr;
  if(p.player_inventory_available)a.player_inventory_contains_reference=
   std::find(p.player_artifacts.begin(),p.player_artifacts.end(),*out.requested_artifact_id)!=p.player_artifacts.end();
  if(!Artifact(b,*out.requested_artifact_id,artifact))a.unavailable_reason="requested_artifact_full_reference_unavailable";
  else {
   std::uint32_t owner=absent;std::int32_t rarity=0;a.object_resolved=true;
   p.requested_artifact=artifact;
   p.observed_artifacts.emplace_back(*out.requested_artifact_id,artifact);
   if(Read(b,artifact,0x7C,owner)){a.native_holy_site_owner_id=Id(owner);p.requested_owner_raw=owner;}
   if(Read(b,artifact,0xB0,rarity)){a.rarity_level=rarity;p.requested_rarity=rarity;}
   if(!p.window_available)a.unavailable_reason="requested_site_window_context_unavailable";
   else {
    Permission(b,b.can_enshrine,p.window,artifact,out,a.can_enshrine);
    Permission(b,b.can_remove,p.window,artifact,out,a.can_remove);
    a.available=a.can_enshrine.available&&a.can_remove.available;
    a.unavailable_reason=a.available?"":"one_or_more_native_artifact_permissions_unavailable";
   }
  }
 }
 auto&buttons=out.current_buttons;buttons.selected_artifact_id=out.window_context.selected_artifact_id;
 if(!p.window_available){buttons.unavailable_reason="requested_site_window_context_unavailable";return;}
 if(out.requested_artifact_id)buttons.context_matches_requested_artifact=p.selected_artifact==*out.requested_artifact_id;
 const void*selected=nullptr;
 if(p.selected_artifact!=absent&&!Artifact(b,p.selected_artifact,selected)){
  buttons.unavailable_reason="selected_button_artifact_full_reference_unavailable";return;}
 if(selected)p.observed_artifacts.emplace_back(p.selected_artifact,selected);
 Button(b,b.enshrine_button,p.window,out,buttons.can_enshrine);
 Button(b,b.remove_button,p.window,out,buttons.can_remove);
 buttons.available=buttons.can_enshrine.available&&buttons.can_remove.available;
 buttons.unavailable_reason=buttons.available?"":"one_or_more_native_button_permissions_unavailable";
}
bool Stable(const Bindings&b,const void*owner,const ck3_12002::religion::Context&context,
 std::uint32_t site_id,const Pass&before) {
 Pass after{};if(!Base(b,context,site_id,after)||after.actor!=before.actor||after.site!=before.site||
  after.current_actor!=before.current_actor||after.player_rite!=before.player_rite||after.player_faith!=before.player_faith)return false;
 for(const auto&[id,pointer]:before.observed_artifacts){const void*now=nullptr;if(!Artifact(b,id,now)||now!=pointer)return false;}
 if(before.requested_owner_raw||before.requested_rarity){
  std::uint32_t artifact_owner=absent;std::int32_t rarity=0;
  if(before.requested_owner_raw&&(!Read(b,before.requested_artifact,0x7C,artifact_owner)||artifact_owner!=*before.requested_owner_raw))return false;
  if(before.requested_rarity&&(!Read(b,before.requested_artifact,0xB0,rarity)||rarity!=*before.requested_rarity))return false;
 }
 if(before.slots_available){Header h{};std::vector<SlotRow> rows;
  if(!Array(b,before.site,0x68,h)||h!=before.site_slots||!Rows(b,h,rows)||rows!=before.slots)return false;}
 if(before.player_inventory_available){const void*data=nullptr;Header h{};std::vector<std::uint32_t> rows;std::uint32_t character=0,site=0;
  if(!Read(b,before.actor,0x1B0,data)||data!=before.actor_data||
   !Read(b,before.inventory,0x38,character)||character!=before.owner_character||
   !Read(b,before.inventory,0x3C,site)||site!=before.owner_site||
   !Array(b,before.inventory,0x58,h)||h!=before.player_ids||!Rows(b,h,rows)||rows!=before.player_artifacts)return false;}
 if(before.window_available){Snapshot scratch{};after.slots_available=before.slots_available;
  after.site_slots=before.site_slots;after.slots=before.slots;
  ReadWindow(b,owner,site_id,after,scratch);
  if(!after.window_available||after.gfx!=before.gfx||after.handler!=before.handler||after.window!=before.window||
   after.root!=before.root||after.selected_site!=before.selected_site||after.selected_artifact!=before.selected_artifact||
   after.selected_slot!=before.selected_slot||after.cache_available!=before.cache_available||
   (before.cache_available&&(after.window_candidates!=before.window_candidates||after.window_artifacts!=before.window_artifacts)))return false;}
 return true;
}
}
Bindings BindHolySiteRelicPermissionsImage12004(std::uintptr_t base,std::string_view sha) noexcept {
 Bindings b{};b.model=holy_site_relic::BindHolySiteRelicContextImage12004(base,sha);
 if(!b.model.enabled)return b;
 b.current_actor_reference=reinterpret_cast<const std::uint32_t*>(base+0x54DBC00);
 b.player_inventory=&NativeInventory;b.candidate_predicate=&NativeCandidate;
 b.can_enshrine=&NativeEnshrine;b.can_remove=&NativeRemove;
 b.enshrine_button=&NativeEnshrineButton;b.remove_button=&NativeRemoveButton;
 b.getter_backend="source_bound_native_getter";b.source_bound=true;return b;
}
bool ReadHolySiteRelicPermissions12004(const Bindings&b,const void*owner,
 const ck3_12002::religion::Context&context,std::uint32_t site_id,
 std::optional<std::uint32_t> artifact_id,Snapshot&out) noexcept {
 out={};out.capture_epoch=context.capture_epoch;out.date_raw=context.date_raw;
 out.played_character_id=context.played_character_id;out.player_faith_id=context.available?context.faith_id:std::nullopt;
 out.requested_holy_site_id=site_id;out.requested_artifact_id=artifact_id;out.getter_backend=b.source_bound?"unavailable":b.getter_backend;
 out.artifact_permissions.artifact_id=artifact_id;
 if(artifact_id)out.artifact_permissions.unavailable_reason="artifact_permissions_not_read";
 const auto fail=[&](const char*why){out.available=false;out.unavailable_reason=why;return false;};
 try {
  if(!b.model.enabled||!b.model.read_memory||!context.available||context.played_character_id<=0||site_id==absent||artifact_id==absent)
   return fail("relic_permissions_context_or_full_reference_unavailable");
  if(b.source_bound){if(!SourcePins(b))return fail("relic_permissions_loaded_source_pins_changed");out.loaded_source_pins_verified=true;out.getter_backend=b.getter_backend;}
  Pass pass{};if(!Base(b,context,site_id,pass))return fail("relic_permissions_actor_site_or_faith_binding_unavailable");
  out.holy_site_id=site_id;
  ReadSlots(b,pass,out);ReadPlayerInventory(b,pass,out);ReadWindow(b,owner,site_id,pass,out);
  EvaluateCandidates(b,pass,out);EvaluatePermissions(b,pass,out);
  if(!Stable(b,owner,context,site_id,pass))return fail("relic_permissions_inputs_changed_during_read");
  out.available=true;out.unavailable_reason.clear();return true;
 }catch(...){return fail("relic_permissions_reader_exception");}
}
}

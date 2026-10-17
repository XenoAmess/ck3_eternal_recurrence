#include "xar_bridge/holy_site_relic_action_preview_adapter12004.hpp"
#include "xar_bridge/ck3_12004_holy_site_relic_action_context.hpp"
#include <algorithm>
#include <limits>
namespace xar::ck3_12004::religion::relic_actions {
namespace {
using Model=holy_site_relic::Bindings;
template<class T>bool Read(const Model&b,const void*p,std::size_t offset,T&v) noexcept {
 const auto address=reinterpret_cast<std::uintptr_t>(p);return address&&offset<=std::numeric_limits<std::uintptr_t>::max()-address&&
  b.read_memory&&b.read_memory(b.read_context,reinterpret_cast<const void*>(address+offset),&v,sizeof(v));
}
bool Resolve(const Model&b,void**global,std::uint32_t id,std::size_t id_offset,const void*&object) noexcept {
 const void*storage=nullptr,*rows=nullptr;std::uint32_t count=0,actual=absent;object=nullptr;
 return id!=absent&&Read(b,global,0,storage)&&storage&&Read(b,storage,0x20,rows)&&rows&&Read(b,storage,0x2C,count)&&
  (id&0xFFFFFFU)<count&&Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)&&object&&Read(b,object,id_offset,actual)&&actual==id;
}
bool CurrentContext(const relic_action_context::Bindings&b,const Frame&frame,ck3_12002::religion::Context&c) noexcept {
 c={};c.capture_epoch=frame.capture_epoch;c.date_raw=frame.date_raw;c.played_character_id=frame.played_character_id;
 const auto&m=b.permissions.model;const void*actor=nullptr,*rite=nullptr,*faith=nullptr;
 std::uint32_t current=absent,rite_id=absent,faith_id=absent,magic=0;
 if(frame.played_character_id<=0||!Read(m,b.permissions.current_actor_reference,0,current)||current!=static_cast<std::uint32_t>(frame.played_character_id)||
  !Resolve(m,m.character_storage,current,0x18,actor)||!Read(m,actor,0x1C,magic)||magic!=0x43686172U||
  !Read(m,actor,0xB4,rite_id)||!Resolve(m,m.rite_storage,rite_id,8,rite)||!Read(m,rite,0x4B8,faith_id)||
  !Resolve(m,m.faith_storage,faith_id,8,faith))return false;
 c.rite_id=rite_id;c.faith_id=faith_id;c.available=true;c.failure=ck3_12002::religion::Failure::none;return true;
}
bool ActualWindow(const Model&b,const Admission&a,std::uint32_t site_id) noexcept {
 const void*gfx=nullptr,*handler=nullptr,*window=nullptr,*root=nullptr,*back=nullptr;std::uint32_t selected=absent;
 return a.jomini_owner&&a.handler&&a.actual_root&&Read(b,a.jomini_owner,0x10,gfx)&&gfx&&Read(b,gfx,0x88,handler)&&handler==a.handler&&
  Read(b,handler,0x5D8,window)&&window&&Read(b,window,0xA0,back)&&back==handler&&Read(b,window,0x60,root)&&root==a.actual_root&&
  Read(b,window,0xC8,selected)&&selected==site_id;
}
}
bool ReadProductionRelicActionPreview12004(void*opaque,const Admission&a,const Frame&frame,const Request&r,PreviewProof&proof) noexcept {
 proof={};if(!opaque||!a.owner_tls_paused_verified||!a.modal_admitted||!a.actual_root_visible||!a.actual_root_enabled||
  (r.operation!=Operation::enshrine&&r.operation!=Operation::remove)||!ValidateRequest(r))return false;
 try {
  const auto&cfg=*static_cast<const ProductionRelicActionPreviewContext12004*>(opaque);
  auto b=relic_action_context::BindHolySiteRelicActionContextImage12004(cfg.image_base,cfg.executable_sha256);
  if(!b.source_bound||!b.permissions.source_bound||!b.permissions.model.enabled||!ActualWindow(b.permissions.model,a,r.holy_site_id))return false;
  ck3_12002::religion::Context c{};if(!CurrentContext(b,frame,c))return false;
  relic_action_context::Snapshot s{};
  if(!relic_action_context::ReadHolySiteRelicActionContext12004(b,a.jomini_owner,c,r.holy_site_id,r.artifact_id,s)||
   !s.available||!s.loaded_source_pins_verified||!s.permissions.loaded_source_pins_verified||
   s.getter_backend!="source_bound_native_getter"||s.permissions.getter_backend!="source_bound_native_getter"||
   !s.selected_artifact_matches_request||!s.preview_identity_available||!s.artifact_ownership.available||!s.destination.available||
   !s.permissions.artifact_permissions.available||!s.permissions.current_buttons.available||
   s.permissions.current_buttons.context_matches_requested_artifact!=true||!ActualWindow(b.permissions.model,a,r.holy_site_id))return false;
  if((r.operation==Operation::enshrine&&s.destination.action_kind!="enshrine")||(r.operation==Operation::remove&&s.destination.action_kind!="remove"))return false;
  const auto&owner=s.artifact_ownership;
  if(r.operation==Operation::enshrine){
   const auto&rows=s.permissions.current_candidates.evaluations;
   const bool requested_seen=std::any_of(rows.begin(),rows.end(),[&](const auto&row){return row.artifact_id==r.artifact_id;});
   const bool requested_rows_known_valid=std::all_of(rows.begin(),rows.end(),[&](const auto&row){return row.artifact_id!=r.artifact_id||(row.available&&row.can_be_candidate==true);});
   if(!requested_seen||!requested_rows_known_valid)return false;
  }
  if(r.operation==Operation::enshrine&&(!owner.character_owner_matches_player.value_or(false)||!owner.player_owned_reference_member.value_or(false)||
   owner.holy_site_owner_id||!s.permissions.artifact_permissions.can_enshrine.value.value_or(false)||!s.permissions.current_buttons.can_enshrine.value.value_or(false)))return false;
  if(r.operation==Operation::remove&&(!owner.holy_site_owner_matches_requested.value_or(false)||!owner.site_equipped_slot_member.value.value_or(false)||
   !s.permissions.artifact_permissions.can_remove.value.value_or(false)||!s.permissions.current_buttons.can_remove.value.value_or(false)))return false;
  proof.frame=frame;proof.holy_site_id=r.holy_site_id;proof.artifact_id=r.artifact_id;
  proof.selected_slot_index=s.destination.selected_slot_index;proof.effective_slot_index=s.destination.effective_slot_index;proof.replacing_artifact_id=s.destination.replacing_artifact_id;
  proof.artifact_character_owner_matches_player=owner.character_owner_matches_player.value_or(false);
  proof.player_owned_ids_contains_artifact=owner.player_owned_reference_member.value_or(false);proof.site_equipped_slot_member=owner.site_equipped_slot_member.value.value_or(false);
  proof.preview_observed=true;proof.preview_identity_sha256=s.preview_identity_sha256;
  proof.source_qualified=true;proof.live_qualified=true;proof.available=true;return true;
 }catch(...){proof={};return false;}
}
}

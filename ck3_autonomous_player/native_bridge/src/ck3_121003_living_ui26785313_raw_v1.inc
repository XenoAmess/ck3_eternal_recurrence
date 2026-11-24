// One actual Inventory Raw TU, after weapon/detail/event-scope/finite helpers.
#include "xar_bridge/ck3_121003_living_ui26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_entry26785313_owner_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct LivingUiRaw267V1::State {
 living_inventory_private::Snapshot inventory;
 std::optional<living_inventory_private::WeaponSnapshot>weapon;
 std::optional<living_inventory_private::DetailSnapshot>detail;
 std::optional<LydRaw267V1>events;
 std::vector<std::vector<std::byte>>scope_proof;
 LivingUiSource267V1 source;
 friend bool operator==(const State&,const State&)=default;
};
bool SameLivingUiRaw267V1(const LivingUiRaw267V1&a,const LivingUiRaw267V1&b)noexcept {
 try{return a.cleanup_known&&b.cleanup_known&&a.state_&&b.state_&&
  a.source==b.source&&a.inventory==b.inventory&&*a.state_==*b.state_;}catch(...){return false;}
}
bool ReadLivingUiRaw267V1(const ReadonlyBindings&b,const LivingUiFrame267V1&f,
 const LivingUiRequest267V1&q,std::uint64_t mono,living_inventory_private::LivingFiniteCase267V1&finite,
 LivingUiRaw267V1&out,std::string&why)noexcept {
 out={};why="living_UI_Raw_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 using namespace living_inventory_private;
 try{
  if(!Fresh(b,f.inventory,q,mono)||!VerifyLivingEntryImage267V1(b.module_base)||
     !VerifyReadonlyImage(b.module_base))return false;
  const auto take=[&](LivingUiRaw267V1::State&state,LivingFiniteCase267V1&case_state){
   LivingInventoryRaw267V1 inv;
   if(!Take(b,f.inventory,q,mono,state.inventory,inv,why)){out.entered|=inv.entered;out.cleanup_known&=inv.cleanup_known;return false;}
   out.entered|=inv.entered;out.cleanup_known&=inv.cleanup_known;
   auto actual=state.inventory.source;actual.complete_inventory=actual.sampled_twice=true;
   if(!case_state.bound)LivingFiniteBind267V1(case_state,f.inventory,actual);
   if(case_state.bound&&!LivingFiniteSameOwner267V1(case_state,f.inventory))return false;
   auto&s=state.source;s.kind=LivingUiKindFor267V1(q.action);s.actor_full_id=actual.actor_full_id;s.sampled_twice=true;
   if(s.kind==LivingUiKind267V1::weapon){
    if(!f.weapon)return false;state.weapon.emplace();bool clean=true;
    if(!TakeWeapon(b,*f.weapon,q,mono,*state.weapon,clean,why)){out.cleanup_known&=clean;return false;}
    out.entered=true;const auto&w=*state.weapon;
    if(w.inventory!=state.inventory)return false;
    const auto target=std::find_if(actual.artifacts.begin(),actual.artifacts.end(),[&](const auto&a){return a.full_id==w.target_id;});
    if(target==actual.artifacts.end()||!actual.weapon_slot)return false;
    LivingWeaponData267V1 data;data.target_full_id=w.target_id;
    data.weapon_artifact_full_id=actual.slots[*actual.weapon_slot].artifact_full_id;
    data.window_found=f.weapon->gui.window_found;data.visible=w.logical_visible;data.enabled=f.weapon->gui.root.enabled;
    data.target_equipped=target->equipped;data.weapon_selected=w.selected==w.slot;
    data.native_slot_available=w.available;data.native_can_hold=w.compatible;
    data.select_admissible=WeaponAdmissible(w,LivingWeaponAction267V1::select_weapon);
    data.equip_admissible=WeaponAdmissible(w,LivingWeaponAction267V1::equip_target);
    data.unequip_admissible=WeaponAdmissible(w,LivingWeaponAction267V1::unequip_target);
    s.weapon=std::move(data);return true;
   }
   if(s.kind==LivingUiKind267V1::detail){
    if(!f.detail)return false;state.detail.emplace();LivingDetailRaw267V1 detail;
    if(!DetailTake(b,*f.detail,q,mono,*state.detail,detail,why)){out.entered|=detail.entered;out.cleanup_known&=detail.cleanup_known;return false;}
    out.entered|=detail.entered;out.cleanup_known&=detail.cleanup_known;
    if(state.detail->inventory!=state.inventory)return false;s.detail=state.detail->source;return true;
   }
   if(!f.events||!VerifyLydImage267V1(b.module_base))return false;
   state.events.emplace();LydRequest267V1 read;read.action=LydAction267V1::query_events;
   read.expected=q.expected;read.request_id=q.request_id;read.request_id_size=q.request_id_size;read.deadline_unix_ms=q.deadline_unix_ms;
   if(!ReadLydRaw267V1(b,f.events->core,f.events->scene,mono,read,{},*state.events,why)){
    out.entered|=state.events->native_read_entered;out.cleanup_known&=state.events->cleanup_known;return false;}
   out.entered|=state.events->native_read_entered;out.cleanup_known&=state.events->cleanup_known;
   if(!state.events->source.events||state.events->source.events->events.size()!=state.events->event_rows.size()||
      state.events->manager_census.game!=f.inventory.game||state.events->manager_census.jomini!=f.inventory.jomini)return false;
   LivingEventData267V1 data;data.census=*state.events->source.events;
   // This is DATA projection, not permission borrowed from the original LYD roles.
   for(auto&e:data.census.events)for(auto&o:e.options){o.permitted_role.reset();o.source_bound_option_key.reset();}
   using A=LivingUiAction267V1;
   constexpr std::array<A,8>actions{A::open_tutorial,A::feed_common,A::feed_masterwork,A::feed_famed,A::feed_illustrious,A::cancel_review,A::confirm_review,A::close_management};
   for(std::size_t n=0;n<data.census.events.size();++n){
    const auto&e=data.census.events[n];
    if(e.recipient_character_id!=f.inventory.core.played_character_id||
       (e.definition_key!="xalw.12"&&e.definition_key!="xalw.10"&&e.definition_key!="xalw.11"))continue;
    LivingEventScopeRaw267V1 held;
    if(!ReadLivingEventArtifactScopes267V1(b,f.inventory,q,mono,state.events->event_rows[n],e,held,why)){
     out.entered|=held.entered;out.cleanup_known&=held.cleanup_known;return false;}
    out.entered|=held.entered;out.cleanup_known&=held.cleanup_known;
    state.scope_proof.push_back(held.fingerprint);data.bindings.push_back(held.source);
    const bool observed=case_state.bound&&LivingFiniteObserve267V1(case_state,f.inventory,held.source,actual);
    for(const auto action:actions){
     int index=-1;
     if(e.definition_key=="xalw.12"&&action==A::open_tutorial)index=0;
     if(e.definition_key=="xalw.10"&&action>=A::feed_common&&action<=A::feed_illustrious)index=1+static_cast<int>(action)-static_cast<int>(A::feed_common);
     if(e.definition_key=="xalw.10"&&action==A::close_management)index=9;
     if(e.definition_key=="xalw.11"&&action==A::confirm_review)index=0;
     if(e.definition_key=="xalw.11"&&action==A::cancel_review)index=1;
     if(index<0)continue;
     const auto option=std::find_if(e.options.begin(),e.options.end(),[&](const auto&o){return o.authored_option_index==index;});
     if(option==e.options.end())return false;
     data.fixed_actions.push_back({action,e.instance_id,index,observed&&e.named_root_bound&&e.window_visible&&e.window_enabled&&
      option->native_can_select&&!option->text.empty()&&LivingFiniteMayConsume267V1(case_state,action,held.source)});
    }
   }
   data.complete_bindings=true;s.events=std::move(data);return true;
  };
  auto a=std::make_shared<LivingUiRaw267V1::State>(),z=std::make_shared<LivingUiRaw267V1::State>();
  auto first=finite,last=finite;
  if(!take(*a,first)||!take(*z,last)||*a!=*z||!Fresh(b,f.inventory,q,mono)||
     !LivingUiSourceShape267V1(z->source,f.inventory.core))return false;
  finite=std::move(last);out.source=z->source;out.inventory=z->inventory.source;
  out.inventory.complete_inventory=out.inventory.sampled_twice=true;out.state_=std::move(z);why.clear();return true;
 }catch(...){why="living_UI_private_snapshot_copy_unavailable";return false;}
#else
 (void)b;(void)f;(void)q;(void)mono;(void)finite;return false;
#endif
}
struct LivingUiCallAccess267V1 {
 static bool Can(std::uintptr_t image,std::uintptr_t option,bool&out)noexcept{
  __try{out=reinterpret_cast<bool(__fastcall*)(const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x1B6CC30))(reinterpret_cast<const void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
 }
 static bool Select(std::uintptr_t image,std::uintptr_t option)noexcept{
  __try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x1B6CA10))(reinterpret_cast<void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
 }
 static LivingUiCall267V1 Submit(const ReadonlyBindings&b,const LivingUiFrame267V1&f,
  const LivingUiRequest267V1&q,std::uint64_t mono,const LivingUiRaw267V1&issued,
  living_inventory_private::LivingFiniteCase267V1&finite,LivingWeaponPrivateSession267V1&weapon)noexcept{
  LivingUiCall267V1 call;
  using namespace living_inventory_private;
  try{
   auto copy=finite;LivingUiRaw267V1 actual;std::string why;
   if(!ReadLivingUiRaw267V1(b,f,q,mono,copy,actual,why)||!SameLivingUiRaw267V1(actual,issued)){
    call.cleanup_known=actual.cleanup_known;return call;}
   if(LivingUiKindFor267V1(q.action)==LivingUiKind267V1::weapon){
    if(!f.weapon)return call;LivingWeaponAction267V1 action;
    switch(q.action){case LivingUiAction267V1::select_weapon:action=LivingWeaponAction267V1::select_weapon;break;
     case LivingUiAction267V1::equip_target:action=LivingWeaponAction267V1::equip_target;break;
     case LivingUiAction267V1::unequip_target:action=LivingWeaponAction267V1::unequip_target;break;default:return call;}
    LivingWeaponLease267V1 lease;
    if(!PrepareLivingWeapon267V1(weapon,b,*f.weapon,q,mono,action,lease,why)){
     call.cleanup_known=!LivingWeaponSessionUnknown267V1(weapon);return call;
    }
    auto verify_case=finite;LivingUiRaw267V1 verify;
    if(!ReadLivingUiRaw267V1(b,f,q,mono,verify_case,verify,why)||!SameLivingUiRaw267V1(verify,issued)){
     call.cleanup_known=verify.cleanup_known;return call;
    }
    const auto result=SubmitLivingWeapon267V1(lease);
    return {result.entered,result.native_returned,result.cleanup_known};
   }
   if(!actual.source.events||!actual.state_->events)return call;
   const LivingEventActionData267V1*selected=nullptr;
   for(const auto&a:actual.source.events->fixed_actions)if(a.action==q.action&&a.admissible){if(selected)return call;selected=&a;}
   if(!selected)return call;const auto&data=*actual.source.events;
   const auto binding=std::find_if(data.bindings.begin(),data.bindings.end(),[&](const auto&v){return v.instance_id==selected->instance_id;});
   if(binding==data.bindings.end()||!LivingFiniteMayConsume267V1(finite,q.action,*binding))return call;
   std::uintptr_t option=0;
   for(std::size_t n=0;n<data.census.events.size();++n){const auto&e=data.census.events[n];if(e.instance_id!=selected->instance_id)continue;
    const auto&r=actual.state_->events->event_rows[n];if(r.instance_id!=e.instance_id||r.options.size()!=e.options.size())return call;
    for(std::size_t k=0;k<e.options.size();++k)if(e.options[k].authored_option_index==selected->authored_option_index)option=r.options[k];
   }
   bool legal=false;
   if(!option)return call;
   if(!Can(b.module_base,option,legal)){call.cleanup_known=false;return call;}
   if(!legal||!Fresh(b,f.inventory,q,mono)||!LivingFiniteClaim267V1(finite,q.action,*binding))return call;
   call.entered=true;if(!Select(b.module_base,option)){call.cleanup_known=false;return call;}
   call.native_returned=true;call.cleanup_known=Fresh(b,f.inventory,q,mono);return call;
  }catch(...){call.cleanup_known=false;return call;}
 }
};
LivingUiCall267V1 CallLivingUiRaw267V1(const ReadonlyBindings&b,const LivingUiFrame267V1&f,
 const LivingUiRequest267V1&q,std::uint64_t mono,const LivingUiRaw267V1&issued,
 living_inventory_private::LivingFiniteCase267V1&finite,LivingWeaponPrivateSession267V1&weapon)noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 return LivingUiCallAccess267V1::Submit(b,f,q,mono,issued,finite,weapon);
#else
 (void)b;(void)f;(void)q;(void)mono;(void)issued;(void)finite;(void)weapon;return {};
#endif
}
}

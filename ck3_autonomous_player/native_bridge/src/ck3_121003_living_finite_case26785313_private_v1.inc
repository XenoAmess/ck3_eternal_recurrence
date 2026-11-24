#include "xar_bridge/ck3_121003_living_finite_case26785313_private_v1.hpp"
// Private SOURCE helper for the future new Living owner, not a public ledger
// endpoint. All inputs must come from its actual full source reacquisition;
// serialized DTO rows/flags are never sufficient to call an effect.
namespace xar::ck3_121003::build26785313 {namespace living_inventory_private {
const LivingArtifact267V1*FiniteArtifact(const LivingInventorySource267V1&s,std::uint32_t id){
 const auto p=std::find_if(s.artifacts.begin(),s.artifacts.end(),[&](const auto&a){return a.full_id==id;});
 return p==s.artifacts.end()?nullptr:&*p;
}
bool LivingFiniteSameOwner267V1(const LivingFiniteCase267V1&c,const LivingInventoryFrame267V1&f){
 return c.bound&&!c.unknown&&c.initial.connection_generation==f.connection_generation&&
  c.initial.game==f.game&&c.initial.jomini==f.jomini&&c.initial.character_storage==f.character_storage&&
  c.initial.actor==f.actor&&Same(c.initial.core,f.core); // Original8 finite case is0day, no borrowed14day epoch.
}
int LivingFeedBit267V1(LivingUiAction267V1 a){switch(a){
 case LivingUiAction267V1::feed_common:return 0;case LivingUiAction267V1::feed_masterwork:return 1;
 case LivingUiAction267V1::feed_famed:return 2;case LivingUiAction267V1::feed_illustrious:return 3;default:return -1;}}
bool LivingFiniteBind267V1(LivingFiniteCase267V1&c,const LivingInventoryFrame267V1&f,
 const LivingInventorySource267V1&actual){
 if(c.bound||c.unknown||!f.facts_verified||!actual.complete_inventory||!actual.sampled_twice)return false;
 const auto&r=actual.fixed_references[0];if(r.state!=LivingReferenceState267V1::artifact||!r.full_id)return false;
 const auto*t=FiniteArtifact(actual,*r.full_id);
 if(!t||t->owner_full_id!=actual.actor_full_id||actual.actor_full_id!=std::bit_cast<std::uint32_t>(f.core.played_character_id))return false;
 c.initial=f;c.target=*r.full_id;c.bound=true;return true;
}
bool LivingFiniteObserve267V1(LivingFiniteCase267V1&c,const LivingInventoryFrame267V1&f,
 const LivingEventScopeData267V1&event,const LivingInventorySource267V1&actual){
 if(!LivingFiniteSameOwner267V1(c,f)||!actual.complete_inventory||!actual.sampled_twice||
  !event.complete_named_scopes||!event.sampled_twice||event.recipient_id!=f.core.played_character_id||
  !event.target_owned||event.target.full_id!=c.target||!FiniteArtifact(actual,c.target))return false;
 if(event.definition_key=="xalw.10"){
  if(c.phase==LivingFinitePhase267V1::cancel_dispatched){
   if(!c.cancel_before)return false;
   const auto*oldTarget=FiniteArtifact(*c.cancel_before,c.target);const auto*newTarget=FiniteArtifact(actual,c.target);
   const auto*oldMaterial=FiniteArtifact(*c.cancel_before,c.review_material);const auto*newMaterial=FiniteArtifact(actual,c.review_material);
   if(!oldTarget||!newTarget||!oldMaterial||!newMaterial||*oldTarget!=*newTarget||*oldMaterial!=*newMaterial)return false;
   // Complete independent inventory + exact4numeric fields and both fullIDs.
   // Actor selected/material refs may persist; no borrowed event scope alone proves conservation.
   c.phase=LivingFinitePhase267V1::cancel_conserved;
  }else if(c.phase==LivingFinitePhase267V1::confirm_dispatched){
   if(FiniteArtifact(actual,c.review_material))return false;
   const auto*t=FiniteArtifact(actual,c.target);
   if(!std::all_of(t->numeric.begin(),t->numeric.end(),[](const auto&v){return v.state==LivingNumericState267V1::numeric&&v.scope_kind==1&&v.raw.has_value();}))return false;
   const auto bit=LivingFeedBit267V1(c.preview);if(bit<0)return false;
   c.confirmed_mask|=1U<<static_cast<unsigned>(bit);c.phase=LivingFinitePhase267V1::settled;
   // Level/XP/sequence values remain actual DATA for the independent original
   // business assertions; never calculate them as a Native applied flag.
  }else if(c.phase==LivingFinitePhase267V1::initial||c.phase==LivingFinitePhase267V1::tutorial_dispatched)c.phase=LivingFinitePhase267V1::management;
  else if(c.phase!=LivingFinitePhase267V1::management&&c.phase!=LivingFinitePhase267V1::settled&&c.phase!=LivingFinitePhase267V1::cancel_conserved)return false;
  c.last_management_instance=event.instance_id;return true;
 }
 if(event.definition_key=="xalw.11"){
  if((c.phase==LivingFinitePhase267V1::first_review||c.phase==LivingFinitePhase267V1::review)&&
     event.instance_id==c.review_instance&&event.material_owned&&event.material.full_id==c.review_material)return true;

  if(c.phase!=LivingFinitePhase267V1::preview_dispatched||!event.material_required||
   !event.material_owned||!event.material.full_id||event.material.full_id==event.target.full_id||
   event.instance_id==c.review_instance)return false;
  if(c.common_previews==2&&c.preview==LivingUiAction267V1::feed_common&&*event.material.full_id!=c.review_material)return false;
  c.review_instance=event.instance_id;c.review_material=*event.material.full_id;
  c.phase=c.common_previews==1&&c.preview==LivingUiAction267V1::feed_common?
   LivingFinitePhase267V1::first_review:LivingFinitePhase267V1::review;
  if(c.phase==LivingFinitePhase267V1::first_review)c.cancel_before=actual;
  return true;
 }
 return event.definition_key=="xalw.12"&&c.phase==LivingFinitePhase267V1::initial;
}
bool LivingFiniteMayConsume267V1(const LivingFiniteCase267V1&c,LivingUiAction267V1 action,
 const LivingEventScopeData267V1&event){
 if(!c.bound||c.unknown||c.spent.size()>=16||event.target.full_id!=c.target||!event.target_owned||
  std::find(c.spent.begin(),c.spent.end(),std::pair{event.instance_id,action})!=c.spent.end())return false;
 if(action==LivingUiAction267V1::open_tutorial)return c.phase==LivingFinitePhase267V1::initial&&event.definition_key=="xalw.12";
 const int bit=LivingFeedBit267V1(action);
 if(bit>=0){
  if(event.definition_key!="xalw.10"||event.instance_id!=c.last_management_instance||(c.confirmed_mask&(1U<<static_cast<unsigned>(bit))))return false;
  if(bit==0)return(c.phase==LivingFinitePhase267V1::management&&c.common_previews==0)||
   (c.phase==LivingFinitePhase267V1::cancel_conserved&&c.common_previews==1);
  return c.phase==LivingFinitePhase267V1::settled&&(c.confirmed_mask&1U);
 }
 if(action==LivingUiAction267V1::close_management)return event.definition_key=="xalw.10"&&
  event.instance_id==c.last_management_instance&&c.phase==LivingFinitePhase267V1::settled&&c.confirmed_mask==0xFU;
 if(event.definition_key!="xalw.11"||event.instance_id!=c.review_instance||!event.material_owned||event.material.full_id!=c.review_material)return false;
 if(action==LivingUiAction267V1::cancel_review)return c.phase==LivingFinitePhase267V1::first_review;
 if(action==LivingUiAction267V1::confirm_review)return c.phase==LivingFinitePhase267V1::review;
 return false;
}
bool LivingFiniteClaim267V1(LivingFiniteCase267V1&c,LivingUiAction267V1 action,
 const LivingEventScopeData267V1&event){
 if(!LivingFiniteMayConsume267V1(c,action,event))return false;
 c.spent.emplace_back(event.instance_id,action); // Before actual option entry; never unspend0effect.
 if(action==LivingUiAction267V1::open_tutorial)c.phase=LivingFinitePhase267V1::tutorial_dispatched;
 else if(LivingFeedBit267V1(action)>=0){c.preview=action;if(action==LivingUiAction267V1::feed_common)++c.common_previews;c.phase=LivingFinitePhase267V1::preview_dispatched;}
 else if(action==LivingUiAction267V1::cancel_review)c.phase=LivingFinitePhase267V1::cancel_dispatched;
 else if(action==LivingUiAction267V1::confirm_review)c.phase=LivingFinitePhase267V1::confirm_dispatched;
 else if(action==LivingUiAction267V1::close_management)c.phase=LivingFinitePhase267V1::management_close_dispatched;
 return true;
}
void LivingFiniteUnknown267V1(LivingFiniteCase267V1&c){c.unknown=true;}
// Deliberately no NativeSelect call/permission here. New actual common event
// collector/Can/option-owner/custody/lease/deadline/source recheck + once owner
// remain mandatory integration gaps. This helper alone cannot grant a choice.
}}

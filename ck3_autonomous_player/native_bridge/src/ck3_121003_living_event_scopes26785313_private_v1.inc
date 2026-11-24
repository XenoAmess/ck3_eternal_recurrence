// Same inventory Raw TU, after its actual Snapshot/Take helpers. No getter,
// atom factory/lookup, temporary merge or mutable variable owner is called.
#include "xar_bridge/ck3_121003_living_event_scopes26785313_private_v1.hpp"
namespace xar::ck3_121003::build26785313 {namespace living_inventory_private {
bool EventProof(std::vector<std::byte>&out,std::uintptr_t p,std::size_t n){
 if(n>131072||out.size()>131072-n)return false;
 const auto pos=out.size();out.resize(pos+n);return !n||Copy(p,out.data()+pos,n);
}
bool ScopeReference(const std::array<std::byte,16>&bytes,LivingArtifactReference267V1&out){
 std::memcpy(&out.scope_kind,bytes.data(),2);
 if(!out.scope_kind){out.state=LivingReferenceState267V1::present_empty;return true;}
 if(out.scope_kind!=36){out.state=LivingReferenceState267V1::wrong_kind;return true;}
 std::uint64_t id=0;std::memcpy(&id,bytes.data()+8,8);
 if(id>0xFFFFFFFFULL||id==invalid)return false;
 out.state=LivingReferenceState267V1::artifact;out.full_id=static_cast<std::uint32_t>(id);return true;
}
bool ReadLivingNamedArtifactRefs267V1(std::uintptr_t image,std::uintptr_t runtime,
 std::vector<std::byte>&proof,LivingArtifactReference267V1&target,
 LivingArtifactReference267V1&material,std::array<bool,2>&found,std::string&why){
 const auto fail=[&](const char*reason){why=reason;return false;};
 std::uintptr_t rows=0,poolRows=0;std::int32_t count=0;std::uint32_t poolCount=0;
 if(!At(runtime,0x18,rows)||!At(runtime,0x24,count)||count<0||count>256||(!rows&&count)||
  !EventProof(proof,runtime+0x18,16)||(count&&!EventProof(proof,rows,static_cast<std::size_t>(count)*24)))
  return fail("living_actual_event_complete_named_table_unavailable");
 // This is the real already-initialized pool object, not an indirect guessed
 // pointer. Never call45116C0 or45115C0: their miss paths can materialize state.
 const auto pool=image+0x6B14820;
 if(count&&(!At(pool,0x30,poolRows)||!poolRows||!At(pool,0x3C,poolCount)||
  !poolCount||!EventProof(proof,pool+0x30,16)))
  return fail("living_existing_named_atom_pool_unavailable");

 for(std::int32_t index=0;index<count;++index){
  const auto entry=rows+static_cast<std::size_t>(index)*24;
  std::uint32_t atom=0;if(!At(entry,0,atom))return false;
  const auto slot=atom&0xFFFFFFU;
  if(slot>=poolCount||slot>(std::numeric_limits<std::uintptr_t>::max)()/32||
   static_cast<std::uintptr_t>(slot)*32>(std::numeric_limits<std::uintptr_t>::max)()-poolRows)
   return fail("living_named_atom_outside_real_pool");
  const auto nameAddress=poolRows+static_cast<std::size_t>(slot)*32;
  String32 name;if(!String(nameAddress,name)||!EventProof(proof,nameAddress,32))
   return fail("living_actual_named_scope_key_unreadable");
  const auto n=static_cast<std::uint32_t>(name.value.size());
  const auto old=proof.size();if(old>131072-sizeof(n)-name.value.size())return false;
  proof.resize(old+sizeof(n)+name.value.size());std::memcpy(proof.data()+old,&n,sizeof(n));
  if(n)std::memcpy(proof.data()+old+sizeof(n),name.value.data(),n);
  const int wanted=name.value=="xalw_artifact"?0:name.value=="xalw_material"?1:-1;
  if(wanted<0)continue;
  if(found[static_cast<std::size_t>(wanted)])return fail("living_duplicate_required_named_scope");
  found[static_cast<std::size_t>(wanted)]=true;std::array<std::byte,16>ref{};
  auto&value=wanted==0?target:material;
  if(!Copy(entry+8,ref.data(),16)||!ScopeReference(ref,value))
   return fail("living_named_Artifact_full_reference_invalid");
 }
 return true;
}
struct EventScopeSnapshot {
 Snapshot inventory;
 LivingEventScopeData267V1 source;
 std::vector<std::byte>proof;
 friend bool operator==(const EventScopeSnapshot&,const EventScopeSnapshot&)=default;
};
bool EventScopeTake(const ReadonlyBindings&b,const LivingInventoryFrame267V1&f,
 const LivingInventoryRequest267V1&q,std::uint64_t mono,const LydEventRawRow267V1&raw,
 const LydEventRow267V1&row,EventScopeSnapshot&out,LivingEventScopeRaw267V1&state,std::string&why){
 const auto fail=[&](const char*reason){why=reason;return false;};
 const bool review=row.definition_key=="xalw.11";
 if((row.definition_key!="xalw.12"&&row.definition_key!="xalw.10"&&!review)||
  !raw.runtime||raw.runtime==b.module_base+0x668DDD0||raw.runtime!=raw.material.runtime_event||
  raw.instance_id!=row.instance_id||row.instance_id<=0||
  row.recipient_character_id!=f.core.played_character_id||
  raw.definition!=raw.material.definition||!raw.definition||!row.named_root_bound||
  !Fresh(b,f,q,mono))return fail("living_actual_event_scope_ingress_unavailable");
 LivingInventoryRaw267V1 inventory_state;
 if(!Take(b,f,q,mono,out.inventory,inventory_state,why)){
  state.entered|=inventory_state.entered;state.cleanup_known&=inventory_state.cleanup_known;return false;}
 state.entered|=inventory_state.entered;state.cleanup_known&=inventory_state.cleanup_known;
 std::uint32_t recipient=invalid;std::uint16_t rootKind=0;std::int32_t instance=0;
 std::uintptr_t definition=0;std::uint64_t rootID=0;
 if(!At(raw.runtime,0,rootKind)||rootKind!=4||!At(raw.runtime,8,rootID)||
  rootID!=std::bit_cast<std::uint32_t>(f.core.played_character_id)||
  !At(raw.runtime,0x1B8,definition)||definition!=raw.definition||
  !At(raw.runtime,0x1C0,recipient)||recipient!=rootID||
  !At(raw.runtime,0x1C4,instance)||instance!=row.instance_id||
  !EventProof(out.proof,raw.runtime,16)||!EventProof(out.proof,raw.runtime+0x1B8,16))
  return fail("living_actual_event_complete_named_table_unavailable");
 std::array<bool,2>found{};
 if(!ReadLivingNamedArtifactRefs267V1(b.module_base,raw.runtime,out.proof,out.source.target,out.source.material,found,why))return false;
 const auto join=[&](const LivingArtifactReference267V1&ref){
  return ref.state==LivingReferenceState267V1::artifact&&ref.full_id&&
   std::count_if(out.inventory.artifact_rows.begin(),out.inventory.artifact_rows.end(),[&](const auto&a){
    return a.value.full_id==*ref.full_id&&a.value.owner_full_id==recipient&&a.pointer!=0;})==1;
 };
 out.source.target_owned=found[0]&&join(out.source.target);
 out.source.material_owned=found[1]&&join(out.source.material);
 if(!out.source.target_owned||(review&&(!out.source.material_owned||
   out.source.target.full_id==out.source.material.full_id)))return fail("living_event_required_Artifact_not_distinct_owned_inventory_member");
 out.source.instance_id=row.instance_id;out.source.recipient_id=row.recipient_character_id;
 out.source.definition_key=row.definition_key;out.source.material_required=review;
 out.source.complete_named_scopes=out.source.sampled_twice=true;
 // Optional .12/.10 material may be absent, wrong-kind or a stale borrowed ref.
 // Its DATA is retained. It is never called the material of a future review.
 return Fresh(b,f,q,mono);
}
}
bool ReadLivingEventArtifactScopes267V1([[maybe_unused]]const ReadonlyBindings&b,
 [[maybe_unused]]const LivingInventoryFrame267V1&f,[[maybe_unused]]const LivingInventoryRequest267V1&q,
 [[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const LydEventRawRow267V1&raw,
 [[maybe_unused]]const LydEventRow267V1&row,LivingEventScopeRaw267V1&out,std::string&why)noexcept{
 out={};why="living_event_scope_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1
 using namespace living_inventory_private;
 if(!VerifyLivingInventoryImage267V1(b.module_base)||!Fresh(b,f,q,mono))return false;
 try{EventScopeSnapshot a,z;
  if(!EventScopeTake(b,f,q,mono,raw,row,a,out,why)||!EventScopeTake(b,f,q,mono,raw,row,z,out,why))return false;
  if(a!=z){why="living_actual_event_named_Artifact_or_owned_census_drift";return false;}
  out.source=std::move(z.source);out.fingerprint=std::move(z.proof);why.clear();return true;
 }catch(...){out.source={};out.fingerprint.clear();why="living_event_scope_bounded_copy_unavailable";return false;}
#else
 return false;
#endif
}
}

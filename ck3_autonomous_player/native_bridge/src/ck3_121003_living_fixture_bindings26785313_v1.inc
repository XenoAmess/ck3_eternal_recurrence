// Included after actual Living inventory Raw private helpers, not a separate TU.
#include "xar_bridge/ck3_121003_living_fixture_bindings26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {namespace living_inventory_private {
bool ArtifactRefs(std::uintptr_t image,std::uintptr_t actor,std::uint32_t actor_id,
 std::uint64_t wall,std::uint64_t mono,LivingFixtureBindings267V1&out,bool&cleanup)noexcept{
 using Factory=std::uintptr_t(__fastcall*)();Any40 root{},text{};
 std::uintptr_t empty=0,reference=0,string=0;bool initialized=false,good=false;
 volatile bool entered=false,complete=false;cleanup=true;
 __try{
  empty=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8B2EF0))();
  reference=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8B5030))();
  string=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8C21D0))();
  root.type=text.type=empty;initialized=true;
  do{
   if(!Time(wall,mono)||!reinterpret_cast<bool(__fastcall*)(const void*,Any40*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x2BA7A20))(
      reinterpret_cast<const void*>(actor),&root)||root.type!=reference)break;
   std::uint32_t kind=0;std::uint64_t id=0;std::memcpy(&kind,root.storage.data(),4);std::memcpy(&id,root.storage.data()+8,8);
   if(kind!=4||id!=actor_id)break;
   if(!ReadonlyVariableOwner(image,root.storage.data(),4,0x262F5E0,out.official_descriptor,out.variable_owner))break;bool all=true;
   for(std::size_t i=0;i<kLivingArtifactReferenceKeys267V1.size();++i){
    if(!Time(wall,mono)){all=false;break;}text={};text.type=string;
    const auto key=kLivingArtifactReferenceKeys267V1[i];const std::uint64_t cap=15;std::memcpy(text.storage.data()+24,&cap,8);
    entered=true;complete=false;
    reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x896BB0))(
       text.storage.data(),key,std::strlen(key));complete=true;
    ArgTable24 table{&text,1,1,0};Cursor16 args{&table,0,0};
    const auto ref=reinterpret_cast<std::uintptr_t(__fastcall*)(const void*,const Cursor16*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x3D26A70))(root.storage.data(),&args);
    std::array<std::byte,16>before{},after{};std::uint16_t tag=0;std::uint64_t payload=0;
    if(!ref||!Copy(ref,before.data(),16)){all=false;break;}
    std::memcpy(&tag,before.data(),2);std::memcpy(&payload,before.data()+8,8);auto&v=out.refs[i];v.scope_kind=tag;
    if(ref==image+0x4AE2008){if(before!=std::array<std::byte,16>{}){all=false;break;}v.state=LivingReferenceState267V1::absent;}
    else if(!tag)v.state=LivingReferenceState267V1::present_empty;
    else if(tag!=36)v.state=LivingReferenceState267V1::wrong_kind;
    else{if(payload>0xFFFFFFFFULL||payload==0xFFFFFFFFULL){all=false;break;}v.state=LivingReferenceState267V1::artifact;v.full_id=static_cast<std::uint32_t>(payload);}
    if(!Copy(ref,after.data(),16)||before!=after){all=false;break;}out.borrowed[i]=ref;out.raw[i]=before;
    reinterpret_cast<void(__fastcall*)(void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x897460))(text.storage.data());entered=complete=false;text={};text.type=empty;
   }std::uintptr_t owner_after=0,descriptor_after=0;good=all&&ReadonlyVariableOwner(image,root.storage.data(),4,0x262F5E0,descriptor_after,owner_after)&&owner_after==out.variable_owner&&descriptor_after==out.official_descriptor;
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){good=false;cleanup=false;}
 if(entered){if(!complete)cleanup=false;else{__try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x897460))(text.storage.data());}__except(EXCEPTION_EXECUTE_HANDLER){cleanup=false;}}}
 if(initialized){const bool clean=Destroy(image,root,empty,reference);cleanup=cleanup&&clean;}
 return good&&cleanup&&Time(wall,mono);
}
}
bool ReadLivingFixtureBindings267V1(const ReadonlyBindings&b,const LivingInventoryFrame267V1&f,
 const LivingInventoryRequest267V1&q,std::uint64_t mono,LivingFixtureBindings267V1&out,bool&cleanup,std::string&why)noexcept{
 using namespace living_inventory_private;out={};cleanup=true;
 if(!Fresh(b,f,q,mono)||!VerifyLivingInventoryImage267V1(b.module_base)){why="living_fixed_reference_binding_unavailable";return false;}
 LivingFixtureBindings267V1 a,z;bool ca=true,cz=true;
 const auto actor=std::bit_cast<std::uint32_t>(f.core.played_character_id);
 if(!ArtifactRefs(b.module_base,f.actor,actor,q.deadline_unix_ms,mono,a,ca)||!ArtifactRefs(b.module_base,f.actor,actor,q.deadline_unix_ms,mono,z,cz)){
  cleanup=ca&&cz;why=cleanup?"living_fixed_reference_read_unavailable":"living_fixed_reference_cleanup_unknown";return false;}
 if(a!=z||!Fresh(b,f,q,mono)){why="living_fixed_reference_or_Core_drift";return false;}
 out=std::move(z);out.sampled_twice=true;why.clear();return true;
}
}

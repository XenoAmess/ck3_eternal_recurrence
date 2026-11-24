// Same inventory Raw TU, after its actual fixed binding/GUI helpers.
#include "xar_bridge/ck3_121003_living_detail26785313_private_v1.hpp"
namespace xar::ck3_121003::build26785313 {namespace living_inventory_private {
bool DetailString(std::uintptr_t p,std::string&out,std::vector<std::byte>&proof){
 std::array<std::byte,32>before{},after{};std::uint64_t n=0,cap=0;std::uintptr_t data=p;
 if(!Copy(p,before.data(),32))return false;
 std::memcpy(&n,before.data()+16,8);std::memcpy(&cap,before.data()+24,8);
 if(n>16384||cap<n||(cap<=15&&cap!=15)||cap>0x10000000)return false;
 if(cap>15)std::memcpy(&data,before.data(),8);
 std::string text(static_cast<std::size_t>(n)+1,'\0');
 if(!Copy(data,text.data(),text.size())||text.back()!=0||!Copy(p,after.data(),32)||before!=after)return false;
 text.pop_back();if(n&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(n),nullptr,0)<=0)return false;
 // Snapshot bytes, never the address of a temporary owned stack CString.
 if(proof.size()>131072-sizeof(n)-text.size())return false;
 const auto offset=proof.size();proof.resize(offset+sizeof(n)+text.size());std::memcpy(proof.data()+offset,&n,sizeof(n));
 if(n)std::memcpy(proof.data()+offset+sizeof(n),text.data(),text.size());out=std::move(text);return true;
}
bool DetailStringNoThrow(std::uintptr_t p,std::string&out,std::vector<std::byte>&proof)noexcept{
 try{return DetailString(p,out,proof);}catch(...){return false;}
}
bool DetailOwnedText(std::uintptr_t image,std::uintptr_t artifact,bool custom,
 std::string&text,std::vector<std::byte>&proof,bool&cleanup)noexcept{
 alignas(void*)std::array<std::byte,32>out{},key{};const std::uint64_t cap=15;
 std::memcpy(out.data()+24,&cap,8);std::memcpy(key.data()+24,&cap,8);
 // Fixed SSO CString32 input, exact complete header, no caller Custom key.
 constexpr std::string_view literal="XalwEffects";
 const auto length=static_cast<std::uint64_t>(literal.size());
 std::memcpy(key.data(),literal.data(),literal.size());std::memcpy(key.data()+16,&length,8);
 volatile bool entered=false,returned=false;cleanup=true;bool same=false;
 __try{
  entered=true;void*result=nullptr;
  if(custom)result=reinterpret_cast<void*(__fastcall*)(void*,const void*,const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x2628B50))(
   out.data(),reinterpret_cast<const void*>(artifact),key.data());
  else result=reinterpret_cast<void*(__fastcall*)(void*,const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x2965360))(
   out.data(),reinterpret_cast<const void*>(artifact));
  same=result==out.data();returned=true;
 }__except(EXCEPTION_EXECUTE_HANDLER){cleanup=false;}
 const bool copied=returned&&same&&DetailStringNoThrow(reinterpret_cast<std::uintptr_t>(out.data()),text,proof);
 // The actual native getters own the output. On a partial entry, attempt only
 // this known output's cleanup while preserving UNKNOWN even if it returns.
 if(entered){__try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x897460))(out.data());}
  __except(EXCEPTION_EXECUTE_HANDLER){cleanup=false;}}
 if(!returned)cleanup=false;return copied&&same&&cleanup;
}
bool DetailDescription(std::uintptr_t image,std::uintptr_t artifact,
 std::string&text,std::vector<std::byte>&proof,bool&cleanup)noexcept{
 const void*borrowed=nullptr;cleanup=true;
 __try{borrowed=reinterpret_cast<const void*(__fastcall*)(const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0xC48EE0))(
  reinterpret_cast<const void*>(artifact));}__except(EXCEPTION_EXECUTE_HANDLER){cleanup=false;return false;}
 if(reinterpret_cast<std::uintptr_t>(borrowed)!=artifact+0x40)return false;
 return DetailStringNoThrow(artifact+0x40,text,proof);
 // Artifact+40 is borrowed; never destroy it.
}
struct DetailSnapshot {
 Snapshot inventory;LivingDetailData267V1 source;std::vector<std::byte>proof;
 std::uintptr_t view=0,root=0,target=0;
 friend bool operator==(const DetailSnapshot&,const DetailSnapshot&)=default;
};
bool DetailTake(const ReadonlyBindings&b,const LivingDetailFrame267V1&f,
 const LivingInventoryRequest267V1&q,std::uint64_t mono,DetailSnapshot&out,
 LivingDetailRaw267V1&state,std::string&why){
 LivingInventoryRaw267V1 inv;if(!Fresh(b,f.inventory,q,mono)||!Take(b,f.inventory,q,mono,out.inventory,inv,why)){
  state.entered|=inv.entered;state.cleanup_known&=inv.cleanup_known;return false;}
 state.entered|=inv.entered;state.cleanup_known&=inv.cleanup_known;
 const auto&ref=out.inventory.source.fixed_references[0];
 if(ref.state!=LivingReferenceState267V1::artifact||!ref.full_id)return false;
 const auto target=std::find_if(out.inventory.artifact_rows.begin(),out.inventory.artifact_rows.end(),[&](const auto&a){return a.value.full_id==*ref.full_id;});
 if(target==out.inventory.artifact_rows.end())return false;out.target=target->pointer;
 const auto&g=f.gui;std::uintptr_t actual=0,vt=0;std::uint32_t full=invalid;
 if(!f.owner_observed||!g.window_found||g.root.name!="artifact_details_view"||
  g.connection_generation!=f.inventory.connection_generation||
  !At(f.inventory.jomini,0x10,actual)||actual!=f.gfx||!At(actual,0x88,actual)||actual!=f.manager||
  !At(f.manager,0x40,actual)||actual!=f.inventory.jomini||
  !At(f.manager,0x390,out.view)||!out.view||!At(out.view,0,vt)||vt!=b.module_base+0x4C22298||
  !At(out.view,0x98,actual)||actual!=f.inventory.jomini||!At(out.view,0xA0,actual)||actual!=f.manager||
  !At(out.view,0x68,actual)||actual!=g.context||!At(out.view,0x60,out.root)||out.root!=g.root.widget||
  !At(out.view,0xC8,full)||full!=target->value.full_id||
  !WeaponProof(out.proof,f.manager+0x390,8)||!WeaponProof(out.proof,out.view+0x60,0x70))return false;
 out.source.target_full_id=full;out.source.window_found=true;
 if(!EntryLogicalVisible267V1(b.module_base,out.view,out.proof,out.source.visible))return false;
 out.source.enabled=g.root.enabled;out.source.target_bound=true;
 std::uint8_t flags=0;std::uintptr_t context=0,parent=0;
 if(!At(out.root,0xD0,flags)||flags!=g.root.flags||!At(out.root,0xD8,context)||context!=g.context||
  !At(out.root,0xE8,parent)||parent!=g.root.parent||!WeaponProof(out.proof,out.root+0xD0,0x30))return false;
 std::string modifier,custom,description;bool cleanup=true;state.entered=true;
 if(!Fresh(b,f.inventory,q,mono)||!DetailOwnedText(b.module_base,out.target,false,modifier,out.proof,cleanup)){
  state.cleanup_known&=cleanup;return false;}
 if(!Fresh(b,f.inventory,q,mono)||!DetailOwnedText(b.module_base,out.target,true,custom,out.proof,cleanup)){
  state.cleanup_known&=cleanup;return false;}
 if(!Fresh(b,f.inventory,q,mono)||!DetailDescription(b.module_base,out.target,description,out.proof,cleanup)){
  state.cleanup_known&=cleanup;return false;}
 out.source.modifier_effects_text=std::move(modifier);out.source.custom_effects_text=std::move(custom);
 out.source.description_text=std::move(description);return Fresh(b,f.inventory,q,mono);
}
}
bool ReadLivingDetailRaw267V1([[maybe_unused]]const ReadonlyBindings&b,
 [[maybe_unused]]const LivingDetailFrame267V1&f,[[maybe_unused]]const LivingInventoryRequest267V1&q,
 [[maybe_unused]]std::uint64_t mono,LivingDetailRaw267V1&out,std::string&why)noexcept{
 out={};why="living_detail_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1
 using namespace living_inventory_private;
 if(!VerifyLivingInventoryImage267V1(b.module_base)||!Fresh(b,f.inventory,q,mono))return false;
 try{DetailSnapshot a,z;
  if(!DetailTake(b,f,q,mono,a,out,why)||!DetailTake(b,f,q,mono,z,out,why))return false;
  if(a!=z){why="living_complete_Artifact_bound_detail_drift";return false;}
  out.source=std::move(z.source);out.fingerprint=std::move(z.proof);why.clear();return true;
 }catch(...){out.source={};out.fingerprint.clear();why="living_detail_bounded_copy_unavailable";return false;}
#else
 return false;
#endif
}
}

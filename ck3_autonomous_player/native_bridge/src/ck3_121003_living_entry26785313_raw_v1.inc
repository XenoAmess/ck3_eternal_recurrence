// Append once after the sealed Living Raw includes in its actual single TU.
// Does not replace the c661 inventory/query/UI13 implementation.
#include "xar_bridge/ck3_121003_living_entry26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_entry26785313_pins_v1.hpp"
namespace xar::ck3_121003::build26785313 {namespace living_inventory_private {
#include "ck3_121003_living_entry_visibility26785313_private_v1.inc"

bool EntryGuiProof(const LivingWeaponFrame267V1&f,std::uintptr_t image,
 std::vector<std::byte>&proof,bool&blocked){
 const auto&g=f.gui;std::uintptr_t p=0,vt=0;
 if(!f.owner_observed||!g.application||!g.first||!g.context||!g.global_root||
  g.connection_generation!=f.inventory.connection_generation||
  !At(f.inventory.jomini,0x10,p)||p!=f.gfx||!At(p,0,vt)||vt!=image+0x4B24748||
  !At(p,0x20,p)||p!=f.inventory.jomini||!At(f.gfx,0x88,p)||p!=f.manager||
  !At(p,0,vt)||vt!=image+0x4B22578||!At(f.manager,0x40,p)||p!=f.inventory.jomini||
  !At(f.inventory.jomini,0x18,p)||p!=g.application||!At(g.application,0x1B8,p)||p!=g.first||
  !At(g.first,0x58,p)||p!=g.context||!At(g.context,0xD0,p)||p!=g.global_root)return false;
 std::size_t matches=0;
 for(const auto&node:g.tree){
  std::uint8_t flags=0;std::uintptr_t ctx=0,parent=0,children=0;std::int32_t cap=0,count=0;
  if(!At(node.widget,0,vt)||vt!=node.vtable||!At(node.widget,0xD0,flags)||flags!=node.flags||
   (flags&1)||!At(node.widget,0xD8,ctx)||ctx!=g.context||!At(node.widget,0xE8,parent)||parent!=node.parent||
   !At(node.widget,0xF0,children)||children!=node.children||!At(node.widget,0xF8,cap)||cap!=node.child_capacity||
   !At(node.widget,0xFC,count)||count!=node.child_count||!WeaponProof(proof,node.widget+0xD0,0x30))return false;
  String32 name;
  if(!String(node.widget+0x1B8,name)||name.value!=node.name||
   !WeaponProof(proof,node.widget+0x1B8,32)||!WeaponProof(proof,node.name_data,static_cast<std::size_t>(node.name_size)+1)||
   (count&&!WeaponProof(proof,children,static_cast<std::size_t>(count)*8)))return false;
  if(node.name==g.requested_name){++matches;if(!g.window_found||node.widget!=g.root.widget)return false;}
 }
 if(matches!=(g.window_found?1U:0U))return false;
 Array16 modal;blocked=false;
 if(!At(g.context,0x298,modal)||!Array(modal,64,8)||!WeaponProof(proof,g.context+0x298,16))return false;
 for(std::int32_t n=0;n<modal.count;++n){std::uint8_t flags=0;
  if(!At(modal.data,static_cast<std::size_t>(n)*8,p)||!p||!At(p,0xD0,flags)||
   !WeaponProof(proof,modal.data+static_cast<std::size_t>(n)*8,8)||!WeaponProof(proof,p+0xD0,1))return false;
  blocked|=(flags&8)==0;
 }
 return true;
}

struct EntryViewSnapshot {
 std::vector<std::byte>proof;
 std::uintptr_t manager=0,view=0,root=0;
 LivingEntryViewData267V1 source;
 friend bool operator==(const EntryViewSnapshot&,const EntryViewSnapshot&)=default;
};
bool EntryViewTake(const ReadonlyBindings&b,const LivingWeaponFrame267V1&f,
 bool detail,std::uint32_t payload,EntryViewSnapshot&out){
 const auto image=b.module_base;out.manager=f.manager;out.source.expected_payload_full_id=payload;
 if(!EntryGuiProof(f,image,out.proof,out.source.blocked_by_visible_modal))return false;
 const auto slot=detail?0x390U:0x378U;const auto type=detail?0x4C22298U:0x4C213B0U;
 std::uintptr_t p=0,vt=0;
 if(!At(f.manager,slot,out.view)||!WeaponProof(out.proof,f.manager+slot,8))return false;
 if(!out.view){if(f.gui.window_found)return false;}
 else{
  if(!At(out.view,0,vt)||vt!=image+type||!At(out.view,0x98,p)||p!=f.inventory.jomini||
   !At(out.view,0xA0,p)||p!=f.manager||!At(out.view,0x68,p)||p!=f.gui.context||
   !At(out.view,0x60,out.root)||!WeaponProof(out.proof,out.view+0x60,0x70))return false;
  if(!out.root){if(f.gui.window_found)return false;}
  else{
   if(!f.gui.window_found||out.root!=f.gui.root.widget||
    f.gui.root.name!=(detail?"artifact_details_view":"inventory_view")||
    !EntryLogicalVisible267V1(image,out.view,out.proof,out.source.visible))return false;
   std::uint32_t actual=invalid;if(!At(out.view,0xC8,actual))return false;
   out.source.window_found=true;out.source.enabled=f.gui.root.enabled;
   out.source.payload_bound=actual==payload;
  }
 }
 out.source.open_admissible=!out.source.visible&&!out.source.blocked_by_visible_modal;
 return true;
}

LivingEntryCall267V1 EntryOpenNative(const ReadonlyBindings&b,const LivingInventoryFrame267V1&f,
 const LivingEntryRequest267V1&q,std::uint64_t mono,bool detail,std::uint32_t payload)noexcept{
 LivingEntryCall267V1 out;const auto image=b.module_base;
 std::array<Any40,2>args{};alignas(void*)std::array<std::byte,32>key{};
 const std::uint64_t cap=15;std::memcpy(key.data()+24,&cap,8);
 std::uintptr_t empty=0,text=0,u32=0;bool initialized=false;
 volatile bool keyEntered=false,keyComplete=false,firstEntered=false,firstComplete=false;
 volatile bool secondEntered=false,secondComplete=false,effectEntered=false,returned=false;
 __try{
  using Factory=std::uintptr_t(__fastcall*)();
  empty=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8B2EF0))();
  text=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8C21D0))();
  u32=reinterpret_cast<Factory>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0xA6C100))();
  args[0].type=args[1].type=empty;initialized=true;
  const char*name=detail?"artifact_details":"inventory";
  keyEntered=true;
  reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x896BB0))(key.data(),name,std::strlen(name));
  keyComplete=true;
  using CopyAny=void(__fastcall*)(Any40*,const void*,void*);
  firstEntered=true;reinterpret_cast<CopyAny>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8B4960))(&args[0],key.data(),reinterpret_cast<void*>(text));firstComplete=true;
  secondEntered=true;reinterpret_cast<CopyAny>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x8B4960))(&args[1],&payload,reinterpret_cast<void*>(u32));secondComplete=true;
  std::uint32_t actual=invalid;std::memcpy(&actual,args[1].storage.data(),4);
  if(args[0].type==text&&args[1].type==u32&&actual==payload&&Fresh(b,f,q,mono)){
   ArgTable24 table{args.data(),2,2,0};Cursor16 cursor{&table,0,0};effectEntered=true;
   // Official OpenGameViewData, not Toggle. Its bool is routing DATA, not a postcondition.
   (void)reinterpret_cast<bool(__fastcall*)(void*,void*,const Cursor16*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0xBC1C40))(nullptr,nullptr,&cursor);
   returned=true;
  }
 }__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}
 out.entered=effectEntered;out.native_returned=returned;
 if(keyEntered){if(!keyComplete)out.cleanup_known=false;
  __try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x897460))(key.data());}
  __except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}}
 if(initialized){
  if(firstEntered&&!firstComplete)out.cleanup_known=false;
  else if(!Destroy(image,args[0],empty,text))out.cleanup_known=false;
  if(secondEntered&&!secondComplete)out.cleanup_known=false;
  else if(!Destroy(image,args[1],empty,u32))out.cleanup_known=false;
 }
 if(effectEntered&&!returned)out.cleanup_known=false;
 if(returned&&!Fresh(b,f,q,mono))out.cleanup_known=false;
 return out;
}
}

bool VerifyLivingEntryImage267V1(std::uintptr_t image)noexcept{
 if(!VerifyLivingInventoryImage267V1(image))return false;
 for(const auto&pin:living_entry_pins::kCode){
  if(pin.hex.size()%2||pin.hex.empty()||pin.hex.size()>8192||pin.rva>kImageSize-pin.hex.size()/2)return false;
  std::array<unsigned char,4096>sample{};
  if(!living_inventory_private::Copy(image+pin.rva,sample.data(),pin.hex.size()/2))return false;
  const auto hex=[](char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
  for(std::size_t n=0;n<pin.hex.size()/2;++n){const auto a=hex(pin.hex[n*2]),z=hex(pin.hex[n*2+1]);
   if(a<0||z<0||sample[n]!=static_cast<unsigned char>((a<<4)|z))return false;}
 }
 for(const auto&p:living_entry_pins::kPointers){std::uintptr_t actual=0;
  if(!living_inventory_private::At(image,p.slot,actual)||actual!=image+p.target)return false;}
 return true;
}
struct LivingEntryRaw267V1::State {
 living_inventory_private::Snapshot inventory;
 std::optional<living_inventory_private::EntryViewSnapshot>view;
 std::optional<LivingManageRaw267V1>manage;
 LivingEntrySource267V1 source;
 friend bool operator==(const State&,const State&)=default;
};
bool SameLivingEntryRaw267V1(const LivingEntryRaw267V1&a,const LivingEntryRaw267V1&z)noexcept{
 try{return a.cleanup_known&&z.cleanup_known&&a.state_&&z.state_&&a.source==z.source&&
  a.inventory==z.inventory&&*a.state_==*z.state_;}catch(...){return false;}
}
bool ReadLivingEntryRaw267V1(const ReadonlyBindings&b,const LivingEntryFrame267V1&f,
 const LivingEntryRequest267V1&q,std::uint64_t mono,LivingEntryRaw267V1&out,std::string&why)noexcept{
 out={};why="living_entry_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1
 using namespace living_inventory_private;
 try{
  if(!Fresh(b,f.inventory,q,mono)||!VerifyLivingEntryImage267V1(b.module_base))return false;
  const auto take=[&](LivingEntryRaw267V1::State&state){
   LivingInventoryRaw267V1 inv;
   if(!Take(b,f.inventory,q,mono,state.inventory,inv,why)){out.entered|=inv.entered;out.cleanup_known&=inv.cleanup_known;return false;}
   out.entered|=inv.entered;out.cleanup_known&=inv.cleanup_known;
   const auto&ref=state.inventory.source.fixed_references[0];
   if(ref.state!=LivingReferenceState267V1::artifact||!ref.full_id)return false;
   const auto target=std::find_if(state.inventory.source.artifacts.begin(),state.inventory.source.artifacts.end(),[&](const auto&a){return a.full_id==*ref.full_id;});
   if(target==state.inventory.source.artifacts.end()||target->owner_full_id!=state.inventory.source.actor_full_id)return false;
   auto&s=state.source;s.actor_full_id=state.inventory.source.actor_full_id;s.kind=LivingEntryKindFor267V1(q.action);s.sampled_twice=true;
   if(s.kind==LivingEntryKind267V1::manage){
    if(!f.manage||!f.manage->facts_verified||!Same(f.manage->core,f.inventory.core))return false;
    auto scene=f.manage->scene;scene.owner_bound=true;state.manage.emplace();
    const bool good=ReadLivingManageRaw267V1(b,f.inventory.core,scene,mono,*state.manage,why);
    out.entered|=state.manage->native_read_entered;out.cleanup_known&=state.manage->cleanup_known;
    if(!good)return false;s.manage=state.manage->source;return true;
   }
   if(!f.view)return false;state.view.emplace();
   const bool detail=s.kind==LivingEntryKind267V1::detail;
   const auto payload=detail?*ref.full_id:s.actor_full_id;
   if(!EntryViewTake(b,*f.view,detail,payload,*state.view))return false;
   if(detail)s.detail=state.view->source;else s.inventory=state.view->source;
   return true;
  };
  auto a=std::make_shared<LivingEntryRaw267V1::State>(),z=std::make_shared<LivingEntryRaw267V1::State>();
  if(!take(*a)||!take(*z)||*a!=*z||!Fresh(b,f.inventory,q,mono)||!LivingEntrySourceShape267V1(z->source,f.inventory.core))return false;
  out.source=z->source;out.inventory=z->inventory.source;
  out.inventory.complete_inventory=out.inventory.sampled_twice=true;out.state_=std::move(z);why.clear();return true;
 }catch(...){why="living_entry_complete_source_copy_unavailable";return false;}
#else
 (void)b;(void)f;(void)q;(void)mono;return false;
#endif
}
struct LivingEntryCallAccess267V1 {
 static LivingEntryCall267V1 Submit(const ReadonlyBindings&b,const LivingEntryFrame267V1&f,
  const LivingEntryRequest267V1&q,std::uint64_t mono,const LivingEntryRaw267V1&issued)noexcept{
  using A=LivingEntryAction267V1;LivingEntryCall267V1 out;
  try{
   LivingEntryRaw267V1 actual;std::string why;
   if(!ReadLivingEntryRaw267V1(b,f,q,mono,actual,why)||!SameLivingEntryRaw267V1(actual,issued)){
    out.cleanup_known=actual.cleanup_known;return out;}
   if(q.action==A::open_inventory||q.action==A::open_detail){
    const auto&v=actual.state_->view;
    if(!v||!v->source.open_admissible)return out;
    return living_inventory_private::EntryOpenNative(b,f.inventory,q,mono,q.action==A::open_detail,v->source.expected_payload_full_id);
   }
   if(!actual.state_->manage||!f.manage)return out;
   auto scene=f.manage->scene;scene.owner_bound=true;LivingManageAction267V1 action;std::optional<LivingManage267V1>key;
   if(q.action==A::open_manage_list)action=LivingManageAction267V1::open_list;
   else if(q.action==A::open_manage_detail){action=LivingManageAction267V1::open_detail;key=LivingManage267V1::manage;}
   else if(q.action==A::confirm_manage){action=LivingManageAction267V1::confirm;key=LivingManage267V1::manage;}
   else return out;
   const auto call=CallLivingManageRaw267V1(b,f.inventory.core,scene,mono,*actual.state_->manage,action,key);
   return {call.effect_entered,call.status==LivingManageRawCallStatus267V1::returned,call.cleanup_known};
  }catch(...){out.cleanup_known=false;return out;}
 }
};
LivingEntryCall267V1 CallLivingEntryRaw267V1(const ReadonlyBindings&b,const LivingEntryFrame267V1&f,
 const LivingEntryRequest267V1&q,std::uint64_t mono,const LivingEntryRaw267V1&issued)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1
 return LivingEntryCallAccess267V1::Submit(b,f,q,mono,issued);
#else
 (void)b;(void)f;(void)q;(void)mono;(void)issued;return {};
#endif
}
}

// Included after the actual inventory and fixed-reference helpers, one Raw TU.
#include "xar_bridge/ck3_121003_living_weapon26785313_private_v1.hpp"
#include <mutex>
#include <atomic>
namespace xar::ck3_121003::build26785313 {namespace living_inventory_private {
bool EntryLogicalVisible267V1(std::uintptr_t,std::uintptr_t,std::vector<std::byte>&,bool&);
struct WeaponSnapshot {
 Snapshot inventory;
 LivingFixtureBindings267V1 references;
 std::vector<std::byte>ui;
 std::uintptr_t view=0,root=0,target=0,slot=0,selected=0;
 std::uint32_t target_id=invalid;
 bool available=false,compatible=false,logical_visible=false;
 friend bool operator==(const WeaponSnapshot&,const WeaponSnapshot&)=default;
};
bool WeaponProof(std::vector<std::byte>&out,std::uintptr_t p,std::size_t n){
 if(n>131072||out.size()>131072-n)return false;
 const auto at=out.size();out.resize(at+n);return !n||Copy(p,out.data()+at,n);
}
bool WeaponGui(const ReadonlyBindings&b,const LivingWeaponFrame267V1&f,
 WeaponSnapshot&out){
 const auto image=b.module_base;const auto&g=f.gui;std::uintptr_t gfx=0,manager=0,back=0,vt=0;
 if(!f.owner_observed||!f.inventory.facts_verified||g.connection_generation!=f.inventory.connection_generation||
  !g.application||!g.first||!g.context||!g.global_root||!g.window_found||
  !At(f.inventory.jomini,0x10,gfx)||gfx!=f.gfx||!At(gfx,0,vt)||vt!=image+0x4B24748||
  !At(gfx,0x20,back)||back!=f.inventory.jomini||!At(gfx,0x88,manager)||manager!=f.manager||
  !At(manager,0,vt)||vt!=image+0x4B22578||!At(manager,0x40,back)||back!=f.inventory.jomini||
  !At(f.inventory.jomini,0x18,back)||back!=g.application||!At(g.application,0x1B8,back)||back!=g.first||
  !At(g.first,0x58,back)||back!=g.context||!At(g.context,0xD0,back)||back!=g.global_root||
  !At(manager,0x378,out.view)||!out.view||!At(out.view,0,vt)||vt!=image+0x4C213B0||
  !At(out.view,0x98,back)||back!=f.inventory.jomini||!At(out.view,0xA0,back)||back!=manager||
  !At(out.view,0x68,back)||back!=g.context||!At(out.view,0x60,out.root)||out.root!=g.root.widget||
  g.root.name!="inventory_view"||!g.root.enabled)return false;
 std::uint32_t actor=invalid;std::size_t matches=0;
 if(!At(out.view,0xC8,actor)||actor!=out.inventory.source.actor_full_id||
  !At(out.view,0x2D0,out.selected))return false;
 // Each complete captured parent/children header and each root identity remain
 // unchanged. Hidden siblings are included; a duplicate matching name rejects.
 for(const auto&node:g.tree){
  std::uint8_t flags=0;std::uintptr_t context=0,parent=0,children=0;std::int32_t cap=0,count=0;
  if(!At(node.widget,0,vt)||vt!=node.vtable||!At(node.widget,0xD0,flags)||flags!=node.flags||
   (flags&1)||!At(node.widget,0xD8,context)||context!=g.context||
   !At(node.widget,0xE8,parent)||parent!=node.parent||
   !At(node.widget,0xF0,children)||children!=node.children||
   !At(node.widget,0xF8,cap)||cap!=node.child_capacity||
   !At(node.widget,0xFC,count)||count!=node.child_count||
   !WeaponProof(out.ui,node.widget+0xD0,0x30))return false;
  String32 name;
  if(!String(node.widget+0x1B8,name)||name.value!=node.name||
   !WeaponProof(out.ui,node.widget+0x1B8,32)||
   !WeaponProof(out.ui,node.name_data,static_cast<std::size_t>(node.name_size)+1)||
   (node.child_count&&!WeaponProof(out.ui,node.children,static_cast<std::size_t>(node.child_count)*8)))return false;
  if(node.name=="inventory_view"){++matches;if(node.widget!=out.root)return false;}
 }
 // Reuse the existing current modal-array shape; a visible unrelated modal is
 // a real blocker, not permission inferred from the inventory being visible.
 Array16 modal;
 if(matches!=1||!At(g.context,0x298,modal)||!Array(modal,64,8)||
  !WeaponProof(out.ui,g.context+0x298,16))return false;
 for(std::int32_t n=0;n<modal.count;++n){std::uintptr_t p=0;std::uint8_t flags=0;
  if(!At(modal.data,static_cast<std::size_t>(n)*8,p)||!p||!At(p,0xD0,flags)||
   !(flags&8)||!WeaponProof(out.ui,modal.data+static_cast<std::size_t>(n)*8,8)||
   !WeaponProof(out.ui,p+0xD0,1))return false;
 }
 return EntryLogicalVisible267V1(image,out.view,out.ui,out.logical_visible)&&out.logical_visible&&
  WeaponProof(out.ui,manager+0x378,8)&&WeaponProof(out.ui,out.view+0x60,0x70)&&
  WeaponProof(out.ui,out.view+0x2D0,8);
}
bool WeaponPredicates(std::uintptr_t image,const WeaponSnapshot&x,bool&available,bool&compatible)noexcept{
 __try{
  available=reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x180E460))(
   reinterpret_cast<const void*>(x.view),reinterpret_cast<const void*>(x.slot));
  compatible=reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x26C7C40))(
   reinterpret_cast<const void*>(x.slot),reinterpret_cast<const void*>(x.target));return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool TakeWeapon(const ReadonlyBindings&b,const LivingWeaponFrame267V1&f,
 const LivingInventoryRequest267V1&q,std::uint64_t mono,WeaponSnapshot&out,
 bool&cleanup,std::string&why){
 LivingInventoryRaw267V1 state;
 if(!Fresh(b,f.inventory,q,mono)||!Take(b,f.inventory,q,mono,out.inventory,state,why)){
  cleanup&=state.cleanup_known;return false;}
 bool references_clean=true;
 if(!ArtifactRefs(b.module_base,f.inventory.actor,out.inventory.source.actor_full_id,
  q.deadline_unix_ms,mono,out.references,references_clean)){
  cleanup&=references_clean;why="living_private_target_reference_unavailable";return false;}
 const auto&ref=out.references.refs[0];
 if(ref.state!=LivingReferenceState267V1::artifact||!ref.full_id){why="living_fixture_target_not_actual_Artifact_ref";return false;}
 const auto target=std::find_if(out.inventory.artifact_rows.begin(),out.inventory.artifact_rows.end(),
  [&](const auto&a){return a.value.full_id==*ref.full_id;});
 if(target==out.inventory.artifact_rows.end()||!out.inventory.source.weapon_slot){why="living_target_or_weapon_outside_owned_complete_census";return false;}
 out.target=target->pointer;out.target_id=target->value.full_id;
 out.slot=out.inventory.slot_rows[*out.inventory.source.weapon_slot].pointer;
 if(!WeaponGui(b,f,out)){why="living_owned_inventory_view_or_modal_unavailable";return false;}
 if(!WeaponPredicates(b.module_base,out,out.available,out.compatible)){
  cleanup=false;why="living_weapon_native_predicate_cleanup_unknown";return false;}
 return Fresh(b,f.inventory,q,mono);
}
bool WeaponAdmissible(const WeaponSnapshot&x,LivingWeaponAction267V1 action){
 const auto target=std::find_if(x.inventory.artifact_rows.begin(),x.inventory.artifact_rows.end(),
  [&](const auto&a){return a.pointer==x.target&&a.value.full_id==x.target_id;});
 if(target==x.inventory.artifact_rows.end())return false;
 const auto&slot=x.inventory.slot_rows[*x.inventory.source.weapon_slot].value;
 switch(action){
  case LivingWeaponAction267V1::select_weapon:return x.available&&x.compatible&&x.selected!=x.slot&&!target->value.equipped;
  case LivingWeaponAction267V1::equip_target:return x.available&&x.compatible&&x.selected==x.slot&&!target->value.equipped;
  case LivingWeaponAction267V1::unequip_target:return target->value.equipped&&slot.artifact_full_id==x.target_id;
 }return false;
}
LivingWeaponCall267V1 WeaponNative(std::uintptr_t image,const WeaponSnapshot&x,LivingWeaponAction267V1 action)noexcept{
 LivingWeaponCall267V1 out;
 if(action!=LivingWeaponAction267V1::select_weapon&&action!=LivingWeaponAction267V1::equip_target&&
  action!=LivingWeaponAction267V1::unequip_target)return out;
 volatile bool entered=false,returned=false;
 __try{
  entered=true;
  if(action==LivingWeaponAction267V1::select_weapon)
   reinterpret_cast<void(__fastcall*)(void*,const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x180F000))(
    reinterpret_cast<void*>(x.view),reinterpret_cast<const void*>(x.slot));
  else if(action==LivingWeaponAction267V1::equip_target)
   reinterpret_cast<void(__fastcall*)(void*,const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x180E0C0))(
    reinterpret_cast<void*>(x.view),reinterpret_cast<const void*>(x.target));
  else if(action==LivingWeaponAction267V1::unequip_target)
   reinterpret_cast<void(__fastcall*)(void*,const void*)>(XAR_LIVING_INVENTORY_CALL_ADDRESS(image,0x180EDE0))(
    reinterpret_cast<void*>(x.view),reinterpret_cast<const void*>(x.target));
  returned=true;
 }__except(EXCEPTION_EXECUTE_HANDLER){}
 out.entered=entered;out.native_returned=returned;
 out.cleanup_known=returned;out.status=returned?LivingWeaponCallStatus267V1::returned:LivingWeaponCallStatus267V1::indeterminate;
 return out;
}
}
struct LivingWeaponPrivateSession267V1::State {
 std::mutex mutex;std::atomic_bool unknown{false};std::uint64_t claim=0,connection=0;
 std::uintptr_t game=0,jomini=0;std::uint32_t actor=0xFFFFFFFFU;bool owner_bound=false;
 std::array<bool,3>effect_spent{};
};
struct LivingWeaponLease267V1::State {
 std::shared_ptr<LivingWeaponPrivateSession267V1::State>issuer;
 ReadonlyBindings bindings;LivingWeaponFrame267V1 frame;LivingInventoryRequest267V1 request;
 living_inventory_private::WeaponSnapshot before;
 std::uint64_t original_mono=0,claim=0;LivingWeaponAction267V1 action=LivingWeaponAction267V1::select_weapon;
 bool spent=false;
};
LivingWeaponPrivateSession267V1::LivingWeaponPrivateSession267V1():state_(std::make_shared<State>()){}
LivingWeaponPrivateSession267V1::~LivingWeaponPrivateSession267V1()=default;
bool LivingWeaponSessionUnknown267V1(const LivingWeaponPrivateSession267V1&s)noexcept{return s.state_->unknown.load(std::memory_order_acquire);}
bool PrepareLivingWeapon267V1([[maybe_unused]]LivingWeaponPrivateSession267V1&session,
 [[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const LivingWeaponFrame267V1&f,
 [[maybe_unused]]const LivingInventoryRequest267V1&q,[[maybe_unused]]std::uint64_t mono,
 [[maybe_unused]]LivingWeaponAction267V1 action,LivingWeaponLease267V1&out,std::string&why)noexcept{
 out={};why="living_weapon_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1
 using namespace living_inventory_private;
 try{
  std::scoped_lock lock(session.state_->mutex);
  if(session.state_->unknown||!Fresh(b,f.inventory,q,mono)||!VerifyLivingInventoryImage267V1(b.module_base))return false;
  auto&issuer=*session.state_;
  const auto action_index=static_cast<unsigned>(action);
  if(action_index>=issuer.effect_spent.size()||issuer.effect_spent[action_index])return false;
  const auto actual_actor=std::bit_cast<std::uint32_t>(f.inventory.core.played_character_id);
  if(issuer.owner_bound&&(issuer.connection!=f.inventory.connection_generation||issuer.game!=f.inventory.game||
   issuer.jomini!=f.inventory.jomini||issuer.actor!=actual_actor))return false;
  WeaponSnapshot a,z;bool cleanup=true;
  if(!TakeWeapon(b,f,q,mono,a,cleanup,why)||!TakeWeapon(b,f,q,mono,z,cleanup,why)){
   if(!cleanup)session.state_->unknown=true;return false;}
  if(a!=z||!WeaponAdmissible(z,action)){why="living_weapon_actual_source_drift_or_not_admissible";return false;}
  issuer.owner_bound=true;issuer.connection=f.inventory.connection_generation;issuer.game=f.inventory.game;
  issuer.jomini=f.inventory.jomini;issuer.actor=actual_actor;
  if(session.state_->claim==(std::numeric_limits<std::uint64_t>::max)())return false;
  auto lease=std::make_shared<LivingWeaponLease267V1::State>();lease->issuer=session.state_;
  lease->bindings=b;lease->frame=f;lease->request=q;lease->before=std::move(z);lease->original_mono=mono;
  lease->action=action;lease->claim=++session.state_->claim;out.state_=std::move(lease);why.clear();return true;
 }catch(...){why="living_weapon_private_preparation_copy_unavailable";return false;}
#else
 return false;
#endif
}
LivingWeaponCall267V1 SubmitLivingWeapon267V1([[maybe_unused]]LivingWeaponLease267V1&lease)noexcept{
 LivingWeaponCall267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1
 using namespace living_inventory_private;
 try{
  if(!lease.state_)return out;auto&x=*lease.state_;std::scoped_lock lock(x.issuer->mutex);
  const auto action_index=static_cast<unsigned>(x.action);
  if(x.spent||x.issuer->unknown||x.claim!=x.issuer->claim||
   action_index>=x.issuer->effect_spent.size()||x.issuer->effect_spent[action_index]||
   !Fresh(x.bindings,x.frame.inventory,x.request,x.original_mono))return out;
  WeaponSnapshot now;bool cleanup=true;std::string why;
  if(!TakeWeapon(x.bindings,x.frame,x.request,x.original_mono,now,cleanup,why)){
   if(!cleanup){x.issuer->unknown=true;out.cleanup_known=false;out.status=LivingWeaponCallStatus267V1::indeterminate;}return out;}
  if(now!=x.before||!WeaponAdmissible(now,x.action)||!Fresh(x.bindings,x.frame.inventory,x.request,x.original_mono))return out;
  x.spent=true;x.issuer->effect_spent[action_index]=true;
  out=WeaponNative(x.bindings.module_base,now,x.action);
  if(!out.cleanup_known||!Time(x.request.deadline_unix_ms,x.original_mono)){
   x.issuer->unknown=true;out.status=LivingWeaponCallStatus267V1::indeterminate;out.cleanup_known=false;}
  return out;
 }catch(...){if(lease.state_)lease.state_->issuer->unknown=true;out.status=LivingWeaponCallStatus267V1::indeterminate;out.cleanup_known=false;return out;}
#else
 return out;
#endif
}
}

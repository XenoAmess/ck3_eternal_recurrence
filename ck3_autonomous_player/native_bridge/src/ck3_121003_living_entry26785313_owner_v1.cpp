#include "xar_bridge/ck3_121003_living_entry26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_gui_identity26785313_private_v1.hpp"
#include <algorithm>
#include <chrono>
#include <limits>
#include <mutex>
#include <unordered_set>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
#ifndef XAR_LIVING_ENTRY_READ_CURRENT_RAW
#define XAR_LIVING_ENTRY_READ_CURRENT_RAW ReadLivingEntryRaw267V1
#endif
void AppendLivingEntryRawDifference267V1(const LivingEntryRaw267V1&,const LivingEntryRaw267V1&,std::string&)noexcept;
bool SameLivingEntryManageNavigationLease267V1(const LivingEntryRaw267V1&,const LivingManageFrame267V1&,const LivingEntryRaw267V1&,const LivingManageFrame267V1&,bool&)noexcept;
namespace {
using A=LivingEntryAction267V1;using Status=LivingEntryStatus267V1;
[[maybe_unused]]std::uint64_t Wall(){const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const LivingEntryContext267V1&q){const auto wall=Wall();return wall&&wall<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Core(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&z){
 return a.clock.date_raw==z.clock.date_raw&&a.clock.speed==z.clock.speed&&a.clock.paused==z.clock.paused&&
  a.local_player_id==z.local_player_id&&a.map_ready==z.map_ready&&a.has_played_character==z.has_played_character&&
  a.played_character_id==z.played_character_id&&a.played_character_alive==z.played_character_alive;
}
[[maybe_unused]]bool World(const LivingInventoryFrame267V1&a,const LivingInventoryFrame267V1&z){
 return a.facts_verified&&z.facts_verified&&Core(a.core,z.core)&&a.game==z.game&&a.jomini==z.jomini&&
  a.actor==z.actor&&a.character_storage==z.character_storage&&a.data==z.data&&a.players==z.players&&
  a.player==z.player&&a.connection_generation==z.connection_generation;
}
[[maybe_unused]]bool Frame(const LivingEntryFrame267V1&a,const LivingEntryFrame267V1&z){
 if(!World(a.inventory,z.inventory)||a.manage.has_value()!=z.manage.has_value()||a.view.has_value()!=z.view.has_value())return false;
 if(a.manage&&(!a.manage->facts_verified||!z.manage->facts_verified||!Core(a.manage->core,z.manage->core)||
  a.manage->scene!=z.manage->scene||a.manage->witness!=z.manage->witness))return false;
 if(a.view){const auto&x=*a.view;const auto&y=*z.view;
  if(!x.owner_observed||!y.owner_observed||x.gfx!=y.gfx||x.manager!=y.manager||
   !SameLivingGuiIdentity267V1(x.gui,y.gui))return false;
 }

 return true;
}
// Stable action-owned leaves, evaluated only from complete captured copies.
[[maybe_unused]]const GuiWindowNodeV1* EntryUniqueNode(const std::vector<GuiWindowNodeV1>&v,std::uintptr_t id){
 const GuiWindowNodeV1*out=nullptr;for(const auto&n:v)if(n.widget==id){if(out)return nullptr;out=&n;}return out;
}
[[maybe_unused]]const GuiWindowNodeV1* EntryUniqueNamed(const std::vector<GuiWindowNodeV1>&v,std::string_view name,std::uintptr_t parent,bool restrict_parent){
 const GuiWindowNodeV1*out=nullptr;for(const auto&n:v)if(n.name==name&&(!restrict_parent||n.parent==parent)){if(out)return nullptr;out=&n;}return out;
}
[[maybe_unused]]bool EntryStableNode(const GuiWindowNodeV1&a,const GuiWindowNodeV1&z){
 return a.widget&&a.widget==z.widget&&a.vtable==z.vtable&&a.parent==z.parent&&a.context==z.context&&
  a.name==z.name&&a.flags==z.flags&&a.visible==z.visible&&a.enabled==z.enabled;
}
[[maybe_unused]]bool EntrySceneScalars(const LivingManageScene267V1&a,const LivingManageScene267V1&z){
 return a.connection_generation==z.connection_generation&&a.wall_deadline==z.wall_deadline&&
  a.jomini==z.jomini&&a.gfx==z.gfx&&a.handler==z.handler&&a.context==z.context&&a.global==z.global&&
  a.list_root==z.list_root&&a.detail_root==z.detail_root&&a.list_visible==z.list_visible&&
  a.list_enabled==z.list_enabled&&a.detail_visible==z.detail_visible&&a.detail_enabled==z.detail_enabled&&a.owner_bound==z.owner_bound;
}
[[maybe_unused]]bool EntryNavigationProjection(const LivingManageFrame267V1&a,const LivingManageFrame267V1&z,std::uintptr_t nav){
 if(!nav||!a.facts_verified||!z.facts_verified||!Core(a.core,z.core)||!EntrySceneScalars(a.scene,z.scene)||
  a.witness.empty()||z.witness.empty()||a.witness.size()>4096||z.witness.size()>4096||
  a.scene.hud.empty()||z.scene.hud.empty()||a.scene.hud.size()>4096||z.scene.hud.size()>4096)return false;
 const auto&b=a.scene;const auto&c=z.scene;
 const auto global_b=EntryUniqueNode(a.witness,b.global),global_a=EntryUniqueNode(z.witness,c.global);
 if(!global_b||!global_a||global_b->parent||global_a->parent||global_b->context!=b.context||global_a->context!=c.context||!EntryStableNode(*global_b,*global_a))return false;
 const GuiWindowNodeV1*layers_b[3]{},*layers_a[3]{};
 constexpr const char*names[]{"windows_layer","middle","hud_layer"};
 for(std::size_t n=0;n<3;++n){layers_b[n]=EntryUniqueNamed(a.witness,names[n],b.global,true);layers_a[n]=EntryUniqueNamed(z.witness,names[n],c.global,true);
  if(!layers_b[n]||!layers_a[n]||layers_b[n]->context!=b.context||layers_a[n]->context!=c.context||!EntryStableNode(*layers_b[n],*layers_a[n]))return false;}
 const std::uintptr_t roots_b[]{b.list_root,b.detail_root},roots_a[]{c.list_root,c.detail_root};
 constexpr const char*root_names[]{"decisions_view","decisiondetail_view"};
 for(std::size_t n=0;n<2;++n){const auto x=EntryUniqueNamed(a.witness,root_names[n],layers_b[n]->widget,true),y=EntryUniqueNamed(z.witness,root_names[n],layers_a[n]->widget,true);
  if(roots_b[n]!=roots_a[n]||bool(x)!=bool(roots_b[n])||bool(y)!=bool(roots_a[n]))return false;
  if(x&&(!y||x->widget!=roots_b[n]||y->widget!=roots_a[n]||x->context!=b.context||y->context!=c.context||!EntryStableNode(*x,*y)))return false;}
 const auto tab_b=EntryUniqueNamed(b.hud,"tab_decisions",0,false),tab_a=EntryUniqueNamed(c.hud,"tab_decisions",0,false);
 if(!tab_b||!tab_a||!EntryStableNode(*tab_b,*tab_a)||nav==tab_b->widget)return false;
 std::unordered_set<std::uintptr_t>seen;bool tab=false;std::uintptr_t current=nav;
 for(std::size_t depth=0;depth<=32;++depth){
  if(!seen.insert(current).second)return false;
  const auto x=EntryUniqueNode(b.hud,current),y=EntryUniqueNode(c.hud,current);
  if(!x||!y||x->context!=b.context||y->context!=c.context||!EntryStableNode(*x,*y))return false;
  const auto wx=EntryUniqueNode(a.witness,current),wy=EntryUniqueNode(z.witness,current);
  if(!wx||!wy||!EntryStableNode(*x,*wx)||!EntryStableNode(*y,*wy))return false;
  tab|=current==tab_b->widget;
  if(current==layers_b[2]->widget)return tab&&x->parent==b.global&&y->parent==c.global;
  if(!x->parent)return false;current=x->parent;
 }return false;
}
[[maybe_unused]]bool EntryLeaseFrame(LivingEntryAction267V1 action,const LivingEntryFrame267V1&a,const LivingEntryRaw267V1&raw_a,const LivingEntryFrame267V1&z,const LivingEntryRaw267V1&raw_z){
 if(action!=A::open_manage_list||!a.manage||!z.manage)return Frame(a,z);
 bool applied=false;const bool projected=SameLivingEntryManageNavigationLease267V1(raw_a,*a.manage,raw_z,*z.manage,applied);
 if(!applied)return Frame(a,z);
 return World(a.inventory,z.inventory)&&a.view.has_value()==z.view.has_value()&&!a.view&&projected;
}

// Only compares already captured private copies after the original stale gate.
// No extra capture/native call, public address, selector or authority change.
[[maybe_unused]]void EntryDiffField(std::string&why,const char*key,std::uint64_t value){
 if(why.size()>1400)return;why+=';';why+=key;why+='=';why+=std::to_string(value);
}
[[maybe_unused]]std::uint32_t EntryNodeDiff(const GuiWindowNodeV1&a,const GuiWindowNodeV1&z){
 std::uint32_t m=0;
 if(a.widget!=z.widget||a.vtable!=z.vtable||a.parent!=z.parent||a.context!=z.context||a.children!=z.children||a.name_data!=z.name_data)m|=1;
 if(a.child_count!=z.child_count||a.child_capacity!=z.child_capacity)m|=2;
 if(a.name_size!=z.name_size||a.name_capacity!=z.name_capacity)m|=4;
 if(a.parent_index!=z.parent_index||a.depth!=z.depth||a.sibling_index!=z.sibling_index)m|=8;
 if(a.flags!=z.flags)m|=16;if(a.visible!=z.visible||a.enabled!=z.enabled)m|=32;if(a.name!=z.name)m|=64;
 return m;
}
[[maybe_unused]]void EntryNodeVectorDiff(std::string&why,const std::vector<GuiWindowNodeV1>&before,const std::vector<GuiWindowNodeV1>&after,const char*key){
 std::uint32_t mask=before.size()!=after.size()?128U:0U;std::size_t first=4096;
 for(std::size_t n=0;n<(std::min)(before.size(),after.size());++n){const auto m=EntryNodeDiff(before[n],after[n]);mask|=m;if(m&&first==4096)first=n;}
 EntryDiffField(why,key,mask);
 if(mask){EntryDiffField(why,"node_first",first);EntryDiffField(why,"nodes_b",before.size());EntryDiffField(why,"nodes_a",after.size());
  if(first<before.size()&&first<after.size()){EntryDiffField(why,"flags_b",before[first].flags);EntryDiffField(why,"flags_a",after[first].flags);}}
}
[[maybe_unused]]std::string EntryDiagnosticName(std::string_view text){
 constexpr char hex[]="0123456789ABCDEF";std::string out;const auto size=(std::min)(text.size(),std::size_t{16});
 for(std::size_t n=0;n<size;++n){const auto c=static_cast<unsigned char>(text[n]);if((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-')out+=static_cast<char>(c);else{out+='%';out+=hex[c>>4];out+=hex[c&15];}}
 if(text.size()>size)out+='~';return out;
}
[[maybe_unused]]void EntryJoinedNodeDifference(std::string&why,const std::vector<GuiWindowNodeV1>&before,const std::vector<GuiWindowNodeV1>&after){
 std::size_t added=0,removed=0,changed=0;std::vector<std::pair<char,const GuiWindowNodeV1*>>samples;
 const auto sample=[&](char tag,const GuiWindowNodeV1&node){if(samples.size()<2)samples.emplace_back(tag,&node);};
 for(const auto&n:after){const auto old=EntryUniqueNode(before,n.widget);if(!old){++added;sample('+',n);}else if(!EntryStableNode(*old,n)){++changed;sample('~',n);}}
 for(const auto&n:before)if(!EntryUniqueNode(after,n.widget)){++removed;sample('-',n);}
 EntryDiffField(why,"gui_added",added);EntryDiffField(why,"gui_removed",removed);EntryDiffField(why,"gui_changed",changed);
 std::vector<std::uintptr_t>types;
 for(const auto*nodes:{&before,&after})for(const auto&n:*nodes)if(std::find(types.begin(),types.end(),n.vtable)==types.end())types.push_back(n.vtable);
 for(std::size_t i=0;i<samples.size();++i){const auto[tag,node]=samples[i];const auto&nodes=tag=='-'?before:after;const auto parent=EntryUniqueNode(nodes,node->parent);
  const char*role="unknown";if(node->name=="windows_layer"||node->name=="middle"||node->name=="hud_layer")role="layer";else if(node->name=="decisions_view"||node->name=="decisiondetail_view")role="decision_root";else if(node->name=="tab_decisions")role="fixed_tab";else if(!node->parent)role="global";
  const auto type=static_cast<std::size_t>(std::find(types.begin(),types.end(),node->vtable)-types.begin())+1;
  std::string text=";gui_d"+std::to_string(i)+'='+tag+",name="+EntryDiagnosticName(node->name)+",parent="+(parent?EntryDiagnosticName(parent->name):std::string(node->parent?"missing_or_ambiguous":"root"))+",visible="+(node->visible?"1":"0")+",enabled="+(node->enabled?"1":"0")+",type_group="+std::to_string(type)+",role="+role;
  if(why.size()+text.size()<=1000)why+=text;
 }
}

[[maybe_unused]]void AppendLivingEntryFrameDifference(const LivingEntryFrame267V1&before,const LivingEntryFrame267V1&after,std::string&why)noexcept{
 try{
  std::uint64_t mask=0;const auto&a=before.inventory;const auto&z=after.inventory;
  if(!a.facts_verified||!z.facts_verified||!Core(a.core,z.core))mask|=1;
  if(a.game!=z.game||a.jomini!=z.jomini||a.actor!=z.actor||a.character_storage!=z.character_storage||a.data!=z.data||a.players!=z.players||a.player!=z.player)mask|=2;
  if(a.connection_generation!=z.connection_generation)mask|=4;
  if(before.manage.has_value()!=after.manage.has_value())mask|=8;
  if(before.view.has_value()!=after.view.has_value())mask|=16;
  if(before.manage&&after.manage){const auto&b=*before.manage;const auto&c=*after.manage;const auto&x=b.scene;const auto&y=c.scene;
   if(!b.facts_verified||!c.facts_verified||!Core(b.core,c.core))mask|=32;
   if(x.jomini!=y.jomini||x.gfx!=y.gfx||x.handler!=y.handler||x.context!=y.context||x.global!=y.global||x.list_root!=y.list_root||x.detail_root!=y.detail_root)mask|=64;
   if(x.connection_generation!=y.connection_generation||x.wall_deadline!=y.wall_deadline)mask|=128;
   if(x.list_visible!=y.list_visible||x.list_enabled!=y.list_enabled||x.detail_visible!=y.detail_visible||x.detail_enabled!=y.detail_enabled||x.owner_bound!=y.owner_bound)mask|=256;
   if(x.hud!=y.hud)mask|=512;if(b.witness!=c.witness)mask|=1024;
  }
  if(before.view&&after.view){const auto&b=*before.view;const auto&c=*after.view;
   if(!b.owner_observed||!c.owner_observed||b.gfx!=c.gfx||b.manager!=c.manager)mask|=2048;
   if(!SameLivingGuiIdentity267V1(b.gui,c.gui))mask|=4096;
  }
  EntryDiffField(why,"frame_mask",mask);
  if(before.manage&&after.manage){EntryNodeVectorDiff(why,before.manage->scene.hud,after.manage->scene.hud,"hud_mask");EntryNodeVectorDiff(why,before.manage->witness,after.manage->witness,"witness_mask");EntryJoinedNodeDifference(why,before.manage->witness,after.manage->witness);}
 }catch(...){/* Diagnostics never alter the original refusal/cleanup outcome. */}
}
[[maybe_unused]]bool CaptureFrame(LivingEntryContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,LivingEntryFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||
  q.mailbox->permitted_executor_artifact_personal_read12004!=&ExecuteLivingOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
 std::string why;const bool good=ReadLivingEntryFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,
  &q.invocation,q.request,q.monotonic_deadline_ms,out,why);
 if(out.inventory.facts_verified){q.result.facts_available=true;q.result.facts=out.inventory.core;
  q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;
  q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}
 return World(out.inventory,out.inventory)&&Core(q.request.expected,out.inventory.core)&&
  out.inventory.connection_generation==q.connection_generation&&Time(q);
}
}
bool SameLivingEntryNavigationProjection267V1(const LivingManageFrame267V1&a,const LivingManageFrame267V1&z,std::uintptr_t nav){return EntryNavigationProjection(a,z,nav);}
struct LivingEntrySession267V1::State {
 struct Lease {LivingEntryFrame267V1 frame;LivingEntryRaw267V1 raw;LivingEntryRequest267V1 request;
  std::uint64_t sequence=0,connection=0,mono=0;bool spent=false;};
 std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query=0,claim=0;
 std::optional<Lease>latest;std::optional<LivingInventoryFrame267V1>initial;
 std::uint32_t target=0xFFFFFFFFU;std::array<bool,8>once{};
 std::vector<std::pair<std::string,std::uint64_t>>claims;
};
LivingEntrySession267V1::LivingEntrySession267V1():state_(std::make_unique<State>()){}
LivingEntrySession267V1::~LivingEntrySession267V1()=default;
LivingEntrySession267V1&RetainedLivingEntrySession267V1(){static LivingEntrySession267V1 state;return state;}
void ArmLivingEntryDeadline267V1(LivingEntryContext267V1&q)noexcept{
 q.monotonic_deadline_ms=0;const auto wall=Wall();
 if(wall&&q.request.deadline_unix_ms>wall)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-wall,std::uint64_t{8000});
}
bool ExecuteLivingEntryInner267V1(LivingEntryContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.reason="living_entry_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1
 try{
  const auto reject=[&](Status status,const char*why){q.result.status=status;q.result.reason=why;q.result.source_available=false;q.result.source.reset();return true;};
  if(!q.session||!LivingEntryRequestShape267V1(q.request))return reject(Status::unavailable,"living_entry_actual_request_or_session_unavailable");
  auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&old:state.claims)if(old.first==q.request.id()){q.result.claim_sequence=old.second;return reject(Status::rejected,"living_entry_original_effect_id_retained");}
  if(LivingFamilyUnknown267V1()){q.result.cleanup_known=false;return reject(Status::indeterminate,"living_entry_prior_family_UNKNOWN");}
  if(!Time(q))return reject(Status::expired,"living_entry_original_deadline_expired");
  const auto capture=[&](LivingEntryFrame267V1&frame,LivingEntryRaw267V1&raw){
   if(!CaptureFrame(q,s,frame))return false;std::string why;
   const bool good=XAR_LIVING_ENTRY_READ_CURRENT_RAW(q.bindings,frame,q.request,q.monotonic_deadline_ms,raw,why);
   q.observation_entered|=raw.entered;q.result.cleanup_known&=raw.cleanup_known;
   if(!good){q.result.reason=why;return false;}
   LivingEntryFrame267V1 after;
   if(!CaptureFrame(q,s,after)||!Frame(frame,after)||!Time(q))return false;
   const auto&r=raw.inventory.fixed_references[0];
   if(r.state!=LivingReferenceState267V1::artifact||!r.full_id)return false;
   if(state.initial&&(!World(*state.initial,frame.inventory)||state.target!=*r.full_id))return false;
   return true;
  };
  const auto failed=[&]{
   if(!q.result.cleanup_known){BlockLivingFamilyUnknown267V1();return reject(Status::indeterminate,"living_entry_owned_read_cleanup_UNKNOWN");}
   const auto why=q.result.reason;
   return reject(Time(q)?Status::unavailable:Status::expired,why.empty()?"living_entry_complete_source_unavailable":why.c_str());
  };
  if(LivingEntryQuery267V1(q.request.action)){
   state.latest.reset();LivingEntryFrame267V1 frame;LivingEntryRaw267V1 raw;
   if(!capture(frame,raw))return failed();
   if(state.query==(std::numeric_limits<std::uint64_t>::max)())return reject(Status::unavailable,"living_entry_query_sequence_exhausted");
   if(!state.initial){state.initial=frame.inventory;state.target=*raw.inventory.fixed_references[0].full_id;}
   state.latest=LivingEntrySession267V1::State::Lease{frame,raw,q.request,++state.query,q.connection_generation,q.monotonic_deadline_ms,false};
   q.result.source=raw.source;q.result.source_available=true;q.result.status=Status::available;
   q.result.provider_generation=state.generation;q.result.query_sequence=state.query;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(Status::stale_source,"living_entry_private_query_missing");auto&lease=*state.latest;
  q.result.provider_generation=state.generation;q.result.query_sequence=lease.sequence;
  const auto action=static_cast<std::size_t>(q.request.action);
  if(action>=state.once.size()||state.once[action]||lease.spent||q.request.provider_generation!=state.generation||
   q.request.query_sequence!=lease.sequence||q.connection_generation!=lease.connection||q.request.id()==lease.request.id()||
   q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!Core(q.request.expected,lease.request.expected)||
   LivingEntryKindFor267V1(q.request.action)!=LivingEntryKindFor267V1(lease.request.action))
   return reject(Status::stale_source,"living_entry_original_owner_Core_body_or_once_mismatch");
  if(GetTickCount64()>=lease.mono)return reject(Status::expired,"living_entry_original_query_deadline_expired");
  q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  LivingEntryFrame267V1 frame;LivingEntryRaw267V1 actual;
  if(!capture(frame,actual))return failed();
  const bool lease_frame_equal=EntryLeaseFrame(q.request.action,frame,actual,lease.frame,lease.raw);
  if(!lease_frame_equal||!SameLivingEntryRaw267V1(actual,lease.raw)){
   std::string why="living_entry_complete_physical_source_changed";
   EntryDiffField(why,"lease_frame_equal",lease_frame_equal);
   AppendLivingEntryFrameDifference(lease.frame,frame,why);AppendLivingEntryRawDifference267V1(lease.raw,actual,why);
   return reject(Status::stale_source,why.c_str());
  }
  if(state.claims.size()>=16||state.claim==(std::numeric_limits<std::uint64_t>::max)())return reject(Status::rejected,"living_entry_finite_claim_capacity");
  const auto claim=++state.claim;state.claims.emplace_back(std::string(q.request.id()),claim);
  lease.spent=true;state.once[action]=true;q.result.claim_sequence=claim;
  const auto call=CallLivingEntryRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,actual);
  q.result.effect_attempted=call.entered;q.result.native_returned=call.native_returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known){BlockLivingFamilyUnknown267V1();return reject(Status::indeterminate,"living_entry_native_completion_UNKNOWN_claim_retained");}
  if(!call.entered||!call.native_returned)return reject(Status::stale_source,"living_entry_preeffect_refused_claim_retained");
  q.result.source=lease.raw.source;q.result.source_available=true;q.result.status=Status::dispatched;q.result.reason.clear();return true;
 }catch(...){BlockLivingFamilyUnknown267V1();q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();
  q.result.status=Status::indeterminate;q.result.reason="living_entry_owner_local_UNKNOWN";}
#endif
 return true;
}
bool ExecuteLivingEntryOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 if(!p)return false;auto&q=*static_cast<LivingEntryContext267V1*>(p);
 __try{return ExecuteLivingEntryInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){BlockLivingFamilyUnknown267V1();
  q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();q.result.status=Status::indeterminate;
  q.result.reason="living_entry_original_native_exception_UNKNOWN";return true;}
}
}

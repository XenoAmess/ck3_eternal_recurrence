#include "xar_bridge/ck3_121003_frontend_menu26785313_v1.hpp"
#include "xar_bridge/ck3_121003_application_exit26785313_v1.hpp"
#include "xar_bridge/ck3_121003_gui_root_index26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <vector>
#include <windows.h>
namespace xar::ck3_121003::build26785313 { namespace {
using Action=FrontendMenuAction267V1;using Status=FrontendMenuStatus267V1;using Route=FrontendMenuRoute267V1;
std::atomic<std::uint64_t> next_frontend_provider{1};
bool Copy(const void*p,void*out,std::size_t n) noexcept {if(!p||!out||!n)return false;
 __try{std::memcpy(out,p,n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t offset,T&out) noexcept {
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 return p&&offset<=max-p&&sizeof(T)-1<=max-p-offset&&Copy(reinterpret_cast<const void*>(p+offset),&out,sizeof(out));}
[[maybe_unused]]bool GuiWindowTypeV1(std::uintptr_t image,std::uintptr_t widget,std::uintptr_t &vtable) noexcept {
 const auto inside=[&](std::uintptr_t p,std::size_t n){return p>=image&&n<=kImageSize&&p-image<=kImageSize-n;};
 std::uintptr_t col=0;std::uint32_t signature=0,offset=0,self=0,chd_rva=0,count=0,bases_rva=0;
 if(!At(widget,0,vtable)||!inside(vtable,8)||vtable<image+8||!At(vtable-8,0,col)||!inside(col,24)||
    !At(col,0,signature)||signature!=1||!At(col,4,offset)||offset!=0||!At(col,8,self)||self!=0||
    !At(col,20,self)||image+self!=col||!At(col,16,chd_rva)||!inside(image+chd_rva,16))return false;
 const auto chd=image+chd_rva;
 if(!At(chd,0,signature)||signature!=0||!At(chd,8,count)||!count||count>64||
    !At(chd,12,bases_rva)||!inside(image+bases_rva,static_cast<std::size_t>(count)*4))return false;
 for(std::uint32_t i=0;i<count;++i) {
  std::uint32_t desc_rva=0,type=0;std::int32_t mdisp=0,pdisp=0;
  if(!At(image+bases_rva,static_cast<std::size_t>(i)*4,desc_rva)||!inside(image+desc_rva,28)||
     !At(image+desc_rva,0,type)||!At(image+desc_rva,8,mdisp)||!At(image+desc_rva,12,pdisp))return false;
  if(type==0x6082F78&&mdisp==0&&pdisp==-1)return true;
 }
 return false;
}
[[maybe_unused]]bool GuiWindowNodeReadV1(std::uintptr_t image,std::uintptr_t widget,std::uintptr_t context,
    std::uintptr_t parent,GuiWindowNodeV1 &out) {
 GuiWindowNodeV1 n;n.widget=widget;std::array<char,kGuiWindowMaxNameBytesV1+1> text{};
 if(!widget||!GuiWindowTypeV1(image,widget,n.vtable)||!At(widget,0xD0,n.flags)||(n.flags&1)!=0||
    !At(widget,0xD8,n.context)||n.context!=context||!At(widget,0xE8,n.parent)||n.parent!=parent||
    !At(widget,0xF0,n.children)||!At(widget,0xF8,n.child_capacity)||!At(widget,0xFC,n.child_count)||
    n.child_count<0||n.child_capacity<n.child_count||static_cast<std::size_t>(n.child_count)>kGuiWindowMaxNodesV1||
    (n.child_count&&!n.children)||!At(widget,0x1C8,n.name_size)||!At(widget,0x1D0,n.name_capacity)||
    n.name_size>kGuiWindowMaxNameBytesV1||n.name_capacity<n.name_size||n.name_capacity>0x1000000)return false;
 if(n.name_capacity<=15) {if(n.name_capacity!=15||n.name_size>15)return false;n.name_data=widget+0x1B8;}
 else if(!At(widget,0x1B8,n.name_data)||!n.name_data)return false;
 if(!Copy(reinterpret_cast<const void*>(n.name_data),text.data(),static_cast<std::size_t>(n.name_size)+1)||
    text[n.name_size]!=0||std::memchr(text.data(),0,static_cast<std::size_t>(n.name_size)))return false;
 if(n.name_size&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(n.name_size),nullptr,0)==0)return false;
 n.name.assign(text.data(),static_cast<std::size_t>(n.name_size));n.visible=(n.flags&0x18)==0;n.enabled=(n.flags&0x06)==0;
 out=std::move(n);return true;
}

struct FrontendSource {
 std::uintptr_t logical_owner=0,application=0,first=0,context=0,global_root=0,route_root=0;
 Route route=Route::unavailable;std::vector<GuiWindowNodeV1> nodes;
 friend bool operator==(const FrontendSource&,const FrontendSource&)=default;
};
std::uint64_t Wall() noexcept {const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Unexpired(const FrontendMenuContext267V1&q) noexcept {const auto t=Wall();return t&&q.monotonic_deadline_ms&&t<q.request.deadline_unix_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Owner(const FrontendMenuContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 if(!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||!q.ticket.sequence||!s.thread_id||!s.pump_epoch||
    !s.tls_initialized_flag_address||s.tls_initialized!=1||!s.tls_context||s.tls_main_thread_marker!=1||
    GetCurrentThreadId()!=s.thread_id||s.game_state!=0||!Unexpired(q))return false;
 const auto&m=*q.mailbox;
 return m.permitted_frontend_executor==&ExecuteFrontendMenuOnOwner267V1&&
  m.state.load(std::memory_order_acquire)==ck3_11906::MainThreadQueryMailboxStateV1::executing&&
  !m.stop_requested.load(std::memory_order_acquire)&&m.failure_flags.load(std::memory_order_acquire)==0&&
  m.published_sequence.load(std::memory_order_acquire)==q.ticket.sequence&&
  m.owner_thread_id.load(std::memory_order_acquire)==s.thread_id&&
  m.owner_verified_pump_epochs.load(std::memory_order_acquire)>=ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs&&
  m.executor==&ExecuteFrontendMenuOnOwner267V1&&m.executor_context==&q;
}
[[maybe_unused]]Route RouteName(std::string_view n) noexcept {if(n=="mainmenu_panel_bottom")return Route::main_menu;if(n=="frontend_bookmarks")return Route::bookmarks;if(n=="lobbyview")return Route::lobby;return Route::unavailable;}
[[maybe_unused]]bool Capture(FrontendMenuContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,FrontendSource&out) {
 out={};if(!Owner(q,s)||!q.bindings.exact_image_admitted||!VerifyGuiWindowImageV1(q.bindings.module_base)||
  !VerifyApplicationExitImage267V1(q.bindings.module_base))return false;
 const auto base=q.bindings.module_base;std::uintptr_t world=1,vt=0;
 if(!At(reinterpret_cast<std::uintptr_t>(q.bindings.core.game_state_slot),0,world)||world!=0||
  !At(reinterpret_cast<std::uintptr_t>(q.bindings.core.jomini_state_slot),0,out.logical_owner)||!out.logical_owner||
  out.logical_owner!=s.jomini_state||!At(out.logical_owner,0x18,out.application)||
  !At(out.application,0,vt)||vt!=base+kGuiRootApplicationVtableRvaV1||
  !At(out.application,0x1B8,out.first)||!At(out.first,0x58,out.context)||!out.context||
  !At(out.context,0xD0,out.global_root))return false;
 std::uint8_t quitting=1;if(!At(out.application,0x89,quitting)||quitting!=0)return false;
 GuiWindowNodeV1 root;if(!GuiWindowNodeReadV1(base,out.global_root,out.context,0,root)||!root.visible)return false;
 out.nodes.push_back(root);std::vector<std::size_t> todo{0};std::unordered_set<std::uintptr_t> unique{root.widget};std::size_t bytes=root.name.size();
 // A bounded readonly search of visible menu ancestors only. Never read an
 // inactive sibling's descendants or call a widget/action while finding roots.
 while(!todo.empty()) {const auto i=todo.back();todo.pop_back();const auto parent=out.nodes[i];
  if(parent.depth>=4)continue;
  for(std::int32_t child=0;child<parent.child_count;++child) {
   if(!Owner(q,s)||out.nodes.size()>=4096)return false;
   std::uintptr_t pointer=0;GuiWindowNodeV1 n;
   if(!At(parent.children,static_cast<std::size_t>(child)*8,pointer)||!unique.insert(pointer).second||
      !GuiWindowNodeReadV1(base,pointer,out.context,parent.widget,n))return false;
   n.depth=parent.depth+1;n.parent_index=static_cast<std::int32_t>(i);n.sibling_index=static_cast<std::uint32_t>(child);
   n.visible=n.visible&&parent.visible;n.enabled=n.enabled&&parent.enabled;bytes+=n.name.size();if(bytes>131072)return false;
   out.nodes.push_back(n);if(!n.visible)continue;
   const auto route=RouteName(n.name);
   if(route!=Route::unavailable){if(out.route_root)return false;out.route_root=n.widget;out.route=route;continue;}
   todo.push_back(out.nodes.size()-1);
  }
 }
 return out.route_root&&Owner(q,s)&&At(reinterpret_cast<std::uintptr_t>(q.bindings.core.game_state_slot),0,world)&&world==0;
}
[[maybe_unused]]FrontendMenuFacts267V1 Facts(const FrontendSource&source,const FrontendMenuContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s) {
 FrontendMenuFacts267V1 f;f.route=source.route;f.application_verified=f.gui_context_verified=f.global_root_verified=f.route_root_visible=f.no_world=true;
 f.connection_generation=q.connection_generation;f.ticket_sequence=q.ticket.sequence;f.pump_epoch=s.pump_epoch;f.thread_id=s.thread_id;
 // Model values are not inferred from a visible name or the configured preset.
 // Current Robert model ABI is a separate migration; absent means null/false.
 return f;
}
struct QuitAdmission {FrontendMenuContext267V1&q;const ck3_11906::MainThreadExecutionStampV1&stamp;const FrontendSource&source;ck3_1210::ApplicationExitBindingsV1 binding;};
[[maybe_unused]]bool BeforeQuit(void*opaque) noexcept {try {
 auto&a=*static_cast<QuitAdmission*>(opaque);FrontendSource current;
 if(!Capture(a.q,a.stamp,current)||current!=a.source)return false;
 const auto bound=BindApplicationExitImage267V1(a.q.bindings.module_base,kExecutableSha256);
 return bound.enabled&&bound.application_slot==a.binding.application_slot&&bound.request_quit==a.binding.request_quit&&
  bound.expected_application_vtable==a.binding.expected_application_vtable;
 }catch(...){return false;}}
} // namespace
struct FrontendMenuSession267V1::State {
 std::atomic_bool unknown{false};bool query_valid=false;
 std::uint64_t provider_generation=0,query_sequence=0,connection_generation=0,query_deadline=0;
 FrontendSource issued{};ck3_1210::ApplicationExitSessionV1 quit_session;
};
FrontendMenuSession267V1::FrontendMenuSession267V1():state_(std::make_unique<State>()){}
FrontendMenuSession267V1::~FrontendMenuSession267V1()=default;
void BlockFrontendMenuUnknown267V1(FrontendMenuSession267V1&s) noexcept {s.state_->unknown.store(true,std::memory_order_release);}
void ArmFrontendMenuDeadline267V1(FrontendMenuContext267V1&q) noexcept {q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteFrontendMenuInner267V1(FrontendMenuContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&stamp) noexcept {
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;
#if defined(XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1) && XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1
 try {
 const auto reject=[&](Status status,const char*reason){q.result.status=status;q.result.reason=reason;return true;};
 if(!q.session||!q.game||!q.game->enabled()||!game::IsCk3_121003Core26785313Descriptor(q.game->descriptor())||
    !q.game->supports(kFrontendMenuQueryCapability267V1)||!FrontendMenuRequestShape267V1(q.request))return reject(Status::unavailable,"current_frontend_profile_unavailable");
 auto&s=*q.session->state_;if(s.unknown.load(std::memory_order_acquire))return reject(Status::indeterminate,"current_frontend_prior_unknown_no_replay");
 if(!Unexpired(q))return reject(Status::expired,"current_frontend_original_deadline_expired");
 if(q.request.action!=Action::query_menu&&q.request.action!=Action::quit_menu)
  return reject(Status::unavailable,"current_frontend_robert_model_abi_unbound");
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
 FrontendSource first,second;if(!Capture(q,stamp,first)||!Capture(q,stamp,second)||first!=second)
  return reject(Status::unavailable,"current_frontend_application_source_unavailable");
 q.result.facts=Facts(second,q,stamp);
 if(q.request.action==Action::query_menu){
  if(!s.provider_generation)s.provider_generation=next_frontend_provider.fetch_add(1);
  if(!s.provider_generation||s.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(Status::capacity_exhausted,"current_frontend_lease_exhausted");
  ++s.query_sequence;s.issued=std::move(second);s.query_valid=true;s.connection_generation=q.connection_generation;s.query_deadline=q.request.deadline_unix_ms;
  q.result.provider_generation=s.provider_generation;q.result.query_sequence=s.query_sequence;q.result.status=Status::available;return true;
 }
 if(!q.game->supports(kFrontendMenuQuitCapability267V1))return reject(Status::unavailable,"current_frontend_quit_capability_unavailable");
 if(!s.query_valid||s.provider_generation!=q.request.provider_generation||s.query_sequence!=q.request.query_sequence||
    s.connection_generation!=q.connection_generation||s.query_deadline!=q.request.deadline_unix_ms||s.issued!=second)
  return reject(Status::query_consumed,"current_frontend_original_private_witness_changed_or_consumed");
 s.query_valid=false;const auto bound=BindApplicationExitImage267V1(q.bindings.module_base,kExecutableSha256);
 if(!bound.enabled)return reject(Status::unavailable,"current_frontend_quit_binding_unavailable");
 FrontendSource final;if(!Capture(q,stamp,final)||final!=second||!Unexpired(q))return reject(Status::source_changed,"current_frontend_prewrite_source_changed");
 QuitAdmission admitted{q,stamp,final,bound};const bool prior=s.quit_session.claimed.load(std::memory_order_acquire);
 const auto call=ck3_1210::RequestApplicationExitV1(bound,s.quit_session,&BeforeQuit,&admitted);
 using Exit=ck3_1210::ApplicationExitStatusV1;
 const bool claimed=!prior&&s.quit_session.claimed.load(std::memory_order_acquire);q.result.claim_sequence=claimed||prior?1:0;
 q.result.effect_attempted=claimed&&(call==Exit::requested||call==Exit::indeterminate);q.result.native_returned=call==Exit::requested;
 q.result.status=call==Exit::requested?Status::exit_requested:call==Exit::indeterminate?Status::indeterminate:Status::claim_consumed;
 if(call==Exit::indeterminate){s.unknown.store(true,std::memory_order_release);q.result.reason="current_frontend_native_unknown_no_replay";}
 else if(call!=Exit::requested)q.result.reason="current_frontend_quit_claim_retained_no_replay";
 return true;
 }catch(...){if(q.result.effect_attempted&&q.session)BlockFrontendMenuUnknown267V1(*q.session);q.result.status=q.result.effect_attempted?Status::indeterminate:Status::unavailable;q.result.reason="current_frontend_executor_exception_no_replay";}
#else
 (void)stamp;q.result.reason="current_frontend_default_off";
#endif
 return true;
}
bool ExecuteFrontendMenuOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 if(!p)return false;auto&q=*static_cast<FrontendMenuContext267V1*>(p);
 __try{return ExecuteFrontendMenuInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.result.effect_attempted&&q.session)BlockFrontendMenuUnknown267V1(*q.session);q.result.status=q.result.effect_attempted?Status::indeterminate:Status::unavailable;return true;}
}
} // namespace xar::ck3_121003::build26785313

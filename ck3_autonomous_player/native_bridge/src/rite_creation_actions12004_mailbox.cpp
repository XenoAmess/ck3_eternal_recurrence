#include "xar_bridge/rite_creation_actions12004_mailbox.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <windows.h>
#include <algorithm>
#include <array>
#include <atomic>
#include <utility>

namespace xar::ck3_12004::religion::rite_creation_actions {
namespace {
namespace ui=ck3_11906;
bool Read(const void*p,void*out,std::size_t size) noexcept {
 SIZE_T count=0;return p&&out&&size&&ReadProcessMemory(GetCurrentProcess(),p,out,size,&count)&&count==size;
}
template<class T>bool Value(const void*p,std::size_t offset,T&out) noexcept {
 return p&&Read(static_cast<const unsigned char*>(p)+offset,&out,sizeof(out));
}
struct GuiContext {
 const ui::ZhongguoScoreboardNativeEnvironmentV1*environment=nullptr;
 ui::IngameUiGuiOwnerBindingV1 owner{};
};
bool CurrentGui(const GuiContext&c) noexcept {
 ui::IngameUiGuiOwnerBindingV1 current{};
 return c.environment&&ui::ReadIngameUiGuiOwnerBindingV1(*c.environment,current)&&current==c.owner;
}
bool RootState(void*opaque,const void*expected,std::string_view expected_name,bool&visible,bool&enabled) noexcept {
 visible=enabled=false;try{
  auto*c=static_cast<GuiContext*>(opaque);if(!c||!expected||!CurrentGui(*c))return false;
  ui::ZhongguoScoreboardAccessV1 access{};void*root=nullptr,*widget=nullptr,*vt=nullptr;std::string name;
  if(!ui::ResolveNamedGuiWidgetV1(*c->environment,access,expected_name,expected_name,root,widget)||
     root!=expected||widget!=root||!ui::ReadGuiWidgetRuntimeV1(access,root,name,vt,visible,enabled)||name!=expected_name)return false;
  return CurrentGui(*c);
 }catch(...){return false;}
}
bool AncestorsEnabled(const ui::NamedGuiTreeInspectionV1&tree,const ui::NamedGuiWidgetInspectionV1&row) {
 // Runtime rows supply effective visibility; check each parent's enabled
 // property explicitly instead of assuming enabled propagates identically.
 for(const auto&parent:tree.widgets){
  const auto&prefix=parent.child_path;
  const bool ancestor=prefix.empty()||prefix==row.child_path||
   (row.child_path.size()>prefix.size()&&row.child_path.compare(0,prefix.size(),prefix)==0&&row.child_path[prefix.size()]=='/');
  if(ancestor&&(!parent.effective_visible||!parent.enabled))return false;
 }
 return true;
}
bool NamedButton(void*opaque,const void*expected_root,std::string_view button,bool&visible,bool&enabled) noexcept {
 visible=enabled=false;try{
  auto*c=static_cast<GuiContext*>(opaque);if(!c||!expected_root||!CurrentGui(*c))return false;
  if(button!="edit_rite"&&button!="create_rite"&&button!="create_rite_puppet")return false;
  ui::ZhongguoScoreboardAccessV1 access{};void*root=nullptr,*widget=nullptr;
  ui::NamedGuiTreeInspectionV1 tree{};
  if(!ui::ResolveNamedGuiWidgetV1(*c->environment,access,"faith_window","faith_window",root,widget)||root!=expected_root||widget!=root||
     !ui::InspectNamedGuiSubtreeV1(access,c->environment->module_base,root,"faith_window",tree)||
     !tree.root_available||tree.truncated||tree.widget_count!=tree.widgets.size())return false;
  const ui::NamedGuiWidgetInspectionV1*found=nullptr;
  for(const auto&row:tree.widgets)if(row.runtime_name==button){if(found)return false;found=&row;}
  if(!found)return false;visible=found->effective_visible;enabled=found->enabled&&AncestorsEnabled(tree,*found);
  return CurrentGui(*c);
 }catch(...){return false;}
}
bool ModalScope(void*opaque,const void*original_modal_root) noexcept {
 try{
  auto*c=static_cast<GuiContext*>(opaque);if(!c||!CurrentGui(*c))return false;
  const void*rows=nullptr,*later_rows=nullptr;std::int32_t count=0,later_count=0;
  if(!Value(c->owner.context,ui::kZhongguoGuiModalReceiversOffset,rows)||
     !Value(c->owner.context,ui::kZhongguoGuiModalReceiverCountOffset,count)||
     count<0||count>256||(count&&!rows))return false;
  std::array<const void*,256>receivers{};std::array<std::uint8_t,256>flags{};unsigned admitted=0;
  for(std::int32_t i=0;i<count;++i){
   auto index=static_cast<std::size_t>(i);
   if(!Value(rows,index*sizeof(void*),receivers[index])||!receivers[index]||
      !Value(receivers[index],ui::kZhongguoWidgetHiddenFlagsOffset,flags[index]))return false;
   if((flags[index]&ui::kZhongguoWidgetEffectiveHiddenMask)==0){
    // A narrow allowance for the actual original type/owner/root resolved by
    // the controller. No name, child-path or arbitrary descendant exception.
    if(!original_modal_root||receivers[index]!=original_modal_root||++admitted>1)return false;
   }
  }
  if(!Value(c->owner.context,ui::kZhongguoGuiModalReceiversOffset,later_rows)||later_rows!=rows||
     !Value(c->owner.context,ui::kZhongguoGuiModalReceiverCountOffset,later_count)||later_count!=count)return false;
  for(std::int32_t i=0;i<count;++i){const void*receiver=nullptr;std::uint8_t later=0;auto index=static_cast<std::size_t>(i);
   if(!Value(rows,index*sizeof(void*),receiver)||receiver!=receivers[index]||
      !Value(receiver,ui::kZhongguoWidgetHiddenFlagsOffset,later)||later!=flags[index])return false;}
  return (!original_modal_root||admitted==1)&&CurrentGui(*c);
 }catch(...){return false;}
}
}
std::string_view PrepareMailbox12004(const game::GameAdapter&game,const game::Snapshot*previous,
 std::string_view payload,std::uint64_t revision,std::uint64_t generation,std::uintptr_t base,
 ui::MainThreadQueryMailboxV1&mailbox,MailboxContext&query) noexcept {
 query={};try{
  if(!revision||!generation||!base||!previous)return "rite_creation_actual_connection_or_frame_unavailable";
  const auto&descriptor=game.descriptor();
  if(descriptor.game_version!=ck3_12004::kGameVersion||descriptor.executable_sha256!=ck3_12004::kExecutableSha256)
   return "rite_creation_requires_exact12004";
  game::Snapshot actual{};
  if(!game::ReadSnapshot(game,actual)||actual!=*previous||!actual.paused||!actual.map_ready||
     !actual.has_played_character||!actual.played_character_alive||actual.played_character_id<=0||actual.has_active_event)
   return "rite_creation_actual_alive_paused_noevent_frame_changed";
  std::string failure;
  if(!ParseRequest12004(payload,query.wire,failure))return "rite_creation_typed_request_invalid";
  query.actual_frame={generation,revision,0,actual.date_raw,actual.played_character_id};
  if(!MatchRequestFrame(query.wire,query.actual_frame))return "rite_creation_expected_frame_assertion_changed";
  query.envelope.game=&game;query.envelope.mailbox=&mailbox;query.envelope.expected_snapshot=actual;
  query.envelope.expected_snapshot_revision=revision;
  query.envelope.snapshot_comparison=ck3_12002::QuerySnapshotComparison12002::core_frame;
  query.environment=ui::BindZhongguoScoreboardNativeEnvironmentV1(base,true,ui::GuiAbiRevisionV1::crozier12004,descriptor.executable_sha256);
  if(!query.environment.exact_build_admitted||query.environment.offline_fixture_function_overrides)
   return "rite_creation_actual_gui_environment_unavailable";
  return {};
 }catch(...){return "rite_creation_mailbox_preparation_exception";}
}
bool ExecuteMailbox12004(void*opaque,const ui::MainThreadExecutionStampV1&stamp) noexcept {
 auto*envelope=static_cast<ck3_12002::QueryMailboxEnvelope*>(opaque);
 if(!envelope||!envelope->typed_context)return false;
 auto&q=*static_cast<MailboxContext*>(envelope->typed_context);
 try{
  if(!ck3_12002::EnterQueryMailbox(*envelope,stamp,&ExecuteMailbox12004)||
     !ui::IsIngameUiPausedOwnerStampV1(*envelope->mailbox,stamp,GetCurrentThreadId())){
   q.failure="rite_creation_actual_owner_tls_ticket_or_frame_changed";return true;}
  q.actual_frame.capture_epoch=stamp.pump_epoch;
  q.actual_frame.date_raw=stamp.date_raw;
  q.actual_frame.played_character_id=envelope->expected_snapshot.played_character_id;
  if(!MatchRequestFrame(q.wire,q.actual_frame)){
   q.failure="rite_creation_owner_frame_assertion_changed";return true;}
  GuiContext gui{&q.environment,{}};
  if(!ui::ReadIngameUiGuiOwnerBindingV1(q.environment,gui.owner)){
   q.failure="rite_creation_actual_gui_owner_unavailable";return true;}
  void*gfx=nullptr,*handler=nullptr;
  if(!Value(reinterpret_cast<const void*>(stamp.jomini_state),0x10,gfx)||!gfx||!Value(gfx,0x88,handler)||!handler){
   q.failure="rite_creation_actual_ingame_handler_unavailable";return true;}
  Admission admission{};admission.owner_tls_paused_verified=true;admission.exact_build_admitted=true;
  admission.draft_action_opt_in=true;admission.gameplay_commit_opt_in=true;
  admission.jomini_owner=reinterpret_cast<void*>(stamp.jomini_state);admission.handler=handler;
  admission.gui_root_state=&RootState;admission.named_button_state=&NamedButton;admission.modal_scope_state=&ModalScope;admission.gui_context=&gui;
  const auto binding=BindRiteCreationActionsImage12004(q.environment.module_base,q.environment.executable_sha256);
  (void)ExecuteRiteCreationAction12004(binding,admission,q.actual_frame,q.wire.request,q.result);
  q.completed=true;
  const bool stable=ck3_12002::FinishQueryMailbox(*envelope)&&CurrentGui(gui);
  if(!stable){q.result.available=false;q.result.status=q.result.native_dispatch_attempted?"dispatch_result_unknown":"unavailable";
   q.result.verification_pending=q.result.native_dispatch_attempted;
   q.result.unavailable_reason="rite_creation_owner_completion_changed_do_not_retry_if_attempted";}
  return true;
 }catch(...){q.failure="rite_creation_mailbox_exception_do_not_retry_if_attempted";
  q.result.available=false;q.result.verification_pending=q.result.native_dispatch_attempted;
  q.result.original_writer_may_have_been_queued=q.wire.request.operation==Operation::confirm_once&&q.result.native_dispatch_attempted;
  q.completed=q.result.native_dispatch_attempted;return true;}
}
bool RunMailbox12004(MailboxContext&q,std::string_view request_id,std::string&serialized,std::string&failure) noexcept {
 serialized.clear();failure.clear();try{
  auto&e=q.envelope;if(!e.game||!e.mailbox||request_id.empty()||request_id.size()>128){failure="rite_creation_mailbox_context_invalid";return false;}
  e.typed_context=&q;
  if(ui::TrySubmitMainThreadQueryV1(*e.mailbox,&ExecuteMailbox12004,&e,e.ticket)!=ui::MainThreadQuerySubmitResultV1::submitted){
   failure="rite_creation_owner_ticket_not_submitted";return false;}
  auto waited=ui::WaitForMainThreadQueryV1(*e.mailbox,e.ticket,8000);
  // An executing ticket owns this exact stack context until terminal. Waiting
  // is result collection, never a second send or another Confirm.
  while(waited==ui::MainThreadQueryWaitResultV1::timeout_executor_already_running)
   waited=ui::WaitForMainThreadQueryV1(*e.mailbox,e.ticket,100);
  const auto reclaimed=ui::ReclaimMainThreadQueryV1(*e.mailbox,e.ticket);
  if(waited!=ui::MainThreadQueryWaitResultV1::completed||reclaimed!=ui::MainThreadQueryReclaimResultV1::reclaimed||!q.completed){
   failure=q.failure.empty()?"rite_creation_owner_completion_unavailable_do_not_retry":q.failure;return false;}
  serialized=SerializeCommandResult12004(q.result,request_id);return !serialized.empty();
 }catch(...){failure="rite_creation_mailbox_result_collection_exception_do_not_retry";return false;}
}
}

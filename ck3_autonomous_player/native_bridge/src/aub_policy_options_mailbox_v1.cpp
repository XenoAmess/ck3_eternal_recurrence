#include "xar_bridge/aub_policy_options_mailbox_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include <Windows.h>
#include <utility>
namespace xar::ck3_12003 {
namespace {
using namespace ck3_11906;
struct Frame {
  AubPolicyMailboxContextV1 *query=nullptr;
  MainThreadQueryMailboxV1 *mailbox=nullptr;
  const MainThreadExecutionStampV1 *stamp=nullptr;
  const ZhongguoScoreboardNativeEnvironmentV1 *env=nullptr;
  void *gui_context=nullptr,*gui_owner=nullptr,*root=nullptr;
};
bool CurrentCompleteRoot(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *&root) {
  ZhongguoScoreboardAccessV1 access{};void *widget=nullptr;NamedGuiTreeInspectionV1 tree{};
  if(!ResolveNamedGuiWidgetV1(env,access,"decisiondetail_view","decisiondetail_view",root,widget) ||
      !root || widget!=root || !InspectNamedGuiSubtreeV1(access,env.module_base,root,"decisiondetail_view",tree) ||
      tree.truncated || !tree.widget_count || tree.widget_count!=tree.widgets.size()) return false;
  std::size_t roots=0;
  for(const auto &row:tree.widgets) if(row.child_path.empty()) {
    if(row.runtime_name!="decisiondetail_view" || !row.effective_visible) return false;
    ++roots;
  }
  return roots==1;
}
bool FrameCheck(void *raw) noexcept {
  auto *f=static_cast<Frame *>(raw);
  if(!f || !f->query || !f->query->observation.game || !f->mailbox || !f->stamp || !f->env) return false;
  try {
    const auto &q=f->query->observation;
    game::Snapshot current{};ZhongguoScoreboardAccessV1 access{};
    void *context=nullptr,*owner=nullptr,*root=nullptr;
    return IsIngameUiPausedOwnerStampV1(*f->mailbox,*f->stamp,GetCurrentThreadId()) &&
      q.native_revision>0 && q.connection_generation>0 &&
      game::ReadSnapshot(*q.game,current) && current==q.expected_snapshot &&
      current.paused && current.map_ready && current.has_played_character && current.played_character_alive &&
      current.played_character_id>0 && !current.has_active_event && !current.has_pending_character_interaction &&
      current.date_raw==f->stamp->date_raw &&
      ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(*f->env,access,context,owner) &&
      context==f->gui_context && owner==f->gui_owner &&
      CurrentCompleteRoot(*f->env,root) && root==f->root;
  }catch(...){return false;}
}
bool MainThread(void *raw) noexcept {
  const auto *f=static_cast<const Frame *>(raw);
  return f && f->mailbox && f->stamp && IsIngameUiPausedOwnerStampV1(*f->mailbox,*f->stamp,GetCurrentThreadId());
}
bool SelectedAub(const IngameDecisionItemResultV1 &v) {
  return v.available && v.owner_thread_verified && v.frame_verified && v.gui_owner_binding_verified &&
    v.source_abi_pins_verified && v.decisions_root_visible && v.decisions_tree_complete && v.row_owner_verified &&
    v.matching_row_count==1 && v.detail_root_visible && v.detail_tree_complete && v.detail_definition_available &&
    v.detail_definition_matches_target && v.detail_actor_binding_verified &&
    v.decision_key=="enable_auto_build" && v.detail_decision_key=="enable_auto_build" &&
    v.played_character_id>0 && v.detail_actor_reference_key==v.played_character_id;
}
} // namespace
bool ExecuteAubPolicyOptionsMailboxV1(AubPolicyMailboxContextV1 &q,
    MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  q.query_result={};q.select_result={};q.keyed_owner_before={};q.keyed_owner_after={};
  const auto reject=[&](const char *reason){q.query_result.unavailable_reason=reason;q.select_result.unavailable_reason=reason;return true;};
  try {
    if(q.observation.requested_key!="enable_auto_build" || env.offline_fixture_function_overrides)
      return reject("fixed_aub_decision_or_production_environment_unverified");
    if(!ExecuteIngameDecisionItemQueryV1(q.observation,mailbox,stamp,env)) return reject("keyed_before_infrastructure_unavailable");
    q.keyed_owner_before=q.observation.result;
    if(!SelectedAub(q.keyed_owner_before)) return reject("actual_selected_aub_detail_owner_unqualified");
    Frame frame{&q,&mailbox,&stamp,&env};ZhongguoScoreboardAccessV1 access{};
    if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,frame.gui_context,frame.gui_owner) ||
       !CurrentCompleteRoot(env,frame.root) || !FrameCheck(&frame)) return reject("actual_aub_root_frame_owner_unqualified");
    access.context=&frame;access.is_main_thread=MainThread;
    AubPolicyNativeAdmissionV1 a{};
    a.executable_sha256="94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6";
    a.jomini_state=reinterpret_cast<const void *>(stamp.jomini_state);a.decision_detail_root=frame.root;
    a.gui_context=frame.gui_context;a.native_root_effectively_visible=true;a.native_tree_complete=true;
    a.played_character_id=q.keyed_owner_before.played_character_id;a.frame_context=&frame;a.revalidate_paused_episode_frame=FrameCheck;
    bool succeeded=false;
    if(q.action==AubPolicyMailboxActionV1::query) succeeded=ProbeAubPolicyOptionsV1(env,access,a,q.query_result);
    else if(q.action==AubPolicyMailboxActionV1::select) succeeded=SelectAubPolicyOptionV1(env,access,a,q.expected_selected_key,q.desired_key,q.select_result);
    else return reject("unknown_fixed_aub_policy_operation");
    // Independent keyed owner census after source selection; its failure cannot
    // turn an invoked action into retryable or success. No Confirm is dispatched.
    IngameDecisionItemContextV1 after=q.observation;after.result={};
    const bool keyed_after=ExecuteIngameDecisionItemQueryV1(after,mailbox,stamp,env);q.keyed_owner_after=std::move(after.result);
    if(!keyed_after || !SelectedAub(q.keyed_owner_after) || !FrameCheck(&frame)) {
      if(q.action==AubPolicyMailboxActionV1::query) {q.query_result.ready=false;q.query_result.unavailable_reason="keyed_after_or_frame_changed";}
      else {q.select_result.postcondition_verified=false;q.select_result.unavailable_reason="keyed_after_or_frame_changed_no_retry";}
    }
    return succeeded;
  }catch(...){q.query_result.ready=false;q.select_result.postcondition_verified=false;return reject("aub_mailbox_exception_result_unknown_no_retry");}
}

namespace {
std::string JsonText(std::string_view v) {
  std::string out="\"";
  for(unsigned char c:v) {
    if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
    else if(c<32){const char *hex="0123456789abcdef";out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
    else out+=static_cast<char>(c);
  }
  return out+'"';
}
std::string PolicyJson(const AubPolicyOptionsObservationV1 &v) {
  std::string s="{\"ready\":";s+=v.ready?"true":"false";
  s+=",\"played_character_id\":"+std::to_string(v.played_character_id)+",\"decision_key\":"+JsonText(v.decision_key);
  s+=",\"selected_key\":"+JsonText(v.selected_key)+",\"selected_index\":"+std::to_string(v.selected_index);
  s+=",\"unavailable_reason\":"+JsonText(v.unavailable_reason)+",\"entries\":[";
  bool comma=false;for(const auto &e:v.entries){if(comma)s+=',';comma=true;s+="{\"value_key\":"+JsonText(e.value_key)+",\"selected\":"+(e.selected?"true":"false")+'}';}
  return s+"]}";
}
}
std::string SerializeAubPolicyMailboxV1(const AubPolicyMailboxContextV1 &q) {
  const bool action=q.action==AubPolicyMailboxActionV1::select;
  const auto &v=q.keyed_owner_before;
  std::string s="{\"schema\":\"ck3-aub-policy-options-v1\",\"step\":";
  s+=JsonText(action?kAubPolicySelectV1Step:kAubPolicyQueryV1Step);
  s+=",\"read_only\":";s+=action?"false":"true";
  s+=",\"game_version\":\"1.20.0.3\",\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\"";
  s+=",\"native_revision\":"+std::to_string(q.observation.native_revision);
  s+=",\"connection_generation\":"+std::to_string(q.observation.connection_generation);
  s+=",\"game_pid\":"+std::to_string(GetCurrentProcessId());
  s+=",\"played_character_id\":"+std::to_string(v.played_character_id)+",\"date_raw\":"+std::to_string(v.date_raw);
  s+=",\"tooltip_available\":false,\"enabled_available\":false,\"rendered_down_available\":false,\"production_confirmed\":false";
  s+=",\"before_actual_model\":"+SerializeIngameDecisionItemV1(q.keyed_owner_before);
  s+=",\"after_actual_model\":"+SerializeIngameDecisionItemV1(q.keyed_owner_after);
  if(action){
    const auto &a=q.select_result;
    s+=",\"before_policy\":"+PolicyJson(a.before)+",\"after_policy\":"+PolicyJson(a.after);
    s+=",\"expected_selected_key\":"+JsonText(q.expected_selected_key)+",\"desired_key\":"+JsonText(q.desired_key);
    const auto b=[&](const char *name,bool value){s+=",\"";s+=name;s+="\":";s+=value?"true":"false";};
    b("already_selected",a.already_selected);b("dispatch_invoked",a.dispatch_invoked);b("native_call_completed",a.native_call_completed);
    b("postcondition_verified",a.postcondition_verified);b("verification_pending",(a.dispatch_invoked||a.already_selected)&&!a.postcondition_verified);
    s+=",\"unavailable_reason\":"+JsonText(a.unavailable_reason);
  }else s+=",\"policy\":"+PolicyJson(q.query_result)+",\"unavailable_reason\":"+JsonText(q.query_result.unavailable_reason);
  return s+'}';
}
} // namespace xar::ck3_12003

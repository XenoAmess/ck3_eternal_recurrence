// Pure synthetic C++ tests; never start/attach CK3. ROOT executes after review.
#include "xar_bridge/ingame_decision_item_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include <array>
#include <limits>
#include <new>
#include <stdexcept>
#include <string>
#include <vector>
using namespace xar::ck3_11906;
namespace {
void Need(bool value,const char *why){if(!value)throw std::runtime_error(why);}
namespace frozen_source11 {
std::string SerializeIngameDecisionItemV1(const IngameDecisionItemResultV1 &v) {
  std::string s="{\"schema\":\"ck3-ingame-decision-item-v1\",\"step\":\"query-ingame-decision-item-v1\",\"read_only\":true,\"game_version\":\""+v.game_version+"\",\"executable_sha256\":\""+v.executable_sha256+"\"";
  const auto number=[&](const char *key,auto n){s+=",\"";s+=key;s+="\":";s+=std::to_string(n);};
  const auto boolean=[&](const char *key,bool b){s+=",\"";s+=key;s+="\":";s+=b?"true":"false";};
  const auto text=[&](const char *key,const std::string &value){s+=",\"";s+=key;s+="\":\"";s+=value;s+='"';};
  number("native_revision",v.native_revision);number("connection_generation",v.connection_generation);number("game_pid",v.game_pid);
  number("played_character_id",v.played_character_id);number("date_raw",v.date_raw);number("group_count",v.group_count);
  number("row_count",v.row_count);number("matching_row_count",v.matching_row_count);number("row_context_reference_key",v.row_context_reference_key);
  number("detail_actor_reference_key",v.detail_actor_reference_key);
  boolean("available",v.available);boolean("owner_thread_verified",v.owner_thread_verified);boolean("frame_verified",v.frame_verified);
  boolean("source_abi_pins_verified",v.source_abi_pins_verified);boolean("gui_owner_binding_verified",v.gui_owner_binding_verified);
  boolean("decisions_tree_complete",v.decisions_tree_complete);boolean("decisions_root_visible",v.decisions_root_visible);
  boolean("row_owner_verified",v.row_owner_verified);boolean("row_scope_reference_available",v.row_scope_reference_available);
  boolean("detail_tree_complete",v.detail_tree_complete);boolean("detail_root_visible",v.detail_root_visible);
  boolean("detail_definition_available",v.detail_definition_available);boolean("detail_definition_matches_target",v.detail_definition_matches_target);
  boolean("detail_actor_binding_verified",v.detail_actor_binding_verified);
  // Scope/context scalar is observed but deliberately not cast to player identity or action qualification.
  boolean("row_widget_datacontext_verified",false);boolean("action_qualified",false);
  if(!v.model_failed_stage.empty()){
    text("model_read_pass",v.model_read_pass);text("model_failed_stage",v.model_failed_stage);
    number("model_observed_pointer",v.model_observed_pointer);number("model_expected_pointer",v.model_expected_pointer);
  }
  text("decision_key",v.decision_key);text("detail_decision_key",v.detail_decision_key);text("unavailable_reason",v.unavailable_reason);return s+'}';
}}
namespace reviewed_candidate {
std::string SerializeIngameDecisionItemV1(const IngameDecisionItemResultV1 &v) {
  std::string s="{\"schema\":\"ck3-ingame-decision-item-v1\",\"step\":\"query-ingame-decision-item-v1\",\"read_only\":true,\"game_version\":\""+v.game_version+"\",\"executable_sha256\":\""+v.executable_sha256+"\"";
  const auto number=[&](const char *key,auto n){s+=",\"";s+=key;s+="\":";s+=std::to_string(n);};
  const auto boolean=[&](const char *key,bool b){s+=",\"";s+=key;s+="\":";s+=b?"true":"false";};
  const auto text=[&](const char *key,const std::string &value){s+=",\"";s+=key;s+="\":\"";s+=value;s+='"';};
  number("native_revision",v.native_revision);number("connection_generation",v.connection_generation);number("game_pid",v.game_pid);
  number("played_character_id",v.played_character_id);number("date_raw",v.date_raw);number("group_count",v.group_count);
  number("row_count",v.row_count);number("matching_row_count",v.matching_row_count);number("row_context_reference_key",v.row_context_reference_key);
  number("detail_actor_reference_key",v.detail_actor_reference_key);
  boolean("available",v.available);boolean("owner_thread_verified",v.owner_thread_verified);boolean("frame_verified",v.frame_verified);
  boolean("source_abi_pins_verified",v.source_abi_pins_verified);boolean("gui_owner_binding_verified",v.gui_owner_binding_verified);
  boolean("decisions_tree_complete",v.decisions_tree_complete);boolean("decisions_root_visible",v.decisions_root_visible);
  boolean("row_owner_verified",v.row_owner_verified);boolean("row_scope_reference_available",v.row_scope_reference_available);
  boolean("detail_tree_complete",v.detail_tree_complete);boolean("detail_root_visible",v.detail_root_visible);
  boolean("detail_definition_available",v.detail_definition_available);boolean("detail_definition_matches_target",v.detail_definition_matches_target);
  boolean("detail_actor_binding_verified",v.detail_actor_binding_verified);
  // Scope/context scalar is observed but deliberately not cast to player identity or action qualification.
  boolean("row_widget_datacontext_verified",false);boolean("action_qualified",false);
  if(!v.model_failed_stage.empty()){
    text("model_read_pass",v.model_read_pass);text("model_failed_stage",v.model_failed_stage);
    number("model_observed_pointer",v.model_observed_pointer);number("model_expected_pointer",v.model_expected_pointer);
  }
  if(v.completion_diagnostics.present){
    const auto &d=v.completion_diagnostics;
    s+=",\"completion_diagnostics\":{\"schema\":\"ck3-keyed-query-completion-diagnostics-v1\"";
    boolean("snapshot_read_succeeded",d.snapshot_read_succeeded);
    const auto optional_boolean=[&](const char *key,const std::optional<bool> &value){
      s+=",\"";s+=key;s+="\":";s+=value.has_value()?(*value?"true":"false"):"null";
    };
    optional_boolean("snapshot_equal",d.snapshot_equal);optional_boolean("state_revision_equal",d.state_revision_equal);
    number("expected_state_revision",d.expected_state_revision);
    s+=",\"compared_state_revision\":";s+=d.compared_state_revision.has_value()?std::to_string(*d.compared_state_revision):"null";
    number("post_guard_state_revision",d.post_guard_state_revision);
    text("first_failed_predicate",d.first_failed_predicate);
    s+=",\"changed_snapshot_fields\":[";
    for(std::size_t i=0;i<d.changed_snapshot_fields.size();++i){
      if(i)s+=',';s+='"';s+=d.changed_snapshot_fields[i];s+='"';
    }
    s+="]}";
  }
  text("decision_key",v.decision_key);text("detail_decision_key",v.detail_decision_key);text("unavailable_reason",v.unavailable_reason);return s+'}';
}}
// The failure block is projected from the reviewed production branch. Capture
// is an injected callable only so allocation and non-standard exceptions can
// be exercised; no diagnostic implementation is marked noexcept.
template<class Capture> void RejectBestEffort(IngameDecisionItemResultV1 &out,Capture capture){
  out.available=false;out.frame_verified=false;
  out.unavailable_reason="pipe_completion_keyed_query_binding_changed";
  try {out.completion_diagnostics=capture();}
  catch(...){out.completion_diagnostics.present=false;}
}
void GuardTruthPaths(){
  for(int path=0;path<4;++path){
    int reads=0,equals=0,revisions=0;
    bool read_ok=false,snapshot_equal=false,revision_equal=false;
    std::uint64_t compared=0;
    const auto read=[&](){++reads;return path!=0;};
    const auto equal=[&](){++equals;return path!=1;};
    const auto revision=[&](){++revisions;return path==2?145ULL:144ULL;};
    IngameDecisionItemResultV1 out{};out.available=true;out.frame_verified=true;
    xar::game::Snapshot expected{},completion{};
    if(path==1)++completion.played_character_stress_points;
    if(!(read_ok=read())||!(snapshot_equal=equal())||!(revision_equal=((compared=revision())==144ULL))){
      RejectBestEffort(out,[&](){return CaptureKeyedQueryCompletionFailureV1(read_ok,snapshot_equal,
          revision_equal,expected,completion,144,compared,146);});
    }
    Need(reads==1,"guard repeats native read");
    Need(equals==(path==0?0:1),"equality short circuit changed");
    Need(revisions==(path<2?0:1),"revision short circuit changed");
    if(path==3){Need(out.available&&out.frame_verified&&!out.completion_diagnostics.present,"success changed");continue;}
    const auto &d=out.completion_diagnostics;
    Need(!out.available&&!out.frame_verified&&out.unavailable_reason=="pipe_completion_keyed_query_binding_changed","original refusal lost");
    Need(d.present,"failure diagnostics missing");
    Need(d.first_failed_predicate==(path==0?"snapshot_read":path==1?"snapshot_equal":"state_revision_equal"),"wrong first predicate");
    Need(d.snapshot_equal.has_value()==(path!=0),"unknown snapshot comparison invented");
    Need(d.state_revision_equal.has_value()==(path==2),"unknown revision comparison invented");
    Need(d.compared_state_revision.has_value()==(path==2),"unknown compared revision invented");
    if(path==2)Need(*d.compared_state_revision==145&&d.post_guard_state_revision==146,"compared revision overwritten");
  }
}
struct Mutation{const char *name;void(*apply)(xar::game::Snapshot &);};
const std::array<Mutation,27> mutations{{
  {"date_raw",[](xar::game::Snapshot &s){++s.date_raw;}},
  {"speed",[](xar::game::Snapshot &s){++s.speed;}},
  {"paused",[](xar::game::Snapshot &s){s.paused=!s.paused;}},
  {"player_id",[](xar::game::Snapshot &s){++s.player_id;}},
  {"map_ready",[](xar::game::Snapshot &s){s.map_ready=!s.map_ready;}},
  {"has_played_character",[](xar::game::Snapshot &s){s.has_played_character=!s.has_played_character;}},
  {"played_character_id",[](xar::game::Snapshot &s){++s.played_character_id;}},
  {"played_character_alive",[](xar::game::Snapshot &s){s.played_character_alive=!s.played_character_alive;}},
  {"played_character_stress_points",[](xar::game::Snapshot &s){++s.played_character_stress_points;}},
  {"played_character_event_trait_membership",[](xar::game::Snapshot &s){s.played_character_event_trait_membership.emplace();}},
  {"played_character_gold",[](xar::game::Snapshot &s){++s.played_character_gold.raw;}},
  {"played_character_prestige",[](xar::game::Snapshot &s){++s.played_character_prestige.raw;}},
  {"played_character_piety",[](xar::game::Snapshot &s){++s.played_character_piety.raw;}},
  {"played_character_betrothed_id",[](xar::game::Snapshot &s){++s.played_character_betrothed_id;}},
  {"played_character_primary_spouse_id",[](xar::game::Snapshot &s){++s.played_character_primary_spouse_id;}},
  {"played_character_spouse_ids",[](xar::game::Snapshot &s){s.played_character_spouse_ids.push_back(42);}},
  {"has_active_event",[](xar::game::Snapshot &s){s.has_active_event=!s.has_active_event;}},
  {"active_event_instance_id",[](xar::game::Snapshot &s){++s.active_event_instance_id;}},
  {"active_event_option_count",[](xar::game::Snapshot &s){++s.active_event_option_count;}},
  {"has_pending_character_interaction",[](xar::game::Snapshot &s){s.has_pending_character_interaction=!s.has_pending_character_interaction;}},
  {"pending_character_interaction_id",[](xar::game::Snapshot &s){++s.pending_character_interaction_id;}},
  {"pending_sender_character_id",[](xar::game::Snapshot &s){++s.pending_sender_character_id;}},
  {"pending_auto_accept_notification",[](xar::game::Snapshot &s){s.pending_auto_accept_notification=!s.pending_auto_accept_notification;}},
  {"active_wars",[](xar::game::Snapshot &s){s.active_wars.emplace_back();}},
  {"player_armies",[](xar::game::Snapshot &s){s.player_armies.emplace_back();}},
  {"has_one_life_settlement",[](xar::game::Snapshot &s){s.has_one_life_settlement=!s.has_one_life_settlement;}},
  {"one_life_settlement",[](xar::game::Snapshot &s){++s.one_life_settlement.commit_serial;}},
}};
void AllSnapshotMembers(){
  const xar::game::Snapshot expected{};
  for(const auto &mutation:mutations){
    auto completion=expected;mutation.apply(completion);
    Need(completion!=expected,"mutation did not change actual default Snapshot equality");
    const auto d=CaptureKeyedQueryCompletionFailureV1(true,false,false,expected,completion,1,0,1);
    Need(d.changed_snapshot_fields==std::vector<std::string>{mutation.name},"Snapshot field omitted or mislabeled");
  }
  auto before=expected;before.player_armies.emplace_back();before.active_wars.emplace_back();
  auto after=before;after.player_armies.front().route_province_ids.push_back(42);++after.active_wars.front().player_relative_war_score;
  const auto nested=CaptureKeyedQueryCompletionFailureV1(true,false,false,before,after,1,0,1);
  Need(nested.changed_snapshot_fields==std::vector<std::string>{"active_wars","player_armies"},"nested compound equality reduced to counts");
  auto partial=expected;for(const auto &mutation:mutations)mutation.apply(partial);
  const auto unread=CaptureKeyedQueryCompletionFailureV1(false,false,false,expected,partial,1,0,2);
  Need(unread.changed_snapshot_fields.empty()&&!unread.snapshot_equal&&!unread.state_revision_equal,"partial unread Snapshot interpreted");
}
void RevisionAndWire(){
  xar::game::Snapshot same{};
  const auto maximum=(std::numeric_limits<std::uint64_t>::max)();
  const auto d=CaptureKeyedQueryCompletionFailureV1(true,true,false,same,same,maximum,maximum-1,7);
  Need(d.expected_state_revision==maximum&&d.compared_state_revision==maximum-1&&d.post_guard_state_revision==7,"uint64 revision truncated");
  IngameDecisionItemResultV1 out{};out.available=true;out.frame_verified=true;out.decision_key="lyd_change_school_decision";
  for(bool existing_failure:{false,true}){
    out.available=!existing_failure;out.frame_verified=!existing_failure;
    out.unavailable_reason=existing_failure?"old_noncompletion_failure":"";
    const auto baseline=frozen_source11::SerializeIngameDecisionItemV1(out);
    Need(reviewed_candidate::SerializeIngameDecisionItemV1(out)==baseline,"successful or noncompletion wire bytes changed");
    out.completion_diagnostics.expected_state_revision=maximum;
    out.completion_diagnostics.changed_snapshot_fields={"date_raw"};
    Need(reviewed_candidate::SerializeIngameDecisionItemV1(out)==baseline,"presentfalse stale fields leaked");
  }
  out.completion_diagnostics=d;
  auto wire=reviewed_candidate::SerializeIngameDecisionItemV1(out);
  const auto key=wire.find("\"completion_diagnostics\":{");Need(key!=std::string::npos,"diagnostic object missing");
  const auto begin=wire.find('{',key),end=wire.find('}',begin);
  const auto object=wire.substr(begin,end-begin+1);
  std::uint64_t parsed=0;std::string text;
  Need(xar::bridge::JsonUnsignedField(object,"expected_state_revision",parsed)&&parsed==maximum,"wire expected uint64 lost");
  Need(xar::bridge::JsonUnsignedField(object,"compared_state_revision",parsed)&&parsed==maximum-1,"wire compared uint64 lost");
  Need(xar::bridge::JsonStringField(object,"first_failed_predicate",text,64)&&text=="state_revision_equal","wire first predicate lost");
  out.completion_diagnostics=CaptureKeyedQueryCompletionFailureV1(false,false,false,same,same,1,0,2);
  wire=reviewed_candidate::SerializeIngameDecisionItemV1(out);
  Need(wire.find("\"snapshot_equal\":null")!=std::string::npos&&wire.find("\"state_revision_equal\":null")!=std::string::npos&&
       wire.find("\"compared_state_revision\":null")!=std::string::npos,"unknown serialized as false or zero");
}
void CaptureExceptionsPreserveRefusal(){
  for(bool allocation:{false,true}){
    IngameDecisionItemResultV1 out{};out.available=true;out.frame_verified=true;
    bool saw_refusal=false;
    RejectBestEffort(out,[&]() -> KeyedQueryCompletionDiagnosticsV1 {
      saw_refusal=!out.available&&!out.frame_verified&&out.unavailable_reason=="pipe_completion_keyed_query_binding_changed";
      if(allocation)throw std::bad_alloc{};
      throw 7;
    });
    Need(saw_refusal,"capture runs before refusal");
    Need(!out.available&&!out.frame_verified&&!out.completion_diagnostics.present,"capture exception escaped or lost refusal");
    Need(out.unavailable_reason=="pipe_completion_keyed_query_binding_changed","capture exception changed original reason");
  }
  IngameDecisionItemContextV1 next{};Need(!next.result.completion_diagnostics.present,"fresh query reused prior diagnostics");
}
} // namespace
void RunKeyedQueryCompletionDiagnosticsFocusedV1(){
  GuardTruthPaths();AllSnapshotMembers();RevisionAndWire();CaptureExceptionsPreserveRefusal();
}

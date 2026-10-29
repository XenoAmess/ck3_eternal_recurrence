// Serialization regression only. Receiver/model flags below are fixture inputs,
// never an assertion that the paused application mailbox or real GUI ran.
#define main OriginalAubPolicyDeltaMain
#include "tests/aub_policy_options_delta.cpp"
#undef main
#include "xar_bridge/aub_policy_options_mailbox_v1.hpp"
#include "xar_bridge/aub_business_state_v1.hpp"
#include <Windows.h>
#include <fstream>
#include <iterator>
#include <limits>
#include <cstdint>

namespace {
constexpr std::uint64_t kNativeRevision=std::numeric_limits<std::uint64_t>::max()-1;
constexpr std::uint64_t kGeneration=std::numeric_limits<std::uint64_t>::max();
xar::ck3_11906::IngameDecisionItemResultV1 model() {
  xar::ck3_11906::IngameDecisionItemResultV1 v{};
  v.native_revision=kNativeRevision;v.connection_generation=kGeneration;v.game_pid=GetCurrentProcessId();v.played_character_id=5;v.date_raw=1234;
  v.group_count=1;v.row_count=1;v.matching_row_count=1;v.row_context_reference_key=5;v.detail_actor_reference_key=5;
  v.available=true;v.owner_thread_verified=true;v.frame_verified=true;v.source_abi_pins_verified=true;v.gui_owner_binding_verified=true;
  v.decisions_tree_complete=true;v.decisions_root_visible=true;v.row_owner_verified=true;v.row_scope_reference_available=true;
  v.detail_tree_complete=true;v.detail_root_visible=true;v.detail_definition_available=true;v.detail_definition_matches_target=true;v.detail_actor_binding_verified=true;
  v.decision_key="enable_auto_build";v.detail_decision_key="enable_auto_build";return v;
}
xar::ck3_12003::AubBusinessStateResultV1 state(bool enabled) {
  xar::ck3_12003::AubBusinessStateResultV1 v{};
  v.native_revision=kNativeRevision;v.connection_generation=kGeneration;v.game_pid=GetCurrentProcessId();v.played_character_id=5;v.date_raw=1234;
  v.available=true;v.owner_thread_verified=true;v.frame_verified=true;v.source_abi_pins_verified=true;v.gui_owner_binding_verified=true;
  v.stable_two_pass_verified=true;v.detail_census_verified=true;v.detail_root_available=true;v.detail_tree_complete=true;v.detail_effectively_visible=!enabled;
  for(std::size_t i=0;i<v.flags.size();++i){auto &f=v.flags[i];f.key=xar::ck3_12003::kAubBusinessFlagKeysV1[i];f.available=true;f.atom_registered=true;f.present=enabled&&i==0;}
  return v;
}
}
int main(int argc,char **argv) {
  try {
    require(argc==3&&std::string_view(argv[1])=="serialization","serialization plus exact source-ref array path required");
    std::ifstream source_input(argv[2],std::ios::binary);require(source_input.good(),"exact serializer source refs unavailable");
    const std::string source_refs((std::istreambuf_iterator<char>(source_input)),std::istreambuf_iterator<char>());
    require(!source_refs.empty()&&source_refs.size()<131072,"bounded exact source refs required");
    Harness h;const auto initial=h.query();require(initial.ready,"actual original policy probe failed");
    const auto selected=h.select();require(selected.dispatch_invoked&&selected.native_call_completed&&selected.postcondition_verified&&h.memory.action_calls==1,"actual source selection failed or repeated");
    const auto later=h.query();require(later.ready&&later.selected_key==selected.after.selected_key,"actual independent policy probe differs");
    xar::ck3_12003::AubPolicyMailboxContextV1 q{};q.observation.native_revision=kNativeRevision;q.observation.connection_generation=kGeneration;q.keyed_owner_before=model();q.keyed_owner_after=model();q.query_result=initial;
    const auto query_before=xar::ck3_12003::SerializeAubPolicyMailboxV1(q);
    q.action=xar::ck3_12003::AubPolicyMailboxActionV1::select;q.expected_selected_key=initial.selected_key;q.desired_key=selected.after.selected_key;q.select_result=selected;
    const auto select=xar::ck3_12003::SerializeAubPolicyMailboxV1(q);
    q.action=xar::ck3_12003::AubPolicyMailboxActionV1::query;q.query_result=later;
    const auto query_after=xar::ck3_12003::SerializeAubPolicyMailboxV1(q);
    xar::ck3_12003::AubConfirmResultV1 c{};c.keyed_before=model();c.policy_before=later;c.state_before=state(false);c.state_after=state(true);
    c.receiver_qualified=true;c.selected_policy_revalidated=true;c.dispatch_attempted=true;c.dispatch_invoked=true;c.native_handled=true;c.postcondition_verified=true;c.selected_key=later.selected_key;c.target_child_path="fixture-confirm-receiver";
    require(xar::ck3_12003::AubFlagsMatchSelectedPolicyV1(c.selected_key,c.state_after),"production six-policy flag tuple differs");
    std::cout<<"{\"schema\":\"xar.aub.actual-native-family-serialization-input/v1\",\"fixture_scope\":\"production_serializers_and_offline_source_selection_only\",\"real_gui_confirm_executed\":false,\"producer_sources\":"<<source_refs;
    std::cout<<",\"binding\":{\"machine_id\":\"fixture-machine\",\"game_pid\":"<<GetCurrentProcessId()<<",\"game_birth_filetime\":\"1\",\"played_character_id\":5,\"native_revision\":"<<kNativeRevision<<",\"date_raw\":1234,\"snapshot_id\":\"aub-serialization-fixture\",\"public_revision\":\"18446744073709551615\",\"episode_run_id\":\"aub-serialization-episode\",\"connection_generation\":\""<<kGeneration<<"\"}";
    std::cout<<",\"desired_key\":\""<<later.selected_key<<"\",\"options_before\":"<<query_before<<",\"select\":"<<select<<",\"options_after\":"<<query_after;
    std::cout<<",\"confirm\":"<<xar::ck3_12003::SerializeAubConfirmV1(c)<<",\"business_after\":"<<xar::ck3_12003::SerializeAubBusinessStateV1(c.state_after)<<"}\n";return 0;
  } catch(const std::exception &failure){std::cerr<<failure.what()<<'\n';return 1;}
}

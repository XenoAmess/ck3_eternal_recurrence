#include "xar_bridge/ck3_12002_sway_completion_execution_mailbox.hpp"
#include "xar_bridge/ck3_12002_sway_completion_termination_mailbox.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/sway_child_end_causal_path_12004.hpp"
#include <iostream>

// This new fixture exercises the existing retained record/query/envelope
// serializers and the optional whole wire. Native entry/read/ABI/source-path
// qualification belongs to21/22/27 and is reused, not replayed here.
int main() {
  using namespace xar::ck3_12002;
  constexpr std::uint32_t actor = 29829;
  constexpr std::uint32_t target = 31900;
  constexpr std::uint32_t scheme = 0x02000016;
  SwayExecutionSource12002 complete{};
  complete.branch = SwayExecutionSourceBranch12002::authored_sway_complete_100_source;
  complete.date_raw = 53289936;
  complete.actor_character_id = actor; complete.target_character_id = target; complete.scheme_id = scheme;
  complete.root = {4, 0, 0, actor}; complete.owner = complete.root;
  complete.target = {4, 0, 0, target}; complete.scheme = {9, 0, 0, scheme};
  const SwayExecutionInvocation12004 parent{9, 7, 41};
  SwayExecutionRecorder12002 execution{};
  execution.SetObserverAttached(true);
  std::uint64_t sequence = 0;
  if (!execution.Append(complete, &sequence, &parent) || sequence != 1) return 1;
  SwayExecutionQueryResult12002 execution_query{};
  if (!execution.Query({actor, target, scheme, 0}, execution_query)) return 2;

  SwayTerminationSource12002 end{};
  end.source_class = SwayTerminationSourceClass12002::authored_end_scheme_true_execute;
  end.date_raw = complete.date_raw; end.actor_character_id = actor;
  end.target_character_id = target; end.scheme_id = scheme;
  end.input_root_scope_kind = 9; end.pre_status = 0; end.pre_owner = actor;
  end.executing_source_observed = true; end.post_read_succeeded = true;
  end.post_instance_present = true; end.post_exact_instance_join_ready = true;
  end.post_status_observed = true; end.post_status = 1; end.post_owner = 0xFFFFFFFFu;
  end.native_terminal_state_observed = true; end.native_terminal_transition_observed = true;
  SwayTerminationInvocation12004 detail{};
  detail.present = true; detail.observer_session_identity = parent.observer_session_identity;
  detail.owner_thread_id = parent.owner_thread_id; detail.original_invocation_id = 42;
  detail.original_rva = xar::ck3_12004::kSwayEndInvocationOriginalRvas12004[2];
  detail.incoming_return_address_observed = true;
  detail.caller_return_rva = xar::ck3_12004::kSwayChildEndReturn12004;
  detail.original_forwarded_once = true; detail.original_returned = true;
  detail.pre_frame_observed = true; detail.pre_date_raw = complete.date_raw;
  detail.post_frame_observed = true; detail.post_date_raw = complete.date_raw;
  detail.causal_relationship_observed = true; detail.branch_source_sequence = sequence;
  detail.parent_toast_invocation_id = parent.toast_invocation_id;
  detail.native_returns_observed = true; detail.native_return_count = 3;
  detail.native_return_rvas[0] = xar::ck3_12004::kSwayChildEndReturn12004;
  detail.native_return_rvas[1] = xar::ck3_12004::kSwayChildDispatcherReturn12004;
  detail.native_return_rvas[2] = xar::ck3_12004::kSwayToastChildReturn12004;
  SwayTerminationRecorder12002 termination{};
  termination.SetObserverAttached(true);
  if (!termination.Append(end, &detail)) return 3;
  SwayTerminationQueryResult12002 termination_query{};
  if (!termination.Query({actor, target, scheme, 0}, termination_query)) return 4;
  std::cout << "{\"execution\":" << SerializeSwayCompletionExecutionCommandResultV1(
      execution_query, 71, complete.date_raw, "new-wholewire-execution",
      xar::ck3_12004::kGameVersion, xar::ck3_12004::kExecutableSha256)
      << ",\"termination\":" << SerializeSwayCompletionTerminationCommandResultV1(
      termination_query, 71, complete.date_raw, "new-wholewire-termination",
      xar::ck3_12004::kGameVersion, xar::ck3_12004::kExecutableSha256) << "}";
  return 0;
}

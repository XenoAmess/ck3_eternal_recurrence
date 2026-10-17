#pragma once
#include "xar_bridge/ck3_12004_county_predicate_trace_context.hpp"
#include "xar_bridge/ck3_12004_county_relation_inputs_reader.hpp"

namespace xar::ck3_12004 {
using CountyRelationOriginal12004 = CountyPredicateOriginal12004;

inline bool InvokeCountyRelationInputs12004(CountyRelationOriginal12004 original,
    void *receiver, void *actor, std::uintptr_t auxiliary, std::uintptr_t opaque_r9,
    std::optional<std::uint64_t> bridge_caller, std::uint32_t thread,
    const ArmyRegularCoreReadonlyAccess12004 &access) {
  if (!original) return false;
  auto *const frame = g_county_predicate_trace12004;
  // Native helper-internal calls return into CK3, not the bridge. The P tail
  // return has the actual bridge provenance supplied by the installed hook.
  if (!frame || !frame->trace.scope_entered || !bridge_caller ||
      !frame->active_relation_stage || frame->callback_depth != 1 ||
      frame->relation_callback_depth != 0)
    return original(receiver, actor, auxiliary, opaque_r9);
  const auto stage_index = *frame->active_relation_stage;
  if (stage_index >= frame->trace.stages.size())
    return original(receiver, actor, auxiliary, opaque_r9);
  auto &stage = frame->trace.stages[stage_index];
  if (stage.argument_identity_matched != true || stage.call_count != 1)
    return original(receiver, actor, auxiliary, opaque_r9);
  ++frame->relation_callback_depth;
  struct DepthExit {
    CountyPredicateTraceFrame12004 *frame;
    ~DepthExit() { --frame->relation_callback_depth; }
  } depth_exit{frame};
  if (stage.relation_inputs_v1) {
    auto &duplicate = *stage.relation_inputs_v1;
    ++duplicate.call_count;
    duplicate.available = false;
    duplicate.unavailable_reason = "county_relation_multiple_tail_calls";
    return original(receiver, actor, auxiliary, opaque_r9);
  }
  stage.relation_inputs_v1 = ReadCountyRelationInputs12004(access,
      reinterpret_cast<std::uintptr_t>(receiver),
      reinterpret_cast<std::uintptr_t>(actor), auxiliary);
  auto &out = *stage.relation_inputs_v1;
  out.call_count = 1;
  out.actual_bridge_caller_return_rva = bridge_caller;
  out.argument_identity_matched = actor == frame->actor && auxiliary == 0;
  out.same_thread = thread == frame->thread_id;
  const bool result = original(receiver, actor, auxiliary, opaque_r9);
  out.returned = result; // Never replace the naturally returned AL.
  const auto receiver_after = ReadCountyRelationFullId12004(access,
      reinterpret_cast<std::uintptr_t>(receiver));
  const auto actor_after = ReadCountyRelationFullId12004(access,
      reinterpret_cast<std::uintptr_t>(actor));
  if (out.receiver_full_id && out.actor_full_id && receiver_after && actor_after)
    out.identity_before_after_match = out.receiver_full_id == receiver_after &&
                                     out.actor_full_id == actor_after;
  out.available = out.argument_identity_matched && out.same_thread &&
                  out.identity_before_after_match == true;
  out.unavailable_reason = out.available ? "" :
      "county_relation_arguments_thread_or_full_ids_unstable";
  return result;
}
}

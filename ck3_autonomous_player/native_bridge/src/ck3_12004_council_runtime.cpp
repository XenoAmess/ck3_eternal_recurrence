#include "xar_bridge/ck3_12004_council_runtime.hpp"

namespace xar::ck3_12004 {

bool ExecuteCouncilMailbox12004(void* raw,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept {
  if (raw == nullptr) return false;
  auto& context = *static_cast<CouncilMailboxContext12004*>(raw);
  if (context.operation !=
      bridge::CouncilApplicationMainOperationV1::query_candidates)
    return ExecuteCouncilActionMailbox12004(raw, stamp);
  context.wire.operation = context.operation;
  context.wire.ticket = context.ticket;
  context.wire.completion =
      bridge::CouncilApplicationMainCompletionV1::infrastructure_red;
  context.wire.failure = bridge::CouncilApplicationMainFailureV1::none;
  context.wire.failure_reason.clear();
  context.wire.query_result = {};
  context.active_stamp = &stamp;
  struct Clear {
    CouncilMailboxContext12004& context;
    ~Clear() { context.active_stamp = nullptr; }
  } clear{context};
  try {
    if (stamp.thread_id == 0 || !stamp.paused || stamp.game_state == 0 ||
        !context.candidates_environment.exact_build_admitted ||
        context.candidates_environment.admitted_executable_sha256 !=
            kExecutableSha256) {
      context.wire.failure_reason = "requires_exact_paused_application_main";
      return true;
    }
    const bool available = ReadCouncilCandidates12004(
        context.candidates_environment, context.candidates_access,
        context.query_request, context.wire.query_result) ==
        ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1::available;
    context.wire.completion = available ?
        bridge::CouncilApplicationMainCompletionV1::query_available :
        bridge::CouncilApplicationMainCompletionV1::query_unavailable;
    return true;
  } catch (...) {
    context.wire.failure_reason = "council_executor_exception";
    return false;
  }
}

std::string SerializeCouncilMailbox12004(
    const CouncilMailboxContext12004& context, std::string_view request_id) {
  const auto candidates = SerializeCouncilCandidates12004(context.wire.query_result);
  return bridge::SerializeCouncilApplicationMainResultEnvelopeWithCandidatesV1(
      context.wire, request_id, candidates);
}

} // namespace xar::ck3_12004

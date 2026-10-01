#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>

namespace xar::ck3_12002 {
namespace {
bool Parse(std::string_view payload, std::uint64_t &expected_revision,
           SwayInvalidationReasonQuery12002 &request) noexcept {
  std::uint64_t actor{}, target{}, scheme{};
  if (!bridge::JsonUnsignedField(payload, "expected_revision", expected_revision) ||
      !bridge::JsonUnsignedField(payload, "actor_character_id", actor) ||
      !bridge::JsonUnsignedField(payload, "target_character_id", target) ||
      !bridge::JsonUnsignedField(payload, "scheme_instance_id", scheme) ||
      !bridge::JsonUnsignedField(payload, "after_sequence", request.after_sequence) ||
      actor > std::numeric_limits<std::int32_t>::max() ||
      target > std::numeric_limits<std::int32_t>::max() ||
      scheme >= std::numeric_limits<std::uint32_t>::max()) {
    return false;
  }
  request.actor_character_id = static_cast<std::uint32_t>(actor);
  request.target_character_id = static_cast<std::uint32_t>(target);
  request.scheme_id = static_cast<std::uint32_t>(scheme);
  return expected_revision != 0 && actor != 0 && target != 0 && actor != target;
}
} // namespace

bool HandleSwayCompletionInvalidationReasonV1(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const SwayInvalidationReasonRecorder12002 &recorder,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear();
  failure.clear();
  try {
    SwayCompletionInvalidationReasonMailboxContextV1 query{};
    std::uint64_t expected_revision{};
    if (step != kSwayCompletionInvalidationReasonStepV1 || !Parse(payload, expected_revision, query.request) ||
        expected_revision != revision || !adapter.enabled() ||
        xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 ||
        !published.paused || !published.map_ready || !published.has_played_character ||
        !published.played_character_alive ||
        static_cast<std::uint32_t>(published.played_character_id) != query.request.actor_character_id) {
      failure = "sway_invalidation_reason_frame_or_request_invalid";
      return false;
    }
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = &query;
    query.recorder = &recorder;
    if (TrySubmitMainThreadQueryV1(mailbox, &ExecuteSwayCompletionInvalidationReasonMailboxV1,
                                  &query.envelope, query.envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "sway_invalidation_reason_executor_unavailable";
      return false;
    }
    auto waited = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 8000);
    while (waited == MainThreadQueryWaitResultV1::timeout_executor_already_running) {
      waited = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 2000);
    }
    const auto reclaimed = ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (waited != MainThreadQueryWaitResultV1::completed ||
        reclaimed != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !query.envelope.frame_stable || !query.failure.empty()) {
      failure = query.failure.empty() ? "sway_invalidation_reason_executor_result_unavailable" : query.failure;
      return false;
    }
    serialized = SerializeSwayCompletionInvalidationReasonCommandResultV1(
        query.result, revision, query.envelope.execution_stamp.date_raw, request_id);
    return true;
  } catch (...) {
    failure = "sway_invalidation_reason_handler_exception";
    return false;
  }
}

} // namespace xar::ck3_12002

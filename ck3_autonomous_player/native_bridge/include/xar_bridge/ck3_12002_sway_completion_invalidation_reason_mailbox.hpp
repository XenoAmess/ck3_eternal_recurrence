#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kSwayCompletionInvalidationReasonStepV1 =
    "query-sway-completion-invalidation-reason-v1-private";

struct SwayCompletionInvalidationReasonMailboxContextV1 {
  QueryMailboxEnvelope envelope{};
  const SwayInvalidationReasonRecorder12002 *recorder = nullptr;
  SwayInvalidationReasonQuery12002 request{};
  SwayInvalidationReasonQueryResult12002 result{};
  bool completed = false;
  std::string failure;
};

std::string SerializeSwayCompletionInvalidationReasonCommandResultV1(
    const SwayInvalidationReasonQueryResult12002 &output, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view request_id);

bool ExecuteSwayCompletionInvalidationReasonMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Reads copied records from the recorder owned by the actual native entry
// installer. This handler cannot attach an observer or create native records.
bool HandleSwayCompletionInvalidationReasonV1(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const SwayInvalidationReasonRecorder12002 &recorder,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002

#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_sway_completion_termination.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kSwayCompletionTerminationStepV1 =
    "query-sway-completion-termination-v1-private";

struct SwayCompletionTerminationMailboxContextV1 {
  QueryMailboxEnvelope envelope{};
  const SwayTerminationRecorder12002 *recorder = nullptr;
  SwayTerminationQuery12002 request{};
  SwayTerminationQueryResult12002 result{};
  bool completed = false;
  std::string failure;
};

std::string SerializeSwayCompletionTerminationCommandResultV1(
    const SwayTerminationQueryResult12002 &output, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view request_id,
    std::string_view build_version = "1.20.0.2",
    std::string_view executable_sha256 = kExecutableSha256);

bool ExecuteSwayCompletionTerminationMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Reads copied records from the recorder owned by the actual native entry
// installer. This handler cannot attach an observer or create native records.
bool HandleSwayCompletionTerminationV1(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const SwayTerminationRecorder12002 &recorder,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002

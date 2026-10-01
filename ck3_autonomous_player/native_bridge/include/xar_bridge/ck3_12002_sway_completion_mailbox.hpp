#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_sway_completion.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kSwayCompletionStepV1 =
    "query-sway-completion-v1-private";

struct SwayCompletionMailboxContextV1 {
  QueryMailboxEnvelope envelope{};
  SwayCompletionBindings12002 bindings{};
  SwayCompletionRequestV1 request{};
  SwayCompletionStateV1 result{};
  bool completed = false;
  std::string failure;
};

std::string SerializeSwayCompletion12002(const SwayCompletionStateV1 &output,
                                       std::uint64_t snapshot_revision,
                                       std::int32_t date_raw);

// The worker and offline fixture use this same production envelope formatter.
std::string SerializeSwayCompletionCommandResultV1(
    const SwayCompletionStateV1 &output, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view request_id);

bool ExecuteSwayCompletionMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Payload: expected_revision, actor_character_id, target_character_id and
// scheme_instance_id. This is a readonly query of the exact tracked instance.
bool HandleSwayCompletionV1(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002

#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_sway_outcome.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kSwayOutcomeEventStepV1 =
    "query-sway-outcome-event-v1-private";
inline constexpr std::string_view kSwayOutcomeOpinionStepV1 =
    "query-sway-outcome-opinion-v1-private";

struct SwayOutcomeMailboxContextV1 {
  QueryMailboxEnvelope envelope{};
  SwayOutcomeBindings bindings{};
  SwayOutcomeRequestV1 request{};
  SwayOutcomeEventV1 result{};
  SwayOutcomeOpinionV1 opinion_result{};
  bool opinion_only = false;
  bool completed = false;
  std::string failure;
};

bool ExecuteSwayOutcomeMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Payload: expected_revision, event_instance_id, actor_character_id,
// target_character_id and scheme_instance_id (all JSON integers).
// Opinion selector: expected_revision, actor_character_id, target_character_id.
// The bridge selector routes either kSwayOutcome*StepV1 to this helper.
bool HandleSwayOutcomeEventV1(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002

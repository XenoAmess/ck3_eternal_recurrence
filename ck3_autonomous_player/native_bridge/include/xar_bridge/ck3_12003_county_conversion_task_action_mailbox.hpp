#pragma once

#include "xar_bridge/ck3_12003_county_conversion_task_action_v1.hpp"
#include "xar_bridge/ck3_12004_county_conversion_task_action_v1.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerCountyConversionTaskSubmitStep12003 =
    "county-conversion-task-submit-private-v1";
inline constexpr std::string_view kPlayerCountyConversionTaskResultStep12003 =
    "county-conversion-task-result-private-v1";

struct PlayerCountyConversionTaskActionMailboxState12003 {
  ck3_12003::religion::county_conversion::action::Submission submission;
  std::uint64_t submission_sequence = 0;
  bool has_submission = false;
  bool verification_pending = false;
};

enum class PlayerCountyConversionTaskActionMode12003 { submit, result };

// Internal owning mailbox context shared by the existing handler and new
// whole production-path fixture. No context or native pointer enters the SDK.
struct PlayerCountyConversionTaskActionMailboxContext12003 {
  QueryMailboxEnvelope envelope{};
  PlayerCountyConversionTaskActionMailboxState12003 *state = nullptr;
  PlayerCountyConversionTaskActionMode12003 mode =
      PlayerCountyConversionTaskActionMode12003::submit;
  ck3_12003::religion::county_conversion::action::Request request{};
  std::optional<ck3_12004::religion::county_conversion::action::Access> access12004;
  std::uint64_t public_revision = 0;
  std::string request_id;
  std::string submitted_request_id;
  std::string action_id;
  ck3_12003::religion::county_conversion::action::Submission submission{};
  ck3_12003::religion::county_conversion::action::IndependentResult independent_result{};
  std::string status;
  std::string failure;
  bool complete = false;
};

bool IsPlayerCountyConversionTaskActionPrivateStep12003(std::string_view) noexcept;
bool ExecutePlayerCountyConversionTaskActionMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
bool ParsePlayerCountyConversionTaskActionRequest12003(
    std::string_view payload, std::uint64_t native_revision,
    PlayerCountyConversionTaskActionMailboxContext12003 &) noexcept;

// The same fixed named executor, wait/reclaim and serializer used by Handle.
bool RunPlayerCountyConversionTaskActionMailbox12003(
    PlayerCountyConversionTaskActionMailboxContext12003 &,
    std::string_view step, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerCountyConversionTaskActionPrivate12003(
    PlayerCountyConversionTaskActionMailboxState12003 &,
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t native_revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002

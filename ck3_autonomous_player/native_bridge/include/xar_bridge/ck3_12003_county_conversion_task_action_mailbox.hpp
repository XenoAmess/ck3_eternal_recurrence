#pragma once

#include "xar_bridge/ck3_12003_county_conversion_task_action_v1.hpp"
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

bool IsPlayerCountyConversionTaskActionPrivateStep12003(std::string_view) noexcept;
bool ExecutePlayerCountyConversionTaskActionMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
bool HandlePlayerCountyConversionTaskActionPrivate12003(
    PlayerCountyConversionTaskActionMailboxState12003 &,
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t native_revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002

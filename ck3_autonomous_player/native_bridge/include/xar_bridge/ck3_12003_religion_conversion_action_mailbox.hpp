#pragma once

#include "xar_bridge/ck3_12003_religion_conversion_action_v1.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionConversionSubmitStep12003 =
    "submit-player-religion-conversion-private-v1";
inline constexpr std::string_view kPlayerReligionConversionResultStep12003 =
    "query-player-religion-conversion-result-private-v1";

// The existing bridge worker owns this value across MCP reconnections. Owner
// callbacks retain the actual queued request and its independently read before.
struct PlayerReligionConversionActionMailboxState12003 {
  religion_conversion::action12003::Submission submission;
  std::uint64_t submission_sequence = 0;
  bool has_submission = false;
  bool verification_pending = false;
};

bool IsPlayerReligionConversionActionPrivateStep12003(std::string_view) noexcept;
bool ExecutePlayerReligionConversionActionMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
bool HandlePlayerReligionConversionActionPrivate12003(
    PlayerReligionConversionActionMailboxState12003 &,
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t native_revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002

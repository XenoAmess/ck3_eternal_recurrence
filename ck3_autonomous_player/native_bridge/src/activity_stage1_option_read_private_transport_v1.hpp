#pragma once

#include "xar_bridge/activity_stage1_option_read_v1.hpp"
#include "xar_bridge/activity_stage2_gate_read_v1.hpp"
#include "xar_bridge/activity_stage2_location_read_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityStage1OptionReadPrivateStepV1 =
    "query-activity-stage1-option-v1-private";
inline constexpr std::string_view kActivityStage1ConfirmPrivateStepV1 =
    "confirm-activity-feast-stage1-v1-private";
inline constexpr std::string_view kActivityStage2OptionReadPrivateStepV1 =
    "query-activity-feast-stage2-option-v1-private";
inline constexpr std::string_view kActivityStage2GateReadPrivateStepV1 =
    "query-activity-feast-stage2-gate-v1-private";
inline constexpr std::string_view kActivityStage2LocationReadPrivateStepV1 =
    "query-activity-feast-stage2-location-v1-private";

struct ActivityStage1OptionReadPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bool confirm_stage_one = false;
  bool stage_two_read = false;
  bool stage_two_gate_read = false;
  bool stage_two_location_read = false;
  std::array<std::int32_t, bridge::kActivityStage2MaximumCandidatesV1>
      candidate_province_ids{};
  std::uint16_t candidate_province_count = 0;
  bridge::ActivityStage1OptionReadResultV1 result{};
  bridge::ActivityStage2OptionReadResultV1 stage_two_result{};
  bridge::ActivityStage2GateReadResultV1 stage_two_gate_result{};
  bridge::ActivityStage2LocationReadResultV1 stage_two_location_result{};
  bridge::ActivityStage1ConfirmResultV1 confirm_result{};
  game::Snapshot post_snapshot{};
  bool post_snapshot_read = false;
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityStage1OptionReadPrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityStage1OptionReadPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query);
std::string SerializeActivityStage1ConfirmPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query);
std::string SerializeActivityStage2OptionReadPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query);
std::string SerializeActivityStage2GateReadPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query);
std::string SerializeActivityStage2LocationReadPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query);
bool ParseActivityStage2CandidateIdsV1(
    std::string_view json,
    std::array<std::int32_t, bridge::kActivityStage2MaximumCandidatesV1>
        &output,
    std::uint16_t &count) noexcept;

} // namespace xar::ck3_11906

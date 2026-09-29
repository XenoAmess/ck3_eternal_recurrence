#pragma once

#include "xar_bridge/activity_stage1_option_read_v1.hpp"
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

struct ActivityStage1OptionReadPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bool confirm_stage_one = false;
  bridge::ActivityStage1OptionReadResultV1 result{};
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

} // namespace xar::ck3_11906

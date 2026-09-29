#pragma once

#include "xar_bridge/activity_feast_guest_opinion_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityFeastGuestOpinionPrivateStepV1 =
    "query-activity-feast-guest-opinion-v1";

struct ActivityFeastGuestOpinionPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  std::int32_t guest_character_id = -1;
  bridge::ActivityFeastGuestOpinionResultV1 opinion{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityFeastGuestOpinionPrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityFeastGuestOpinionPrivateV1(
    const ActivityFeastGuestOpinionPrivateQueryV1 &query);

} // namespace xar::ck3_11906

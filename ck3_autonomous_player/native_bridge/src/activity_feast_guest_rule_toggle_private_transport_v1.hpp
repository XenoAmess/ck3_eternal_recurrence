#pragma once

#include "xar_bridge/activity_feast_guest_rule_toggle_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityFeastGuestRuleReadPrivateStepV1 =
    "query-activity-feast-guest-rule-v1";
inline constexpr std::string_view kActivityFeastGuestRuleActivatePrivateStepV1 =
    "activate-activity-feast-guest-rule-v1";

struct ActivityFeastGuestRulePrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  std::string authored_rule_key{};
  bool activate = false;
  bool policy_approved = false;
  bridge::ActivityFeastGuestRuleResultV1 rule{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityFeastGuestRulePrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityFeastGuestRulePrivateV1(
    const ActivityFeastGuestRulePrivateQueryV1 &query);

} // namespace xar::ck3_11906

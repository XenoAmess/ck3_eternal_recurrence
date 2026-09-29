#pragma once

#include "xar_bridge/activity_feast_guest_rule_toggle_v1.hpp"
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
#include "xar_bridge/activity_feast_guest_rule_provenance_v1.hpp"
#endif
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
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
inline constexpr std::string_view kActivityFeastGuestRuleProvenancePrivateStepV1 =
    "query-activity-feast-guest-rule-provenance-v1";
#endif

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
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
  bridge::ActivityGuestRuleProvenanceObserverV1 *provenance_observer = nullptr;
  std::uint32_t candidate_character_id = 0;
  bool query_provenance = false;
  bridge::ActivityGuestRuleProvenanceResultV1 provenance{};
#endif
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityFeastGuestRulePrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityFeastGuestRulePrivateV1(
    const ActivityFeastGuestRulePrivateQueryV1 &query);
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
std::string SerializeActivityFeastGuestRuleProvenancePrivateV1(
    const ActivityFeastGuestRulePrivateQueryV1 &query);
#endif

} // namespace xar::ck3_11906

#pragma once

#include "xar_bridge/activity_feast_guest_candidate_v1.hpp"
#include "xar_bridge/activity_stage5_canstart_read_v1.hpp"
#include "xar_bridge/activity_feast_guest_rule_toggle_v1.hpp"
#include "xar_bridge/activity_feast_guest_opinion_v1.hpp"
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
#include "xar_bridge/activity_feast_guest_rule_provenance_v1.hpp"
#endif
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12002 {
using ck3_11906::MainThreadQueryMailboxV1;
using ck3_11906::MainThreadQueryTicketV1;
using ck3_11906::MainThreadExecutionStampV1;
struct ActivityFeastGuestTransportSource12002 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  void *snapshot_context = nullptr;
  bool (*read_snapshot)(void *, game::Snapshot &) noexcept = nullptr;
};
inline constexpr std::string_view kActivityFeastGuestCandidatePrivateStepV1 =
    "query-activity-feast-guest-candidate-v1";
inline constexpr std::string_view kActivityFeastGuestRouteProofPrivateStepV1 =
    "query-activity-feast-stage5-guest-route-proof-v1-private";
inline constexpr std::string_view kActivityFeastGuestTargetPrivateStepV1 =
    "query-activity-feast-stage5-guest-target-v1-private";

struct ActivityFeastGuestCandidatePrivateQueryV1 : ActivityFeastGuestTransportSource12002 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};

  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  bool route_proof = false;
  std::int32_t target_character_id = 0;
  bridge::ActivityFeastGuestCandidateResultV1 candidate{};
  bridge::ActivityFeastGuestJoinResultV1 selected_guests{};
  bridge::ActivityStage5CanStartResultV1 start_gate{};
  bool route_proof_consistent = false;
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityFeastGuestCandidatePrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityFeastGuestCandidatePrivateV1(
    const ActivityFeastGuestCandidatePrivateQueryV1 &query);
std::string SerializeActivityFeastGuestRouteProofPrivateV1(
    const ActivityFeastGuestCandidatePrivateQueryV1 &query);
std::string SerializeActivityFeastGuestTargetPrivateV1(
    const ActivityFeastGuestCandidatePrivateQueryV1 &query);


inline constexpr std::string_view kActivityFeastGuestRuleReadPrivateStepV1 =
    "query-activity-feast-guest-rule-v1";
inline constexpr std::string_view kActivityFeastGuestRuleActivatePrivateStepV1 =
    "activate-activity-feast-guest-rule-v1";
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
inline constexpr std::string_view kActivityFeastGuestRuleProvenancePrivateStepV1 =
    "query-activity-feast-guest-rule-provenance-v1";
#endif

struct ActivityFeastGuestRulePrivateQueryV1 : ActivityFeastGuestTransportSource12002 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};

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
// Read the existing rule/provenance sources on an already owned application-
// main execution. No mailbox submission, Toggle or scripted effect invocation.
bool ReadActivityFeastGuestRuleSources12002V1(
    ActivityFeastGuestRulePrivateQueryV1 &query,
    std::uint32_t owner_thread_id) noexcept;
std::string SerializeActivityFeastGuestRulePrivateV1(
    const ActivityFeastGuestRulePrivateQueryV1 &query);
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
std::string SerializeActivityFeastGuestRuleProvenancePrivateV1(
    const ActivityFeastGuestRulePrivateQueryV1 &query);
#endif


inline constexpr std::string_view kActivityFeastGuestOpinionPrivateStepV1 =
    "query-activity-feast-guest-opinion-v1";

struct ActivityFeastGuestOpinionPrivateQueryV1 : ActivityFeastGuestTransportSource12002 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};

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


} // namespace xar::ck3_12002

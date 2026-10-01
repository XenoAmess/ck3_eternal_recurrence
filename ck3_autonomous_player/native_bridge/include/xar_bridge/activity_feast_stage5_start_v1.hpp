#pragma once

#include "xar_bridge/activity_feast_resource_balance_v1.hpp"
#include "xar_bridge/activity_stage5_feast_full_cost_v1.hpp"
#include "xar_bridge/activity_stage5_feast_guest_join_v1.hpp"
#include "xar_bridge/activity_feast_guest_candidate_v1.hpp"
#include "xar_bridge/activity_feast_guest_rule_toggle_v1.hpp"
#include "xar_bridge/activity_feast_guest_rule_provenance_v1.hpp"
#include "xar_bridge/ck3_12002_feast_outcome_values.hpp"

#include <array>
#include <cstdint>

namespace xar::bridge {

// One observed ordinary category route, kept separate from selected guest rows.
// The source is the original natural rule effect intersected with its native
// filter, paired with a current native candidate prediction. This is no claim
// that an invitation was sent or that a guest accepted it.
struct ActivityFeastOrdinaryGuestRouteV1 {
  ActivityFeastGuestCandidateResultV1 candidate{};
  ActivityFeastGuestRuleStatusV1 rule_status =
      ActivityFeastGuestRuleStatusV1::exact_build_rejected;
  ActivityGuestRuleProvenanceStatusV1 provenance_status =
      ActivityGuestRuleProvenanceStatusV1::exact_build_rejected;
  std::string_view authored_rule_key = "activity_invite_rule_close_family";
  bool rule_active = false;
  bool candidate_membership = false;
  std::uint32_t native_key_hash = 0;
  std::uint32_t provenance_key_hash = 0;
  std::uint64_t provenance_refresh_sequence = 0;
  std::uint32_t raw_rule_character_count = 0;
  std::uint32_t filtered_rule_character_count = 0;

  friend bool operator==(const ActivityFeastOrdinaryGuestRouteV1 &,
                         const ActivityFeastOrdinaryGuestRouteV1 &) = default;
};

// The transport must build this from the native four-cost, final CanStart,
// selected-option, balance, and hosted-identity readers in ONE paused frame.
struct ActivityFeastStage5StartSnapshotV1 {
  ActivityHostedIdentityFrameV1 frame{};
  std::uintptr_t planner = 0;
  std::uint64_t normal_cost_refresh_sequence = 0;
  bool feast_type_verified = false;
  bool generic_option_verified = false;
  bool final_can_start_observed = false;
  bool final_can_start = false;
  bool four_costs_observed = false;
  std::array<std::uint32_t, 4> cost_resource_indices{};
  std::array<std::int64_t, 4> cost_raw{};
  ActivityFeastResourceBalancesV1 balances{};
  bool hosted_identities_observed = false;
  std::uint32_t hosted_count = 0;
  std::array<ActivityHostedIdentityV1, 64> hosted{};
  ActivityFeastGuestJoinResultV1 selected_guests{};
  ActivityFeastOrdinaryGuestRouteV1 ordinary_guest{};
  FeastOutcomeValuesV1 outcome_values{};
};

bool IsActivityFeastSelectedGuestRouteQualifiedV1(
    const ActivityFeastStage5StartSnapshotV1 &snapshot) noexcept;
bool IsActivityFeastOrdinaryGuestRouteObservedV1(
    const ActivityFeastStage5StartSnapshotV1 &snapshot) noexcept;
bool IsActivityFeastOrdinaryGuestRouteQualifiedV1(
    const ActivityFeastStage5StartSnapshotV1 &snapshot) noexcept;
bool IsActivityFeastGuestRouteQualifiedV1(
    const ActivityFeastStage5StartSnapshotV1 &snapshot) noexcept;

using ActivityFeastStage5CaptureV1 = bool (*)(
    void *, const ActivityHostedIdentityFrameV1 &,
    ActivityFeastStage5StartSnapshotV1 &) noexcept;
// true means the original commit branch returned. It is only a pending
// submission receipt; the queued command's application is read separately.
using ActivityFeastStage5InvokeCommitV1 = bool (*)(
    void *, std::uintptr_t module_base, std::uintptr_t planner) noexcept;

struct ActivityFeastStage5StartEnvironmentV1 {
  bool enabled = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  void *context = nullptr;
  ActivityHostedIdentityReadMemoryV1 read_memory = nullptr;
  ActivityFeastStage5CaptureV1 capture = nullptr;
  ActivityFeastStage5InvokeCommitV1 invoke_commit = nullptr;
};

struct ActivityFeastStage5StartRequestV1 {
  ActivityHostedIdentityFrameV1 expected{};
  bool policy_approved = false;
  bool previous_submit_pending = false;
  // Same Q100000 units as configured cost and balance. Caller includes any
  // committed war cash or other obligation in this reserve.
  std::array<std::int64_t, 4> reserve_raw{};
};

enum class ActivityFeastStage5StartStatusV1 {
  submitted_pending,
  rejected,
  submission_outcome_unknown,
};

struct ActivityFeastStage5StartResultV1 {
  ActivityFeastStage5StartStatusV1 status =
      ActivityFeastStage5StartStatusV1::rejected;
  bool invoked = false;
  ActivityFeastStage5StartSnapshotV1 before{};
};

ActivityFeastStage5StartResultV1 StartActivityFeastStage5V1(
    const ActivityFeastStage5StartEnvironmentV1 &environment,
    const ActivityFeastStage5StartRequestV1 &request) noexcept;

// An independent later paused read, after the queued command had a chance to
// apply. Caller must retain StartResult before and never retry while pending.
struct ActivityFeastStage5PostV1 {
  ActivityHostedIdentityFrameV1 frame{};
  ActivityFeastResourceBalancesV1 balances{};
  bool hosted_identities_observed = false;
  std::uint32_t hosted_count = 0;
  std::array<ActivityHostedIdentityV1, 64> hosted{};
  FeastOutcomeValuesV1 outcome_values{};
};

enum class ActivityFeastStage5PostStatusV1 {
  pending,
  created_and_debited,
  created_zero_cost,
  created_debit_unresolved,
  invalid_observation,
};

struct ActivityFeastStage5PostResultV1 {
  ActivityFeastStage5PostStatusV1 status =
      ActivityFeastStage5PostStatusV1::invalid_observation;
  std::uint32_t new_activity_id = 0;
  bool new_identity_observed = false;
  bool same_date_exact_debit = false;
};

ActivityFeastStage5PostResultV1 ReconcileActivityFeastStage5StartV1(
    const ActivityFeastStage5StartResultV1 &submission,
    const ActivityFeastStage5PostV1 &post) noexcept;

// Exact CK3 1.19.0.6 common accept branch at RVA 0x10B13F0. The caller
// must have passed the Start core's exact build, ABI, and same-frame gates.
bool InvokeActivityFeastNativeCommitV1(void *, std::uintptr_t module_base,
                                      std::uintptr_t planner) noexcept;
// Exact 1.20.0.2 original accept branch; the Start core selects it only after
// that build's prefix, same-frame final gate and resource/guest checks pass.
bool InvokeActivityFeastNativeCommit12002V1(void *, std::uintptr_t module_base,
                                          std::uintptr_t planner) noexcept;

} // namespace xar::bridge

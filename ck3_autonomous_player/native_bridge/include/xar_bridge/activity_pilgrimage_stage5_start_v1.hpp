#pragma once

#include "xar_bridge/activity_typed_planner_v1.hpp"
#include "xar_bridge/activity_hosted_identity_v1.hpp"

namespace xar::bridge {

// Software-owned evidence. Production capture must populate every component
// from its real reader in ONE owner-thread paused frame, then recheck that frame.
struct ActivityPilgrimageStage5SnapshotV1 {
  ActivityTypedPlannerCostQuoteV1 quote{};
  ActivityTypedPlannerDestinationV1 destination{};
  ActivityPlannerDiagFrameV1 balance_frame{};
  std::array<bool, 10> balance_available{};
  std::array<std::int64_t, 10> balance_raw{};
  ActivityHostedIdentityResultV1 hosted{};
};

using ActivityPilgrimageStage5CaptureV1 = bool (*)(
    void *, const ActivityPlannerDiagFrameV1 &,
    ActivityPilgrimageStage5SnapshotV1 &) noexcept;
using ActivityPilgrimageInvokeCommitV1 = bool (*)(
    void *, std::uintptr_t module_base, std::uintptr_t planner) noexcept;

struct ActivityPilgrimageStage5StartEnvironmentV1 {
  bool enabled = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  void *context = nullptr;
  ActivityPlannerDiagReadMemoryV1 read_memory = nullptr;
  ActivityPilgrimageStage5CaptureV1 capture = nullptr;
  ActivityPilgrimageInvokeCommitV1 invoke_commit = nullptr;
};

struct ActivityPilgrimageStage5StartRequestV1 {
  ActivityPlannerDiagFrameV1 expected{};
  bool policy_approved = false;
  std::uint32_t destination_province_id = 0;
  // Q100000; includes war cash/other obligations. Indexes belong to THIS quote.
  std::array<std::int64_t, 10> reserve_raw{};
};

enum class ActivityPilgrimageStartStateV1 {
  idle,
  submitted_pending,
  submission_outcome_unknown,
  identity_observed,
};

// Retain this per case, before submission, across timeout/reconciliation.
// Neither ACK loss nor absent identity resets it; there is no automatic retry.
struct ActivityPilgrimageStartLedgerV1 {
  ActivityPilgrimageStartStateV1 state = ActivityPilgrimageStartStateV1::idle;
  ActivityPilgrimageStage5SnapshotV1 before{};
  std::uint32_t observed_activity_id = 0;
};

struct ActivityPilgrimageStage5StartResultV1 {
  bool accepted = false;
  bool invoked = false;
  ActivityPilgrimageStartStateV1 state = ActivityPilgrimageStartStateV1::idle;
};

ActivityPilgrimageStage5StartResultV1 StartActivityPilgrimageStage5V1(
    const ActivityPilgrimageStage5StartEnvironmentV1 &,
    const ActivityPilgrimageStage5StartRequestV1 &,
    ActivityPilgrimageStartLedgerV1 &) noexcept;

// A later independently read hosted set proves only a newly observed full ID.
// Empty/missing identities never prove rejection, completion or free retry.
enum class ActivityPilgrimageReconcileStatusV1 {
  pending,
  identity_observed,
  ambiguous_new_identities,
  rejected_observation,
};
struct ActivityPilgrimageReconcileResultV1 {
  ActivityPilgrimageReconcileStatusV1 status =
      ActivityPilgrimageReconcileStatusV1::rejected_observation;
  ActivityHostedIdentityV1 identity{};
};
ActivityPilgrimageReconcileResultV1 ReconcileActivityPilgrimageStartV1(
    ActivityPilgrimageStartLedgerV1 &,
    const ActivityHostedIdentityResultV1 &) noexcept;

// Same admitted .4 native commit as existing Feast wrapper; no new RVA.
// The Start core checks original function bytes BEFORE invoking this wrapper.
bool InvokeActivityPilgrimageNativeCommit12004V1(
    void *, std::uintptr_t module_base, std::uintptr_t planner) noexcept;

} // namespace xar::bridge

#pragma once

#include "xar_bridge/major_decision_found_kingdom_shared_glue_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kMajorDecisionFoundKingdomInternalRouteKeyV1 =
        "major_decision_found_kingdom_internal_route_v1";
inline constexpr std::string_view
    kMajorDecisionFoundKingdomInternalCandidateRequestIdV1 =
        "g2-m6-decision8-found-kingdom-fixed";
inline constexpr bool
    kMajorDecisionFoundKingdomInternalRouteCapabilityAdvertisedV1 = false;

#if defined(XAR_CK3_ENABLE_G2_MAJOR_DECISION_FOUND_KINGDOM_INTERNAL_ROUTE_V1)
inline constexpr bool kMajorDecisionFoundKingdomInternalRouteBuildEnabledV1 =
    true;
#else
inline constexpr bool kMajorDecisionFoundKingdomInternalRouteBuildEnabledV1 =
    false;
#endif

enum class MajorDecisionFoundKingdomInternalRoutePhaseV1 : std::uint8_t {
  unconfigured = 0,
  build_disabled,
  missing_capture_binding,
  ready,
  submit_permitted,
  submit_queued,
  awaiting_receipt_permit,
  receipt_permitted,
  receipt_queued,
  receipt_red_awaiting_fresh_permit,
  applied,
  red,
};

enum class MajorDecisionFoundKingdomInternalRouteFailureV1 : std::uint8_t {
  none = 0,
  build_disabled,
  missing_capture_binding,
  configuration,
  permit_contract,
  stale_permit,
  candidate_drift,
  prepare,
  transport,
  ticket_identity,
  executor,
  shared_red,
};

enum class MajorDecisionFoundKingdomInternalRouteDriveResultV1 : std::uint8_t {
  idle = 0,
  retry_later,
  queued,
  in_flight,
  awaiting_fresh_receipt,
  applied,
  red,
};

struct MajorDecisionFoundKingdomInternalRouteAccessV1 {
  MajorDecisionFoundKingdomNativeSubmitEnvironmentV1 submit_environment{};
  MajorDecisionFoundKingdomActionAccessV1 precondition_access{};
  void *postcondition_context = nullptr;
  CaptureMajorDecisionFoundKingdomActionPostconditionV1
      capture_postcondition = nullptr;
};

// This process-lifetime object is a private, fixed-candidate route. It never
// accepts a protocol action or a decision id. An explicit monotonically newer
// permit freezes one concrete precondition, and the application-main executor
// requires every immediate re-observation to match it exactly before submit.
struct MajorDecisionFoundKingdomInternalRouteV1 {
  MajorDecisionFoundKingdomSharedStateV1 shared_state{};
  MajorDecisionFoundKingdomSharedContextV1 shared_context{};
  MajorDecisionFoundKingdomActionAccessV1 upstream_precondition_access{};
  void *upstream_postcondition_context = nullptr;
  CaptureMajorDecisionFoundKingdomActionPostconditionV1
      upstream_capture_postcondition = nullptr;
  MajorDecisionFoundKingdomActionPreconditionV1 permitted_candidate{};
  std::uint64_t permit_generation = 0;
  std::uint64_t receipt_snapshot_revision = 0;
  std::uint64_t last_receipt_attempt_snapshot_revision = 0;
  ck3_11906::MainThreadQuerySubmitResultV1 last_submit =
      ck3_11906::MainThreadQuerySubmitResultV1::invalid_request;
  ck3_11906::MainThreadQueryReclaimResultV1 last_reclaim =
      ck3_11906::MainThreadQueryReclaimResultV1::not_terminal;
  MajorDecisionFoundKingdomInternalRoutePhaseV1 phase =
      MajorDecisionFoundKingdomInternalRoutePhaseV1::unconfigured;
  MajorDecisionFoundKingdomInternalRouteFailureV1 failure =
      MajorDecisionFoundKingdomInternalRouteFailureV1::none;
  bool configured = false;

  MajorDecisionFoundKingdomInternalRouteV1() = default;
  MajorDecisionFoundKingdomInternalRouteV1(
      const MajorDecisionFoundKingdomInternalRouteV1 &) = delete;
  MajorDecisionFoundKingdomInternalRouteV1 &operator=(
      const MajorDecisionFoundKingdomInternalRouteV1 &) = delete;
  MajorDecisionFoundKingdomInternalRouteV1(
      MajorDecisionFoundKingdomInternalRouteV1 &&) = delete;
  MajorDecisionFoundKingdomInternalRouteV1 &operator=(
      MajorDecisionFoundKingdomInternalRouteV1 &&) = delete;
};

bool ConfigureMajorDecisionFoundKingdomInternalRouteV1(
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const MajorDecisionFoundKingdomInternalRouteAccessV1 &access,
    MajorDecisionFoundKingdomInternalRouteV1 &route) noexcept;

bool GrantMajorDecisionFoundKingdomSubmitPermitV1(
    MajorDecisionFoundKingdomInternalRouteV1 &route,
    std::uint64_t permit_generation,
    const MajorDecisionFoundKingdomActionPreconditionV1
        &fixed_candidate) noexcept;

// Receipt is independently permitted only after submit ACK. The observed
// revision is a lower bound for the capture made later on application-main.
bool GrantMajorDecisionFoundKingdomReceiptPermitV1(
    MajorDecisionFoundKingdomInternalRouteV1 &route,
    std::uint64_t permit_generation,
    std::uint64_t fresh_snapshot_revision) noexcept;

MajorDecisionFoundKingdomInternalRouteDriveResultV1
DriveMajorDecisionFoundKingdomInternalRouteV1(
    MajorDecisionFoundKingdomInternalRouteV1 &route) noexcept;

std::string_view MajorDecisionFoundKingdomInternalRoutePhaseNameV1(
    MajorDecisionFoundKingdomInternalRoutePhaseV1 phase) noexcept;
std::string_view MajorDecisionFoundKingdomInternalRouteFailureNameV1(
    MajorDecisionFoundKingdomInternalRouteFailureV1 failure) noexcept;

} // namespace xar::bridge

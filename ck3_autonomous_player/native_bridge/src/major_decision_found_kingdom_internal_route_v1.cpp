#include "xar_bridge/major_decision_found_kingdom_internal_route_v1.hpp"

#include <atomic>

namespace xar::bridge {
namespace {

using DriveResult = MajorDecisionFoundKingdomInternalRouteDriveResultV1;
using Failure = MajorDecisionFoundKingdomInternalRouteFailureV1;
using Phase = MajorDecisionFoundKingdomInternalRoutePhaseV1;
using MailboxState = ck3_11906::MainThreadQueryMailboxStateV1;
using ReclaimResult = ck3_11906::MainThreadQueryReclaimResultV1;
using SubmitResult = ck3_11906::MainThreadQuerySubmitResultV1;

void SetRed(MajorDecisionFoundKingdomInternalRouteV1 &route,
            Failure failure) noexcept {
  route.phase = Phase::red;
  route.failure = failure;
}

bool CaptureFixedPrecondition(
    void *context,
    MajorDecisionFoundKingdomActionPreconditionV1 &output) noexcept {
  auto *route =
      static_cast<MajorDecisionFoundKingdomInternalRouteV1 *>(context);
  if (route == nullptr ||
      route->upstream_precondition_access.capture_precondition == nullptr ||
      !route->upstream_precondition_access.capture_precondition(
          route->upstream_precondition_access.context, output)) {
    return false;
  }
  if (output != route->permitted_candidate) {
    route->failure = Failure::candidate_drift;
    return false;
  }
  return true;
}

bool CaptureFreshPostcondition(
    void *context,
    MajorDecisionFoundKingdomActionPostconditionV1 &output) noexcept {
  auto *route =
      static_cast<MajorDecisionFoundKingdomInternalRouteV1 *>(context);
  if (route == nullptr || route->upstream_capture_postcondition == nullptr ||
      !route->upstream_capture_postcondition(
          route->upstream_postcondition_context, output)) {
    return false;
  }
  return route->shared_state.has_pending_ack &&
         route->receipt_snapshot_revision >
             route->shared_state.pending_ack.pre_binding.snapshot_revision &&
         output.snapshot_revision >= route->receipt_snapshot_revision &&
         output.snapshot_revision >
             route->shared_state.pending_ack.pre_binding.snapshot_revision;
}

bool IsRetryable(SubmitResult result) noexcept {
  return result == SubmitResult::paused_main_thread_not_observed ||
         result == SubmitResult::mailbox_busy ||
         result == SubmitResult::application_main_not_observed;
}

bool IsTerminal(MailboxState state) noexcept {
  return state == MailboxState::completed ||
         state == MailboxState::executor_failed ||
         state == MailboxState::cancelled ||
         state == MailboxState::infrastructure_failed;
}

DriveResult QueuePrepared(
    MajorDecisionFoundKingdomInternalRouteV1 &route,
    Phase queued_phase) noexcept {
  route.last_submit =
      TryQueueMajorDecisionFoundKingdomSharedV1(route.shared_context);
  if (route.last_submit == SubmitResult::submitted) {
    route.phase = queued_phase;
    route.failure = Failure::none;
    return DriveResult::queued;
  }
  if (IsRetryable(route.last_submit)) {
    route.failure = Failure::none;
    return DriveResult::retry_later;
  }
  SetRed(route, Failure::transport);
  return DriveResult::red;
}

DriveResult ReclaimTerminal(
    MajorDecisionFoundKingdomInternalRouteV1 &route,
    bool receipt) noexcept {
  auto &mailbox = *route.shared_context.mailbox;
  const auto state = mailbox.state.load(std::memory_order_acquire);
  if (!IsTerminal(state)) return DriveResult::in_flight;
  if (route.shared_context.ticket.sequence == 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          route.shared_context.ticket.sequence ||
      mailbox.completed_sequence.load(std::memory_order_acquire) !=
          route.shared_context.ticket.sequence) {
    SetRed(route, Failure::ticket_identity);
    return DriveResult::red;
  }

  const auto completion = route.shared_context.completion;
  const auto shared_failure = route.shared_context.failure;
  route.last_reclaim =
      ReclaimMajorDecisionFoundKingdomSharedV1(route.shared_context);
  if (route.last_reclaim != ReclaimResult::reclaimed) {
    SetRed(route, Failure::ticket_identity);
    return DriveResult::red;
  }
  if (state != MailboxState::completed) {
    SetRed(route, Failure::executor);
    return DriveResult::red;
  }

  if (!receipt) {
    if (completion == MajorDecisionFoundKingdomSharedCompletionV1::
                          submitted_verification_pending &&
        shared_failure == MajorDecisionFoundKingdomSharedFailureV1::none &&
        route.shared_state.has_pending_ack) {
      route.phase = Phase::awaiting_receipt_permit;
      route.failure = Failure::none;
      return DriveResult::awaiting_fresh_receipt;
    }
    SetRed(route, route.failure == Failure::candidate_drift
                      ? Failure::candidate_drift
                      : Failure::shared_red);
    return DriveResult::red;
  }

  if (completion ==
          MajorDecisionFoundKingdomSharedCompletionV1::receipt_applied &&
      shared_failure == MajorDecisionFoundKingdomSharedFailureV1::none &&
      !route.shared_state.has_pending_ack) {
    route.phase = Phase::applied;
    route.failure = Failure::none;
    return DriveResult::applied;
  }

  // A receipt RED consumes only this fresh-read permit. The persisted ACK is
  // deliberately retained by DECISION7 for a later, newer observation.
  if (completion == MajorDecisionFoundKingdomSharedCompletionV1::receipt_red &&
      route.shared_state.has_pending_ack) {
    route.phase = Phase::receipt_red_awaiting_fresh_permit;
    route.failure = Failure::shared_red;
    return DriveResult::awaiting_fresh_receipt;
  }
  SetRed(route, Failure::shared_red);
  return DriveResult::red;
}

} // namespace

bool ConfigureMajorDecisionFoundKingdomInternalRouteV1(
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const MajorDecisionFoundKingdomInternalRouteAccessV1 &access,
    MajorDecisionFoundKingdomInternalRouteV1 &route) noexcept {
  if (route.shared_context.ticket.sequence != 0 || route.configured) {
    SetRed(route, Failure::configuration);
    return false;
  }
  if (!kMajorDecisionFoundKingdomInternalRouteBuildEnabledV1) {
    route.phase = Phase::build_disabled;
    route.failure = Failure::build_disabled;
    return false;
  }
  if (access.precondition_access.context == nullptr ||
      access.precondition_access.capture_precondition == nullptr ||
      access.postcondition_context == nullptr ||
      access.capture_postcondition == nullptr) {
    route.phase = Phase::missing_capture_binding;
    route.failure = Failure::missing_capture_binding;
    return false;
  }

  route.upstream_precondition_access = access.precondition_access;
  route.upstream_precondition_access.submit = nullptr;
  route.upstream_postcondition_context = access.postcondition_context;
  route.upstream_capture_postcondition = access.capture_postcondition;
  MajorDecisionFoundKingdomActionAccessV1 fixed_access{};
  fixed_access.context = &route;
  fixed_access.capture_precondition = &CaptureFixedPrecondition;
  if (!ConfigureMajorDecisionFoundKingdomSharedGlueV1(
          mailbox, access.submit_environment, route.shared_state, fixed_access,
          &route, &CaptureFreshPostcondition, route.shared_context)) {
    SetRed(route, Failure::configuration);
    return false;
  }
  route.configured = true;
  route.phase = Phase::ready;
  route.failure = Failure::none;
  return true;
}

bool GrantMajorDecisionFoundKingdomSubmitPermitV1(
    MajorDecisionFoundKingdomInternalRouteV1 &route,
    std::uint64_t permit_generation,
    const MajorDecisionFoundKingdomActionPreconditionV1
        &fixed_candidate) noexcept {
  if (!route.configured || route.phase != Phase::ready ||
      permit_generation == 0 || permit_generation <= route.permit_generation ||
      fixed_candidate.decision_id !=
          kMajorDecisionFoundKingdomDecisionIdV1 ||
      !fixed_candidate.available || !fixed_candidate.paused ||
      !fixed_candidate.application_main_thread) {
    route.failure = permit_generation != 0 &&
                            permit_generation <= route.permit_generation
                        ? Failure::stale_permit
                        : Failure::permit_contract;
    return false;
  }
  try {
    route.permitted_candidate = fixed_candidate;
  } catch (...) {
    SetRed(route, Failure::permit_contract);
    return false;
  }
  route.permit_generation = permit_generation;
  route.phase = Phase::submit_permitted;
  route.failure = Failure::none;
  return true;
}

bool GrantMajorDecisionFoundKingdomReceiptPermitV1(
    MajorDecisionFoundKingdomInternalRouteV1 &route,
    std::uint64_t permit_generation,
    std::uint64_t fresh_snapshot_revision) noexcept {
  const bool phase_accepts =
      route.phase == Phase::awaiting_receipt_permit ||
      route.phase == Phase::receipt_red_awaiting_fresh_permit;
  if (!route.configured || !phase_accepts ||
      !route.shared_state.has_pending_ack || permit_generation == 0 ||
      permit_generation <= route.permit_generation ||
      fresh_snapshot_revision <= route.last_receipt_attempt_snapshot_revision ||
      fresh_snapshot_revision <=
          route.shared_state.pending_ack.pre_binding.snapshot_revision) {
    route.failure = permit_generation != 0 &&
                            permit_generation <= route.permit_generation
                        ? Failure::stale_permit
                        : Failure::permit_contract;
    return false;
  }
  route.permit_generation = permit_generation;
  route.receipt_snapshot_revision = fresh_snapshot_revision;
  route.last_receipt_attempt_snapshot_revision = fresh_snapshot_revision;
  route.phase = Phase::receipt_permitted;
  route.failure = Failure::none;
  return true;
}

MajorDecisionFoundKingdomInternalRouteDriveResultV1
DriveMajorDecisionFoundKingdomInternalRouteV1(
    MajorDecisionFoundKingdomInternalRouteV1 &route) noexcept {
  if (!route.configured) return DriveResult::red;
  switch (route.phase) {
  case Phase::ready:
  case Phase::awaiting_receipt_permit:
  case Phase::receipt_red_awaiting_fresh_permit:
    return DriveResult::idle;
  case Phase::submit_permitted:
    if (route.shared_context.operation ==
            MajorDecisionFoundKingdomSharedOperationV1::none &&
        !PrepareMajorDecisionFoundKingdomSubmitV1(
            route.shared_context,
            kMajorDecisionFoundKingdomInternalCandidateRequestIdV1)) {
      SetRed(route, Failure::prepare);
      return DriveResult::red;
    }
    return QueuePrepared(route, Phase::submit_queued);
  case Phase::receipt_permitted:
    if (route.shared_context.operation ==
            MajorDecisionFoundKingdomSharedOperationV1::none &&
        !PrepareMajorDecisionFoundKingdomReceiptV1(route.shared_context)) {
      SetRed(route, Failure::prepare);
      return DriveResult::red;
    }
    return QueuePrepared(route, Phase::receipt_queued);
  case Phase::submit_queued:
    return ReclaimTerminal(route, false);
  case Phase::receipt_queued:
    return ReclaimTerminal(route, true);
  case Phase::applied:
    return DriveResult::applied;
  case Phase::unconfigured:
  case Phase::build_disabled:
  case Phase::missing_capture_binding:
  case Phase::red:
    return DriveResult::red;
  }
  SetRed(route, Failure::configuration);
  return DriveResult::red;
}

std::string_view MajorDecisionFoundKingdomInternalRoutePhaseNameV1(
    Phase phase) noexcept {
  switch (phase) {
  case Phase::unconfigured: return "unconfigured";
  case Phase::build_disabled: return "build_disabled";
  case Phase::missing_capture_binding: return "missing_capture_binding";
  case Phase::ready: return "ready";
  case Phase::submit_permitted: return "submit_permitted";
  case Phase::submit_queued: return "submit_queued";
  case Phase::awaiting_receipt_permit: return "awaiting_receipt_permit";
  case Phase::receipt_permitted: return "receipt_permitted";
  case Phase::receipt_queued: return "receipt_queued";
  case Phase::receipt_red_awaiting_fresh_permit:
    return "receipt_red_awaiting_fresh_permit";
  case Phase::applied: return "applied";
  case Phase::red: return "red";
  }
  return "red";
}

std::string_view MajorDecisionFoundKingdomInternalRouteFailureNameV1(
    Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::build_disabled: return "build_disabled";
  case Failure::missing_capture_binding: return "missing_capture_binding";
  case Failure::configuration: return "configuration";
  case Failure::permit_contract: return "permit_contract";
  case Failure::stale_permit: return "stale_permit";
  case Failure::candidate_drift: return "candidate_drift";
  case Failure::prepare: return "prepare";
  case Failure::transport: return "transport";
  case Failure::ticket_identity: return "ticket_identity";
  case Failure::executor: return "executor";
  case Failure::shared_red: return "shared_red";
  }
  return "shared_red";
}

} // namespace xar::bridge

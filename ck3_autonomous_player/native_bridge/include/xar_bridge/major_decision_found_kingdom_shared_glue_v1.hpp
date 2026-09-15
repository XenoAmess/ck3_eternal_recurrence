#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/major_decision_found_kingdom_native_submit_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <type_traits>

namespace xar::bridge {

inline constexpr std::string_view
    kMajorDecisionFoundKingdomSharedGlueKeyV1 =
        "major_decision_found_kingdom_shared_glue_v1";
inline constexpr std::string_view
    kMajorDecisionFoundKingdomSharedGlueBackendV1 =
        "application_main_thread_fixed_mailbox_v1";
// The transport is compiled into the shared bridge, but remains private until
// a production paused artifact closes the full pre/post observer dependency.
inline constexpr bool
    kMajorDecisionFoundKingdomSharedGlueCapabilityAdvertisedV1 = false;

enum class MajorDecisionFoundKingdomSharedOperationV1 : std::uint8_t {
  none = 0,
  submit_candidate,
  verify_receipt,
};

enum class MajorDecisionFoundKingdomSharedCompletionV1 : std::uint8_t {
  not_executed = 0,
  candidate_red,
  action_red,
  submitted_verification_pending,
  receipt_red,
  receipt_applied,
  infrastructure_red,
};

enum class MajorDecisionFoundKingdomSharedFailureV1 : std::uint8_t {
  none = 0,
  not_configured,
  mailbox_identity,
  candidate_capture,
  candidate_contract,
  action_rejected,
  postcondition_capture,
  receipt_rejected,
  transport,
};

using CaptureMajorDecisionFoundKingdomActionPostconditionV1 = bool (*)(
    void *context,
    MajorDecisionFoundKingdomActionPostconditionV1 &output) noexcept;

struct MajorDecisionFoundKingdomSharedStateV1 {
  MajorDecisionFoundKingdomActionStateV1 action{};
  MajorDecisionFoundKingdomActionAckV1 pending_ack{};
  bool has_pending_ack = false;
};

// This context owns one reusable mailbox client. Configure once, then run a
// submit transaction and a later independent receipt transaction. Reclaiming
// the mailbox never clears the persistent pending ACK.
struct MajorDecisionFoundKingdomSharedContextV1 {
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  MajorDecisionFoundKingdomSharedOperationV1 operation =
      MajorDecisionFoundKingdomSharedOperationV1::none;
  MajorDecisionFoundKingdomSharedStateV1 *shared_state = nullptr;
  MajorDecisionFoundKingdomNativeSubmitStateV1 native_submit_state{};
  MajorDecisionFoundKingdomActionEnvironmentV1 action_environment{};
  MajorDecisionFoundKingdomActionAccessV1 action_access{};
  void *postcondition_context = nullptr;
  CaptureMajorDecisionFoundKingdomActionPostconditionV1
      capture_postcondition = nullptr;

  std::string request_id;
  MajorDecisionFoundKingdomActionPreconditionV1 concrete_candidate{};
  MajorDecisionFoundKingdomActionRequestV1 concrete_request{};
  MajorDecisionFoundKingdomActionReceiptV1 receipt{};
  MajorDecisionFoundKingdomSharedCompletionV1 completion =
      MajorDecisionFoundKingdomSharedCompletionV1::not_executed;
  MajorDecisionFoundKingdomSharedFailureV1 failure =
      MajorDecisionFoundKingdomSharedFailureV1::not_configured;
  MajorDecisionFoundKingdomActionFailureClassV1 action_failure_class =
      MajorDecisionFoundKingdomActionFailureClassV1::none;
  std::string failure_reason;
  ck3_11906::MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
  bool concrete_candidate_generated = false;
  bool configured = false;

  MajorDecisionFoundKingdomSharedContextV1() = default;
  MajorDecisionFoundKingdomSharedContextV1(
      const MajorDecisionFoundKingdomSharedContextV1 &) = delete;
  MajorDecisionFoundKingdomSharedContextV1 &operator=(
      const MajorDecisionFoundKingdomSharedContextV1 &) = delete;
  MajorDecisionFoundKingdomSharedContextV1(
      MajorDecisionFoundKingdomSharedContextV1 &&) = delete;
  MajorDecisionFoundKingdomSharedContextV1 &operator=(
      MajorDecisionFoundKingdomSharedContextV1 &&) = delete;
};

// upstream_action_access must provide the full paused precondition capture.
// Its submit member is ignored and replaced by DECISION6's exact ABI binder.
bool ConfigureMajorDecisionFoundKingdomSharedGlueV1(
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const MajorDecisionFoundKingdomNativeSubmitEnvironmentV1
        &submit_environment,
    MajorDecisionFoundKingdomSharedStateV1 &shared_state,
    const MajorDecisionFoundKingdomActionAccessV1 &upstream_action_access,
    void *postcondition_context,
    CaptureMajorDecisionFoundKingdomActionPostconditionV1
        capture_postcondition,
    MajorDecisionFoundKingdomSharedContextV1 &context) noexcept;

bool PrepareMajorDecisionFoundKingdomSubmitV1(
    MajorDecisionFoundKingdomSharedContextV1 &context,
    std::string_view request_id) noexcept;

bool PrepareMajorDecisionFoundKingdomReceiptV1(
    MajorDecisionFoundKingdomSharedContextV1 &context) noexcept;

ck3_11906::MainThreadQuerySubmitResultV1
TryQueueMajorDecisionFoundKingdomSharedV1(
    MajorDecisionFoundKingdomSharedContextV1 &context) noexcept;

ck3_11906::MainThreadQueryReclaimResultV1
ReclaimMajorDecisionFoundKingdomSharedV1(
    MajorDecisionFoundKingdomSharedContextV1 &context) noexcept;

bool ExecuteMajorDecisionFoundKingdomSharedMailboxV1(
    void *opaque_context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view MajorDecisionFoundKingdomSharedFailureNameV1(
    MajorDecisionFoundKingdomSharedFailureV1 failure) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteMajorDecisionFoundKingdomSharedMailboxV1),
              ck3_11906::MainThreadQueryExecutorV1>);

} // namespace xar::bridge

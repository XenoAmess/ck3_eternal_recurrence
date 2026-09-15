#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/realm_law_native_shared_glue_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <type_traits>

namespace xar::bridge {

inline constexpr std::string_view kRealmLawApplicationMainKeyV1 =
    "realm_law_application_main_v1";
inline constexpr std::string_view kRealmLawApplicationMainBackendV1 =
    "application_main_thread_fixed_mailbox_v1";
inline constexpr bool kRealmLawApplicationMainCapabilityAdvertisedV1 = false;

enum class RealmLawApplicationMainOperationV1 : std::uint8_t {
  none = 0,
  submit,
  verify_receipt,
};

enum class RealmLawApplicationMainCompletionV1 : std::uint8_t {
  not_executed = 0,
  binding_red,
  action_red,
  submitted_verification_pending,
  receipt_red,
  receipt_enacted,
  infrastructure_red,
};

enum class RealmLawApplicationMainFailureV1 : std::uint8_t {
  none = 0,
  not_configured,
  mailbox_identity,
  native_binding,
  stamp_mismatch,
  pending_ack,
  action_rejected,
  receipt_rejected,
  transport,
};

struct RealmLawApplicationMainStateV1 {
  RealmLawNativeSharedGlueStateV1 native_glue{};
  RealmLawNativeBinderStateV1 native_binder{};
  RealmLawEnactActionAckV1 pending_ack{};
  std::uint64_t pending_submit_sequence = 0;
  bool initialized = false;
  bool has_pending_ack = false;

  RealmLawApplicationMainStateV1() = default;
  RealmLawApplicationMainStateV1(
      const RealmLawApplicationMainStateV1 &) = delete;
  RealmLawApplicationMainStateV1 &operator=(
      const RealmLawApplicationMainStateV1 &) = delete;
  RealmLawApplicationMainStateV1(
      RealmLawApplicationMainStateV1 &&) = delete;
  RealmLawApplicationMainStateV1 &operator=(
      RealmLawApplicationMainStateV1 &&) = delete;
};

// The context and state belong in durable global or heap storage. They must
// outlive a published ticket and cannot be copied because LAW5 retains pointers
// into the LAW7 state. Submit and receipt are always separate mailbox
// transactions.
struct RealmLawApplicationMainContextV1 {
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  RealmLawApplicationMainOperationV1 operation =
      RealmLawApplicationMainOperationV1::none;
  RealmLawApplicationMainStateV1 *shared_state = nullptr;
  RealmLawNativeSharedGlueConfigurationV1 configuration{};
  std::array<char, kRealmLawNativeBinderV1DigestCapacity>
      source_signature_manifest_sha256{};
  RealmLawEnactActionRequestV1 request{};
  RealmLawEnactActionAckV1 attempt_ack{};
  RealmLawEnactActionReceiptV1 receipt{};
  RealmLawApplicationMainCompletionV1 completion =
      RealmLawApplicationMainCompletionV1::not_executed;
  RealmLawApplicationMainFailureV1 failure =
      RealmLawApplicationMainFailureV1::not_configured;
  RealmLawEnactActionFailureV1 action_failure =
      RealmLawEnactActionFailureV1::none;
  RealmLawEnactActionReceiptFailureV1 receipt_failure =
      RealmLawEnactActionReceiptFailureV1::none;
  std::string failure_reason;
  ck3_11906::MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
  bool configured = false;

  RealmLawApplicationMainContextV1() = default;
  RealmLawApplicationMainContextV1(
      const RealmLawApplicationMainContextV1 &) = delete;
  RealmLawApplicationMainContextV1 &operator=(
      const RealmLawApplicationMainContextV1 &) = delete;
  RealmLawApplicationMainContextV1(
      RealmLawApplicationMainContextV1 &&) = delete;
  RealmLawApplicationMainContextV1 &operator=(
      RealmLawApplicationMainContextV1 &&) = delete;
};

// Configuration stores a private copy of the source-manifest digest. Callback
// contexts and the ABI reader remain borrowed and must outlive context.
bool ConfigureRealmLawApplicationMainV1(
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const RealmLawNativeSharedGlueConfigurationV1 &configuration,
    RealmLawApplicationMainStateV1 &shared_state,
    RealmLawApplicationMainContextV1 &context) noexcept;

bool PrepareRealmLawApplicationMainSubmitV1(
    RealmLawApplicationMainContextV1 &context,
    const RealmLawEnactActionRequestV1 &request) noexcept;

bool PrepareRealmLawApplicationMainReceiptV1(
    RealmLawApplicationMainContextV1 &context) noexcept;

ck3_11906::MainThreadQuerySubmitResultV1 TryQueueRealmLawApplicationMainV1(
    RealmLawApplicationMainContextV1 &context) noexcept;

ck3_11906::MainThreadQueryReclaimResultV1 ReclaimRealmLawApplicationMainV1(
    RealmLawApplicationMainContextV1 &context) noexcept;

bool ExecuteRealmLawApplicationMainV1(
    void *opaque_context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view RealmLawApplicationMainFailureNameV1(
    RealmLawApplicationMainFailureV1 failure) noexcept;

static_assert(std::is_same_v<decltype(&ExecuteRealmLawApplicationMainV1),
                             ck3_11906::MainThreadQueryExecutorV1>);

} // namespace xar::bridge

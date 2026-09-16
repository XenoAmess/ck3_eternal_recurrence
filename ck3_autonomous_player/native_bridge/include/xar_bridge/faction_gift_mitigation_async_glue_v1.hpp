#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/faction_gift_mitigation_native_binder_v1.hpp"
#include "xar_bridge/faction_gift_mitigation_integration_gate_v1.hpp"
#include "xar_bridge/faction_gift_receivers_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view kFactionGiftMitigationAsyncGlueV1Key =
    "g2_faction_gift_mitigation_async_glue_v1";
inline constexpr bool kFactionGiftMitigationAsyncGlueV1Public = false;
inline constexpr std::string_view kFactionGiftPrivateQueryStepV1 =
    "private-query-faction-gift-member-v1";
inline constexpr std::string_view kFactionGiftPrivateSubmitStepV1 =
    "private-submit-faction-gift-member-v1";
inline constexpr std::string_view kFactionGiftPrivateReceiptStepV1 =
    "private-query-faction-gift-receipt-v1";
inline constexpr std::string_view kFactionGiftPrivateColdRecoveryStepV1 =
    "private-query-faction-gift-cold-recovery-v1";

enum class FactionGiftMitigationAsyncCompletionV1 : std::uint8_t {
  not_executed = 0,
  preview_ready = 1,
  unavailable = 2,
};

enum FactionGiftMitigationAsyncFailureV1 : std::uint32_t {
  faction_gift_async_failure_none = 0,
  faction_gift_async_failure_frame = 1U << 0,
  faction_gift_async_failure_recipient = 1U << 1,
  faction_gift_async_failure_preview = 1U << 2,
  // Typed receiver REDs remain explicit and prevent command submission.
  faction_gift_async_failure_faction_war_receiver = 1U << 3,
  faction_gift_async_failure_opinion_receiver = 1U << 4,
  faction_gift_async_failure_faction_metric_receiver = 1U << 5,
  faction_gift_async_failure_read_only_preflight = 1U << 6,
  faction_gift_async_failure_independent_entity_receiver = 1U << 7,
};

struct FactionGiftMitigationAsyncContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  std::uintptr_t module_base = 0;
  // Data-only store view used by deterministic fixtures. Production leaves
  // this false and reads the exact module-relative stores directly.
  bool offline_receivers_fixture = false;
  FactionAtWarExactStoresV1 faction_at_war_exact_stores{};
  FactionMetricsExactFixtureV1 faction_metrics_exact_fixture{};
  GiftOpinionReceiverFixtureV1 gift_opinion_exact_fixture{};
  game::Snapshot expected_snapshot{};
  bridge::FactionTargetingRowProbeResultV1 targeting_rows{};
  bool use_direct_source_rows = false;
  std::uint64_t expected_public_revision = 0;
  bool direct_source_known_empty = false;
  std::uint64_t prior_query_native_revision = 0;
  std::vector<std::int32_t> direct_landed_vassal_character_ids;
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  bool execute_request = false;
  bool verify_receipt = false;
  game::FactionGiftMitigationAckV1 pending_ack{};
  game::FactionGiftMitigationRequestV1 request{};

  FactionGiftMitigationAsyncCompletionV1 completion =
      FactionGiftMitigationAsyncCompletionV1::not_executed;
  std::uint32_t failure_flags = faction_gift_async_failure_none;
  game::FactionGiftMitigationObservationV1 observation{};
  game::FactionGiftMitigationAckV1 ack{};
  FactionGiftMitigationIntegrationGateResultV1 preflight{};
  bool preflight_attempted = false;
  bool receipt_pending = false;
  bool idempotency_claimed = false;
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
};

// Exact-build production helpers. They reuse CK3's loaded definition lookup,
// two-role context, validator, compiled-cost evaluator and send command.
bool ReadFactionGiftPreviewThroughGenericInteractionV1(
    const Bindings &bindings, std::uintptr_t module_base,
    const GiftOpinionReceiverFixtureV1 *offline_fixture,
    std::uint32_t player_character_id,
    std::uint32_t recipient_character_id,
    game::FactionGiftPreviewV1 &output) noexcept;
bool ValidateFactionGiftThroughGenericInteractionDirectV1(
    const Bindings &bindings, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    std::uint64_t expected_definition_stable_hash, bool &valid,
    std::string &native_reason_key) noexcept;
bool SubmitFactionGiftThroughGenericInteractionDirectV1(
    const Bindings &bindings, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    std::uint64_t expected_definition_stable_hash) noexcept;

// Read the persisted faction and recipient identities without consulting the
// player's current targeting vector.  This is the native fact source used
// after a real CK3 process replacement; process/checkpoint identity remains a
// Python owner responsibility and is never inferred from this observation.
bool CaptureFactionGiftColdRecoveryObservationV1(
    const Bindings &bindings, std::uintptr_t module_base,
    const game::Snapshot &current, std::uint64_t public_revision,
    std::uint64_t native_revision, std::uint32_t source_faction_id,
    std::uint32_t recipient_character_id,
    game::FactionGiftMitigationObservationV1 &output) noexcept;

bool ExecuteFactionGiftMitigationAsyncMailboxV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeFactionGiftMitigationAsyncContextV1(
    const FactionGiftMitigationAsyncContextV1 &context);

} // namespace xar::ck3_11906

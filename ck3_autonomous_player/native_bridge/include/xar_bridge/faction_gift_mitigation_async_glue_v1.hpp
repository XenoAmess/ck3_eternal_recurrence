#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/faction_gift_mitigation_native_binder_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view kFactionGiftMitigationAsyncGlueV1Key =
    "g2_faction_gift_mitigation_async_glue_v1";
inline constexpr bool kFactionGiftMitigationAsyncGlueV1Public = false;

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
  // Exact 1.19.0.6 receivers are not yet closed for these fields. They are
  // explicit REDs and prevent command submission; real preview fields remain
  // independently useful to targeting and budget policy.
  faction_gift_async_failure_faction_war_receiver = 1U << 3,
  faction_gift_async_failure_opinion_receiver = 1U << 4,
};

struct FactionGiftMitigationAsyncContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  std::uintptr_t module_base = 0;
  game::Snapshot expected_snapshot{};
  bridge::FactionTargetingRowProbeResultV1 targeting_rows{};
  std::vector<std::int32_t> direct_landed_vassal_character_ids;
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  bool execute_request = false;
  game::FactionGiftMitigationRequestV1 request{};

  FactionGiftMitigationAsyncCompletionV1 completion =
      FactionGiftMitigationAsyncCompletionV1::not_executed;
  std::uint32_t failure_flags = faction_gift_async_failure_none;
  game::FactionGiftMitigationObservationV1 observation{};
  game::FactionGiftMitigationAckV1 ack{};
  bool receipt_pending = false;
  bool idempotency_claimed = false;
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
};

// Exact-build production helpers. They reuse CK3's loaded definition lookup,
// two-role context, validator, compiled-cost evaluator and send command.
bool ReadFactionGiftPreviewThroughGenericInteractionV1(
    const Bindings &bindings, std::uint32_t player_character_id,
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

bool ExecuteFactionGiftMitigationAsyncMailboxV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeFactionGiftMitigationAsyncContextV1(
    const FactionGiftMitigationAsyncContextV1 &context);

} // namespace xar::ck3_11906

#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class FactionGiftMembershipRoleV1 : std::uint32_t {
  leader = 0,
  character_member = 1,
};

enum class FactionGiftMitigationFailureClassV1 : std::uint32_t {
  none = 0,
  request_contract,
  snapshot_binding,
  faction_binding,
  recipient_binding,
  gift_preview_legality,
  budget_gate,
  idempotency,
  native_command_dispatch,
};

enum class FactionGiftMitigationAckStatusV1 : std::uint32_t {
  rejected_before_submit = 0,
  submitted_verification_pending = 1,
};

enum class FactionGiftMitigationReceiptStatusV1 : std::uint32_t {
  rejected = 0,
  mitigated = 1,
  left = 2,
  failed = 3,
};

struct FactionGiftPreviewV1 {
  bool available = false;
  std::string definition_key;
  std::uint64_t definition_stable_hash = 0;
  bool interaction_legal = false;
  bool auto_accept = false;
  std::int64_t gold_cost_raw = 0;
  std::uint32_t gold_scale = 0;
  std::int32_t opinion_delta = 0;

  friend bool operator==(const FactionGiftPreviewV1 &,
                         const FactionGiftPreviewV1 &) = default;
};

// A single observer must populate the targeting-faction row, recipient
// opinion and player resources from one paused snapshot. Character and
// faction handles are kept as full 32-bit generation-bearing identities.
struct FactionGiftMitigationObservationV1 {
  bool available = false;
  bool paused = false;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_snapshot_revision = 0;
  std::int32_t observed_date_raw = 0;

  bool player_resources_query_complete = false;
  std::uint32_t player_character_id = 0;
  std::int64_t player_gold_raw = 0;
  std::uint32_t player_gold_scale = 0;

  bool source_faction_requery_complete = false;
  std::uint32_t queried_source_faction_id = 0;
  bool source_faction_present = false;
  std::uint32_t source_faction_target_character_id = 0;
  bool source_faction_targeting_player = false;
  bool source_faction_at_war = false;
  std::optional<std::uint32_t> source_faction_leader_character_id;
  std::vector<std::uint32_t> source_faction_member_character_ids;
  bool source_faction_metrics_available = false;
  std::int64_t source_faction_power_raw = 0;
  std::int64_t source_faction_discontent_raw = 0;
  std::uint32_t source_faction_metric_scale = 0;

  bool recipient_identity_resolved = false;
  std::uint32_t recipient_character_id = 0;
  bool recipient_alive = false;
  bool recipient_is_ai = false;
  bool recipient_is_direct_landed_vassal = false;
  bool recipient_opinion_query_complete = false;
  std::int32_t recipient_opinion_of_player = 0;
  bool gift_opinion_present = false;
  std::optional<std::int32_t> gift_opinion_modifier_value;

  FactionGiftPreviewV1 gift_preview;

  friend bool operator==(const FactionGiftMitigationObservationV1 &,
                         const FactionGiftMitigationObservationV1 &) =
      default;
};

struct FactionGiftMitigationRequestV1 {
  std::string request_id;
  std::string idempotency_key;
  std::uint64_t expected_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::uint32_t player_character_id = 0;
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  FactionGiftMembershipRoleV1 membership_role =
      FactionGiftMembershipRoleV1::character_member;
  std::string expected_definition_key;
  std::uint64_t expected_definition_stable_hash = 0;
  std::int64_t expected_gold_cost_raw = 0;
  std::uint32_t expected_gold_scale = 0;
  std::int32_t expected_opinion_delta = 0;
  std::int64_t minimum_gold_reserve_raw = 0;
  std::uint32_t minimum_gold_reserve_scale = 0;
};

struct FactionGiftMitigationAckV1 {
  FactionGiftMitigationAckStatusV1 status =
      FactionGiftMitigationAckStatusV1::rejected_before_submit;
  bool verification_pending = false;
  std::string request_id;
  std::uint64_t pre_snapshot_revision = 0;
  std::uint64_t pre_native_snapshot_revision = 0;
  std::int32_t pre_observed_date_raw = 0;
  std::uint32_t player_character_id = 0;
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  FactionGiftMembershipRoleV1 membership_role =
      FactionGiftMembershipRoleV1::character_member;
  std::string definition_key;
  std::uint64_t definition_stable_hash = 0;
  std::int64_t expected_gold_cost_raw = 0;
  std::uint32_t gold_scale = 0;
  std::int32_t expected_opinion_delta = 0;
  std::int64_t pre_player_gold_raw = 0;
  std::int64_t minimum_gold_reserve_raw = 0;
  FactionGiftMitigationFailureClassV1 failure_class =
      FactionGiftMitigationFailureClassV1::none;
  std::string rejection_reason;
  std::string native_reason_key;
};

struct FactionGiftMitigationReceiptV1 {
  FactionGiftMitigationReceiptStatusV1 status =
      FactionGiftMitigationReceiptStatusV1::failed;
  std::string request_id;
  std::string reason;
  std::uint64_t post_snapshot_revision = 0;
  std::uint64_t post_native_snapshot_revision = 0;
  std::int32_t post_observed_date_raw = 0;
  std::uint32_t player_character_id = 0;
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  std::int64_t post_player_gold_raw = 0;
  std::int32_t post_recipient_opinion_of_player = 0;
  bool post_gift_opinion_present = false;
  std::optional<std::int32_t> post_gift_opinion_modifier_value;
  bool source_faction_present = false;
  bool recipient_still_in_source_faction = false;
  bool faction_dissolved = false;
  bool recipient_left = false;
  bool mitigation_applied = false;
  bool threat_resolved = false;
  bool postcondition_verified = false;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kFactionGiftMitigationActionV1Capability =
    "private.game.command.send-gift-to-faction-member-v1";
inline constexpr std::string_view kFactionGiftMitigationActionV1Step =
    "send-gift-to-faction-member-v1";
inline constexpr std::string_view kFactionGiftMitigationActionV1DefinitionKey =
    "gift_interaction";
inline constexpr std::uint32_t kFactionGiftMitigationActionV1GoldScale =
    100000;
inline constexpr std::string_view kFactionGiftMitigationActionV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view
    kFactionGiftMitigationActionV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kFactionGiftMitigationActionV1BackendId =
    "ck3-1.19.0.6-private-faction-gift-mitigation-action-v1";
inline constexpr std::string_view kFactionGiftMitigationActionV1ContractStage =
    "exact_build_private_action_core_pending_command_abi_certification";

struct FactionGiftMitigationNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool command_abi_certified = false;
  bool offline_fixture_command = false;
};

using CaptureFactionGiftMitigationObservationV1 = bool (*)(
    void *context, game::FactionGiftMitigationObservationV1 &output) noexcept;

// A true return means the native validator ran. `valid` is its verdict and
// the reason key is preserved on a native rejection.
using ValidateFactionGiftMitigationCommandV1 = bool (*)(
    void *context, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    bool &valid, std::string &native_reason_key) noexcept;

// The key is claimed immediately before the sole submit attempt. Once
// claimed, this core never retries the semantic action.
using ClaimFactionGiftMitigationIdempotencyKeyV1 = bool (*)(
    void *context, std::string_view idempotency_key) noexcept;

// A true return means exactly one command was handed to the engine submitter.
// It is queue acknowledgement only; receipt verification determines outcome.
using SubmitFactionGiftMitigationCommandV1 = bool (*)(
    void *context, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id,
    std::uint64_t definition_stable_hash) noexcept;

struct FactionGiftMitigationActionAccessV1 {
  void *context = nullptr;
  CaptureFactionGiftMitigationObservationV1 capture_observation = nullptr;
  ValidateFactionGiftMitigationCommandV1 validate_native = nullptr;
  ClaimFactionGiftMitigationIdempotencyKeyV1 claim_idempotency_key = nullptr;
  SubmitFactionGiftMitigationCommandV1 submit_native = nullptr;
};

FactionGiftMitigationNativeEnvironmentV1
BindFactionGiftMitigationNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::FactionGiftMitigationAckStatusV1 ExecuteFactionGiftMitigationActionV1(
    const FactionGiftMitigationNativeEnvironmentV1 &environment,
    const FactionGiftMitigationActionAccessV1 &access,
    const game::FactionGiftMitigationRequestV1 &request,
    game::FactionGiftMitigationAckV1 &ack) noexcept;

game::FactionGiftMitigationReceiptStatusV1
VerifyFactionGiftMitigationReceiptV1(
    const game::FactionGiftMitigationAckV1 &ack,
    const game::FactionGiftMitigationObservationV1 &post_observation,
    game::FactionGiftMitigationReceiptV1 &receipt) noexcept;

std::string_view FactionGiftMitigationFailureClassKeyV1(
    game::FactionGiftMitigationFailureClassV1 value) noexcept;
std::string SerializeFactionGiftMitigationAckV1(
    const game::FactionGiftMitigationAckV1 &ack);
std::string SerializeFactionGiftMitigationReceiptV1(
    const game::FactionGiftMitigationReceiptV1 &receipt);

} // namespace xar::ck3_11906

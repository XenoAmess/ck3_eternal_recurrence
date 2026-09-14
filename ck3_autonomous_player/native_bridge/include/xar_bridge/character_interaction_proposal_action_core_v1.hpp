#pragma once

#include "xar_bridge/character_interaction_preview_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class CharacterInteractionProposalActionFailureV1 : std::uint32_t {
  none = 0,
  invalid_request,
  interaction_not_allowlisted,
  exact_build_not_admitted,
  proposal_preview_unavailable,
  snapshot_binding_mismatch,
  proposal_payload_mismatch,
  religious_option_deferred,
  can_send_rejected,
  acceptance_not_actionable,
  budget_exceeded,
  proposal_changed_before_submit,
  submission_already_in_flight,
  submit_seam_unavailable,
  submit_not_acknowledged,
};

enum class CharacterInteractionProposalActionAckStatusV1 : std::uint32_t {
  rejected_before_submit = 0,
  submitted_verification_pending = 1,
};

enum class CharacterInteractionProposalReceiptStatusV1 : std::uint32_t {
  rejected = 0,
  response_pending = 1,
  applied = 2,
  postcondition_failed = 3,
};

enum class CharacterInteractionProposalPostconditionKindV1 : std::uint32_t {
  unavailable = 0,
  gift_opinion_and_payment,
  recruit_to_court,
  invite_to_court_and_cooldown,
  ordinary_vassalization,
  demand_payment_and_hook,
  educate_child_relation,
  offer_ward_relation,
  offer_guardianship_relation,
  grant_selected_titles,
  grant_vassal_transfer,
  ransom_prisoner_release,
};

struct CharacterInteractionProposalPayloadV1 {
  bool complete = false;
  std::int32_t semantic_subject_character_id = -1;
  std::int32_t semantic_object_character_id = -1;
  std::uint32_t selected_title_count = 0;
  std::string fingerprint;
  bool religious_option_selected = false;
  bool ordinary_feudal_or_clan_vassalization = false;

  friend bool operator==(const CharacterInteractionProposalPayloadV1 &,
                         const CharacterInteractionProposalPayloadV1 &) =
      default;
};

struct CharacterInteractionProposalPreviewEnvelopeV1 {
  CharacterInteractionPreviewV1 preview{};
  CharacterInteractionProposalPayloadV1 payload{};
};

struct CharacterInteractionProposalBudgetV1 {
  std::array<std::int64_t, kCharacterInteractionPreviewCostCountV1>
      maximum_actor_spend_raw{};

  friend bool operator==(const CharacterInteractionProposalBudgetV1 &,
                         const CharacterInteractionProposalBudgetV1 &) =
      default;
};

struct CharacterInteractionProposalActionRequestV1 {
  std::string request_id;
  std::string expected_snapshot_id;
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_proof_epoch = 0;
  std::int32_t expected_date_raw = 0;
  std::string interaction_key;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t semantic_subject_character_id = -1;
  std::int32_t semantic_object_character_id = -1;
  std::uint32_t selected_title_count = 0;
  std::string payload_fingerprint;
  CharacterInteractionProposalBudgetV1 budget{};
};

struct CharacterInteractionProposalActionAckV1 {
  CharacterInteractionProposalActionAckStatusV1 status =
      CharacterInteractionProposalActionAckStatusV1::rejected_before_submit;
  bool verification_pending = false;
  std::string request_id;
  CharacterInteractionProposalActionFailureV1 failure =
      CharacterInteractionProposalActionFailureV1::none;
  std::string reason;
  std::string snapshot_id;
  std::uint64_t pre_public_revision = 0;
  std::uint64_t pre_native_revision = 0;
  std::uint64_t pre_proof_epoch = 0;
  std::int32_t pre_date_raw = 0;
  std::string interaction_key;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t semantic_subject_character_id = -1;
  std::int32_t semantic_object_character_id = -1;
  std::uint32_t selected_title_count = 0;
  std::string payload_fingerprint;
  CharacterInteractionPreviewCostsV1 costs{};
  CharacterInteractionPreviewAcceptanceV1 acceptance{};
  CharacterInteractionProposalPostconditionKindV1 postcondition_kind =
      CharacterInteractionProposalPostconditionKindV1::unavailable;
};

// A later paused observer supplies explicit interaction-specific state. A
// native submit acknowledgement is deliberately absent from this structure.
struct CharacterInteractionProposalPostconditionObservationV1 {
  bool available = false;
  bool paused = false;
  std::string snapshot_id;
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::string interaction_key;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t semantic_subject_character_id = -1;
  std::int32_t semantic_object_character_id = -1;
  std::uint32_t selected_title_count = 0;
  std::string payload_fingerprint;
  bool matching_pending_proposal = false;

  bool terms_reconciled = false;
  bool recipient_has_gift_opinion_toward_actor = false;
  std::int64_t actor_gold_spent_raw = 0;
  std::int32_t recipient_court_owner_character_id = -1;
  bool invite_cooldown_present = false;
  std::int32_t recipient_immediate_liege_character_id = -1;
  bool obligation_state_matches = false;
  bool actor_hook_to_recipient_consumed = false;
  std::int64_t actor_gold_received_raw = 0;
  std::int32_t observed_guardian_character_id = -1;
  std::int32_t observed_ward_character_id = -1;
  bool education_relation_present = false;
  bool education_travel_pending = false;
  std::uint32_t selected_titles_held_by_subject_count = 0;
  bool title_transfer_graph_consistent = false;
  std::int32_t transferred_vassal_immediate_liege_character_id = -1;
  std::int32_t prisoner_imprisoned_by_character_id = -1;
};

struct CharacterInteractionProposalReceiptV1 {
  CharacterInteractionProposalReceiptStatusV1 status =
      CharacterInteractionProposalReceiptStatusV1::postcondition_failed;
  std::string request_id;
  std::string interaction_key;
  std::string reason;
  std::uint64_t post_public_revision = 0;
  std::uint64_t post_native_revision = 0;
  std::int32_t post_date_raw = 0;
  CharacterInteractionProposalPostconditionKindV1 postcondition_kind =
      CharacterInteractionProposalPostconditionKindV1::unavailable;
  bool interaction_specific_postcondition_verified = false;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kCharacterInteractionProposalActionCorePrivateKeyV1 =
        "character_interaction_proposal_action_core_v1";
inline constexpr std::string_view
    kCharacterInteractionProposalActionCoreGameVersionV1 = "1.19.0.6";
inline constexpr std::string_view
    kCharacterInteractionProposalActionCoreExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

struct CharacterInteractionProposalActionEnvironmentV1 {
  bool exact_build_admitted = false;
  bool submit_abi_certified = false;
  bool offline_fixture_submit = false;
};

struct CharacterInteractionProposalActionStateV1 {
  bool submission_in_flight = false;
  std::string in_flight_request_id;
  std::uint64_t acknowledged_submission_count = 0;
};

using CaptureCharacterInteractionProposalPreviewV1 = bool (*)(
    void *context,
    game::CharacterInteractionProposalPreviewEnvelopeV1 &output) noexcept;

// A true return is only a queue/transport ACK for exactly one submit attempt.
// The later interaction-specific receipt is the sole success authority.
using SubmitCharacterInteractionProposalOnceV1 = bool (*)(
    void *context,
    const game::CharacterInteractionProposalActionRequestV1 &request,
    const game::CharacterInteractionProposalPreviewEnvelopeV1
        &bound_preview) noexcept;

struct CharacterInteractionProposalActionAccessV1 {
  void *context = nullptr;
  CaptureCharacterInteractionProposalPreviewV1 capture_preview = nullptr;
  SubmitCharacterInteractionProposalOnceV1 submit_once = nullptr;
};

game::CharacterInteractionProposalActionAckStatusV1
ExecuteCharacterInteractionProposalActionCoreV1(
    const CharacterInteractionProposalActionEnvironmentV1 &environment,
    const CharacterInteractionProposalActionAccessV1 &access,
    CharacterInteractionProposalActionStateV1 &state,
    const game::CharacterInteractionProposalActionRequestV1 &request,
    game::CharacterInteractionProposalActionAckV1 &ack) noexcept;

game::CharacterInteractionProposalReceiptStatusV1
VerifyCharacterInteractionProposalReceiptV1(
    CharacterInteractionProposalActionStateV1 &state,
    const game::CharacterInteractionProposalActionAckV1 &ack,
    const game::CharacterInteractionProposalPostconditionObservationV1
        &post_observation,
    game::CharacterInteractionProposalReceiptV1 &receipt) noexcept;

std::string_view CharacterInteractionProposalActionFailureKeyV1(
    game::CharacterInteractionProposalActionFailureV1 failure) noexcept;
std::string_view CharacterInteractionProposalPostconditionKeyV1(
    game::CharacterInteractionProposalPostconditionKindV1 kind) noexcept;

} // namespace xar::ck3_11906

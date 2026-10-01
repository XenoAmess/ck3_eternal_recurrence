#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"
#include "xar_bridge/player_prisoner_ransom_private_v1.hpp"

namespace xar::ck3_12002 {

// Reuse the existing portable value contract and its formal recovery ledger.
// Native addresses and interaction layouts are bound by this version only.
using PlayerPrisonerRansomQuoteV1 = ck3_11906::PlayerPrisonerRansomQuoteV1;
using PlayerPrisonerRansomQuoteFailureV1 = ck3_11906::PlayerPrisonerRansomQuoteFailureV1;
using PlayerPrisonerRansomSubmitV1 = ck3_11906::PlayerPrisonerRansomSubmitV1;

bool ReadPlayerPrisonerCollectionV1(
    const bridge::PlayerPrisonerCollectionAccessV1 &access,
    bridge::PlayerPrisonerCollectionSnapshotV1 &output) noexcept;

struct PrisonerRansomBindings {
  bool enabled = false;
  ContextBindings context{};
  ck3_11906::GetCharacterInteractionDatabase get_character_interaction_database = nullptr;
  ck3_11906::HashStableKey hash_stable_key = nullptr;
  ck3_11906::LookupCharacterInteraction lookup_character_interaction = nullptr;
  MarriageRedirectInteractionRoles redirect_character_interaction_roles = nullptr;
  MarriageConstructInteractionAllRoles construct_character_interaction_context_all_roles = nullptr;
  MarriageValidateInteractionContext validate_character_interaction_context = nullptr;
  MarriageReadInteractionAnswerScore read_character_interaction_answer_score = nullptr;
  ck3_11906::EvaluateCharacterInteractionAnswer evaluate_character_interaction_answer = nullptr;
  MarriageDestroyInteractionContext destroy_character_interaction_context = nullptr;
  ck3_11906::GetScriptIdentifierTable get_script_identifier_table = nullptr;
  ck3_11906::LookupScriptIdentifierId lookup_script_identifier_id = nullptr;
  MarriageConstructSendInteractionCommand construct_send_character_interaction_command = nullptr;
  std::uintptr_t send_character_interaction_primary_vtable = 0;
  std::uintptr_t send_character_interaction_secondary_vtable = 0;
  void (*clear_local_options)(void *) = nullptr;
  void (*select_local_option)(void *, std::int32_t) = nullptr;
  using ReadNamedCost = bool (*)(void *, std::uintptr_t, const void *,
      std::int32_t, std::int32_t, std::int32_t, std::int64_t &) noexcept;
  void *named_cost_context = nullptr;
  ReadNamedCost read_named_cost = nullptr;
};

PrisonerRansomBindings BindPrisonerRansomImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

PlayerPrisonerRansomQuoteV1 ReadPlayerPrisonerRansomQuotePrivateV1(
    const PrisonerRansomBindings &bindings, std::uintptr_t module_base,
    std::int32_t jailer_character_id, std::int32_t prisoner_character_id) noexcept;

PlayerPrisonerRansomSubmitV1 SubmitPlayerPrisonerRansomPrivateV1(
    const PrisonerRansomBindings &bindings, std::uintptr_t module_base,
    const PlayerPrisonerRansomQuoteV1 &observed_quote,
    std::uint64_t expected_native_revision, std::int64_t expected_date_raw) noexcept;

std::string SerializePlayerPrisonerCollectionPrivateV1(
    const bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t snapshot_revision,
    const std::array<PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> &quotes,
    bool quotes_complete);

std::string SerializePrisonerWarRetentionV1(
    const ck3_11906::WarPrisonerReleasePairsObservationV1 &value);

} // namespace xar::ck3_12002

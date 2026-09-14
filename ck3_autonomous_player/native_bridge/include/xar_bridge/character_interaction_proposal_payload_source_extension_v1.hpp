#pragma once

#include "xar_bridge/character_interaction_proposal_action_core_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class CharacterInteractionProposalPayloadSourceFailureV1 : std::uint32_t {
  none = 0,
  invalid_request,
  interaction_not_supported,
  exact_build_not_admitted,
  native_bindings_unavailable,
  collector_capture_failed,
  collector_frame_mismatch,
  collector_context_malformed,
  definition_identity_mismatch,
  role_identity_unavailable,
  selected_options_malformed,
  religious_option_deferred,
  title_offer_identity_mismatch,
  selected_titles_malformed,
  selected_title_identity_unavailable,
};

struct CharacterInteractionProposalPayloadSourceV1 {
  bool available = false;
  CharacterInteractionProposalPayloadSourceFailureV1 failure =
      CharacterInteractionProposalPayloadSourceFailureV1::none;
  std::string reason;

  std::array<char, kCharacterInteractionPreviewSnapshotIdCapacityV1>
      snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;

  std::string interaction_key;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t secondary_actor_character_id = -1;
  std::int32_t secondary_recipient_character_id = -1;
  std::int32_t intermediary_character_id = -1;
  std::uint32_t selected_option_mask = 0;
  std::vector<std::int32_t> selected_title_ids;
  CharacterInteractionProposalPayloadV1 payload{};
};

enum class ReadCharacterInteractionProposalPayloadSourceResultV1
    : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kCharacterInteractionProposalPayloadSourcePrivateKeyV1 =
        "character_interaction_proposal_payload_source_extension_v1";
inline constexpr std::string_view
    kCharacterInteractionProposalPayloadSourceGameVersionV1 = "1.19.0.6";
inline constexpr std::string_view
    kCharacterInteractionProposalPayloadSourceExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

inline constexpr std::uintptr_t
    kCharacterInteractionProposalPayloadCharacterStorageSlotRvaV1 =
        0x570C130;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalPayloadTitleStorageSlotRvaV1 = 0x570C410;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalPayloadGrantTitlesOfferVtableRvaV1 =
        0x4112BA8;

struct CharacterInteractionProposalPayloadCollectorMemoryV1 {
  void *interaction_context = nullptr;
  CharacterInteractionPreviewFrameV1 frame{};
};

using CaptureCharacterInteractionProposalPayloadCollectorV1 = bool (*)(
    void *context, std::string_view interaction_key,
    std::int32_t actor_character_id, std::int32_t recipient_character_id,
    CharacterInteractionProposalPayloadCollectorMemoryV1 &output) noexcept;
using ReadCharacterInteractionProposalPayloadMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using LookupCharacterInteractionProposalPayloadDefinitionV1 = bool (*)(
    void *context, std::string_view canonical_key, void *&output) noexcept;

struct CharacterInteractionProposalPayloadSourceEnvironmentV1 {
  bool enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void **character_storage_slot = nullptr;
  void **landed_title_storage_slot = nullptr;
};

struct CharacterInteractionProposalPayloadSourceAccessV1 {
  void *context = nullptr;
  CaptureCharacterInteractionProposalPayloadCollectorV1 capture_collector =
      nullptr;
  ReadCharacterInteractionProposalPayloadMemoryV1 read_memory = nullptr;
  LookupCharacterInteractionProposalPayloadDefinitionV1 lookup_definition =
      nullptr;
};

game::ReadCharacterInteractionProposalPayloadSourceResultV1
ReadCharacterInteractionProposalPayloadSourceV1(
    const CharacterInteractionProposalPayloadSourceEnvironmentV1 &environment,
    const CharacterInteractionProposalPayloadSourceAccessV1 &access,
    const game::CharacterInteractionPreviewV1 &bound_preview,
    game::CharacterInteractionProposalPayloadSourceV1 &output) noexcept;

std::string_view CharacterInteractionProposalPayloadSourceFailureKeyV1(
    game::CharacterInteractionProposalPayloadSourceFailureV1 failure) noexcept;

} // namespace xar::ck3_11906

#pragma once

#include "xar_bridge/character_interaction_preview_v1_source_adapter.hpp"
#include "xar_bridge/character_interaction_proposal_action_core_v1.hpp"
#include "xar_bridge/character_interaction_proposal_payload_source_extension_v1.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kCharacterInteractionProposalNativeBinderPrivateKeyV1 =
        "character_interaction_proposal_native_binder_v1";
inline constexpr std::string_view
    kCharacterInteractionProposalNativeBinderExecutableSha256V1 =
        kCharacterInteractionProposalActionCoreExecutableSha256V1;

inline constexpr std::uintptr_t
    kCharacterInteractionProposalCommandManagerRvaV1 = 0x57621F0;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalDatabaseGetterRvaV1 =
        kCharacterInteractionPreviewDatabaseGetterRvaV1;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalStableKeyHashRvaV1 =
        kCharacterInteractionPreviewStableKeyHashRvaV1;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalDefinitionLookupRvaV1 =
        kCharacterInteractionPreviewDefinitionLookupRvaV1;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalConstructTwoRoleContextRvaV1 =
        kCharacterInteractionPreviewConstructContextRvaV1;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalRefreshContextRvaV1 =
        kCharacterInteractionPreviewRefreshContextRvaV1;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalFinalizeContextRvaV1 =
        kCharacterInteractionPreviewFinalizeContextRvaV1;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalCompleteCanSendRvaV1 =
        kCharacterInteractionPreviewCanSendRvaV1;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalDestroyContextRvaV1 =
        kCharacterInteractionPreviewDestroyContextRvaV1;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalConstructCommandRvaV1 = 0x26B3220;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalSubmitCommandRvaV1 = 0x0973E00;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalCommandPrimaryVtableRvaV1 = 0x40829F8;
inline constexpr std::uintptr_t
    kCharacterInteractionProposalCommandSecondaryVtableRvaV1 = 0x40829C8;
inline constexpr std::size_t
    kCharacterInteractionProposalNativeContextSizeV1 = 0x338;
inline constexpr std::size_t
    kCharacterInteractionProposalNativeCommandSizeV1 = 0x368;
inline constexpr std::size_t
    kCharacterInteractionProposalCommandContextOffsetV1 = 0x20;
inline constexpr std::size_t
    kCharacterInteractionProposalCommandSecondaryVtableOffsetV1 = 0x18;
inline constexpr std::uint32_t
    kCharacterInteractionProposalSubmitFlagsV1 = 0x0E;

enum class CharacterInteractionProposalNativeBinderFailureV1
    : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  native_binding_mismatch,
  native_signature_mismatch,
  native_lifecycle_unavailable,
  capture_unavailable,
  capture_drift,
  typed_payload_source_required,
  typed_payload_source_mismatch,
  special_context_materializer_unavailable,
  special_context_materialization_failed,
  definition_lookup_failed,
  character_identity_unavailable,
  context_construction_failed,
  context_identity_mismatch,
  complete_can_send_rejected,
  command_construction_failed,
  command_identity_mismatch,
  command_queue_rejected,
};

enum class CharacterInteractionProposalNativeBindResultV1
    : std::uint32_t {
  available = 0,
  blocked = 1,
  failed = 2,
};

struct CharacterInteractionProposalNativeCaptureV1 {
  game::CharacterInteractionProposalPreviewEnvelopeV1 envelope{};
  bool typed_payload_source_present = false;
  game::CharacterInteractionProposalPayloadSourceV1 typed_payload_source{};
};

using CaptureCharacterInteractionProposalNativeV1 = bool (*)(
    void *context,
    const game::CharacterInteractionProposalActionRequestV1 &request,
    CharacterInteractionProposalNativeCaptureV1 &output) noexcept;

// The materializer owns construction of the six role/option/special-payload
// shapes. It must return a fresh binder-owned context in context_storage. The
// binder refreshes, finalizes, rereads it through DIPLO5 and destroys it.
using MaterializeCharacterInteractionProposalSpecialContextV1 = bool (*)(
    void *context,
    const game::CharacterInteractionProposalPayloadSourceV1 &source,
    void *context_storage, std::size_t context_storage_size,
    void *definition, void *&output_context) noexcept;

using CharacterInteractionProposalGetDatabaseV1 = void *(*)();
using CharacterInteractionProposalHashStableKeyV1 = std::int32_t (*)(
    void *database, const char *data, std::uint32_t size);
using CharacterInteractionProposalLookupDefinitionV1 = void *(*)(
    void *database, std::int32_t stable_hash);
using CharacterInteractionProposalConstructTwoRoleContextV1 = void *(*)(
    void *context_storage, void *definition,
    std::int32_t actor_character_id,
    std::int32_t recipient_character_id, void *extra_context,
    bool initialize_options);
using CharacterInteractionProposalRefreshContextV1 = void (*)(
    void *interaction_context, bool refresh);
using CharacterInteractionProposalContextStepV1 = void (*)(
    void *interaction_context);
using CharacterInteractionProposalCanSendV1 = bool (*)(
    void *interaction_context, void *error_output);
using ConstructCharacterInteractionProposalCommandV1 = void *(*)(
    void *command_storage, const void *interaction_context);
using SubmitCharacterInteractionProposalCommandV1 = bool (*)(
    void *command_manager, void *command, std::uint32_t channel_flags);

struct CharacterInteractionProposalNativeBinderEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;

  void *memory_context = nullptr;
  ReadCharacterInteractionProposalPayloadMemoryV1 read_memory = nullptr;

  void **character_storage_slot = nullptr;
  void **landed_title_storage_slot = nullptr;
  CharacterInteractionProposalGetDatabaseV1 get_database = nullptr;
  CharacterInteractionProposalHashStableKeyV1 hash_stable_key = nullptr;
  CharacterInteractionProposalLookupDefinitionV1 lookup_definition = nullptr;
  CharacterInteractionProposalConstructTwoRoleContextV1
      construct_two_role_context = nullptr;
  CharacterInteractionProposalRefreshContextV1 refresh_context = nullptr;
  CharacterInteractionProposalContextStepV1 finalize_context = nullptr;
  CharacterInteractionProposalCanSendV1 complete_can_send = nullptr;
  CharacterInteractionProposalContextStepV1 destroy_context = nullptr;

  void *command_manager = nullptr;
  ConstructCharacterInteractionProposalCommandV1 construct_command = nullptr;
  SubmitCharacterInteractionProposalCommandV1 submit_command = nullptr;
  std::uintptr_t command_primary_vtable = 0;
  std::uintptr_t command_secondary_vtable = 0;

  void *capture_context = nullptr;
  CaptureCharacterInteractionProposalNativeV1 capture = nullptr;
  void *special_materializer_context = nullptr;
  MaterializeCharacterInteractionProposalSpecialContextV1
      materialize_special_context = nullptr;
};

struct CharacterInteractionProposalNativeBinderStateV1 {
  CharacterInteractionProposalNativeBinderEnvironmentV1 environment{};
  CharacterInteractionProposalActionStateV1 action_state{};
  const game::CharacterInteractionProposalActionRequestV1 *active_request =
      nullptr;
  CharacterInteractionProposalNativeCaptureV1 bound_capture{};
  std::uint32_t capture_count = 0;
  bool configured = false;
  bool submit_called = false;
  std::atomic<std::uint32_t> last_failure{
      static_cast<std::uint32_t>(
          CharacterInteractionProposalNativeBinderFailureV1::none)};
};

CharacterInteractionProposalNativeBinderEnvironmentV1
BindCharacterInteractionProposalNativeBinderEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

CharacterInteractionProposalNativeBindResultV1
ConfigureCharacterInteractionProposalNativeBinderV1(
    CharacterInteractionProposalNativeBinderStateV1 &binder) noexcept;

game::CharacterInteractionProposalActionAckStatusV1
ExecuteCharacterInteractionProposalFromNativeBinderV1(
    CharacterInteractionProposalNativeBinderStateV1 &binder,
    const game::CharacterInteractionProposalActionRequestV1 &request,
    game::CharacterInteractionProposalActionAckV1 &ack) noexcept;

CharacterInteractionProposalNativeBinderFailureV1
ReadCharacterInteractionProposalNativeBinderFailureV1(
    const CharacterInteractionProposalNativeBinderStateV1 &binder) noexcept;
std::string_view CharacterInteractionProposalNativeBinderFailureKeyV1(
    CharacterInteractionProposalNativeBinderFailureV1 failure) noexcept;

} // namespace xar::ck3_11906

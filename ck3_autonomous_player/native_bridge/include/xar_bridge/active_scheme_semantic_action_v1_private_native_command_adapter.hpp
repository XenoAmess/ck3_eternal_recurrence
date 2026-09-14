#pragma once

#include "xar_bridge/active_scheme_semantic_action_v1_private.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kActiveSchemeSemanticActionV1PrivateNativeCommandGameVersion =
        "1.19.0.6";
inline constexpr std::string_view
    kActiveSchemeSemanticActionV1PrivateNativeCommandEvidenceRevision =
        "scheme_state_1_19_0_6@a5438595+scheme6-route-prefixes-v1";
inline constexpr std::uint32_t
    kActiveSchemeSemanticActionV1PrivateNativeCommandChannel = 0x0E;
inline constexpr std::uintptr_t
    kActiveSchemeSemanticActionV1PrivateConstructContextRva = 0x2C3EE50;
inline constexpr std::uintptr_t
    kActiveSchemeSemanticActionV1PrivateValidateContextRva = 0x2C43F00;
inline constexpr std::uintptr_t
    kActiveSchemeSemanticActionV1PrivateConstructCommandRva = 0x26B3220;
inline constexpr std::uintptr_t
    kActiveSchemeSemanticActionV1PrivateSubmitCommandRva = 0x0973E00;
inline constexpr std::uintptr_t
    kActiveSchemeSemanticActionV1PrivateDestroyContextRva = 0x2C3F380;
inline constexpr std::uintptr_t
    kActiveSchemeSemanticActionV1PrivateCommandPrimaryVtableRva = 0x40829F8;
inline constexpr std::uintptr_t
    kActiveSchemeSemanticActionV1PrivateCommandSecondaryVtableRva = 0x40829C8;

struct ActiveSchemeSemanticActionV1PrivateNativeCommandSignature {
  std::uintptr_t rva = 0;
  std::uint8_t size = 0;
  std::array<std::uint8_t, 40> bytes{};
};

// validate/construct-command are the frozen SCHEME1 reuse prefixes. Context
// construction, command submission and context destruction are exact bytes
// captured from the same admitted executable for this private adapter.
inline constexpr std::array<
    ActiveSchemeSemanticActionV1PrivateNativeCommandSignature, 5>
    kActiveSchemeSemanticActionV1PrivateNativeCommandSignatures{{
        {kActiveSchemeSemanticActionV1PrivateConstructContextRva, 39,
         {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x6C, 0x24, 0x18,
          0x48, 0x89, 0x74, 0x24, 0x20, 0x48, 0x89, 0x4C, 0x24, 0x08,
          0x57, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56, 0x41, 0x57, 0x48,
          0x83, 0xEC, 0x30, 0x41, 0x8B, 0xF9, 0x41, 0x8B, 0xD8}},
        {kActiveSchemeSemanticActionV1PrivateValidateContextRva, 29,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x81, 0xEC, 0x90,
          0x00, 0x00, 0x00, 0x48, 0x8B, 0xFA, 0x48, 0x8B, 0xD9, 0x4C,
          0x8B, 0xCA, 0x41, 0xB0, 0x01, 0x41, 0x0F, 0xB6, 0xD0}},
        {kActiveSchemeSemanticActionV1PrivateConstructCommandRva, 39,
         {0x48, 0x89, 0x5C, 0x24, 0x18, 0x48, 0x89, 0x74, 0x24, 0x20,
          0x48, 0x89, 0x4C, 0x24, 0x08, 0x57, 0x48, 0x83, 0xEC, 0x20,
          0x48, 0x8B, 0xFA, 0x48, 0x8B, 0xF1, 0xC6, 0x41, 0x08, 0x00,
          0x33, 0xC0, 0x48, 0x89, 0x41, 0x0C, 0x89, 0x41, 0x14}},
        {kActiveSchemeSemanticActionV1PrivateSubmitCommandRva, 39,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x4C, 0x89, 0x4C, 0x24, 0x20,
          0x57, 0x48, 0x83, 0xEC, 0x20, 0x41, 0x8B, 0xD8, 0x4C, 0x8B,
          0xC2, 0x48, 0x8B, 0xF9, 0x48, 0x8B, 0x02, 0x48, 0x8D, 0x54,
          0x24, 0x38, 0x49, 0x8B, 0xC8, 0xFF, 0x50, 0x40, 0x90}},
        {kActiveSchemeSemanticActionV1PrivateDestroyContextRva, 38,
         {0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B, 0xD9, 0x48,
          0x8B, 0x89, 0x30, 0x03, 0x00, 0x00, 0x48, 0x85, 0xC9, 0x74,
          0x0A, 0x48, 0x8B, 0x01, 0xBA, 0x01, 0x00, 0x00, 0x00, 0xFF,
          0x10, 0x48, 0x8B, 0x93, 0x00, 0x03, 0x00, 0x00}},
    }};

struct ActiveSchemeSemanticActionV1PrivateNativeCharacterLease {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint32_t observed_full_id = 0;
  std::uint32_t slot_index = 0;
  std::uint32_t generation = 0;
  std::uint64_t proof_epoch = 0;

  friend bool operator==(
      const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &,
      const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &) =
      default;
};

struct ActiveSchemeSemanticActionV1PrivateNativeInteractionLease {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::string interaction_key;
  std::string scheme_type_key;
  std::int32_t stable_key_hash = 0;
  std::uint64_t definition_generation = 0;
  std::uint64_t proof_epoch = 0;

  friend bool operator==(
      const ActiveSchemeSemanticActionV1PrivateNativeInteractionLease &,
      const ActiveSchemeSemanticActionV1PrivateNativeInteractionLease &) =
      default;
};

struct ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease {
  bool identity_round_trip = false;
  std::uintptr_t command_manager_address = 0;
  std::uint64_t command_manager_generation = 0;
  std::uintptr_t submitter_address = 0;
  std::uint64_t proof_epoch = 0;

  friend bool operator==(
      const ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease &,
      const ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease &) =
      default;
};

struct ActiveSchemeSemanticActionV1PrivateNativeContextLease {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t generation = 0;
  std::uint64_t proof_epoch = 0;
  std::uint32_t actor_full_id = 0;
  std::uint32_t target_full_id = 0;
  std::int32_t interaction_stable_key_hash = 0;
  std::uint64_t interaction_generation = 0;
  bool starter_options_exclusive = false;
  std::uint32_t starter_option_count = 0;
  std::string selected_starter_package;
};

struct ActiveSchemeSemanticActionV1PrivateNativeValidationProof {
  bool evaluated = false;
  bool valid = false;
  std::uintptr_t validator_address = 0;
  std::uintptr_t context_address = 0;
  std::uint64_t context_generation = 0;
  std::uint64_t proof_epoch = 0;
};

struct ActiveSchemeSemanticActionV1PrivateNativeCommandLease {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t generation = 0;
  std::uint64_t proof_epoch = 0;
  std::uintptr_t constructor_address = 0;
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
  std::uintptr_t copied_context_address = 0;
  std::uint64_t copied_context_generation = 0;
  std::uint32_t actor_full_id = 0;
  std::uint32_t target_full_id = 0;
  std::int32_t interaction_stable_key_hash = 0;
};

using ActiveSchemeSemanticActionV1PrivateNativeReadMemory = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeResolveCharacter = bool (*)(
    void *context, std::uint32_t full_id,
    ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &output) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeResolveInteraction = bool (*)(
    void *context, std::string_view interaction_key,
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease
        &output) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeResolveSubmitRoute = bool (*)(
    void *context,
    ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease
        &output) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeConstructContext = bool (*)(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateCommand &semantic_command,
    const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &actor,
    const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &target,
    const ActiveSchemeSemanticActionV1PrivateNativeInteractionLease
        &interaction,
    ActiveSchemeSemanticActionV1PrivateNativeContextLease &output) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeValidateContext = bool (*)(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease
        &native_context,
    ActiveSchemeSemanticActionV1PrivateNativeValidationProof
        &output) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeConstructCommand = bool (*)(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease
        &native_context,
    ActiveSchemeSemanticActionV1PrivateNativeCommandLease &output) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeSubmit = bool (*)(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease &route,
    const ActiveSchemeSemanticActionV1PrivateNativeCommandLease &command,
    std::uint32_t channel_flags) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeReleaseContext = void (*)(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease
        &native_context) noexcept;
using ActiveSchemeSemanticActionV1PrivateNativeReleaseCommand = void (*)(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeCommandLease
        &native_command) noexcept;

struct ActiveSchemeSemanticActionV1PrivateNativeCommandOperations {
  ActiveSchemeSemanticActionV1PrivateNativeReadMemory read_memory = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeResolveCharacter
      resolve_character = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeResolveInteraction
      resolve_interaction = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeResolveSubmitRoute
      resolve_submit_route = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeConstructContext
      construct_context = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeValidateContext validate_context =
      nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeConstructCommand
      construct_command = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeSubmit submit = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeReleaseContext release_context =
      nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeReleaseCommand release_command =
      nullptr;
};

struct ActiveSchemeSemanticActionV1PrivateNativeRouteProofGate {
  std::string_view evidence_revision{};
  bool stable_interaction_key_lookup_proven = false;
  bool full_character_identity_generation_proven = false;
  bool starter_package_encoding_proven = false;
  bool command_copy_lifetime_proven = false;
};

struct ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment {
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::string_view admitted_game_version{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeCommandOperations operations{};
  ActiveSchemeSemanticActionV1PrivateNativeRouteProofGate proof_gate{};
};

// Retains callback metadata only. Every native character, definition,
// context, command and command-manager lease is transaction-local.
struct ActiveSchemeSemanticActionV1PrivateNativeCommandState {
  bool attached = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeCommandOperations operations{};
  void *upstream_context = nullptr;
  CaptureActiveSchemeSemanticActionObservationV1Private
      upstream_capture_observation = nullptr;
  CaptureActiveSchemeSemanticActionPreconditionV1Private
      upstream_capture_precondition = nullptr;
};

// Wraps the existing Scheme5 access without changing its observer or
// precondition implementations, installs the native submit adapter, and
// returns the exact environment that Scheme5 must consume.
bool BindActiveSchemeSemanticActionV1PrivateNativeCommand(
    const ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment
        &binding,
    ActiveSchemeSemanticActionV1PrivateNativeCommandState &state,
    ActiveSchemeSemanticActionV1PrivateAccess &access,
    ActiveSchemeSemanticActionV1PrivateEnvironment
        &action_environment) noexcept;

} // namespace xar::bridge

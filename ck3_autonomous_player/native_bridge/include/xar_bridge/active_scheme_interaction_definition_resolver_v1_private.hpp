#pragma once

#include "xar_bridge/active_scheme_semantic_action_v1_private_native_command_adapter.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kActiveSchemeInteractionDefinitionResolverV1PrivateGameVersion =
        "1.19.0.6";
inline constexpr std::string_view
    kActiveSchemeInteractionDefinitionResolverV1PrivateExecutableSha256 =
        kActiveSchemeSemanticActionV1PrivateExecutableSha256;
inline constexpr std::string_view
    kActiveSchemeInteractionDefinitionResolverV1PrivateEvidenceRevision =
        "active_scheme_definition_resolver_1_19_0_6@scheme7-v1";

inline constexpr std::uintptr_t
    kActiveSchemeInteractionDefinitionDatabaseGetterRva = 0x0831890;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionStableKeyHashRva = 0x3B8B000;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionDatabaseEnumerationReferenceRva = 0x0F928A0;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionLoadedLookupReferenceRva = 0x0997930;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionOriginalStableKeyLookupCallerRva = 0x2C46E40;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionDatabaseSingletonSlotRva = 0x570C100;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionLookupFallbackSlotRva = 0x570C628;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionDatabaseObjectKeyConstructorRva = 0x345E620;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionDefinitionRttiRva = 0x50401B0;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionDefinitionPrimaryVtableRva = 0x4403CE0;
inline constexpr std::uintptr_t
    kActiveSchemeInteractionDefinitionSecondaryVtableRva = 0x4403CA8;

inline constexpr std::size_t kActiveSchemeInteractionDatabaseRowsOffset =
    0x68;
inline constexpr std::size_t kActiveSchemeInteractionDatabaseCountOffset =
    0x74;
inline constexpr std::size_t
    kActiveSchemeInteractionDefinitionRuntimeOrdinalOffset = 0x10;
inline constexpr std::size_t
    kActiveSchemeInteractionDefinitionStableHashOffset = 0x14;
inline constexpr std::size_t
    kActiveSchemeInteractionDefinitionCanonicalKeyOffset = 0x18;
inline constexpr std::size_t
    kActiveSchemeInteractionDefinitionSecondarySubobjectOffset = 0x2A80;
inline constexpr std::int32_t
    kActiveSchemeInteractionDefinitionMaximumCount = 4096;
inline constexpr std::uint32_t kActiveSchemeSwayInteractionStableHash =
    0x5783F850U;
inline constexpr std::uint32_t kActiveSchemeMurderInteractionStableHash =
    0xDF3F9819U;

struct ActiveSchemeInteractionDefinitionResolverV1PrivateSignature {
  std::uintptr_t rva = 0;
  std::uint8_t size = 0;
  std::array<std::uint8_t, 48> bytes{};
};

inline constexpr std::array<
    ActiveSchemeInteractionDefinitionResolverV1PrivateSignature, 6>
    kActiveSchemeInteractionDefinitionResolverV1PrivateSignatures{{
        {kActiveSchemeInteractionDefinitionDatabaseGetterRva, 40,
         {0x48, 0x83, 0xEC, 0x38, 0x48, 0x8B, 0x05, 0x65, 0xA8, 0xED,
          0x04, 0x48, 0x85, 0xC0, 0x75, 0x42, 0xC7, 0x44, 0x24, 0x28,
          0x1E, 0x00, 0x00, 0x00, 0x48, 0x8D, 0x05, 0x39, 0x24, 0x85,
          0x03, 0x48, 0x89, 0x44, 0x24, 0x20, 0x48, 0x8D, 0x54, 0x24}},
        {kActiveSchemeInteractionStableKeyHashRva, 40,
         {0x89, 0x4C, 0x24, 0x08, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x33,
          0xC0, 0x48, 0x8D, 0x4C, 0x24, 0x30, 0x41, 0x8B, 0xD8, 0x89,
          0x44, 0x24, 0x30, 0x45, 0x8B, 0xC8, 0x89, 0x44, 0x24, 0x40,
          0x4C, 0x8B, 0xC2, 0x48, 0x8D, 0x54, 0x24, 0x40, 0xE8, 0x95}},
        {kActiveSchemeInteractionDatabaseEnumerationReferenceRva, 40,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24, 0x10,
          0x48, 0x89, 0x74, 0x24, 0x18, 0x57, 0x41, 0x54, 0x41, 0x55,
          0x41, 0x56, 0x41, 0x57, 0x48, 0x81, 0xEC, 0x70, 0x03, 0x00,
          0x00, 0x4C, 0x8B, 0xE2, 0x48, 0x8B, 0xD9, 0x45, 0x33, 0xED}},
        {kActiveSchemeInteractionLoadedLookupReferenceRva, 40,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x45, 0x33, 0xC0, 0x48, 0x63,
          0xDA, 0x44, 0x38, 0x81, 0xF8, 0x0E, 0x00, 0x00, 0x45, 0x8B,
          0xC8, 0x41, 0x0F, 0x94, 0xC1, 0x45, 0x8D, 0x58, 0xFE, 0x45,
          0x85, 0xC9, 0x0F, 0x84, 0x8D, 0x00, 0x00, 0x00, 0x41, 0x83}},
        {kActiveSchemeInteractionDatabaseObjectKeyConstructorRva, 48,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83, 0xEC, 0x20,
          0x48, 0x8B, 0x41, 0x08, 0x48, 0x8B, 0xD9, 0x48, 0x8D, 0x0D,
          0x08, 0x4C, 0xC3, 0x00, 0x49, 0x8B, 0xF8, 0x48, 0x89, 0x0B,
          0x48, 0x8D, 0x0D, 0x1B, 0x4C, 0xC3, 0x00, 0x48, 0x63, 0x40,
          0x04, 0x48, 0x89, 0x4C, 0x18, 0x08, 0x89, 0x53}},
        {kActiveSchemeInteractionOriginalStableKeyLookupCallerRva, 40,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10,
          0x48, 0x89, 0x7C, 0x24, 0x18, 0x4C, 0x89, 0x74, 0x24, 0x20,
          0x55, 0x48, 0x8D, 0xAC, 0x24, 0x00, 0xFD, 0xFF, 0xFF, 0x48,
          0x81, 0xEC, 0x00, 0x04, 0x00, 0x00, 0x49, 0x8B, 0xF1, 0x49}},
    }};

struct ActiveSchemeInteractionDefinitionResolverV1PrivateImagePointerSlot {
  std::uintptr_t slot_rva = 0;
  std::uintptr_t target_rva = 0;
};

inline constexpr std::array<
    ActiveSchemeInteractionDefinitionResolverV1PrivateImagePointerSlot, 11>
    kActiveSchemeInteractionDefinitionResolverV1PrivateImagePointerSlots{{
        {0x4403CE0, 0x07E9220},
        {0x4403CE8, 0x2C3B8C0},
        {0x4403CF0, 0x07E6490},
        {0x4403CA0, 0x4A7B450},
        {0x4403CA8, 0x2C4BF4C},
        {0x4403CB0, 0x2BA47D4},
        {0x4403CB8, 0x188FBB4},
        {0x4403CC0, 0x3B8B110},
        {0x4403CC8, 0x2BA49B8},
        {0x4403CD0, 0x07E6490},
        {0x4403CD8, 0x4A7B478},
    }};

struct ActiveSchemeInteractionDefinitionResolverV1PrivateFrame {
  bool application_main_thread = false;
  bool paused = false;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;

  friend bool operator==(
      const ActiveSchemeInteractionDefinitionResolverV1PrivateFrame &,
      const ActiveSchemeInteractionDefinitionResolverV1PrivateFrame &) =
      default;
};

using CaptureActiveSchemeInteractionDefinitionResolverV1PrivateFrame =
    bool (*)(void *context,
             ActiveSchemeInteractionDefinitionResolverV1PrivateFrame
                 &output) noexcept;
using InvokeActiveSchemeInteractionDefinitionDatabaseGetterV1Private =
    bool (*)(void *context, std::uintptr_t getter_address,
             std::uintptr_t &output) noexcept;
using InvokeActiveSchemeInteractionStableKeyHashV1Private = bool (*)(
    void *context, std::uintptr_t hash_function_address,
    std::uintptr_t database, std::string_view key,
    std::int32_t &output) noexcept;
using InvokeActiveSchemeInteractionLoadedLookupV1Private = bool (*)(
    void *context, std::uintptr_t lookup_function_address,
    std::uintptr_t database, std::int32_t stable_key_hash,
    std::uintptr_t &output) noexcept;

struct ActiveSchemeInteractionDefinitionResolverV1PrivateEnvironment {
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::string_view admitted_game_version{};
  std::string_view evidence_revision{};
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  CaptureActiveSchemeInteractionDefinitionResolverV1PrivateFrame
      capture_frame = nullptr;
  InvokeActiveSchemeInteractionDefinitionDatabaseGetterV1Private
      invoke_database_getter = nullptr;
  InvokeActiveSchemeInteractionStableKeyHashV1Private invoke_stable_key_hash =
      nullptr;
  InvokeActiveSchemeInteractionLoadedLookupV1Private invoke_loaded_lookup =
      nullptr;
};

// The state forwards all pre-existing SCHEME6 native operations to their
// original context. It retains no database, vector or definition pointer.
struct ActiveSchemeInteractionDefinitionResolverV1PrivateState {
  bool attached = false;
  std::uintptr_t module_base = 0;
  void *resolver_context = nullptr;
  CaptureActiveSchemeInteractionDefinitionResolverV1PrivateFrame
      capture_frame = nullptr;
  InvokeActiveSchemeInteractionDefinitionDatabaseGetterV1Private
      invoke_database_getter = nullptr;
  InvokeActiveSchemeInteractionStableKeyHashV1Private invoke_stable_key_hash =
      nullptr;
  InvokeActiveSchemeInteractionLoadedLookupV1Private invoke_loaded_lookup =
      nullptr;
  void *upstream_context = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeCommandOperations
      upstream_operations{};
};

// Installs only resolve_interaction and context-forwarding thunks into a
// not-yet-bound SCHEME6 environment. SCHEME6 still owns the double-resolution
// transaction and final submit.
bool BindActiveSchemeInteractionDefinitionResolverV1Private(
    const ActiveSchemeInteractionDefinitionResolverV1PrivateEnvironment
        &resolver,
    ActiveSchemeInteractionDefinitionResolverV1PrivateState &state,
    ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment
        &command_binding) noexcept;

} // namespace xar::bridge

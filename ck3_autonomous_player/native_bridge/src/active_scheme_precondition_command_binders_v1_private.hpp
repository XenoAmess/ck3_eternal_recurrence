#pragma once

#include "active_scheme_paused_live_native_glue_v1_private.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kActiveSchemePreconditionCommandBindersV1PrivateStage =
        "scheme10_precondition_command_binders_mailbox_backend_pending";
inline constexpr std::string_view
    kActiveSchemePreconditionCommandBindersV1PrivateEvidenceRevision =
        "active_scheme_precondition_command_binders_1_19_0_6@scheme10-v1";

inline constexpr std::uintptr_t
    kActiveSchemePreconditionRefreshContextRva = 0x2C40950;
inline constexpr std::uintptr_t
    kActiveSchemePreconditionFinalizeContextRva = 0x2C40B20;
inline constexpr std::uintptr_t
    kActiveSchemePreconditionGetScriptIdentifierTableRva = 0x3B971A0;
inline constexpr std::uintptr_t
    kActiveSchemePreconditionLookupScriptIdentifierRva = 0x3B97020;
inline constexpr std::uintptr_t
    kActiveSchemeCommandManagerRva = 0x57621F0;
inline constexpr std::uintptr_t
    kActiveSchemeCharacterStorageSlotRva = 0x570C130;
inline constexpr std::uintptr_t
    kActiveSchemeCharacterFallbackSlotRva = 0x570C138;

inline constexpr std::size_t kActiveSchemeNativeContextSize = 0x338;
inline constexpr std::size_t kActiveSchemeNativeCommandSize = 0x368;
inline constexpr std::size_t kActiveSchemeContextActorOffset = 0x2D8;
inline constexpr std::size_t kActiveSchemeContextRecipientOffset = 0x2DC;
inline constexpr std::size_t kActiveSchemeContextSelectedOptionsOffset = 0x300;
inline constexpr std::size_t kActiveSchemeContextSelectedOptionsCountOffset =
    0x30C;
inline constexpr std::size_t kActiveSchemeDefinitionOptionsOffset = 0x2548;
inline constexpr std::size_t kActiveSchemeDefinitionOptionsCountOffset =
    0x2554;
inline constexpr std::size_t kActiveSchemeDefinitionOptionsExclusiveOffset =
    0x2A4E;
inline constexpr std::size_t kActiveSchemeDefinitionOptionStride = 0x7D0;
inline constexpr std::size_t kActiveSchemeDefinitionOptionFlagOffset = 0x3A8;
inline constexpr std::size_t kActiveSchemeCopiedCommandContextOffset = 0x20;

struct ActiveSchemePreconditionCommandBindersV1PrivateSignature {
  std::uintptr_t rva = 0;
  std::uint8_t size = 0;
  std::array<std::uint8_t, 24> bytes{};
};

// Prefixes are additionally covered by the full-span verifier. They prevent a
// callback-only fixture from being confused with the admitted production image.
inline constexpr std::array<
    ActiveSchemePreconditionCommandBindersV1PrivateSignature, 4>
    kActiveSchemePreconditionCommandBindersV1PrivateSignatures{{
        {kActiveSchemePreconditionRefreshContextRva, 16,
         {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18,
          0x55, 0x57, 0x41, 0x54, 0x41, 0x56}},
        {kActiveSchemePreconditionFinalizeContextRva, 16,
         {0x40, 0x53, 0x57, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48,
          0x8B, 0x01, 0x48, 0x8B, 0xD9, 0x44}},
        {kActiveSchemePreconditionGetScriptIdentifierTableRva, 16,
         {0x48, 0x83, 0xEC, 0x28, 0x65, 0x48, 0x8B, 0x04, 0x25, 0x58,
          0x00, 0x00, 0x00, 0xBA, 0x10, 0x00}},
        {kActiveSchemePreconditionLookupScriptIdentifierRva, 16,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10,
          0x57, 0x48, 0x83, 0xEC, 0x20, 0x48}},
    }};

using ActiveSchemeBinderReadMemory = bool (*)(void *, const void *, void *,
                                               std::size_t) noexcept;
using ActiveSchemeBinderWriteMemory = bool (*)(void *, void *, const void *,
                                                std::size_t) noexcept;
using ActiveSchemeBinderInvokeGetter = bool (*)(void *, std::uintptr_t,
                                                 std::uintptr_t &) noexcept;
using ActiveSchemeBinderInvokeHash = bool (*)(void *, std::uintptr_t,
                                               std::uintptr_t,
                                               std::string_view,
                                               std::int32_t &) noexcept;
using ActiveSchemeBinderInvokeLookup = bool (*)(void *, std::uintptr_t,
                                                 std::uintptr_t, std::int32_t,
                                                 std::uintptr_t &) noexcept;
using ActiveSchemeBinderResolveIdentifier = bool (*)(
    void *, std::uintptr_t, std::uintptr_t, std::string_view,
    std::int32_t &) noexcept;
using ActiveSchemeBinderConstructContext = bool (*)(
    void *, std::uintptr_t, void *, std::uintptr_t, std::int32_t,
    std::int32_t) noexcept;
using ActiveSchemeBinderInvokeContext = bool (*)(void *, std::uintptr_t,
                                                  void *) noexcept;
using ActiveSchemeBinderValidateContext = bool (*)(
    void *, std::uintptr_t, void *, bool &) noexcept;
using ActiveSchemeBinderConstructCommand = bool (*)(
    void *, std::uintptr_t, void *, const void *) noexcept;
using ActiveSchemeBinderSubmit = bool (*)(void *, std::uintptr_t,
                                           std::uintptr_t, void *,
                                           std::uint32_t, bool &) noexcept;

struct ActiveSchemePreconditionCommandBindersV1PrivateOperations {
  ActiveSchemeBinderReadMemory read_memory = nullptr;
  ActiveSchemeBinderWriteMemory write_memory = nullptr;
  ActiveSchemeBinderInvokeGetter invoke_database_getter = nullptr;
  ActiveSchemeBinderInvokeHash invoke_stable_key_hash = nullptr;
  ActiveSchemeBinderInvokeLookup invoke_loaded_lookup = nullptr;
  ActiveSchemeBinderResolveIdentifier resolve_script_identifier = nullptr;
  ActiveSchemeBinderConstructContext construct_context = nullptr;
  ActiveSchemeBinderInvokeContext refresh_context = nullptr;
  ActiveSchemeBinderInvokeContext finalize_context = nullptr;
  ActiveSchemeBinderValidateContext validate_context = nullptr;
  ActiveSchemeBinderConstructCommand construct_command = nullptr;
  ActiveSchemeBinderSubmit submit = nullptr;
  ActiveSchemeBinderInvokeContext destroy_context = nullptr;
};

struct ActiveSchemePreconditionCommandBindersV1PrivateEnvironment {
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::string_view admitted_game_version{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  ActiveSchemeStateV1PrivateSourceAccess source_access{};
  void *operation_context = nullptr;
  ActiveSchemePreconditionCommandBindersV1PrivateOperations operations{};
};

enum class ActiveSchemePreconditionCommandBindersV1PrivateFailure :
    std::uint8_t {
  none,
  binding_contract,
  exact_build_mismatch,
  primitive_callbacks_unavailable,
  exact_image_mismatch,
  glue_binding_rejected,
  not_bound,
  reentrant_execution,
  not_application_main_thread,
  request_contract,
  native_precondition_red,
  glue_red,
};

struct ActiveSchemePreconditionCommandBindersV1PrivateReadiness {
  bool exact_build_bound = false;
  bool stable_identity_route_bound = false;
  bool native_context_validator_bound = false;
  bool native_single_submit_release_bound = false;
  bool native_precondition_bound = false;
  bool callback_core_ready = false;
  ActiveSchemePreconditionCommandBindersV1PrivateFailure failure =
      ActiveSchemePreconditionCommandBindersV1PrivateFailure::not_bound;
};

// Must remain at a stable address after binding: the nested SCHEME7/9 callback
// chains point back into this state. Native objects are transaction-local.
struct ActiveSchemePreconditionCommandBindersV1PrivateState {
  bool attached = false;
  bool operation_active = false;
  bool request_armed = false;
  bool native_context_active = false;
  bool native_command_active = false;
  bool submit_attempted = false;
  bool native_release_failed = false;
  bool offline_fixture = false;
  std::uint32_t active_current_thread_id = 0;
  std::uint32_t active_application_main_thread_id = 0;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  ActiveSchemePreconditionCommandBindersV1PrivateOperations operations{};
  ActiveSchemeStateV1PrivateSourceAccess source_access{};
  ActiveSchemeSemanticActionV1PrivateRequest armed_request{};
  alignas(8) std::array<std::byte, kActiveSchemeNativeContextSize>
      context_storage{};
  alignas(8) std::array<std::byte, kActiveSchemeNativeCommandSize>
      command_storage{};
  ActiveSchemePausedLiveNativeGlueV1PrivateState glue{};
  ActiveSchemePreconditionCommandBindersV1PrivateReadiness readiness{};
};

bool BindActiveSchemePreconditionCommandBindersV1Private(
    const ActiveSchemePreconditionCommandBindersV1PrivateEnvironment &,
    ActiveSchemePreconditionCommandBindersV1PrivateState &,
    ActiveSchemePreconditionCommandBindersV1PrivateReadiness &) noexcept;

bool CaptureActiveSchemePreconditionCommandSnapshotV1Private(
    ActiveSchemePreconditionCommandBindersV1PrivateState &,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &,
    ActiveSchemeStateV1PrivateObservation &,
    ActiveSchemePreconditionCommandBindersV1PrivateFailure &) noexcept;

bool ResolveActiveSchemePreconditionCommandDefinitionV1Private(
    ActiveSchemePreconditionCommandBindersV1PrivateState &,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &,
    std::string_view,
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease &,
    ActiveSchemePreconditionCommandBindersV1PrivateFailure &) noexcept;

bool CaptureActiveSchemePreconditionCommandPreconditionV1Private(
    ActiveSchemePreconditionCommandBindersV1PrivateState &,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &,
    const ActiveSchemeSemanticActionV1PrivateRequest &,
    ActiveSchemeSemanticActionV1PrivatePrecondition &,
    ActiveSchemePreconditionCommandBindersV1PrivateFailure &) noexcept;

ActiveSchemeSemanticActionV1PrivateAckStatus
ExecuteActiveSchemePreconditionCommandV1Private(
    ActiveSchemePreconditionCommandBindersV1PrivateState &,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &,
    const ActiveSchemeSemanticActionV1PrivateRequest &,
    ActiveSchemeSemanticActionV1PrivateAck &,
    ActiveSchemePreconditionCommandBindersV1PrivateFailure &) noexcept;

ActiveSchemeSemanticActionV1PrivateReceiptStatus
VerifyActiveSchemePreconditionCommandReceiptV1Private(
    ActiveSchemePreconditionCommandBindersV1PrivateState &,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &,
    const ActiveSchemeSemanticActionV1PrivateAck &,
    ActiveSchemeSemanticActionV1PrivateReceipt &,
    ActiveSchemePreconditionCommandBindersV1PrivateFailure &) noexcept;

std::string_view ActiveSchemePreconditionCommandBindersV1PrivateFailureName(
    ActiveSchemePreconditionCommandBindersV1PrivateFailure) noexcept;

} // namespace xar::bridge

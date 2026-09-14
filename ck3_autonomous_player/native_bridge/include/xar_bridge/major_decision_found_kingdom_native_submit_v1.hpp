#pragma once

#include "xar_bridge/major_decision_found_kingdom_action_core_v1.hpp"
#include "xar_bridge/major_decision_found_kingdom_native_binder_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kMajorDecisionFoundKingdomNativeSubmitKeyV1 =
        "major_decision_found_kingdom_native_submit_v1";
inline constexpr std::string_view
    kMajorDecisionFoundKingdomNativeSubmitGameVersionV1 = "1.19.0.6";

inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandPrimaryVtableRvaV1 = 0x43237F8;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandSecondaryVtableRvaV1 = 0x43237C8;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandTypeDescriptorRvaV1 = 0x54C1968;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandDestructorRvaV1 = 0x25E1FE0;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandConstructorRvaV1 = 0x25E2040;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandValidatorRvaV1 = 0x25E2350;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandPrevalidatorRvaV1 = 0x25E24E0;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandExecutorRvaV1 = 0x25E25A0;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomExecuteCommandCloneRvaV1 = 0x25EC440;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomDecisionContextCloneRvaV1 = 0x1356BF0;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomContextOwnerDestructorRvaV1 = 0x0BFEAB0;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomCommandQueueReceiverRvaV1 = 0x341D990;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomCommandQueueContextRvaV1 = 0x57621F0;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomStockSubmitCallsiteRvaV1 = 0x188264E;
inline constexpr std::uintptr_t
    kMajorDecisionFoundKingdomControllerFactoryRvaV1 = 0x13560A0;

inline constexpr std::size_t
    kMajorDecisionFoundKingdomExecuteCommandSizeV1 = 0x38;
inline constexpr std::size_t
    kMajorDecisionFoundKingdomExecuteCommandSecondaryOffsetV1 = 0x18;
inline constexpr std::size_t
    kMajorDecisionFoundKingdomExecuteCommandCharacterIdOffsetV1 = 0x20;
inline constexpr std::size_t
    kMajorDecisionFoundKingdomExecuteCommandDefinitionOffsetV1 = 0x28;
inline constexpr std::size_t
    kMajorDecisionFoundKingdomExecuteCommandContextOffsetV1 = 0x30;
inline constexpr std::uint32_t
    kMajorDecisionFoundKingdomCommandQueueFlagsV1 = 7;

struct MajorDecisionFoundKingdomNativeSubmitSignatureV1 {
  std::uintptr_t rva = 0;
  std::array<std::uint8_t, 16> bytes{};
  std::size_t size = 0;
};

struct MajorDecisionFoundKingdomNativeSubmitSlotV1 {
  std::uintptr_t slot_rva = 0;
  std::uintptr_t function_rva = 0;
};

// The complete instruction spans and their SHA-256 values live in the
// adjacent research JSON. Runtime admission also checks these exact prefixes
// and the command virtual slots before installing the submit callback.
inline constexpr std::array<MajorDecisionFoundKingdomNativeSubmitSignatureV1,
                            11>
    kMajorDecisionFoundKingdomNativeSubmitSignaturesV1{{
        {kMajorDecisionFoundKingdomExecuteCommandDestructorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83,
          0xEC, 0x20, 0x48, 0x8D, 0x05, 0x07, 0x18, 0xD4},
         16},
        {kMajorDecisionFoundKingdomExecuteCommandConstructorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
          0x24, 0x10, 0x57, 0x48, 0x83, 0xEC, 0x20, 0xC6},
         16},
        {kMajorDecisionFoundKingdomExecuteCommandValidatorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
          0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57},
         16},
        {kMajorDecisionFoundKingdomExecuteCommandPrevalidatorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
          0x24, 0x10, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48},
         16},
        {kMajorDecisionFoundKingdomExecuteCommandExecutorRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83,
          0xEC, 0x40, 0x48, 0x8B, 0x79, 0x10, 0x48, 0x8D},
         16},
        {kMajorDecisionFoundKingdomExecuteCommandCloneRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
          0x24, 0x20, 0x48, 0x89, 0x54, 0x24, 0x10, 0x56},
         16},
        {kMajorDecisionFoundKingdomDecisionContextCloneRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
          0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57},
         16},
        {kMajorDecisionFoundKingdomContextOwnerDestructorRvaV1,
         {0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B,
          0x19, 0x48, 0x85, 0xDB, 0x74, 0x49, 0x48, 0x8B},
         16},
        {kMajorDecisionFoundKingdomCommandQueueReceiverRvaV1,
         {0x4C, 0x89, 0x4C, 0x24, 0x20, 0x48, 0x89, 0x54,
          0x24, 0x10, 0x53, 0x56, 0x57, 0x48, 0x83, 0xEC},
         16},
        {kMajorDecisionFoundKingdomStockSubmitCallsiteRvaV1,
         {0x48, 0x8B, 0x85, 0xD8, 0x01, 0x00, 0x00, 0x48,
          0x89, 0x9D, 0xD8, 0x01, 0x00, 0x00, 0x48, 0x89},
         16},
        {kMajorDecisionFoundKingdomControllerFactoryRvaV1,
         {0x48, 0x89, 0x5C, 0x24, 0x20, 0x48, 0x89, 0x54,
          0x24, 0x10, 0x55, 0x56, 0x57, 0x41, 0x56, 0x41},
         16},
    }};

inline constexpr std::array<MajorDecisionFoundKingdomNativeSubmitSlotV1, 4>
    kMajorDecisionFoundKingdomNativeSubmitSlotsV1{{
        {kMajorDecisionFoundKingdomExecuteCommandPrimaryVtableRvaV1 + 0x00,
         kMajorDecisionFoundKingdomExecuteCommandDestructorRvaV1},
        {kMajorDecisionFoundKingdomExecuteCommandPrimaryVtableRvaV1 + 0x30,
         kMajorDecisionFoundKingdomExecuteCommandValidatorRvaV1},
        {kMajorDecisionFoundKingdomExecuteCommandPrimaryVtableRvaV1 + 0x40,
         kMajorDecisionFoundKingdomExecuteCommandCloneRvaV1},
        {kMajorDecisionFoundKingdomExecuteCommandSecondaryVtableRvaV1 + 0x08,
         kMajorDecisionFoundKingdomExecuteCommandExecutorRvaV1},
    }};

using MajorDecisionFoundKingdomNativeSubmitReadMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using MajorDecisionFoundKingdomNativeSubmitResolvePlayerV1 =
    std::uintptr_t (*)(void *context, std::uintptr_t module_base,
                       std::int32_t character_id) noexcept;
using MajorDecisionFoundKingdomNativeSubmitHashNameV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::string_view name,
    std::uint32_t &output) noexcept;
using MajorDecisionFoundKingdomNativeSubmitLookupDefinitionV1 =
    std::uintptr_t (*)(void *context, std::uintptr_t module_base,
                       std::uintptr_t database,
                       std::uint32_t name_hash) noexcept;
using MajorDecisionFoundKingdomNativeSubmitConstructV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *command,
    std::int32_t character_id, std::uintptr_t definition,
    void **owned_decision_context) noexcept;
using MajorDecisionFoundKingdomNativeSubmitValidateV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *command) noexcept;
using MajorDecisionFoundKingdomNativeSubmitCloneV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *command,
    void **owned_clone) noexcept;
using MajorDecisionFoundKingdomNativeSubmitDestroyV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *command,
    std::uint32_t flags) noexcept;
using MajorDecisionFoundKingdomNativeSubmitQueueV1 = bool (*)(
    void *context, std::uintptr_t module_base, void **owned_command,
    std::uint32_t flags) noexcept;

struct MajorDecisionFoundKingdomNativeSubmitOperationsV1 {
  MajorDecisionFoundKingdomNativeSubmitReadMemoryV1 read_memory = nullptr;
  MajorDecisionFoundKingdomNativeSubmitResolvePlayerV1 resolve_player =
      nullptr;
  MajorDecisionFoundKingdomNativeSubmitHashNameV1 hash_name = nullptr;
  MajorDecisionFoundKingdomNativeSubmitLookupDefinitionV1 lookup_definition =
      nullptr;
  MajorDecisionFoundKingdomNativeSubmitConstructV1 construct = nullptr;
  MajorDecisionFoundKingdomNativeSubmitValidateV1 validate = nullptr;
  MajorDecisionFoundKingdomNativeSubmitCloneV1 clone = nullptr;
  MajorDecisionFoundKingdomNativeSubmitDestroyV1 destroy = nullptr;
  MajorDecisionFoundKingdomNativeSubmitQueueV1 queue = nullptr;
};

struct MajorDecisionFoundKingdomNativeSubmitEnvironmentV1 {
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_game_version{};
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  MajorDecisionFoundKingdomNativeSubmitOperationsV1 operations{};
};

struct MajorDecisionFoundKingdomNativeSubmitStateV1 {
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  MajorDecisionFoundKingdomNativeSubmitOperationsV1 operations{};
  void *upstream_context = nullptr;
  CaptureMajorDecisionFoundKingdomActionPreconditionV1
      upstream_capture_precondition = nullptr;
  bool offline_fixture = false;
  bool attached = false;
};

// Installs the exact-build native submit callback while forwarding the
// caller-owned paused precondition observer unchanged. Production binding
// rejects every operation override; operations exist solely for an explicit
// zero-module standalone fixture.
bool BindMajorDecisionFoundKingdomNativeSubmitV1(
    const MajorDecisionFoundKingdomNativeSubmitEnvironmentV1 &environment,
    MajorDecisionFoundKingdomNativeSubmitStateV1 &state,
    MajorDecisionFoundKingdomActionEnvironmentV1 &action_environment,
    MajorDecisionFoundKingdomActionAccessV1 &action_access) noexcept;

} // namespace xar::bridge

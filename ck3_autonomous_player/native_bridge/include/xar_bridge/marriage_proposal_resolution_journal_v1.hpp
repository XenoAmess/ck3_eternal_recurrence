#pragma once

#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::string_view
    kMarriageProposalResolutionJournalExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

inline constexpr std::uintptr_t kMarriageResolutionDispatchRvaV1 = 0x2752620;
inline constexpr std::uintptr_t kMarriageResolutionImmediateRvaV1 = 0x2752900;
inline constexpr std::uintptr_t kMarriageResolutionResponseRvaV1 = 0x2751410;
inline constexpr std::uintptr_t kMarriageResolutionConstructRvaV1 = 0x27541F0;
inline constexpr std::uintptr_t kMarriageResolutionDeleteRvaV1 = 0x2751310;
inline constexpr std::uintptr_t kMarriagePendingStorageSlotRvaV1 = 0x57BF1C8;
inline constexpr std::uintptr_t kMarriagePendingSpecialVtableRvaV1 = 0x40B0F20;
inline constexpr std::uintptr_t kMarriageDeleteInvalidatedCallerRvaV1 =
    0x27518BD;
inline constexpr std::uintptr_t kMarriageDeleteExpiredCallerRvaV1 = 0x2751A1C;
inline constexpr std::uintptr_t kMarriageDeleteResponseCallerRvaV1 = 0x27514B9;

inline constexpr std::size_t kMarriageResolutionHookCountV1 = 5;
inline constexpr std::size_t kMarriageResolutionAbsoluteJumpBytesV1 = 14;
inline constexpr std::array<std::size_t, kMarriageResolutionHookCountV1>
    kMarriageResolutionPatchSizesV1{15, 15, 15, 15, 14};
inline constexpr std::array<std::array<std::uint8_t, 15>,
                           kMarriageResolutionHookCountV1>
    kMarriageResolutionExpectedPrefixesV1{{
        {0x48, 0x89, 0x5C, 0x24, 0x08, 0x44, 0x88, 0x4C,
         0x24, 0x20, 0x44, 0x88, 0x44, 0x24, 0x18},
        {0x40, 0x53, 0x56, 0x57, 0x41, 0x56, 0x41, 0x57,
         0x48, 0x83, 0xEC, 0x60, 0x4D, 0x8B, 0xF9},
        {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
         0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18},
        {0x48, 0x89, 0x5C, 0x24, 0x10, 0x4C, 0x89, 0x44,
         0x24, 0x18, 0x55, 0x56, 0x57, 0x41, 0x54},
        {0x40, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B,
         0x79, 0x50, 0x80, 0x7F, 0x48, 0x00, 0x00},
    }};

enum class MarriageResolutionHookIndexV1 : std::size_t {
  dispatch = 0,
  immediate = 1,
  response = 2,
  construct = 3,
  remove = 4,
};

enum MarriageProposalResolutionJournalInstallFailureV1 : std::uint32_t {
  marriage_resolution_install_failure_none = 0,
  marriage_resolution_install_failure_exact_build = 1U << 0,
  marriage_resolution_install_failure_quiescence = 1U << 1,
  marriage_resolution_install_failure_already_installed = 1U << 2,
  marriage_resolution_install_failure_anchor = 1U << 3,
  marriage_resolution_install_failure_allocation = 1U << 4,
  marriage_resolution_install_failure_protection = 1U << 5,
  marriage_resolution_install_failure_flush = 1U << 6,
  marriage_resolution_install_failure_rollback = 1U << 7,
  marriage_resolution_install_failure_active_calls = 1U << 8,
  marriage_resolution_install_failure_identity = 1U << 9,
};

using MarriageResolutionVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using MarriageResolutionVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size,
    DWORD free_type) noexcept;
using MarriageResolutionVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD protection,
    DWORD &old_protection) noexcept;
using MarriageResolutionFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct MarriageProposalResolutionJournalInstallEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  std::array<std::uintptr_t, kMarriageResolutionHookCountV1> target_overrides{};
  void *memory_context = nullptr;
  MarriageResolutionVirtualAllocV1 virtual_alloc_override = nullptr;
  MarriageResolutionVirtualFreeV1 virtual_free_override = nullptr;
  MarriageResolutionVirtualProtectV1 virtual_protect_override = nullptr;
  MarriageResolutionFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

struct MarriageProposalResolutionIdentityV1 {
  std::uintptr_t interaction_definition = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t candidate_character_id = -1;
  std::int32_t intermediary_character_id = -1;

  friend bool operator==(const MarriageProposalResolutionIdentityV1 &,
                         const MarriageProposalResolutionIdentityV1 &) =
      default;
};

struct MarriageProposalResolutionJournalDetourStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      marriage_resolution_install_failure_none};
  std::atomic<std::uint32_t> active_calls{0};
  std::array<std::uintptr_t, kMarriageResolutionHookCountV1> targets{};
  std::array<void *, kMarriageResolutionHookCountV1> trampolines{};
  std::array<std::array<std::uint8_t, 15>, kMarriageResolutionHookCountV1>
      originals{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  void *memory_context = nullptr;
  MarriageResolutionVirtualFreeV1 virtual_free = nullptr;
  MarriageResolutionVirtualProtectV1 virtual_protect = nullptr;
  MarriageResolutionFlushInstructionCacheV1 flush_instruction_cache = nullptr;

  std::atomic_flag journal_lock = ATOMIC_FLAG_INIT;
  MarriageProposalResolutionIdentityV1 armed_identity{};
  std::int32_t pending_id = -1;
  MarriageProposalNativeResolutionV1 resolution =
      MarriageProposalNativeResolutionV1::pending;
  bool identity_armed = false;
  bool resolution_ready = false;
};

bool InstallMarriageProposalResolutionJournalV1(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    const MarriageProposalResolutionJournalInstallEnvironmentV1 &environment)
    noexcept;

bool RemoveMarriageProposalResolutionJournalV1(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    bool primary_thread_suspended_proven) noexcept;

bool ArmMarriageProposalResolutionJournalV1(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    const MarriageProposalSubmissionV1 &submission,
    std::uintptr_t interaction_definition) noexcept;

bool ConfigureMarriageProposalResolutionJournalV1(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    MarriageProposalNativeBinderStateV1 &binder) noexcept;

bool ReadMarriageProposalResolutionJournalV1(
    void *context, std::uint32_t subject_character_id,
    std::uint32_t candidate_character_id,
    MarriageProposalNativeResolutionV1 &output) noexcept;

// These fixture entries exercise the same identity and status transitions as
// the native hook bodies without executing generated x64 trampolines.
bool CaptureMarriageResolutionDispatchReturnFixtureV1(
    const MarriageProposalResolutionIdentityV1 &identity,
    bool nested_terminal_or_pending_observed) noexcept;
bool CaptureMarriageResolutionImmediateFixtureV1(
    const MarriageProposalResolutionIdentityV1 &identity,
    std::uint8_t recipient_reply) noexcept;
bool CaptureMarriageResolutionConstructFixtureV1(
    const MarriageProposalResolutionIdentityV1 &identity,
    std::int32_t pending_id) noexcept;
bool CaptureMarriageResolutionResponseFixtureV1(
    const MarriageProposalResolutionIdentityV1 &identity,
    std::int32_t pending_id, std::uint8_t route,
    std::int32_t recipient_reply) noexcept;
bool CaptureMarriageResolutionDeleteFixtureV1(
    std::int32_t pending_id, std::uintptr_t caller_rva) noexcept;

using MarriageResolutionDispatchOriginalV1 = void(__fastcall *)(
    void *, void *, std::uint8_t, std::uint8_t);
using MarriageResolutionImmediateOriginalV1 = void(__fastcall *)(
    void *, void *, const std::uint8_t *, const std::uint8_t *);
using MarriageResolutionResponseOriginalV1 = void(__fastcall *)(
    void *, void *, std::int32_t, std::int32_t);
using MarriageResolutionConstructOriginalV1 = void *(__fastcall *)(
    void *, void *, const std::int32_t *, const std::uint8_t *,
    const std::uint8_t *, const std::int32_t *);
using MarriageResolutionDeleteOriginalV1 = void(__fastcall *)(void *,
                                                               std::int32_t);

extern "C" void __fastcall XarMarriageResolutionDispatchHookV1(
    void *manager, void *context, std::uint8_t intermediary_reply,
    std::uint8_t recipient_reply) noexcept;
extern "C" void __fastcall XarMarriageResolutionImmediateHookV1(
    void *manager, void *context, const std::uint8_t *intermediary_reply,
    const std::uint8_t *recipient_reply) noexcept;
extern "C" void __fastcall XarMarriageResolutionResponseHookV1(
    void *manager, void *pending, std::int32_t intermediary_reply,
    std::int32_t recipient_reply) noexcept;
extern "C" void *__fastcall XarMarriageResolutionConstructHookV1(
    void *storage, void *context, const std::int32_t *cutoff,
    const std::uint8_t *intermediary_reply,
    const std::uint8_t *recipient_reply,
    const std::int32_t *notification) noexcept;
extern "C" void __fastcall XarMarriageResolutionDeleteHookV1(
    void *manager, std::int32_t pending_id) noexcept;

} // namespace xar::bridge

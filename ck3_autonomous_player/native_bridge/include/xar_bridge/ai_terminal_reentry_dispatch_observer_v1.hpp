#pragma once

#include "xar_bridge/battle_terminal_journal_v1.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <windows.h>

namespace xar::ck3_11906 {

inline constexpr std::uintptr_t kAiReentryBuilderRvaV1 = 0x186B190;
inline constexpr std::uintptr_t kAiReentryBuilderCallerRvaV1 = 0x187235D;
inline constexpr std::uintptr_t kAiReentryBuilderReturnRvaV1 = 0x1872362;
inline constexpr std::uintptr_t kAiReentrySubmitRvaV1 = 0x973E00;
inline constexpr std::uintptr_t kAiReentrySubmitCallerRvaV1 = 0x186B2C5;
inline constexpr std::uintptr_t kAiReentrySubmitReturnRvaV1 = 0x186B2CA;
inline constexpr std::size_t kAiReentryPatchBytesV1 = 15;
inline constexpr std::size_t kAiReentryJumpBytesV1 = 14;
inline constexpr std::size_t kAiReentryCapacityV1 = 64;
inline constexpr std::int32_t kAiReentryCunitIdV1 = 16777231;
inline constexpr std::int32_t kAiReentryCombatIdV1 = 16777218;
inline constexpr std::string_view kAiReentryStepV1 =
    "query-ai-terminal-reentry-dispatch-v1-16777231-16777218";
inline constexpr std::string_view kAiReentryCapabilityV1 =
    "game.command.query-ai-terminal-reentry-dispatch-v1-private";

enum AiReentryFailureV1 : std::uint32_t {
  ai_reentry_failure_none = 0,
  ai_reentry_failure_admission = 1U << 0,
  ai_reentry_failure_quiescence = 1U << 1,
  ai_reentry_failure_anchor = 1U << 2,
  ai_reentry_failure_allocation = 1U << 3,
  ai_reentry_failure_protection = 1U << 4,
  ai_reentry_failure_flush = 1U << 5,
  ai_reentry_failure_rollback = 1U << 6,
  ai_reentry_failure_reentry = 1U << 7,
  ai_reentry_failure_capture = 1U << 8,
  ai_reentry_failure_capacity = 1U << 9,
  ai_reentry_failure_identity = 1U << 10,
};

struct AiReentryDispatchRecordV1 {
  std::uint64_t sequence = 0;
  std::uint32_t thread_id = 0;
  std::int32_t cunit_id = -1;
  std::int32_t builder_target_province_id = -1;
  std::int32_t command_target_province_id = -1;
  std::uint32_t channel_flags = 0;
  std::uint32_t command_kind = 0;
  std::uint32_t move_mode_raw = 0;
  std::uint32_t route_kind = 0;
  std::uint32_t direct_target = 0;
  std::int32_t observed_date_raw = 0;
  std::uint64_t terminal_sequence_cutoff = 0;
  std::uintptr_t builder_return = 0;
  std::uintptr_t submit_return = 0;
  bool command_header_valid = false;
  bool queue_accepted = false;
  BattleTerminalJournalLookupStatusV1 terminal_status =
      BattleTerminalJournalLookupStatusV1::unavailable;
  std::uint64_t terminal_sequence = 0;
  std::int32_t terminal_date_raw = 0;
  std::uint32_t terminal_capture_failure_flags = 0;
  bool terminal_normal_result = false;
  bool terminal_before_submit = false;
  bool cunit_was_terminal_winner = false;
};

struct AiReentryDispatchSnapshotV1 {
  bool installed = false;
  std::uint32_t failure_flags = 0;
  std::uint64_t builder_matching_calls = 0;
  std::uint64_t submit_matching_calls = 0;
  std::uint64_t overflow_count = 0;
  std::uint32_t count = 0;
  std::array<AiReentryDispatchRecordV1, kAiReentryCapacityV1> records{};
};

using AiReentryAllocV1 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using AiReentryFreeV1 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using AiReentryProtectV1 = bool (*)(void *, void *, std::size_t, DWORD,
                                  DWORD &) noexcept;
using AiReentryFlushV1 = bool (*)(void *, const void *, std::size_t) noexcept;

struct AiReentryDispatchEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t builder_target_override = 0;
  std::uintptr_t submit_target_override = 0;
  std::uintptr_t builder_caller_override = 0;
  std::uintptr_t submit_caller_override = 0;
  void **game_state_slot = nullptr;
  void *memory_context = nullptr;
  AiReentryAllocV1 alloc_override = nullptr;
  AiReentryFreeV1 free_override = nullptr;
  AiReentryProtectV1 protect_override = nullptr;
  AiReentryFlushV1 flush_override = nullptr;
};

struct AiReentryDispatchStateV1 {
  std::atomic<bool> installed{false};
  std::atomic<std::uint32_t> failure_flags{0};
  std::atomic<std::uint64_t> builder_matching_calls{0};
  std::atomic<std::uint64_t> submit_matching_calls{0};
  std::atomic<std::uint64_t> overflow_count{0};
  std::atomic<std::uint32_t> count{0};
  std::atomic<bool> recording{false};
  std::array<AiReentryDispatchRecordV1, kAiReentryCapacityV1> records{};
  std::uintptr_t module_base = 0;
  std::uintptr_t builder_target = 0;
  std::uintptr_t submit_target = 0;
  void **game_state_slot = nullptr;
  void *builder_trampoline = nullptr;
  void *submit_trampoline = nullptr;
  std::array<std::uint8_t, kAiReentryPatchBytesV1> builder_patch{};
  std::array<std::uint8_t, kAiReentryPatchBytesV1> submit_patch{};
  void *memory_context = nullptr;
  AiReentryFreeV1 free_memory = nullptr;
  AiReentryProtectV1 protect = nullptr;
  AiReentryFlushV1 flush = nullptr;
};

bool InstallAiReentryDispatchObserverV1(
    AiReentryDispatchStateV1 &state,
    const AiReentryDispatchEnvironmentV1 &environment) noexcept;
AiReentryDispatchSnapshotV1 ReadAiReentryDispatchObserverV1(
    const AiReentryDispatchStateV1 &state) noexcept;

// Offline fixture surface; never calls game code or a native mutator.
bool RecordAiReentryDispatchFixtureV1(
    AiReentryDispatchStateV1 &state,
    const AiReentryDispatchRecordV1 &record) noexcept;
bool DecodeAiReentryCommandHeaderFixtureV1(
    const void *command, std::uintptr_t module_base,
    AiReentryDispatchRecordV1 &record) noexcept;
void CorrelateAiReentryTerminalAfterPauseV1(
    AiReentryDispatchRecordV1 &record,
    const BattleTerminalJournalLookupV1 &terminal) noexcept;

} // namespace xar::ck3_11906

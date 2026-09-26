#include "xar_bridge/ai_terminal_reentry_dispatch_observer_v1.hpp"

#include <intrin.h>

#include <array>
#include <cstring>

namespace xar::ck3_11906 {
namespace {

static_assert(sizeof(void *) == 8);
constexpr std::array<std::uint8_t, kAiReentryPatchBytesV1> kBuilderAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10,
    0x48, 0x89, 0x7C, 0x24, 0x18};
constexpr std::array<std::uint8_t, kAiReentryPatchBytesV1> kSubmitAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x4C, 0x89, 0x4C, 0x24, 0x20,
    0x57, 0x48, 0x83, 0xEC, 0x20};
constexpr std::array<std::uint8_t, 5> kBuilderCallerAnchor{
    0xE8, 0x2E, 0x8E, 0xFF, 0xFF};
constexpr std::array<std::uint8_t, 5> kSubmitCallerAnchor{
    0xE8, 0x36, 0x8B, 0x10, 0xFF};
constexpr std::array<std::uint8_t, 5> kFallbackSubmitCallerAnchor{
    0xE8, 0xEA, 0x17, 0x10, 0xFF};
constexpr std::array<std::uint8_t, 7> kSubmitGateTestAnchor{
    0xF6, 0x05, 0x01, 0x72, 0xEF, 0x03, 0xFD};
constexpr std::array<std::uint8_t, 4> kBuilderHandledAnchor{
    0xC6, 0x43, 0x08, 0x01};
constexpr std::array<std::uint8_t, 4> kBuilderSecondAnchor{
    0xC6, 0x43, 0x09, 0x01};

std::atomic<AiReentryDispatchStateV1 *> g_active{nullptr};
// Pass R9 through unchanged even though this exact callsite has only three
// proven business arguments. The observed prologues save volatile registers.
using BuilderOriginal = void *(__fastcall *)(void *, void *, void *,
                                              std::uintptr_t);
using SubmitOriginal = bool(__fastcall *)(void *, void *, std::uint32_t,
                                           std::uintptr_t);
std::atomic<BuilderOriginal> g_builder_original{nullptr};
std::atomic<SubmitOriginal> g_submit_original{nullptr};
struct BuilderContext {
  bool active = false;
  std::int32_t cunit_id = -1;
  std::int32_t target_id = -1;
  std::uintptr_t return_address = 0;
  std::uint32_t thread_id = 0;
  std::uint32_t main_submit_calls = 0;
};
thread_local BuilderContext g_builder_context{};

void Fail(AiReentryDispatchStateV1 &state, AiReentryFailureV1 bit) noexcept {
  state.failure_flags.fetch_or(bit, std::memory_order_acq_rel);
}

void *DefaultAlloc(void *, std::size_t size, DWORD type,
                   DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool DefaultFree(void *, void *address, std::size_t size, DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
bool DefaultProtect(void *, void *address, std::size_t size, DWORD protection,
                    DWORD &old) noexcept {
  return VirtualProtect(address, size, protection, &old) != FALSE;
}
bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool IsExecutable(DWORD protection) noexcept {
  return protection == PAGE_EXECUTE_READ ||
         protection == PAGE_EXECUTE_READWRITE ||
         protection == PAGE_EXECUTE_WRITECOPY;
}

bool SafeEqual(std::uintptr_t address, const void *expected,
               std::size_t size) noexcept {
  if (address == 0 || expected == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(address), expected,
                       size) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool SafeCopy(void *destination, const void *source,
              std::size_t size) noexcept {
  if (destination == nullptr || source == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(destination, source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

template <typename Value>
bool ReadAt(const void *base, std::size_t offset, Value &output) noexcept {
  if (base == nullptr) return false;
  return SafeCopy(&output, static_cast<const std::byte *>(base) + offset,
                  sizeof(output));
}

void WriteJump(std::uint8_t *bytes, std::uintptr_t destination) noexcept {
  bytes[0] = 0xFF;
  bytes[1] = 0x25;
  bytes[2] = bytes[3] = bytes[4] = bytes[5] = 0;
  std::memcpy(bytes + 6, &destination, sizeof(destination));
}

bool BuildTrampoline(AiReentryDispatchStateV1 &state, void *trampoline,
                     const std::array<std::uint8_t, 15> &anchor,
                     std::uintptr_t resume) noexcept {
  std::array<std::uint8_t, kAiReentryPatchBytesV1 + kAiReentryJumpBytesV1>
      image{};
  std::memcpy(image.data(), anchor.data(), anchor.size());
  WriteJump(image.data() + anchor.size(), resume);
  if (!SafeCopy(trampoline, image.data(), image.size())) return false;
  DWORD previous = 0;
  if (!state.protect(state.memory_context, trampoline, image.size(),
                     PAGE_EXECUTE_READ, previous) ||
      previous != PAGE_READWRITE) {
    Fail(state, ai_reentry_failure_protection);
    return false;
  }
  if (!state.flush(state.memory_context, trampoline, image.size())) {
    Fail(state, ai_reentry_failure_flush);
    return false;
  }
  return true;
}

// A failed write attempts to restore the expected bytes before returning.
// A rollback failure is fatal to the suspended launch and retains trampolines.
bool WriteTarget(AiReentryDispatchStateV1 &state, std::uintptr_t address,
                 const std::uint8_t *expected,
                 const std::uint8_t *desired) noexcept {
  if (!SafeEqual(address, expected, kAiReentryPatchBytesV1)) {
    Fail(state, ai_reentry_failure_anchor);
    return false;
  }
  DWORD previous = 0;
  if (!state.protect(state.memory_context, reinterpret_cast<void *>(address),
                     kAiReentryPatchBytesV1, PAGE_EXECUTE_READWRITE,
                     previous)) {
    Fail(state, ai_reentry_failure_protection);
    return false;
  }
  if (!IsExecutable(previous)) {
    DWORD ignored = 0;
    (void)state.protect(state.memory_context,
                        reinterpret_cast<void *>(address),
                        kAiReentryPatchBytesV1, previous, ignored);
    Fail(state, ai_reentry_failure_protection);
    return false;
  }
  const bool written = SafeCopy(reinterpret_cast<void *>(address), desired,
                                kAiReentryPatchBytesV1);
  const bool verified = written && SafeEqual(address, desired,
                                             kAiReentryPatchBytesV1);
  const bool flushed = verified && state.flush(
      state.memory_context, reinterpret_cast<const void *>(address),
      kAiReentryPatchBytesV1);
  DWORD ignored = 0;
  const bool protected_again = state.protect(
      state.memory_context, reinterpret_cast<void *>(address),
      kAiReentryPatchBytesV1, previous, ignored);
  if (verified && flushed && protected_again) return true;
  Fail(state, !flushed ? ai_reentry_failure_flush
                       : ai_reentry_failure_protection);
  DWORD rollback_previous = 0;
  const bool rollback_writable = state.protect(
      state.memory_context, reinterpret_cast<void *>(address),
      kAiReentryPatchBytesV1, PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable && SafeCopy(
      reinterpret_cast<void *>(address), expected, kAiReentryPatchBytesV1);
  const bool rollback_verified = rollback_written && SafeEqual(
      address, expected, kAiReentryPatchBytesV1);
  const bool rollback_flushed = rollback_verified && state.flush(
      state.memory_context, reinterpret_cast<const void *>(address),
      kAiReentryPatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable && state.protect(
      state.memory_context, reinterpret_cast<void *>(address),
      kAiReentryPatchBytesV1, previous, rollback_ignored);
  if (!rollback_verified || !rollback_flushed || !rollback_protected)
    Fail(state, ai_reentry_failure_rollback);
  return false;
}

void Release(AiReentryDispatchStateV1 &state) noexcept {
  if (state.failure_flags.load(std::memory_order_acquire) &
      ai_reentry_failure_rollback) return;
  if (state.builder_trampoline != nullptr) {
    if (!state.free_memory(state.memory_context, state.builder_trampoline,
                           0, MEM_RELEASE)) {
      Fail(state, ai_reentry_failure_rollback);
      return;
    }
    state.builder_trampoline = nullptr;
  }
  if (state.submit_trampoline != nullptr) {
    if (!state.free_memory(state.memory_context, state.submit_trampoline,
                           0, MEM_RELEASE)) {
      Fail(state, ai_reentry_failure_rollback);
      return;
    }
    state.submit_trampoline = nullptr;
  }
}

bool ReadCommandHeader(const void *command, std::uintptr_t module_base,
                       AiReentryDispatchRecordV1 &record) noexcept {
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::uint32_t cunit = 0;
  if (!ReadAt(command, 0x00, primary) ||
      !ReadAt(command, 0x18, secondary) ||
      !ReadAt(command, 0x20, record.command_kind) ||
      !ReadAt(command, 0x24, cunit) ||
      !ReadAt(command, 0x28, record.command_target_province_id) ||
      !ReadAt(command, 0x2C, record.move_mode_raw) ||
      !ReadAt(command, 0x30, record.route_kind) ||
      !ReadAt(command, 0x34, record.direct_target)) return false;
  record.command_header_valid =
      primary == module_base + 0x432BF18 &&
      secondary == module_base + 0x432BFB0 &&
      record.command_kind == 2 &&
      cunit == static_cast<std::uint32_t>(record.cunit_id) &&
      (record.submit_site == AiReentrySubmitSiteV1::outer_fallback ||
       record.command_target_province_id ==
           record.builder_target_province_id) &&
      record.route_kind == 2 && record.direct_target == 1 &&
      record.channel_flags == 7;
  return true;
}

extern "C" void *__fastcall XarAiReentryBuilderHookV1(
    void *result, void *cunit, void *province,
    std::uintptr_t opaque_r9) noexcept {
  const auto original = g_builder_original.load(std::memory_order_acquire);
  if (original == nullptr) return result;
  auto *state = g_active.load(std::memory_order_acquire);
  if (state == nullptr) return original(result, cunit, province, opaque_r9);
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  if (caller != state->module_base + kAiReentryBuilderReturnRvaV1)
    return original(result, cunit, province, opaque_r9);
  std::int32_t cunit_id = -1;
  std::int32_t target_id = -1;
  if (!ReadAt(cunit, 0x10, cunit_id) ||
      !ReadAt(province, 0x10, target_id)) {
    Fail(*state, ai_reentry_failure_capture);
    return original(result, cunit, province, opaque_r9);
  }
  if (cunit_id != kAiReentryCunitIdV1)
    return original(result, cunit, province, opaque_r9);
  state->builder_matching_calls.fetch_add(1, std::memory_order_relaxed);
  if (target_id <= 0 || g_builder_context.active) {
    Fail(*state, g_builder_context.active ? ai_reentry_failure_reentry
                                         : ai_reentry_failure_identity);
    return original(result, cunit, province, opaque_r9);
  }
  AiReentryBuilderOutcomeV1 outcome{};
  outcome.thread_id = GetCurrentThreadId();
  outcome.cunit_id = cunit_id;
  outcome.target_province_id = target_id;
  outcome.builder_return = caller;
  outcome.gate_before_valid = ReadAt(
      reinterpret_cast<const void *>(state->module_base +
                                     kAiReentrySubmitGateRvaV1),
      0, outcome.gate_before_raw);
  if (!outcome.gate_before_valid)
    Fail(*state, ai_reentry_failure_capture);
  g_builder_context = {true, cunit_id, target_id, caller,
                       outcome.thread_id, 0};
  void *const returned = original(result, cunit, province, opaque_r9);
  outcome.main_submit_calls = g_builder_context.main_submit_calls;
  outcome.gate_after_valid = ReadAt(
      reinterpret_cast<const void *>(state->module_base +
                                     kAiReentrySubmitGateRvaV1),
      0, outcome.gate_after_raw);
  outcome.result_valid = returned == result &&
      ReadAt(result, 8, outcome.result_handled_raw) &&
      ReadAt(result, 9, outcome.result_second_raw);
  if (!outcome.gate_after_valid || !outcome.result_valid)
    Fail(*state, ai_reentry_failure_capture);
  if (outcome.result_valid) {
    outcome.outcome = ClassifyAiReentryBuilderOutcomeFixtureV1(
        outcome.result_handled_raw, outcome.result_second_raw,
        outcome.main_submit_calls);
    if (outcome.outcome == AiReentryBuilderOutcomeKindV1::unclassified)
      Fail(*state, ai_reentry_failure_identity);
  }
  outcome.terminal_sequence_cutoff = BattleTerminalJournalLatestSequenceV1();
  void *game_state = nullptr;
  if (state->game_state_slot != nullptr &&
      SafeCopy(&game_state, state->game_state_slot, sizeof(game_state)) &&
      game_state != nullptr) {
    if (!ReadAt(game_state, 0x08, outcome.observed_date_raw))
      Fail(*state, ai_reentry_failure_capture);
  } else {
    Fail(*state, ai_reentry_failure_capture);
  }
  (void)RecordAiReentryBuilderOutcomeFixtureV1(*state, outcome);
  g_builder_context = {};
  return returned;
}

extern "C" bool __fastcall XarAiReentrySubmitHookV1(
    void *manager, void *command, std::uint32_t channel_flags,
    std::uintptr_t opaque_r9) noexcept {
  const auto original = g_submit_original.load(std::memory_order_acquire);
  if (original == nullptr) return false;
  auto *state = g_active.load(std::memory_order_acquire);
  if (state == nullptr)
    return original(manager, command, channel_flags, opaque_r9);
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto context = g_builder_context;
  const bool from_builder =
      caller == state->module_base + kAiReentrySubmitReturnRvaV1 &&
      context.active;
  const bool from_fallback =
      caller == state->module_base + kAiReentryFallbackSubmitReturnRvaV1;
  if (!from_builder && !from_fallback)
    return original(manager, command, channel_flags, opaque_r9);
  std::int32_t command_cunit_id = -1;
  if (from_fallback) {
    if (!ReadAt(command, 0x24, command_cunit_id)) {
      Fail(*state, ai_reentry_failure_capture);
      return original(manager, command, channel_flags, opaque_r9);
    }
    if (command_cunit_id != kAiReentryCunitIdV1)
      return original(manager, command, channel_flags, opaque_r9);
  }
  if (from_builder) {
    state->submit_matching_calls.fetch_add(1, std::memory_order_relaxed);
    ++g_builder_context.main_submit_calls;
  } else {
    state->fallback_submit_matching_calls.fetch_add(
        1, std::memory_order_relaxed);
  }
  AiReentryDispatchRecordV1 record{};
  record.thread_id = GetCurrentThreadId();
  record.cunit_id = from_builder ? context.cunit_id : command_cunit_id;
  record.builder_target_province_id = from_builder ? context.target_id : -1;
  record.builder_return = from_builder ? context.return_address : 0;
  record.submit_return = caller;
  record.submit_site = from_builder ? AiReentrySubmitSiteV1::builder
                                    : AiReentrySubmitSiteV1::outer_fallback;
  record.channel_flags = channel_flags;
  record.terminal_sequence_cutoff =
      BattleTerminalJournalLatestSequenceV1();
  void *game_state = nullptr;
  if (state->game_state_slot != nullptr &&
      SafeCopy(&game_state, state->game_state_slot, sizeof(game_state)) &&
      game_state != nullptr) {
    if (!ReadAt(game_state, 0x08, record.observed_date_raw))
      Fail(*state, ai_reentry_failure_capture);
  } else {
    Fail(*state, ai_reentry_failure_capture);
  }
  if ((from_builder && context.thread_id != record.thread_id) ||
      !ReadCommandHeader(command, state->module_base, record))
    Fail(*state, ai_reentry_failure_capture);
  else if (!record.command_header_valid)
    Fail(*state, ai_reentry_failure_identity);
  record.queue_accepted = original(manager, command, channel_flags, opaque_r9);
  (void)RecordAiReentryDispatchFixtureV1(*state, record);
  return record.queue_accepted;
}

} // namespace

bool DecodeAiReentryCommandHeaderFixtureV1(
    const void *command, std::uintptr_t module_base,
    AiReentryDispatchRecordV1 &record) noexcept {
  return ReadCommandHeader(command, module_base, record);
}

void CorrelateAiReentryTerminalAfterPauseV1(
    AiReentryDispatchRecordV1 &record,
    const BattleTerminalJournalLookupV1 &terminal) noexcept {
  record.terminal_status = terminal.status;
  if (terminal.status != BattleTerminalJournalLookupStatusV1::observed ||
      terminal.event.sequence == 0 ||
      terminal.event.combat_id != kAiReentryCombatIdV1 ||
      record.cunit_id != kAiReentryCunitIdV1 ||
      terminal.event.sequence > record.terminal_sequence_cutoff ||
      terminal.event.observed_date_raw > record.observed_date_raw)
    return;
  record.terminal_before_submit = true;
  record.terminal_sequence = terminal.event.sequence;
  record.terminal_date_raw = terminal.event.observed_date_raw;
  record.terminal_capture_failure_flags =
      terminal.event.capture_failure_flags;
  record.terminal_normal_result =
      !terminal.event.suppress_normal_result_envelopes;
  if (terminal.event.winner_raw != 0 && terminal.event.winner_raw != 1)
    return;
  const auto &winner = terminal.event.winner_raw == 0
      ? terminal.event.attacker_public_cunit_ids_in_stored_order
      : terminal.event.defender_public_cunit_ids_in_stored_order;
  const auto winner_count = terminal.event.winner_raw == 0
      ? terminal.event.attacker_public_cunit_count
      : terminal.event.defender_public_cunit_count;
  for (std::uint32_t member = 0;
       member < winner_count && member < winner.size(); ++member) {
    if (winner[member] == record.cunit_id)
      record.cunit_was_terminal_winner = true;
  }
}

bool RecordAiReentryDispatchFixtureV1(
    AiReentryDispatchStateV1 &state,
    const AiReentryDispatchRecordV1 &record) noexcept {
  if (state.recording.exchange(true, std::memory_order_acq_rel)) {
    Fail(state, ai_reentry_failure_reentry);
    return false;
  }
  const auto count = state.count.load(std::memory_order_relaxed);
  if (count >= state.records.size()) {
    state.overflow_count.fetch_add(1, std::memory_order_relaxed);
    Fail(state, ai_reentry_failure_capacity);
    state.recording.store(false, std::memory_order_release);
    return false;
  }
  auto copy = record;
  copy.sequence = count + 1;
  state.records[count] = copy;
  state.count.store(count + 1, std::memory_order_release);
  state.recording.store(false, std::memory_order_release);
  return true;
}

AiReentryBuilderOutcomeKindV1 ClassifyAiReentryBuilderOutcomeFixtureV1(
    std::uint8_t handled, std::uint8_t second,
    std::uint32_t main_submit_calls) noexcept {
  if (handled == 0 && second == 0 && main_submit_calls == 0)
    return AiReentryBuilderOutcomeKindV1::unhandled;
  if (handled == 1 && second == 0 && main_submit_calls == 0)
    return AiReentryBuilderOutcomeKindV1::early_return;
  if (handled == 1 && second == 1 && main_submit_calls == 0)
    return AiReentryBuilderOutcomeKindV1::gate_bypass;
  if (handled == 1 && second == 1 && main_submit_calls == 1)
    return AiReentryBuilderOutcomeKindV1::main_submit;
  return AiReentryBuilderOutcomeKindV1::unclassified;
}

bool RecordAiReentryBuilderOutcomeFixtureV1(
    AiReentryDispatchStateV1 &state,
    const AiReentryBuilderOutcomeV1 &outcome) noexcept {
  if (state.builder_outcome_recording.exchange(true,
                                               std::memory_order_acq_rel)) {
    Fail(state, ai_reentry_failure_reentry);
    return false;
  }
  const auto count = state.builder_outcome_count.load(std::memory_order_relaxed);
  if (count >= state.builder_outcomes.size()) {
    state.overflow_count.fetch_add(1, std::memory_order_relaxed);
    Fail(state, ai_reentry_failure_capacity);
    state.builder_outcome_recording.store(false, std::memory_order_release);
    return false;
  }
  auto copy = outcome;
  copy.sequence = count + 1;
  state.builder_outcomes[count] = copy;
  state.builder_outcome_count.store(count + 1, std::memory_order_release);
  state.builder_outcome_recording.store(false, std::memory_order_release);
  return true;
}

AiReentryDispatchSnapshotV1 ReadAiReentryDispatchObserverV1(
    const AiReentryDispatchStateV1 &state) noexcept {
  AiReentryDispatchSnapshotV1 output{};
  output.installed = state.installed.load(std::memory_order_acquire);
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  output.builder_matching_calls = state.builder_matching_calls.load(
      std::memory_order_acquire);
  output.submit_matching_calls = state.submit_matching_calls.load(
      std::memory_order_acquire);
  output.fallback_submit_matching_calls =
      state.fallback_submit_matching_calls.load(std::memory_order_acquire);
  output.overflow_count = state.overflow_count.load(
      std::memory_order_acquire);
  output.count = state.count.load(std::memory_order_acquire);
  for (std::uint32_t index = 0; index < output.count &&
                                index < output.records.size(); ++index)
    output.records[index] = state.records[index];
  output.builder_outcome_count = state.builder_outcome_count.load(
      std::memory_order_acquire);
  for (std::uint32_t index = 0;
       index < output.builder_outcome_count &&
       index < output.builder_outcomes.size(); ++index)
    output.builder_outcomes[index] = state.builder_outcomes[index];
  return output;
}

bool InstallAiReentryDispatchObserverV1(
    AiReentryDispatchStateV1 &state,
    const AiReentryDispatchEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(0, std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    Fail(state, ai_reentry_failure_admission);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, ai_reentry_failure_quiescence);
    return false;
  }
  if (!environment.offline_fixture &&
      (environment.builder_target_override != 0 ||
       environment.submit_target_override != 0 ||
       environment.builder_caller_override != 0 ||
       environment.submit_caller_override != 0 ||
       environment.game_state_slot == nullptr ||
       environment.memory_context != nullptr ||
       environment.alloc_override != nullptr ||
       environment.free_override != nullptr ||
       environment.protect_override != nullptr ||
       environment.flush_override != nullptr)) {
    Fail(state, ai_reentry_failure_admission);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) ||
      state.builder_trampoline != nullptr ||
      state.submit_trampoline != nullptr) {
    Fail(state, ai_reentry_failure_admission);
    return false;
  }
  AiReentryDispatchStateV1 *expected = nullptr;
  if (!g_active.compare_exchange_strong(expected, &state,
                                        std::memory_order_acq_rel)) {
    Fail(state, ai_reentry_failure_admission);
    return false;
  }
  state.module_base = environment.module_base;
  state.game_state_slot = environment.game_state_slot;
  state.builder_target = environment.builder_target_override != 0
      ? environment.builder_target_override
      : state.module_base + kAiReentryBuilderRvaV1;
  state.submit_target = environment.submit_target_override != 0
      ? environment.submit_target_override
      : state.module_base + kAiReentrySubmitRvaV1;
  const auto builder_caller = environment.builder_caller_override != 0
      ? environment.builder_caller_override
      : state.module_base + kAiReentryBuilderCallerRvaV1;
  const auto submit_caller = environment.submit_caller_override != 0
      ? environment.submit_caller_override
      : state.module_base + kAiReentrySubmitCallerRvaV1;
  // Fixture pages model the original two patched entries. A live admission
  // also freezes every newly interpreted, unpatched instruction site.
  const bool extended_anchors = environment.offline_fixture ||
      (SafeEqual(state.module_base + kAiReentryFallbackSubmitCallerRvaV1,
                 kFallbackSubmitCallerAnchor.data(),
                 kFallbackSubmitCallerAnchor.size()) &&
       SafeEqual(state.module_base + 0x186B278,
                 kSubmitGateTestAnchor.data(),
                 kSubmitGateTestAnchor.size()) &&
       SafeEqual(state.module_base + 0x186B1D6,
                 kBuilderHandledAnchor.data(),
                 kBuilderHandledAnchor.size()) &&
       SafeEqual(state.module_base + 0x186B2EA,
                 kBuilderSecondAnchor.data(),
                 kBuilderSecondAnchor.size()));
  if (!SafeEqual(state.builder_target, kBuilderAnchor.data(),
                 kBuilderAnchor.size()) ||
      !SafeEqual(state.submit_target, kSubmitAnchor.data(),
                 kSubmitAnchor.size()) ||
      !SafeEqual(builder_caller, kBuilderCallerAnchor.data(),
                 kBuilderCallerAnchor.size()) ||
      !SafeEqual(submit_caller, kSubmitCallerAnchor.data(),
                 kSubmitCallerAnchor.size()) || !extended_anchors) {
    Fail(state, ai_reentry_failure_anchor);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  state.memory_context = environment.memory_context;
  state.free_memory = environment.free_override != nullptr
      ? environment.free_override : &DefaultFree;
  state.protect = environment.protect_override != nullptr
      ? environment.protect_override : &DefaultProtect;
  state.flush = environment.flush_override != nullptr
      ? environment.flush_override : &DefaultFlush;
  const auto allocate = environment.alloc_override != nullptr
      ? environment.alloc_override : &DefaultAlloc;
  state.builder_trampoline = allocate(
      state.memory_context, kAiReentryPatchBytesV1 + kAiReentryJumpBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  state.submit_trampoline = allocate(
      state.memory_context, kAiReentryPatchBytesV1 + kAiReentryJumpBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.builder_trampoline == nullptr ||
      state.submit_trampoline == nullptr ||
      !BuildTrampoline(state, state.builder_trampoline, kBuilderAnchor,
                       state.builder_target + kAiReentryPatchBytesV1) ||
      !BuildTrampoline(state, state.submit_trampoline, kSubmitAnchor,
                       state.submit_target + kAiReentryPatchBytesV1)) {
    Fail(state, ai_reentry_failure_allocation);
    Release(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  g_builder_original.store(reinterpret_cast<BuilderOriginal>(
                               state.builder_trampoline),
                           std::memory_order_release);
  g_submit_original.store(reinterpret_cast<SubmitOriginal>(
                              state.submit_trampoline),
                          std::memory_order_release);
  state.builder_patch.fill(0x90);
  state.submit_patch.fill(0x90);
  WriteJump(state.builder_patch.data(), reinterpret_cast<std::uintptr_t>(
                                            &XarAiReentryBuilderHookV1));
  WriteJump(state.submit_patch.data(), reinterpret_cast<std::uintptr_t>(
                                           &XarAiReentrySubmitHookV1));
  const bool builder_written = WriteTarget(state, state.builder_target,
                                            kBuilderAnchor.data(),
                                            state.builder_patch.data());
  const bool submit_written = builder_written && WriteTarget(
      state, state.submit_target, kSubmitAnchor.data(),
      state.submit_patch.data());
  if (!submit_written) {
    if (builder_written && !WriteTarget(state, state.builder_target,
                                        state.builder_patch.data(),
                                        kBuilderAnchor.data()))
      Fail(state, ai_reentry_failure_rollback);
    g_builder_original.store(nullptr, std::memory_order_release);
    g_submit_original.store(nullptr, std::memory_order_release);
    Release(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  state.installed.store(true, std::memory_order_release);
  return true;
}

} // namespace xar::ck3_11906

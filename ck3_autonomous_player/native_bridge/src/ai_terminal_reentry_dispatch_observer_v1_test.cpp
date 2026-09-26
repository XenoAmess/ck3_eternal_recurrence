#include "xar_bridge/ai_terminal_reentry_dispatch_observer_v1.hpp"

#include <array>
#include <cassert>
#include <cstring>

namespace {
using namespace xar::ck3_11906;

constexpr std::array<std::uint8_t, 15> kBuilder{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10,
    0x48, 0x89, 0x7C, 0x24, 0x18};
constexpr std::array<std::uint8_t, 15> kSubmit{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x4C, 0x89, 0x4C, 0x24, 0x20,
    0x57, 0x48, 0x83, 0xEC, 0x20};
constexpr std::array<std::uint8_t, 5> kBuilderCall{
    0xE8, 0x2E, 0x8E, 0xFF, 0xFF};
constexpr std::array<std::uint8_t, 5> kSubmitCall{
    0xE8, 0x36, 0x8B, 0x10, 0xFF};

struct Pages {
  void *builder = nullptr;
  void *submit = nullptr;
  void *builder_call = nullptr;
  void *submit_call = nullptr;
  void *game_state = nullptr;
  void *game_state_slot = nullptr;

  Pages() {
    builder = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                           PAGE_READWRITE);
    submit = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                          PAGE_READWRITE);
    builder_call = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                                PAGE_READWRITE);
    submit_call = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                               PAGE_READWRITE);
    game_state = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                              PAGE_READWRITE);
    assert(builder && submit && builder_call && submit_call && game_state);
    std::memcpy(builder, kBuilder.data(), kBuilder.size());
    std::memcpy(submit, kSubmit.data(), kSubmit.size());
    std::memcpy(builder_call, kBuilderCall.data(), kBuilderCall.size());
    std::memcpy(submit_call, kSubmitCall.data(), kSubmitCall.size());
    game_state_slot = game_state;
    DWORD old = 0;
    assert(VirtualProtect(builder, 4096, PAGE_EXECUTE_READ, &old));
    assert(VirtualProtect(submit, 4096, PAGE_EXECUTE_READ, &old));
    assert(VirtualProtect(builder_call, 4096, PAGE_EXECUTE_READ, &old));
    assert(VirtualProtect(submit_call, 4096, PAGE_EXECUTE_READ, &old));
  }
  ~Pages() {
    if (builder) (void)VirtualFree(builder, 0, MEM_RELEASE);
    if (submit) (void)VirtualFree(submit, 0, MEM_RELEASE);
    if (builder_call) (void)VirtualFree(builder_call, 0, MEM_RELEASE);
    if (submit_call) (void)VirtualFree(submit_call, 0, MEM_RELEASE);
    if (game_state) (void)VirtualFree(game_state, 0, MEM_RELEASE);
  }
  AiReentryDispatchEnvironmentV1 Env() const {
    AiReentryDispatchEnvironmentV1 env{};
    env.exact_build_admitted = true;
    env.primary_thread_suspended_proven = true;
    env.offline_fixture = true;
    env.module_base = 1;
    env.builder_target_override = reinterpret_cast<std::uintptr_t>(builder);
    env.submit_target_override = reinterpret_cast<std::uintptr_t>(submit);
    env.builder_caller_override =
        reinterpret_cast<std::uintptr_t>(builder_call);
    env.submit_caller_override =
        reinterpret_cast<std::uintptr_t>(submit_call);
    env.game_state_slot = const_cast<void **>(&game_state_slot);
    return env;
  }
};

bool FailSubmitProtect(void *context, void *address, std::size_t size,
                       DWORD protection, DWORD &old) noexcept {
  const auto *pages = static_cast<const Pages *>(context);
  if (address == pages->submit && protection == PAGE_EXECUTE_READWRITE)
    return false;
  return VirtualProtect(address, size, protection, &old) != FALSE;
}

void CheckStorage() {
  AiReentryDispatchStateV1 state{};
  AiReentryDispatchRecordV1 row{};
  row.cunit_id = kAiReentryCunitIdV1;
  row.command_kind = 2;
  row.channel_flags = 7;
  for (std::uint32_t i = 0; i < kAiReentryCapacityV1; ++i) {
    row.command_target_province_id = static_cast<std::int32_t>(i + 100);
    assert(RecordAiReentryDispatchFixtureV1(state, row));
  }
  assert(!RecordAiReentryDispatchFixtureV1(state, row));
  auto snapshot = ReadAiReentryDispatchObserverV1(state);
  assert(snapshot.count == kAiReentryCapacityV1);
  assert(snapshot.overflow_count == 1);
  assert(snapshot.failure_flags & ai_reentry_failure_capacity);
  assert(snapshot.records[0].sequence == 1);
  assert(snapshot.records[63].sequence == 64);
  assert(snapshot.records[63].command_target_province_id == 163);
  state.recording.store(true, std::memory_order_release);
  assert(!RecordAiReentryDispatchFixtureV1(state, row));
  assert(state.failure_flags.load() & ai_reentry_failure_reentry);
  state.recording.store(false, std::memory_order_release);
}

void CheckBuilderOutcomeStorageAndClassification() {
  assert(ClassifyAiReentryBuilderOutcomeFixtureV1(0, 0, 0) ==
         AiReentryBuilderOutcomeKindV1::unhandled);
  assert(ClassifyAiReentryBuilderOutcomeFixtureV1(1, 0, 0) ==
         AiReentryBuilderOutcomeKindV1::early_return);
  assert(ClassifyAiReentryBuilderOutcomeFixtureV1(1, 1, 0) ==
         AiReentryBuilderOutcomeKindV1::gate_bypass);
  assert(ClassifyAiReentryBuilderOutcomeFixtureV1(1, 1, 1) ==
         AiReentryBuilderOutcomeKindV1::main_submit);
  assert(ClassifyAiReentryBuilderOutcomeFixtureV1(1, 1, 2) ==
         AiReentryBuilderOutcomeKindV1::unclassified);
  AiReentryDispatchStateV1 state{};
  AiReentryBuilderOutcomeV1 row{};
  row.cunit_id = kAiReentryCunitIdV1;
  row.gate_before_raw = 4;
  row.result_handled_raw = 1;
  row.result_second_raw = 1;
  row.outcome = AiReentryBuilderOutcomeKindV1::gate_bypass;
  for (std::uint32_t i = 0; i < kAiReentryCapacityV1; ++i)
    assert(RecordAiReentryBuilderOutcomeFixtureV1(state, row));
  assert(!RecordAiReentryBuilderOutcomeFixtureV1(state, row));
  const auto snapshot = ReadAiReentryDispatchObserverV1(state);
  assert(snapshot.builder_outcome_count == kAiReentryCapacityV1);
  assert(snapshot.builder_outcomes[0].sequence == 1);
  assert(snapshot.builder_outcomes[63].sequence == 64);
  assert(snapshot.builder_outcomes[63].gate_before_raw == 4);
  assert(snapshot.overflow_count == 1);
  assert(snapshot.failure_flags & ai_reentry_failure_capacity);
}

void CheckCommandAndTerminalState() {
  constexpr std::uintptr_t base = 0x10000000;
  std::array<std::byte, 0x38> command{};
  const auto primary = base + 0x432BF18;
  const auto secondary = base + 0x432BFB0;
  const std::uint32_t kind = 2;
  const std::uint32_t cunit = kAiReentryCunitIdV1;
  const std::int32_t target = 2639;
  const std::uint32_t route_kind = 2;
  const std::uint32_t direct_target = 1;
  std::memcpy(command.data() + 0x00, &primary, sizeof(primary));
  std::memcpy(command.data() + 0x18, &secondary, sizeof(secondary));
  std::memcpy(command.data() + 0x20, &kind, sizeof(kind));
  std::memcpy(command.data() + 0x24, &cunit, sizeof(cunit));
  std::memcpy(command.data() + 0x28, &target, sizeof(target));
  std::memcpy(command.data() + 0x30, &route_kind, sizeof(route_kind));
  std::memcpy(command.data() + 0x34, &direct_target,
              sizeof(direct_target));
  AiReentryDispatchRecordV1 row{};
  row.cunit_id = kAiReentryCunitIdV1;
  row.builder_target_province_id = target;
  row.channel_flags = 7;
  row.terminal_sequence_cutoff = 3;
  row.observed_date_raw = 100;
  assert(DecodeAiReentryCommandHeaderFixtureV1(command.data(), base, row));
  assert(row.command_header_valid);
  assert(row.command_target_province_id == target);
  row.submit_site = AiReentrySubmitSiteV1::outer_fallback;
  row.builder_target_province_id = -1;
  assert(DecodeAiReentryCommandHeaderFixtureV1(command.data(), base, row));
  assert(row.command_header_valid);
  row.submit_site = AiReentrySubmitSiteV1::builder;
  assert(DecodeAiReentryCommandHeaderFixtureV1(command.data(), base, row));
  assert(!row.command_header_valid);
  row.builder_target_province_id = target;
  row.channel_flags = 8;
  assert(DecodeAiReentryCommandHeaderFixtureV1(command.data(), base, row));
  assert(!row.command_header_valid);
  assert(!DecodeAiReentryCommandHeaderFixtureV1(nullptr, base, row));

  BattleTerminalJournalLookupV1 terminal{};
  terminal.status = BattleTerminalJournalLookupStatusV1::observed;
  terminal.event.sequence = 3;
  terminal.event.combat_id = kAiReentryCombatIdV1;
  terminal.event.observed_date_raw = 99;
  terminal.event.winner_raw = 0;
  terminal.event.attacker_public_cunit_count = 1;
  terminal.event.attacker_public_cunit_ids_in_stored_order[0] =
      kAiReentryCunitIdV1;
  CorrelateAiReentryTerminalAfterPauseV1(row, terminal);
  assert(row.terminal_before_submit);
  assert(row.cunit_was_terminal_winner);
  assert(row.terminal_sequence == 3);
  row = {};
  row.cunit_id = kAiReentryCunitIdV1;
  row.terminal_sequence_cutoff = 2;
  row.observed_date_raw = 100;
  CorrelateAiReentryTerminalAfterPauseV1(row, terminal);
  assert(!row.terminal_before_submit);
  row.terminal_sequence_cutoff = 3;
  row.observed_date_raw = 98;
  CorrelateAiReentryTerminalAfterPauseV1(row, terminal);
  assert(!row.terminal_before_submit);
}

void CheckAdmissionAndAnchors() {
  Pages pages{};
  AiReentryDispatchStateV1 state{};
  auto env = pages.Env();
  env.exact_build_admitted = false;
  assert(!InstallAiReentryDispatchObserverV1(state, env));
  assert(state.failure_flags.load() & ai_reentry_failure_admission);
  env = pages.Env();
  env.primary_thread_suspended_proven = false;
  assert(!InstallAiReentryDispatchObserverV1(state, env));
  assert(state.failure_flags.load() & ai_reentry_failure_quiescence);
  env = pages.Env();
  DWORD old = 0;
  assert(VirtualProtect(pages.submit_call, 4096, PAGE_EXECUTE_READWRITE,
                        &old));
  static_cast<std::uint8_t *>(pages.submit_call)[0] = 0x90;
  assert(VirtualProtect(pages.submit_call, 4096, PAGE_EXECUTE_READ, &old));
  assert(!InstallAiReentryDispatchObserverV1(state, env));
  assert(state.failure_flags.load() & ai_reentry_failure_anchor);
  assert(std::memcmp(pages.builder, kBuilder.data(), kBuilder.size()) == 0);
}

void CheckRollback() {
  Pages pages{};
  AiReentryDispatchStateV1 state{};
  auto env = pages.Env();
  env.memory_context = &pages;
  env.protect_override = &FailSubmitProtect;
  assert(!InstallAiReentryDispatchObserverV1(state, env));
  assert(state.failure_flags.load() & ai_reentry_failure_protection);
  assert((state.failure_flags.load() & ai_reentry_failure_rollback) == 0);
  assert(std::memcmp(pages.builder, kBuilder.data(), kBuilder.size()) == 0);
  assert(std::memcmp(pages.submit, kSubmit.data(), kSubmit.size()) == 0);
  assert(!state.installed.load());
  assert(state.builder_trampoline == nullptr);
  assert(state.submit_trampoline == nullptr);
}

void CheckInstall() {
  Pages pages{};
  AiReentryDispatchStateV1 state{};
  assert(InstallAiReentryDispatchObserverV1(state, pages.Env()));
  const auto snapshot = ReadAiReentryDispatchObserverV1(state);
  assert(snapshot.installed);
  assert(snapshot.failure_flags == 0);
  assert(std::memcmp(pages.builder, kBuilder.data(), kBuilder.size()) != 0);
  assert(std::memcmp(pages.submit, kSubmit.data(), kSubmit.size()) != 0);
  assert(!InstallAiReentryDispatchObserverV1(state, pages.Env()));
  assert(state.failure_flags.load() & ai_reentry_failure_admission);
}
} // namespace

int main() {
  CheckStorage();
  CheckBuilderOutcomeStorageAndClassification();
  CheckCommandAndTerminalState();
  CheckAdmissionAndAnchors();
  CheckRollback();
  CheckInstall();
  return 0;
}

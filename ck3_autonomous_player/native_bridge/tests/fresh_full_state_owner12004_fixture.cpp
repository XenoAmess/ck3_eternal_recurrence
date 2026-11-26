#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12002_thread_runtime.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_121003_full_profile111.hpp"
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#include "xar_bridge/fresh_full_state_diagnostic_v1.hpp"
#include "xar_bridge/florin_event_pump_boundary_v1.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <cstring>
#include <thread>
#include <utility>
#include <vector>

namespace {
namespace api = xar::ck3_11906;
namespace build = xar::ck3_12002;
namespace game = xar::game;

// The native hook deliberately pins one mailbox address until process exit.
api::MainThreadQueryMailboxV1 g_fresh_mailbox{};

#define CHECK(expression) do { if (!(expression)) { \
  std::fprintf(stderr, "semantic fixture line %d: %s\n", __LINE__, #expression); \
  return false; } } while (false)

template <class Value, std::size_t Size>
void Store(std::array<std::byte, Size> &bytes, std::size_t offset, Value value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct MemoryFixture {
  void *iat = nullptr;
  void *poll_slot = nullptr;
  DWORD page_protect = PAGE_READONLY;
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x18> state{};
  std::array<std::byte, 0x28> tls{};
  std::uintptr_t jomini_slot = 0;
  std::uintptr_t state_slot = 0;
  std::uintptr_t null_rng_slot = 0;
  std::uint8_t tls_initialized = 1;
};
MemoryFixture *g_memory = nullptr;

BOOL WINAPI FakePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
int __cdecl FakePollEvent(void *) { return 0; }
void *__fastcall FakeTls() noexcept { return g_memory->tls.data(); }
bool FakeQuery(void *opaque, const void *address,
               MEMORY_BASIC_INFORMATION &output) noexcept {
  auto &memory = *static_cast<MemoryFixture *>(opaque);
  if (address != &memory.iat) return false;
  output = {};
  output.BaseAddress = reinterpret_cast<void *>(
      reinterpret_cast<std::uintptr_t>(address) & ~4095ULL);
  output.AllocationBase = output.BaseAddress;
  output.RegionSize = 4096;
  output.State = MEM_COMMIT;
  output.Type = MEM_IMAGE;
  output.Protect = memory.page_protect;
  return true;
}
bool FakeProtect(void *opaque, void *, std::size_t size, DWORD desired,
                 DWORD &previous) noexcept {
  auto &memory = *static_cast<MemoryFixture *>(opaque);
  if (size != 4096) return false;
  previous = memory.page_protect;
  memory.page_protect = desired;
  return true;
}

class FixtureAdapter final : public game::GameAdapter {
public:
  const DWORD owner = GetCurrentThreadId();
  game::Snapshot frame{};
  mutable std::atomic<std::uint32_t> raw_reads{0};
  mutable std::atomic<std::uint32_t> semantic_calls{0};
  mutable std::atomic<std::uint32_t> wrong_owner{0};
  mutable std::atomic<DWORD> queue_thread{0};
  mutable std::atomic<std::int32_t> last_event_option{-1};
  mutable std::atomic<std::int32_t> last_army{-1};
  mutable std::atomic<std::int32_t> last_province{-1};
  mutable std::atomic<std::int32_t> last_family_subject{-1};
  bool reader_available = true;
  bool declarations_available = true;
  bool family_available = true;
  bool patch3 = false;
  bool patch4 = false;
  bool florin = false;
  bool florin_current_patch = false;
  bool wrong_build = false;
  mutable std::atomic<DWORD> read_delay_ms{0};
  void *raw_read_context = nullptr;
  bool (*raw_read_gate)(void *) noexcept = nullptr;

  FixtureAdapter() {
    frame.date_raw = 123456;
    frame.speed = 3;
    frame.player_id = 7;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_id = 0x12000015;
    frame.played_character_alive = true;
    frame.has_active_event = true;
    frame.active_event_instance_id = 91;
    frame.active_event_option_count = 3;
    game::ArmySnapshot army{};
    army.army_id = 0x23000031;
    army.owner_character_id = frame.played_character_id;
    army.controllable = true;
    army.has_current_province = true;
    army.current_province_id = 900;
    frame.player_armies.push_back(army);
  }

  const game::AdapterDescriptor &descriptor() const noexcept override {
    static constexpr std::array<std::string_view, 2> florin_capabilities{
      "game.state.snapshot", "game.query.fresh-full-state.v1"};
    static const game::AdapterDescriptor florin_value{
      xar::ck3_1210::kAdapterId, xar::ck3_1210::kGameVersion,
      xar::ck3_1210::kExecutableSha256, "offline-fresh-fixture",
      std::span<const std::string_view>{florin_capabilities}};
    static const game::AdapterDescriptor wrong_value{
      xar::ck3_1210::kAdapterId, xar::ck3_1210::kGameVersion,
      xar::ck3_12004::kExecutableSha256, "offline-wrong-build-fixture",
      std::span<const std::string_view>{florin_capabilities}};
    static const game::AdapterDescriptor current_value{
      xar::ck3_121003::full111::kAdapterId, xar::ck3_121003::full111::kGameVersion,
      xar::ck3_121003::full111::kExecutableSha256, "offline-fresh-fixture",
      std::span<const std::string_view>{florin_capabilities}};
    if (wrong_build) return wrong_value;
    if (florin_current_patch) return current_value;
    if (florin) return florin_value;
    static constexpr std::array<std::string_view, 1> capabilities{
      "game.state.snapshot"};
    static const game::AdapterDescriptor value{
      xar::ck3_12004::kAdapterId, xar::ck3_12004::kGameVersion,
      xar::ck3_12004::kExecutableSha256, "offline-fresh-fixture",
      std::span<const std::string_view>{capabilities}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  void RecordSemantic() const noexcept {
    ++semantic_calls;
    if (GetCurrentThreadId() != owner) ++wrong_owner;
  }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    ++raw_reads;
    if (GetCurrentThreadId() != owner) {
      ++wrong_owner;
      output = {};
      return false;
    }
    if (raw_read_gate && !raw_read_gate(raw_read_context)) {
      output = {};
      return false;
    }
    const auto delay = read_delay_ms.load(std::memory_order_acquire);
    if (delay != 0) Sleep(delay);
    output = reader_available ? frame : game::Snapshot{};
    return reader_available;
  }
  game::PauseSubmitResult submit_pause_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::PauseSubmitResult::submitted;
  }
  game::ResumeSubmitResult submit_resume_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::ResumeSubmitResult::submitted;
  }
  bool submit_set_speed(std::int32_t speed) const noexcept override {
    queue_thread = GetCurrentThreadId();
    return speed == 4;
  }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    queue_thread = GetCurrentThreadId();
    return {game::SaveCheckpointStatus::submitted, 123456};
  }
  game::SelectEventOptionResult submit_select_event_option(
      std::int32_t option) const noexcept override {
    RecordSemantic();
    last_event_option = option;
    return option < 0 || option >= frame.active_event_option_count
      ? game::SelectEventOptionResult::option_out_of_range
      : game::SelectEventOptionResult::submitted;
  }
  bool read_declarable_wars(
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return false;
    output.push_back({0x14000042, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return true;
  }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t target_id,
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return game::ReadDeclarableWarsResult::unavailable;
    if (target_id != 0x14000042) return game::ReadDeclarableWarsResult::target_not_found;
    output.push_back({target_id, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return game::ReadDeclarableWarsResult::available;
  }
  game::MoveArmyResult submit_move_army(
      std::int32_t army, std::int32_t province) const noexcept override {
    RecordSemantic();
    last_army = army;
    last_province = province;
    return army == frame.player_armies.front().army_id && province == 901
      ? game::MoveArmyResult::submitted : game::MoveArmyResult::validation_failed;
  }
  game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<game::ArmyStrengthSnapshot> &output) const noexcept override {
    RecordSemantic();
    game::ArmyStrengthSnapshot row{};
    row.available = true;
    row.army_id = frame.player_armies.front().army_id;
    row.regiment_count = 2;
    row.current_soldiers = 734;
    row.maximum_soldiers = 1000;
    row.ai_base_power_raw = 123456789;
    output = {row};
    return game::ReadArmyStrengthsResult::available;
  }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<game::ArrangeMarriageChoice> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    output = {{frame.played_character_id, 0x15000011}};
    diagnostics = {};
    diagnostics.storage_capacity = 17;
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageChoicesResult::available;
  }
  game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t war_id, game::WarTerminationOptionsSnapshot &output) const noexcept override {
    RecordSemantic();
    output = {};
    if (frame.active_wars.empty() || frame.active_wars.front().war_id != war_id)
      return game::ReadWarTerminationOptionsResult::war_not_found;
    output.war_id = war_id;
    output.player_relative_war_score = frame.active_wars.front().player_relative_war_score;
    return game::ReadWarTerminationOptionsResult::available;
  }
  game::ReadArrangeMarriageFamilyCandidatesResultV1
  read_arrange_marriage_family_candidates_v1(
      std::int32_t subject_id,
      std::vector<game::ArrangeMarriageFamilyCandidateV1> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    last_family_subject = subject_id;
    output.clear();
    diagnostics = {};
    if (subject_id != 0x13000016)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::subject_not_found;
    diagnostics.storage_capacity = 17;
    diagnostics.slots_scanned = 2;
    if (!family_available)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::unavailable;
    game::ArrangeMarriageFamilyCandidateV1 row{};
    row.played_character_id = frame.played_character_id;
    row.subject_character_id = subject_id;
    row.candidate_character_id = 0x15000011;
    row.recipient_matchmaker_character_id = 0x14000042;
    row.recipient_ai_accept_raw = 2'500'000;
    row.recipient_answer_status_raw = 1;
    row.complete_can_send = true;
    row.recipient_answer_allows_send = true;
    row.heir_adult_measure_raw = std::int16_t{17};
    row.candidate_adult_measure_raw = std::int16_t{19};
    row.played_dynasty_id = 71;
    row.heir_dynasty_id = 71;
    row.candidate_dynasty_id = 72;
    row.realm_backed_actor_recipient = true;
    output.push_back(row);
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageFamilyCandidatesResultV1::available;
  }

#define UNAVAILABLE_RESULT(Result, Name, Parameters) \
  game::Result Name Parameters const noexcept override { \
    RecordSemantic(); return game::Result::unavailable; }
  UNAVAILABLE_RESULT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
                     (game::PendingInteractionReply))
  UNAVAILABLE_RESULT(AcknowledgePendingInteractionResult, submit_acknowledge_pending_interaction,
                     (std::int32_t))
  UNAVAILABLE_RESULT(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE_RESULT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE_RESULT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE_RESULT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE_RESULT(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE_RESULT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  UNAVAILABLE_RESULT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  UNAVAILABLE_RESULT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  UNAVAILABLE_RESULT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE_RESULT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  UNAVAILABLE_RESULT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationTermsResult, read_war_termination_terms,
                     (std::int32_t, game::WarTerminationTermsSnapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
                     (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef UNAVAILABLE_RESULT
  game::PreviewMoveArmyResult preview_move_army(
      std::int32_t, std::int32_t) const noexcept override {
    RecordSemantic();
    return {};
  }
};

// Test-only local seam; not a production API or runtime platform.
struct FreshWorkerProbe {
  std::atomic<build::WorkerAdapter *> proxy{nullptr};
  std::atomic<std::uint32_t> requested{0};
  std::atomic<std::uint32_t> completed{0};
  std::atomic<bool> stop{false};
  std::atomic<bool> failed{false};
  bool read_result = false;
  game::Snapshot output{};
  build::FreshFullSnapshotDiagnosticV1 diagnostic{};
};
void FreshProbeWorker(FreshWorkerProbe &probe, const game::GameAdapter &native,
    api::MainThreadQueryMailboxV1 &mailbox) noexcept;

void FreshProbeWorker(FreshWorkerProbe &probe, const game::GameAdapter &native, api::MainThreadQueryMailboxV1 &mailbox) noexcept {
  build::WorkerAdapter *adapter = nullptr;
  try {
    adapter = new build::WorkerAdapter(native, mailbox, build::ConsoleFixtureBindings{});
    probe.proxy.store(adapter, std::memory_order_release);
  } catch (...) {
    probe.failed.store(true, std::memory_order_release);
    probe.proxy.store(nullptr, std::memory_order_release);
    return;
  }

  while (!probe.stop.load(std::memory_order_acquire)) {
    const auto req = probe.requested.load(std::memory_order_acquire);
    const auto comp = probe.completed.load(std::memory_order_acquire);
    if (req != comp) {
      probe.output = {};
      probe.read_result = build::ReadFreshFullSnapshot12002(*adapter, probe.output);
      probe.diagnostic = build::ReadLastFreshFullSnapshotDiagnosticV1();
      probe.completed.store(req, std::memory_order_release);
    } else {
      Sleep(1);
    }
  }

  probe.proxy.store(nullptr, std::memory_order_release);
  delete adapter;
}

bool TestFreshOwnerExecutor(bool florin = false, bool poll_only = false) {
  FixtureAdapter native;
  native.florin = florin;
  native.patch4 = true;
  native.frame.paused = true;
  MemoryFixture memory;
  g_memory = &memory;
  memory.iat = reinterpret_cast<void *>(&FakePeek);
  memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
  memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
  Store(memory.tls, 0x20, std::uint8_t{1});
  Store(memory.jomini, 0x20, std::uint8_t{1});
  Store(memory.state, 0x08, native.frame.date_raw);
  auto &mailbox = g_fresh_mailbox;
  std::array<api::MainThreadQueryExecutorV1, 14> executors{};
  executors[13] = &build::ExecuteSemanticAdapter12002;
  auto environment = florin
      ? xar::ck3_1210::BindThreadRuntimeImage(0x140000000ULL,
          native.descriptor().executable_sha256,
          std::span<const api::MainThreadQueryExecutorV1>{executors.data() + 13, 1})
      : xar::ck3_12004::BindThreadRuntimeImage(
          0x140000000ULL, native.descriptor().executable_sha256, executors);
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &memory.iat;
  environment.resolved_peek_message_override = &FakePeek;
  environment.global_rng_wrapper_slot_override =
      reinterpret_cast<std::uintptr_t>(&memory.null_rng_slot);
  environment.jomini_state_slot_override =
      reinterpret_cast<std::uintptr_t>(&memory.jomini_slot);
  environment.game_state_slot_override =
      reinterpret_cast<std::uintptr_t>(&memory.state_slot);
  environment.tls_initialized_flag_override =
      reinterpret_cast<std::uintptr_t>(&memory.tls_initialized);
  environment.tls_context_getter_override = &FakeTls;
  environment.memory_protection_context = &memory;
  environment.memory_query_override = &FakeQuery;
  environment.memory_protect_override = &FakeProtect;
  environment.system_page_size_override = 4096;
  if (poll_only) {
    memory.poll_slot = reinterpret_cast<void *>(&FakePollEvent);
    environment.sdl_poll_event_slot_override = &memory.poll_slot;
    environment.resolved_sdl_poll_event_override = &FakePollEvent;
  }
  // No snapshot observer: raw_reads counts only the production fresh executor.
  if (!api::InstallMainThreadQueryMailboxV1(mailbox, environment)) {
    std::fprintf(stderr, "fresh fixture install failed: stage=rapid-fresh florin=%d failure_flags=%llu\n",
        florin ? 1 : 0, static_cast<unsigned long long>(mailbox.failure_flags.load()));
    return false;
  }
  bool installed = true;
  FreshWorkerProbe probe;
  std::thread worker;
  try {
    worker = std::thread([&] { FreshProbeWorker(probe, native, mailbox); });
  } catch (...) {
    (void)api::UninstallMainThreadQueryMailboxV1(mailbox, 0);
    return false;
  }
  const auto pump = [&] {
    (void)api::ObserveMainThreadPumpAndDrainV1(mailbox,
        poll_only ? xar::ck3_1210::kPollEventFirstReturnRvaV1
                  : (florin ? xar::ck3_1210::kSdlWindowsPumpFirstPeekReturnRva
                            : xar::ck3_12004::kSdlWindowsPumpFirstPeekReturnRva), GetCurrentThreadId());
  };
  const auto cleanup = [&] {
    // Detach cancels an actual queued ticket before its stack context can end.
    if (installed) {
      (void)api::UninstallMainThreadQueryMailboxV1(mailbox, 1000);
      installed = false;
    }
    probe.stop.store(true, std::memory_order_release);
    worker.join();
  };
  const auto until = [&](auto predicate) {
    const auto end = GetTickCount64() + 3000;
    while (!predicate() && GetTickCount64() < end) {
      if (probe.failed.load(std::memory_order_acquire)) return false;
      pump();
      Sleep(1);
    }
    return predicate();
  };
  const auto request = [&](std::uint32_t sequence) {
    probe.requested.store(sequence, std::memory_order_release);
    return until([&] {
      return probe.completed.load(std::memory_order_acquire) == sequence;
    });
  };
  bool ok = until([&] {
    return probe.proxy.load(std::memory_order_acquire) != nullptr;
  });
  if (ok) ok = until([&] {
    return api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready;
  });
  if (ok) {
    game::Snapshot wrong;
    wrong.date_raw = 99;
    const auto *proxy = probe.proxy.load(std::memory_order_acquire);
    ok = !build::ReadFreshFullSnapshot12002(*proxy, wrong) &&
         wrong == game::Snapshot{} && native.raw_reads.load() == 0;
  }
  const auto started = GetTickCount64();
  if (ok) {
    native.frame.played_character_gold.raw = 111;
    ok = request(1) && probe.read_result &&
         probe.output.played_character_gold.raw == 111;
  }
  if (ok) {
    native.frame.played_character_gold.raw = 222;
    ok = request(2) && probe.read_result &&
         probe.output.played_character_gold.raw == 222;
  }
  const auto pair_ms = GetTickCount64() - started;
  ok = ok && pair_ms < 250 && native.raw_reads.load() == 2 &&
       native.wrong_owner.load() == 0;
  if (ok) {
    native.reader_available = false;
    ok = request(3) && !probe.read_result && probe.output == game::Snapshot{};
  }
  if (ok) {
    native.reader_available = true;
    native.frame.played_character_gold.raw = 333;
    ok = request(4) && probe.read_result &&
         probe.output.played_character_gold.raw == 333 &&
         native.raw_reads.load() == 4 &&
         api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).failure_flags == 0;
  }
  if (ok) {
    const auto terminal = api::UninstallMainThreadQueryMailboxV1(mailbox, 1000);
    installed = false;
    ok = terminal == api::MainThreadQueryUninstallResultV1::uninstalled &&
         request(5) && !probe.read_result && probe.output == game::Snapshot{} &&
         native.raw_reads.load() == 4;
  }
  cleanup();
  ok = ok && native.wrong_owner.load() == 0 &&
       memory.iat == reinterpret_cast<void *>(&FakePeek) &&
       (!poll_only || memory.poll_slot == reinterpret_cast<void *>(&FakePollEvent)) &&
       memory.page_protect == PAGE_READONLY;
  std::printf("fresh-owner: florin=%d poll_only=%d ok=%d pair_ms=%llu raw_reads=%u wrong_owner=%u\n",
      florin ? 1 : 0, poll_only ? 1 : 0, ok ? 1 : 0, static_cast<unsigned long long>(pair_ms),
      native.raw_reads.load(), native.wrong_owner.load());
  return ok;
}

enum class FreshWakeMode { recover_second_wake, no_pump, running_context, wrong_build };

bool TestFreshOwnerWake(bool florin, FreshWakeMode mode) {
  FixtureAdapter native;
  native.florin = florin;
  native.frame.paused = true;
  if (mode == FreshWakeMode::running_context) native.read_delay_ms.store(8'300);
  MemoryFixture memory;
  g_memory = &memory;
  memory.iat = reinterpret_cast<void *>(&FakePeek);
  memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
  memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
  Store(memory.tls, 0x20, std::uint8_t{1});
  Store(memory.jomini, 0x20, std::uint8_t{1});
  Store(memory.state, 0x08, native.frame.date_raw);
  auto &mailbox = g_fresh_mailbox;
  const std::array<api::MainThreadQueryExecutorV1, 1> executors{
      &build::ExecuteSemanticAdapter12002};
  auto environment = florin
      ? xar::ck3_1210::BindThreadRuntimeImage(0x140000000ULL,
          native.descriptor().executable_sha256, executors)
      : xar::ck3_12004::BindThreadRuntimeImage(0x140000000ULL,
          native.descriptor().executable_sha256, executors);
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &memory.iat;
  environment.resolved_peek_message_override = &FakePeek;
  environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&memory.null_rng_slot);
  environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.jomini_slot);
  environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.state_slot);
  environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&memory.tls_initialized);
  environment.tls_context_getter_override = &FakeTls;
  environment.memory_protection_context = &memory;
  environment.memory_query_override = &FakeQuery;
  environment.memory_protect_override = &FakeProtect;
  environment.system_page_size_override = 4096;
  if (!api::InstallMainThreadQueryMailboxV1(mailbox, environment)) {
    std::fprintf(stderr, "fresh fixture install failed: stage=queued-wake florin=%d failure_flags=%llu\n",
        florin ? 1 : 0, static_cast<unsigned long long>(mailbox.failure_flags.load()));
    return false;
  }
  const auto pump = [&] {
    (void)api::ObserveMainThreadPumpAndDrainV1(mailbox,
        florin ? xar::ck3_1210::kSdlWindowsPumpFirstPeekReturnRva
               : xar::ck3_12004::kSdlWindowsPumpFirstPeekReturnRva, GetCurrentThreadId());
  };
  for (int index = 0; index < 4; ++index) pump();
  MSG message{};
  (void)PeekMessageW(&message, nullptr, 0, 0, PM_NOREMOVE);
  while (PeekMessageW(&message, nullptr, WM_NULL, WM_NULL, PM_REMOVE)) {}
  const auto before = api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  // Installation clears publication/completion counters, but sequence IDs live
  // for the process lifetime. A new ticket advances the actual allocator once.
  const auto sequence_before = mailbox.next_sequence.load(std::memory_order_acquire);
  FreshWorkerProbe probe;
  std::thread worker([&] { FreshProbeWorker(probe, native, mailbox); });
  const auto start = GetTickCount64();
  while (probe.proxy.load(std::memory_order_acquire) == nullptr &&
         !probe.failed.load(std::memory_order_acquire) && GetTickCount64() - start < 1000) Sleep(1);
  if (mode == FreshWakeMode::wrong_build) native.wrong_build = true;
  probe.requested.store(1, std::memory_order_release);
  std::uint32_t null_messages = 0;
  bool drained = false;
  while (probe.completed.load(std::memory_order_acquire) != 1 &&
         GetTickCount64() - start < 9'500) {
    while (PeekMessageW(&message, nullptr, WM_NULL, WM_NULL, PM_REMOVE)) {
      ++null_messages;
      const bool should_drain = mode == FreshWakeMode::running_context ||
          (mode == FreshWakeMode::recover_second_wake && null_messages >= 2);
      if (should_drain && !drained) {
        drained = true;
        pump();
      }
    }
    Sleep(1);
  }
  const bool completed = probe.completed.load(std::memory_order_acquire) == 1;
  const auto after = api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  const auto sequence_after = mailbox.next_sequence.load(std::memory_order_acquire);
  const auto d = completed ? probe.diagnostic : build::FreshFullSnapshotDiagnosticV1{};
  const auto detach = api::UninstallMainThreadQueryMailboxV1(mailbox, 1000);
  probe.stop.store(true, std::memory_order_release);
  worker.join();
  bool ok = completed && !probe.failed.load() && before.ready &&
      detach == api::MainThreadQueryUninstallResultV1::uninstalled && native.wrong_owner.load() == 0;
  if (mode == FreshWakeMode::wrong_build) {
    ok = ok && !probe.read_result && native.raw_reads.load() == 0 &&
        d.stage == build::FreshFullSnapshotStageV1::worker_guard_rejected &&
        !d.submit_result && !d.wait_result && !d.reclaim_result && d.query_sequence == 0 &&
        after.published_sequence == before.published_sequence &&
        after.completed_sequence == before.completed_sequence && sequence_after == sequence_before &&
        after.executor_started_requests == before.executor_started_requests &&
        after.executed_requests == before.executed_requests;
  } else if (mode == FreshWakeMode::no_pump) {
    ok = ok && !probe.read_result && probe.output == game::Snapshot{} && native.raw_reads.load() == 0 &&
        d.stage == build::FreshFullSnapshotStageV1::wait_terminal &&
        d.wait_result == api::MainThreadQueryWaitResultV1::timeout_cancelled_before_execution &&
        d.reclaim_result == api::MainThreadQueryReclaimResultV1::reclaimed &&
        d.wake.wake_attempts >= 2 && d.elapsed_ms >= 8'000 && d.elapsed_ms < 9'000 &&
        d.wake.pump_epoch_at_start == d.wake.pump_epoch_at_end &&
        after.executor_started_requests == before.executor_started_requests &&
        after.executor_started_sequence == before.executor_started_sequence &&
        after.executed_requests == before.executed_requests;
  } else {
    ok = ok && probe.read_result && probe.output == native.frame && native.raw_reads.load() == 1 &&
        d.stage == build::FreshFullSnapshotStageV1::complete && d.fresh_available &&
        d.wait_result == api::MainThreadQueryWaitResultV1::completed &&
        d.reclaim_result == api::MainThreadQueryReclaimResultV1::reclaimed &&
        after.executor_started_requests == before.executor_started_requests + 1 &&
        after.executor_started_sequence == d.query_sequence &&
        after.executed_requests == before.executed_requests + 1;
    if (mode == FreshWakeMode::recover_second_wake)
      ok = ok && null_messages >= 2 && d.wake.wake_attempts >= 2 && d.elapsed_ms < 2'000;
    else
      ok = ok && d.wait_running_timeouts >= 1 && d.elapsed_ms >= 8'300;
  }
  if (mode != FreshWakeMode::wrong_build)
    ok = ok && d.submit_result == api::MainThreadQuerySubmitResultV1::submitted &&
        d.query_sequence == sequence_before + 1 && sequence_after == d.query_sequence &&
        after.published_sequence == d.query_sequence &&
        after.completed_sequence == d.query_sequence &&
        d.wake.wake_attempts == d.wake.wake_succeeded + d.wake.wake_failed;
  std::printf("%s\n", build::SerializeFreshFullSnapshotDiagnosticV1(d).c_str());
  if (!ok) std::fprintf(stderr, "fresh wake fixture mode=%d florin=%d messages=%u failed\n",
      static_cast<int>(mode), florin ? 1 : 0, null_messages);
  return ok;
}


enum class SnapshotWaitCase { cadence, original_epoch, replacement, owner_drift };

struct SnapshotWaitFixture {
  std::mutex mutex;
  std::condition_variable changed;
  build::WorkerAdapter *adapter = nullptr;
  bool read_requested = false;
  bool before_wait = false;
  bool after_wait = false;
  bool continue_after_wait = false;
  bool boundary_timeout = false;
  bool read_ok = false;
  game::Snapshot output{};

  static bool BeginWorkerRead(void *opaque) noexcept {
    auto &state = *static_cast<SnapshotWaitFixture *>(opaque);
    std::unique_lock lock(state.mutex);
    state.read_requested = true;
    state.changed.notify_all();
    return state.changed.wait_for(lock, std::chrono::seconds(2), [&] { return state.before_wait; });
  }

  static void ObserveWait(void *opaque, build::WorkerSnapshotWaitBoundary boundary,
      std::unique_lock<std::mutex> &cache) noexcept {
    auto &state = *static_cast<SnapshotWaitFixture *>(opaque);
    if (boundary == build::WorkerSnapshotWaitBoundary::before_wait) {
      std::lock_guard lock(state.mutex);
      state.before_wait = true;
      state.changed.notify_all();
      return;
    }
    cache.unlock();
    {
      std::unique_lock lock(state.mutex);
      state.after_wait = true;
      state.changed.notify_all();
      state.boundary_timeout = !state.changed.wait_for(lock, std::chrono::seconds(2),
          [&] { return state.continue_after_wait; });
    }
    cache.lock();
  }
};

bool TestWorkerSnapshotWait(SnapshotWaitCase mode, bool florin) {
  FixtureAdapter native;
  native.patch4 = true;
  native.florin_current_patch = florin;
  native.frame.paused = true;
  api::MainThreadQueryMailboxV1 mailbox{};
  SnapshotWaitFixture fixture{};
  std::jthread worker([&] {
    build::WorkerAdapter adapter(native, mailbox, build::ConsoleFixtureBindings{});
    build::BindWorkerSnapshotWaitObserver(&fixture, &SnapshotWaitFixture::ObserveWait);
    {
      std::unique_lock lock(fixture.mutex);
      fixture.adapter = &adapter;
      fixture.changed.notify_all();
      if (!fixture.changed.wait_for(lock, std::chrono::seconds(2),
            [&] { return fixture.read_requested; })) return;
    }
    fixture.read_ok = adapter.read_snapshot(fixture.output);
  });
  {
    std::unique_lock lock(fixture.mutex);
    CHECK(fixture.changed.wait_for(lock, std::chrono::seconds(2),
        [&] { return fixture.adapter != nullptr; }));
  }

  api::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 10;
  stamp.thread_id = GetCurrentThreadId();
  stamp.date_raw = native.frame.date_raw;
  stamp.paused = true;
  stamp.tls_initialized = 1;
  stamp.tls_main_thread_marker = 1;
  stamp.tls_context = 1;
  stamp.game_state = 2;
  stamp.jomini_state = 3;
  mailbox.iat_hook_installed.store(true);
  mailbox.active_hook_calls.store(1);
  mailbox.owner_verified_pump_epochs.store(api::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs);
  mailbox.paused_owner_verified_pump_epochs.store(api::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  const auto observe = [&] {
    mailbox.pump_epochs.store(stamp.pump_epoch);
    mailbox.owner_thread_id.store(stamp.thread_id);
    mailbox.observed_current_thread_id.store(stamp.thread_id);
    mailbox.observed_date_raw.store(stamp.date_raw);
    mailbox.observed_paused.store(stamp.paused);
    mailbox.observed_tls_initialized.store(stamp.tls_initialized);
    mailbox.observed_tls_main_thread_marker.store(stamp.tls_main_thread_marker);
    mailbox.observed_tls_context.store(stamp.tls_context);
    mailbox.observed_game_state.store(stamp.game_state);
    mailbox.observed_jomini_state.store(stamp.jomini_state);
    mailbox.observed_stamp_read_success.store(true);
    return fixture.adapter->Observe(stamp);
  };
  CHECK(observe() && native.raw_reads == 1);
  stamp.date_raw = ++native.frame.date_raw;
  ++stamp.pump_epoch;
  const auto expected = native.frame;
  native.raw_read_context = &fixture;
  native.raw_read_gate = &SnapshotWaitFixture::BeginWorkerRead;
  CHECK(observe());
  native.raw_read_gate = nullptr;
  {
    std::unique_lock lock(fixture.mutex);
    CHECK(fixture.changed.wait_for(lock, std::chrono::seconds(2),
        [&] { return fixture.after_wait; }));
  }
  CHECK(native.raw_reads == 2);
  if (mode != SnapshotWaitCase::original_epoch) {
    ++stamp.pump_epoch;
    if (mode == SnapshotWaitCase::replacement) stamp.date_raw = ++native.frame.date_raw;
    CHECK(observe());
    CHECK(native.raw_reads == (mode == SnapshotWaitCase::replacement ? 3U : 2U));
    if (mode == SnapshotWaitCase::owner_drift) mailbox.owner_thread_id.store(stamp.thread_id + 1);
  }
  {
    std::lock_guard lock(fixture.mutex);
    fixture.continue_after_wait = true;
    fixture.changed.notify_all();
  }
  worker.join();
  CHECK(fixture.before_wait && fixture.after_wait && !fixture.boundary_timeout);
  CHECK(native.wrong_owner == 0 && native.semantic_calls == 0);
  const bool should_read = mode == SnapshotWaitCase::cadence || mode == SnapshotWaitCase::original_epoch;
  if (fixture.read_ok != should_read) {
    std::fprintf(stderr, "worker wait publication mismatch: build=%s mode=%d expected=%d actual=%d\n",
        florin ? "1.21.0.3" : "1.20.0.4", static_cast<int>(mode), should_read, fixture.read_ok);
    return false;
  }
  CHECK(fixture.output == (should_read ? expected : game::Snapshot{}));
  return true;
}

struct FlorinExecutorSlotProbe {
  unsigned calls = 0;
  unsigned slot = 99;
  api::MainThreadExecutionStampV1 observed{};
};

template <unsigned Slot>
bool ExecuteFlorinSlotProbe(void *opaque,
    const api::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &probe = *static_cast<FlorinExecutorSlotProbe *>(opaque);
  ++probe.calls; probe.slot = Slot; probe.observed = stamp;
  return true;
}

bool TestFlorinSixExecutorSlots() {
  MemoryFixture memory;
  g_memory = &memory;
  memory.iat = reinterpret_cast<void *>(&FakePeek);
  memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
  memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
  Store(memory.tls, 0x20, std::uint8_t{1});
  Store(memory.jomini, 0x20, std::uint8_t{1});
  Store(memory.state, 0x08, std::int32_t{53'144'328});
  const std::array<api::MainThreadQueryExecutorV1, 6> executors{
      &ExecuteFlorinSlotProbe<0>, &ExecuteFlorinSlotProbe<1>, &ExecuteFlorinSlotProbe<2>,
      &ExecuteFlorinSlotProbe<3>, &ExecuteFlorinSlotProbe<4>, &ExecuteFlorinSlotProbe<5>};
  auto environment = xar::ck3_1210::BindThreadRuntimeImage(0x140000000ULL,
      xar::ck3_1210::kExecutableSha256, executors);
  CHECK(environment.exact_build_admitted && environment.permitted_executor == executors[0] &&
      environment.permitted_executor_secondary == executors[1] && environment.permitted_executor_tertiary == executors[2] &&
      environment.permitted_executor_quaternary == executors[3] && environment.permitted_executor_quinary == executors[4] &&
      environment.permitted_executor_senary == executors[5]);
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &memory.iat;
  environment.resolved_peek_message_override = &FakePeek;
  environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&memory.null_rng_slot);
  environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.jomini_slot);
  environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.state_slot);
  environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&memory.tls_initialized);
  environment.tls_context_getter_override = &FakeTls;
  environment.memory_protection_context = &memory;
  environment.memory_query_override = &FakeQuery;
  environment.memory_protect_override = &FakeProtect;
  environment.system_page_size_override = 4096;
  auto &mailbox = g_fresh_mailbox;
  CHECK(api::InstallMainThreadQueryMailboxV1(mailbox,environment));
  const auto owner = GetCurrentThreadId();
  const auto pump = [&] { return api::ObserveMainThreadPumpAndDrainV1(mailbox,
      xar::ck3_1210::kSdlWindowsPumpFirstPeekReturnRva, owner); };
  (void)pump(); (void)pump();
  const auto initial = api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  bool ok = initial.ready;
  for (unsigned slot = 0; ok && slot < executors.size(); ++slot) {
    FlorinExecutorSlotProbe probe{};
    api::MainThreadQueryTicketV1 ticket{};
    ok = api::TrySubmitMainThreadQueryV1(mailbox,executors[slot],&probe,ticket) == api::MainThreadQuerySubmitResultV1::submitted &&
        pump() && api::WaitForMainThreadQueryV1(mailbox,ticket,0) == api::MainThreadQueryWaitResultV1::completed &&
        probe.calls == 1 && probe.slot == slot && probe.observed.thread_id == owner &&
        probe.observed.pump_epoch != 0 && probe.observed.paused && probe.observed.date_raw == 53'144'328 &&
        api::ReclaimMainThreadQueryV1(mailbox,ticket) == api::MainThreadQueryReclaimResultV1::reclaimed;
  }
  const auto completed = api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  FlorinExecutorSlotProbe denied{}; api::MainThreadQueryTicketV1 denied_ticket{};
  ok = ok && completed.executed_requests == initial.executed_requests + executors.size() &&
      completed.executor_started_requests == initial.executor_started_requests + executors.size() &&
      api::TrySubmitMainThreadQueryV1(mailbox,&ExecuteFlorinSlotProbe<6>,&denied,denied_ticket) == api::MainThreadQuerySubmitResultV1::invalid_request &&
      denied.calls == 0 && denied_ticket.sequence == 0 && mailbox.failure_flags.load() == 0 &&
      mailbox.completed_sequence.load() == completed.completed_sequence;
  const auto detach = api::UninstallMainThreadQueryMailboxV1(mailbox,1000);
  ok = ok && detach == api::MainThreadQueryUninstallResultV1::uninstalled;
  if (ok) std::puts("PASS Florin exact six-slot binder -> installed mailbox -> six owner callbacks -> independent counters; seventh denied; no Game");
  return ok;
}

bool TestFlorinSevenExecutorSlots() {
  MemoryFixture memory;
  g_memory = &memory;
  memory.iat = reinterpret_cast<void *>(&FakePeek);
  memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
  memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
  Store(memory.tls, 0x20, std::uint8_t{1});
  Store(memory.jomini, 0x20, std::uint8_t{1});
  Store(memory.state, 0x08, std::int32_t{53'144'328});
  const std::array<api::MainThreadQueryExecutorV1, 7> executors{
      &ExecuteFlorinSlotProbe<0>, &ExecuteFlorinSlotProbe<1>, &ExecuteFlorinSlotProbe<2>,
      &ExecuteFlorinSlotProbe<3>, &ExecuteFlorinSlotProbe<4>, &ExecuteFlorinSlotProbe<5>, &ExecuteFlorinSlotProbe<6>};
  auto environment = xar::ck3_1210::BindThreadRuntimeImage(0x140000000ULL,
      xar::ck3_1210::kExecutableSha256, executors);
  CHECK(environment.exact_build_admitted && environment.permitted_executor == executors[0] &&
      environment.permitted_executor_secondary == executors[1] && environment.permitted_executor_tertiary == executors[2] &&
      environment.permitted_executor_quaternary == executors[3] && environment.permitted_executor_quinary == executors[4] &&
      environment.permitted_executor_senary == executors[5] && environment.permitted_executor_septenary == executors[6]);
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &memory.iat;
  environment.resolved_peek_message_override = &FakePeek;
  environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&memory.null_rng_slot);
  environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.jomini_slot);
  environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.state_slot);
  environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&memory.tls_initialized);
  environment.tls_context_getter_override = &FakeTls;
  environment.memory_protection_context = &memory;
  environment.memory_query_override = &FakeQuery;
  environment.memory_protect_override = &FakeProtect;
  environment.system_page_size_override = 4096;
  auto &mailbox = g_fresh_mailbox;
  CHECK(api::InstallMainThreadQueryMailboxV1(mailbox,environment));
  const auto owner = GetCurrentThreadId();
  const auto pump = [&] { return api::ObserveMainThreadPumpAndDrainV1(mailbox,
      xar::ck3_1210::kSdlWindowsPumpFirstPeekReturnRva, owner); };
  (void)pump(); (void)pump();
  const auto initial = api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  bool ok = initial.ready;
  for (unsigned slot = 0; ok && slot < executors.size(); ++slot) {
    FlorinExecutorSlotProbe probe{};
    api::MainThreadQueryTicketV1 ticket{};
    ok = api::TrySubmitMainThreadQueryV1(mailbox,executors[slot],&probe,ticket) == api::MainThreadQuerySubmitResultV1::submitted &&
        pump() && api::WaitForMainThreadQueryV1(mailbox,ticket,0) == api::MainThreadQueryWaitResultV1::completed &&
        probe.calls == 1 && probe.slot == slot && probe.observed.thread_id == owner &&
        probe.observed.pump_epoch != 0 && probe.observed.paused && probe.observed.date_raw == 53'144'328 &&
        api::ReclaimMainThreadQueryV1(mailbox,ticket) == api::MainThreadQueryReclaimResultV1::reclaimed;
  }
  const auto completed = api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  FlorinExecutorSlotProbe denied{}; api::MainThreadQueryTicketV1 denied_ticket{};
  ok = ok && completed.executed_requests == initial.executed_requests + executors.size() &&
      completed.executor_started_requests == initial.executor_started_requests + executors.size() &&
      api::TrySubmitMainThreadQueryV1(mailbox,&ExecuteFlorinSlotProbe<7>,&denied,denied_ticket) == api::MainThreadQuerySubmitResultV1::invalid_request &&
      denied.calls == 0 && denied_ticket.sequence == 0 && mailbox.failure_flags.load() == 0 &&
      mailbox.completed_sequence.load() == completed.completed_sequence;
  const auto detach = api::UninstallMainThreadQueryMailboxV1(mailbox,1000);
  ok = ok && detach == api::MainThreadQueryUninstallResultV1::uninstalled;
  if (ok) std::puts("PASS Florin exact seven-slot binder -> installed mailbox -> seven owner callbacks -> independent counters; eighth denied; no Game");
  return ok;
}

} // namespace

int main(int argc, char **argv) {
  if (argc == 2 && std::string_view(argv[1]) == "--worker-snapshot-wait") {
    bool passed = true;
    for (bool florin : {false, true}) {
      for (auto mode : {SnapshotWaitCase::cadence, SnapshotWaitCase::original_epoch,
                        SnapshotWaitCase::replacement, SnapshotWaitCase::owner_drift})
        passed = TestWorkerSnapshotWait(mode, florin) && passed;
    }
    if (!passed) return 1;
    std::puts("PASS: eight WorkerAdapter wait/publication cases across 1.20.0.4 and 1.21.0.3");
    return 0;
  }
  if(argc==2 && std::strcmp(argv[1],"--florin-seven-executor-only")==0)
    return TestFlorinSevenExecutorSlots()?0:1;
  if (argc == 2 && std::string_view(argv[1]) == "--florin-six-executor-only")
    return TestFlorinSixExecutorSlots() ? 0 : 1;
  if (argc == 2 && std::string_view(argv[1]) == "--no-pump-12004")
    return TestFreshOwnerWake(false, FreshWakeMode::no_pump) ? 0 : 1;
  if (argc == 2 && std::string_view(argv[1]) == "--no-pump-1210")
    return TestFreshOwnerWake(true, FreshWakeMode::no_pump) ? 0 : 1;
  if (argc == 2 && std::string_view(argv[1]) == "--running-context-1210")
    return TestFreshOwnerWake(true, FreshWakeMode::running_context) ? 0 : 1;
  return argc == 1 && TestFreshOwnerExecutor() && TestFreshOwnerExecutor(true) &&
      TestFreshOwnerExecutor(true, true) &&
      TestFreshOwnerWake(false, FreshWakeMode::recover_second_wake) &&
      TestFreshOwnerWake(true, FreshWakeMode::recover_second_wake) &&
      TestFreshOwnerWake(true, FreshWakeMode::wrong_build) && TestFlorinSixExecutorSlots() && TestFlorinSevenExecutorSlots() ? 0 : 1;
}

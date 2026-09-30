#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12002_thread_runtime.hpp"

#include <array>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <thread>
#include <vector>

namespace {
namespace api = xar::ck3_11906;
namespace build = xar::ck3_12002;
namespace game = xar::game;

#define CHECK(expression) do { if (!(expression)) { \
  std::fprintf(stderr, "semantic fixture line %d: %s\n", __LINE__, #expression); \
  return false; } } while (false)

template <class Value, std::size_t Size>
void Store(std::array<std::byte, Size> &bytes, std::size_t offset, Value value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct MemoryFixture {
  void *iat = nullptr;
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
  bool reader_available = true;
  bool declarations_available = true;

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
    static const game::AdapterDescriptor value{
      "ck3-1.20.0.2-msvc-x64", "1.20.0.2", build::kExecutableSha256,
      "fixture-only", {}};
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
    output = reader_available ? frame : game::Snapshot{};
    return reader_available;
  }
  game::PauseSubmitResult submit_pause_map() const noexcept override {
    queue_thread = GetCurrentThreadId();
    return game::PauseSubmitResult::submitted;
  }
  game::ResumeSubmitResult submit_resume_map() const noexcept override {
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
  UNAVAILABLE_RESULT(ReadWarTerminationOptionsResult, read_war_termination_options,
                     (std::int32_t, game::WarTerminationOptionsSnapshot &))
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

struct TypedRequest {
  build::QueryMailboxEnvelope envelope{};
  DWORD executed_thread = 0;
  std::uint32_t calls = 0;
};
bool ExecuteTyped(void *opaque,
                  const api::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &envelope = *static_cast<build::QueryMailboxEnvelope *>(opaque);
  if (!build::EnterQueryMailbox(envelope, stamp, &ExecuteTyped)) return false;
  auto &request = *static_cast<TypedRequest *>(envelope.typed_context);
  request.executed_thread = GetCurrentThreadId();
  ++request.calls;
  return build::FinishQueryMailbox(envelope);
}

void Pump(api::MainThreadQueryMailboxV1 &mailbox) {
  api::ObserveMainThreadPumpAndDrainV1(
      mailbox, build::kSdlWindowsPumpFirstPeekReturnRva, GetCurrentThreadId());
}

template <class Operation>
bool WorkerQuery(api::MainThreadQueryMailboxV1 &mailbox, Operation operation) {
  std::atomic<bool> done{false};
  bool succeeded = false;
  std::thread worker([&] { succeeded = operation(); done = true; });
  const auto deadline = GetTickCount64() + 10'000;
  bool drained = false;
  while (!done.load() && GetTickCount64() < deadline) {
    if (mailbox.state.load() == api::MainThreadQueryMailboxStateV1::queued) {
      Pump(mailbox);
      drained = true;
    }
    Sleep(1);
  }
  worker.join();
  return drained && succeeded;
}

template <class Operation>
bool WorkerOnly(Operation operation) {
  bool succeeded = false;
  std::thread worker([&] { succeeded = operation(); });
  worker.join();
  return succeeded;
}

bool TestWorkerAdapter() {
  FixtureAdapter native;
  MemoryFixture memory;
  g_memory = &memory;
  memory.iat = reinterpret_cast<void *>(&FakePeek);
  memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
  memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
  Store(memory.tls, 0x20, std::uint8_t{1});
  Store(memory.state, 0x08, native.frame.date_raw);
  api::MainThreadQueryMailboxV1 mailbox;
  build::WorkerAdapter proxy(native, mailbox);
  std::array<api::MainThreadQueryExecutorV1, 14> executors{};
  executors[12] = &ExecuteTyped;
  executors[13] = &build::ExecuteSemanticAdapter12002;
  auto environment = build::BindThreadRuntimeImage(
      0x140000000ULL, build::kExecutableSha256, executors);
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
  environment.snapshot_observer_callback = &build::ObserveAdapterSnapshot12002;
  environment.snapshot_observer_context = &proxy;
  CHECK(api::InstallMainThreadQueryMailboxV1(mailbox, environment));
  CHECK(&build::NativeAdapter12002(proxy) == &native);
  CHECK(&build::NativeAdapter12002(native) == &native);
  CHECK(WorkerOnly([&] { game::Snapshot output{}; output.date_raw = 99;
    return !proxy.read_snapshot(output) && output.date_raw == 0; }));
  CHECK(native.raw_reads == 0);

  // A running pump publishes the full native-owned frame. Worker reads it
  // repeatedly without consulting native memory or requiring a paused actor.
  Pump(mailbox);
  CHECK(native.raw_reads == 1);
  CHECK(WorkerOnly([&] {
    game::Snapshot output{};
    return proxy.read_snapshot(output) && output == native.frame && !output.paused;
  }));
  CHECK(native.raw_reads == 1);
  CHECK(WorkerOnly([&] { std::vector<game::DeclarableWarSnapshot> output;
    return !proxy.read_declarable_wars(output) && output.empty(); }));
  CHECK(native.semantic_calls == 0);
  CHECK(WorkerOnly([&] { return proxy.submit_pause_map() == game::PauseSubmitResult::submitted; }));
  CHECK(native.queue_thread != native.owner);
  CHECK(native.raw_reads == 1);

  // Deliver the queued pause in fixture-owned memory, then establish the
  // actor's two paused frames. The changed flag bypasses sample throttling.
  native.frame.paused = true;
  Store(memory.jomini, 0x20, std::uint8_t{1});
  Pump(mailbox);
  Pump(mailbox);
  CHECK(native.raw_reads >= 2);
  CHECK(api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready);
  const auto published_raw_reads = native.raw_reads.load();
  CHECK(WorkerOnly([&] { game::Snapshot output{};
    return proxy.read_snapshot(output) && output == native.frame && output.paused; }));
  CHECK(native.raw_reads == published_raw_reads);

  CHECK(WorkerQuery(mailbox, [&] {
    std::vector<game::DeclarableWarSnapshot> output;
    return proxy.read_declarable_wars(output) && output.size() == 1 &&
      output[0].target_character_id == 0x14000042 &&
      output[0].casus_belli_key == "fixture_claim" &&
      output[0].target_title_ids == std::vector<std::int32_t>{0x11000018, 0x12000019};
  }));
  CHECK(WorkerQuery(mailbox, [&] {
    return proxy.submit_select_event_option(2) == game::SelectEventOptionResult::submitted;
  }));
  CHECK(native.last_event_option == 2);
  CHECK(WorkerQuery(mailbox, [&] {
    return proxy.submit_select_event_option(8) == game::SelectEventOptionResult::option_out_of_range;
  }));
  CHECK(native.last_event_option == 8);
  CHECK(WorkerQuery(mailbox, [&] {
    return proxy.submit_move_army(0x23000031, 901) == game::MoveArmyResult::submitted;
  }));
  CHECK(native.last_army == 0x23000031 && native.last_province == 901);
  CHECK(WorkerQuery(mailbox, [&] {
    std::vector<game::ArmyStrengthSnapshot> output;
    return proxy.read_army_strengths(output) == game::ReadArmyStrengthsResult::available &&
      output.size() == 1 && output[0].current_soldiers == 734 && output[0].ai_base_power_raw == 123456789;
  }));
  CHECK(WorkerQuery(mailbox, [&] {
    std::vector<game::ArrangeMarriageChoice> output;
    game::ArrangeMarriageQueryDiagnostics diagnostics{};
    return proxy.read_arrange_marriage_choices(output, diagnostics) == game::ReadArrangeMarriageChoicesResult::available &&
      output.size() == 1 && output[0].candidate_character_id == 0x15000011 &&
      diagnostics.storage_capacity == 17 && diagnostics.native_validate_true == 1;
  }));
  CHECK(native.wrong_owner == 0);

  // Query-specific unavailability is a valid semantic result and does not
  // turn the shared mailbox into an infrastructure failure.
  native.declarations_available = false;
  CHECK(WorkerQuery(mailbox, [&] { std::vector<game::DeclarableWarSnapshot> output;
    return !proxy.read_declarable_wars(output) && output.empty(); }));
  CHECK(mailbox.failure_flags == 0);
  native.declarations_available = true;

  // Typed slot thirteen reads the native adapter directly. It coexists with
  // semantic slot fourteen, which has already processed seven requests.
  TypedRequest typed{};
  CHECK(WorkerQuery(mailbox, [&] {
    typed.envelope.game = &build::NativeAdapter12002(proxy);
    typed.envelope.mailbox = &mailbox;
    typed.envelope.typed_context = &typed;
    typed.envelope.expected_snapshot_revision = 1;
    if (!proxy.read_snapshot(typed.envelope.expected_snapshot) ||
        api::TrySubmitMainThreadQueryV1(mailbox, &ExecuteTyped,
            &typed.envelope, typed.envelope.ticket) != api::MainThreadQuerySubmitResultV1::submitted) return false;
    const auto wait = api::WaitForMainThreadQueryV1(mailbox, typed.envelope.ticket, 1000);
    const auto reclaim = api::ReclaimMainThreadQueryV1(mailbox, typed.envelope.ticket);
    return wait == api::MainThreadQueryWaitResultV1::completed &&
      reclaim == api::MainThreadQueryReclaimResultV1::reclaimed && typed.envelope.frame_stable;
  }));
  CHECK(typed.calls == 1 && typed.executed_thread == native.owner);
  CHECK(mailbox.executed_requests == 8 && mailbox.failure_flags == 0);
  CHECK(native.wrong_owner == 0);

  // A failed observation invalidates the worker cache and leaves typed
  // request infrastructure usable. Changing the date forces a fresh sample.
  native.reader_available = false;
  ++native.frame.date_raw;
  Store(memory.state, 0x08, native.frame.date_raw);
  Pump(mailbox);
  CHECK(WorkerOnly([&] { game::Snapshot output{}; return !proxy.read_snapshot(output); }));
  CHECK(mailbox.failure_flags == 0);
  native.reader_available = true;
  Pump(mailbox);
  Pump(mailbox);
  CHECK(WorkerQuery(mailbox, [&] { std::vector<game::DeclarableWarSnapshot> output;
    return proxy.read_declarable_wars(output) && output.size() == 1; }));
  CHECK(native.wrong_owner == 0 && mailbox.failure_flags == 0);

  CHECK(WorkerOnly([&] {
    return proxy.submit_set_speed(4) &&
      proxy.submit_save_checkpoint().status == game::SaveCheckpointStatus::submitted &&
      proxy.submit_resume_map() == game::ResumeSubmitResult::submitted;
  }));
  CHECK(native.queue_thread != native.owner);
  native.frame.paused = false;
  ++native.frame.date_raw;
  Store(memory.jomini, 0x20, std::uint8_t{0});
  Store(memory.state, 0x08, native.frame.date_raw);
  Pump(mailbox);
  CHECK(WorkerOnly([&] { game::Snapshot output{};
    return proxy.read_snapshot(output) && output == native.frame && !output.paused; }));
  CHECK(!api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready);
  CHECK(api::UninstallMainThreadQueryMailboxV1(mailbox, 0) == api::MainThreadQueryUninstallResultV1::uninstalled);
  CHECK(memory.iat == reinterpret_cast<void *>(&FakePeek) && memory.page_protect == PAGE_READONLY);
  return true;
}
} // namespace

int main() {
  if (!TestWorkerAdapter()) return 1;
  std::puts("PASS: owner-only raw snapshots, worker cache, queued pause/resume/save, seven semantic actor requests, typed actor coexistence, observation failure recovery; no live CK3 access");
  return 0;
}

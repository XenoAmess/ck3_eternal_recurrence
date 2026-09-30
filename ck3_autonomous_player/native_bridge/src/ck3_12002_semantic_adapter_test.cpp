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

enum class InboxMutation { world, none, player, date, paused };
struct FixtureInboxConsole {
  FixtureAdapter *adapter = nullptr;
  InboxMutation mutation = InboxMutation::world;
  bool accept = true;
  std::uint32_t calls = 0;
  std::uint32_t allocations = 0;
  std::uint32_t frees = 0;
  std::uint32_t wrong_owner = 0;
  std::uint32_t scope_enters = 0;
  std::uint32_t scope_exits = 0;
  DWORD random_owner = 0;
  void *random_wrapper = nullptr;
};
FixtureInboxConsole *g_inbox_console = nullptr;

build::ConsoleFixtureRandomScope *EnterInboxRandomScope(
    build::ConsoleFixtureRandomScope *scope, void *unused,
    const build::ConsoleFixtureSourceLocation *source) {
  auto &fixture = *g_inbox_console;
  if (GetCurrentThreadId() != fixture.adapter->owner || unused != nullptr ||
      source == nullptr || source->path == nullptr || source->function == nullptr ||
      source->line == 0 ||
      (fixture.random_owner != 0 && fixture.random_owner != fixture.adapter->owner))
    std::terminate();
  scope->owner_state = &fixture.random_owner;
  scope->owns_owner = fixture.random_owner == 0 ? 1 : 0;
  fixture.random_owner = fixture.adapter->owner;
  ++fixture.scope_enters;
  return scope;
}
void ExitInboxRandomScope(build::ConsoleFixtureRandomScope *scope) {
  auto &fixture = *g_inbox_console;
  if (GetCurrentThreadId() != fixture.adapter->owner ||
      scope->owner_state != &fixture.random_owner || fixture.random_wrapper != scope ||
      !scope->restore_slot || scope->previous_slot_target != &fixture.random_wrapper ||
      fixture.random_owner != fixture.adapter->owner ||
      fixture.frees != fixture.allocations) std::terminate();
  *scope->previous_slot_target = scope->previous_value;
  if (scope->owns_owner) fixture.random_owner = 0;
  ++fixture.scope_exits;
}

build::ConsoleFixtureNativeString *AssignInboxString(
    build::ConsoleFixtureNativeString *output, const char *input,
    std::uint64_t length) {
  if (length != 21 || std::string_view(input, length) !=
                          build::kPrivateFixtureInboxCommand ||
      output->size != 0 || output->capacity != 15) std::terminate();
  auto *heap = new char[32];
  std::memcpy(heap, input, length);
  heap[length] = '\0';
  std::memcpy(output->storage.data(), &heap, sizeof(heap));
  output->size = length;
  output->capacity = 31;
  ++g_inbox_console->allocations;
  return output;
}
void DestroyInboxString(build::ConsoleFixtureNativeString *command) {
  if (g_inbox_console->random_wrapper == nullptr ||
      g_inbox_console->random_owner != g_inbox_console->adapter->owner)
    std::terminate();
  if (command->capacity >= 16) {
    char *heap = nullptr;
    std::memcpy(&heap, command->storage.data(), sizeof(heap));
    delete[] heap;
    ++g_inbox_console->frees;
  }
  *command = {};
}
bool ExecuteInboxConsole(void *console,
                         const build::ConsoleFixtureNativeString *command) {
  if (console != g_inbox_console || command->size != 21 ||
      command->capacity != 31) std::terminate();
  const char *heap = nullptr;
  std::memcpy(&heap, command->storage.data(), sizeof(heap));
  if (std::string_view(heap, command->size) != build::kPrivateFixtureInboxCommand ||
      heap[command->size] != '\0') std::terminate();
  auto &fixture = *g_inbox_console;
  const auto *scope = static_cast<const build::ConsoleFixtureRandomScope *>(
      fixture.random_wrapper);
  if (scope == nullptr || scope->owner_state != &fixture.random_owner ||
      fixture.random_owner != fixture.adapter->owner || !scope->restore_slot)
    std::terminate();
  ++fixture.calls;
  if (GetCurrentThreadId() != fixture.adapter->owner) ++fixture.wrong_owner;
  if (!fixture.accept) return false;
  auto &frame = fixture.adapter->frame;
  switch (fixture.mutation) {
  case InboxMutation::world:
    frame.active_event_instance_id = 115;
    frame.active_event_option_count = 5;
    frame.played_character_spouse_ids.push_back(55);
    frame.player_armies.front().current_province_id = 902;
    frame.active_wars.front().player_relative_war_score = 20;
    break;
  case InboxMutation::player: ++frame.played_character_id; break;
  case InboxMutation::date: ++frame.date_raw; break;
  case InboxMutation::paused: frame.paused = false; break;
  case InboxMutation::none: break;
  }
  return true;
}

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
bool WorkerQuery(api::MainThreadQueryMailboxV1 &mailbox, Operation operation,
                 DWORD owner_pump_delay_ms = 0) {
  std::atomic<bool> done{false};
  bool succeeded = false;
  std::thread worker([&] { succeeded = operation(); done = true; });
  const auto deadline = GetTickCount64() + 10'000;
  bool drained = false;
  if (owner_pump_delay_ms != 0) {
    while (!done.load() &&
           mailbox.state.load() != api::MainThreadQueryMailboxStateV1::queued &&
           GetTickCount64() < deadline) Sleep(1);
    Sleep(owner_pump_delay_ms);
  }
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

template <class Operation, class Change>
bool WorkerQueryWithFrameChange(api::MainThreadQueryMailboxV1 &mailbox,
                               Operation operation, Change change) {
  std::atomic<bool> done{false};
  bool succeeded = false;
  std::thread worker([&] { succeeded = operation(); done = true; });
  const auto deadline = GetTickCount64() + 1000;
  while (!done.load() && GetTickCount64() < deadline &&
         mailbox.state.load() != api::MainThreadQueryMailboxStateV1::queued) Sleep(1);
  const bool queued = mailbox.state.load() == api::MainThreadQueryMailboxStateV1::queued;
  if (queued) {
    change();
    Pump(mailbox);
  }
  worker.join();
  return queued && succeeded;
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
  FixtureInboxConsole console{&native};
  g_inbox_console = &console;
  void *console_slot = &console;
  const build::ConsoleFixtureBindings console_bindings{
      true, &console_slot, &AssignInboxString, &DestroyInboxString,
      &ExecuteInboxConsole, &console.random_wrapper, &EnterInboxRandomScope,
      &ExitInboxRandomScope};
  build::WorkerAdapter proxy(native, mailbox, console_bindings);
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
  CHECK(WorkerOnly([&] { std::string output;
    return !proxy.run_inbox_fixture(output) && output.empty(); }));
  CHECK(console.calls == 0 && console.allocations == 0 &&
        console.scope_enters == 0 && console.scope_exits == 0);
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

  // The real 1.20 loading tail has stopped owner pumps longer than eight
  // seconds after its first valid map snapshot. Retain the queued request
  // across a nine-second owner pause, then execute and reclaim it normally.
  CHECK(WorkerQuery(mailbox, [&] {
    std::vector<game::DeclarableWarSnapshot> output;
    return proxy.read_declarable_wars(output) && output.size() == 1 &&
      output[0].target_character_id == 0x14000042 &&
      output[0].casus_belli_key == "fixture_claim" &&
      output[0].target_title_ids == std::vector<std::int32_t>{0x11000018, 0x12000019};
  }, 9'000));
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

  // attempt-06 observed only a same-date enemy pathfinder update between
  // the published frame and the owner query. War options do not use routes.
  game::ActiveWarSnapshot war{};
  war.war_id = 16777290;
  war.player_is_primary_war_leader = true;
  game::ArmySnapshot enemy{};
  enemy.army_id = 33554657;
  enemy.route_province_ids = {2579, 2589, 2591, 2602};
  enemy.move_target_observable = true;
  enemy.move_target_province_id = 2602;
  war.enemy_armies.push_back(enemy);
  native.frame.active_wars = {war};
  Sleep(251);
  Pump(mailbox);
  CHECK(WorkerQueryWithFrameChange(mailbox, [&] {
    game::WarTerminationOptionsSnapshot output{};
    return proxy.read_war_termination_options(war.war_id, output) ==
               game::ReadWarTerminationOptionsResult::available &&
           output.war_id == war.war_id && output.player_relative_war_score == 0;
  }, [&] {
    native.frame.active_wars.front().enemy_armies.front().route_province_ids = {2579, 2589};
    native.frame.active_wars.front().enemy_armies.front().move_target_province_id = 2589;
  }));
  CHECK(mailbox.failure_flags == 0 && native.wrong_owner == 0);

  // A changed war score remains part of the complete comparison. The stale
  // request stops before the native options reader and returns unavailable.
  Sleep(251);
  Pump(mailbox);
  auto semantic_calls_before_change = native.semantic_calls.load();
  CHECK(WorkerQueryWithFrameChange(mailbox, [&] {
    game::WarTerminationOptionsSnapshot output{};
    return proxy.read_war_termination_options(war.war_id, output) ==
               game::ReadWarTerminationOptionsResult::unavailable && output.war_id == -1;
  }, [&] { native.frame.active_wars.front().player_relative_war_score = 10; }));
  CHECK(native.semantic_calls == semantic_calls_before_change && mailbox.failure_flags == 0);

  // The relaxation applies to that read only. A write still uses the full
  // frame and does not reach the native command when an enemy route changes.
  Sleep(251);
  Pump(mailbox);
  semantic_calls_before_change = native.semantic_calls.load();
  CHECK(WorkerQueryWithFrameChange(mailbox, [&] {
    return proxy.submit_move_army(0x23000031, 901) == game::MoveArmyResult::unavailable;
  }, [&] {
    native.frame.active_wars.front().enemy_armies.front().route_province_ids.push_back(2604);
    native.frame.active_wars.front().enemy_armies.front().move_target_province_id = 2604;
  }));
  CHECK(native.semantic_calls == semantic_calls_before_change && mailbox.failure_flags == 0);
  Sleep(251);
  Pump(mailbox);

  // Query-specific unavailability is a valid semantic result and does not
  // turn the shared mailbox into an infrastructure failure.
  native.declarations_available = false;
  CHECK(WorkerQuery(mailbox, [&] { std::vector<game::DeclarableWarSnapshot> output;
    return !proxy.read_declarable_wars(output) && output.empty(); }));
  CHECK(mailbox.failure_flags == 0);
  native.declarations_available = true;

  // Typed slot thirteen reads the native adapter directly. It coexists with
  // semantic slot fourteen, which has already processed ten requests.
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
  CHECK(mailbox.executed_requests == 11 && mailbox.failure_flags == 0);
  CHECK(native.wrong_owner == 0);

  // The fixed inbox console command applies fixture effects immediately.
  // Only its Finish scope allows world changes; Enter still compares the
  // complete frame, and native text allocation is released on the owner.
  CHECK(WorkerQuery(mailbox, [&] {
    std::string output;
    const bool executed = proxy.run_inbox_fixture(output);
    if (executed) std::printf("fixture_inbox_json=%s\n", output.c_str());
    return executed && output ==
      "{\"query_status\":\"executed\",\"native_executed\":true,\"fixed_command\":\"run xar_mcp_inbox.txt\",\"marker_confirmed\":false}";
  }));
  CHECK(native.frame.active_event_instance_id == 115 &&
        native.frame.player_armies.front().current_province_id == 902 &&
        native.frame.active_wars.front().player_relative_war_score == 20 &&
        native.frame.played_character_spouse_ids == std::vector<std::int32_t>{55});
  CHECK(console.calls == 1 && console.allocations == 1 && console.frees == 1 &&
        console.wrong_owner == 0 && mailbox.failure_flags == 0 &&
        console.scope_enters == 1 && console.scope_exits == 1 &&
        console.random_owner == 0 && console.random_wrapper == nullptr);
  Sleep(251);
  Pump(mailbox);

  console.accept = false;
  CHECK(WorkerQuery(mailbox, [&] {
    std::string output;
    return !proxy.run_inbox_fixture(output) && output ==
      "{\"query_status\":\"command_rejected\",\"native_executed\":false,\"fixed_command\":\"run xar_mcp_inbox.txt\",\"marker_confirmed\":false}";
  }));
  CHECK(console.calls == 2 && console.allocations == 2 && console.frees == 2 &&
        console.scope_enters == 2 && console.scope_exits == 2 &&
        console.random_owner == 0 && console.random_wrapper == nullptr);
  console.accept = true;

  // A changed frame before execution still prevents the console call.
  CHECK(WorkerQueryWithFrameChange(mailbox, [&] {
    std::string output;
    return !proxy.run_inbox_fixture(output) && output.empty();
  }, [&] { ++native.frame.active_event_instance_id; }));
  CHECK(console.calls == 2 && console.allocations == 2 &&
        console.scope_enters == 2 && console.scope_exits == 2);
  Sleep(251);
  Pump(mailbox);

  const auto scope_frame = native.frame;
  for (auto mutation : {InboxMutation::player, InboxMutation::date, InboxMutation::paused}) {
    console.mutation = mutation;
    CHECK(WorkerQuery(mailbox, [&] {
      std::string output;
      return !proxy.run_inbox_fixture(output) && output.empty();
    }));
    native.frame = scope_frame;
    Sleep(251);
    Pump(mailbox);
  }
  CHECK(console.calls == 5 && console.allocations == 5 && console.frees == 5 &&
        console.wrong_owner == 0 && mailbox.failure_flags == 0 &&
        console.scope_enters == 5 && console.scope_exits == 5 &&
        console.random_owner == 0 && console.random_wrapper == nullptr);

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
  std::puts("PASS: owner-only raw snapshots, worker cache, nine-second queued owner delay, war-options route update, war-score rejection, unchanged write scope, fixed inbox owner execution/allocation/release/RNG owner-scope restoration/JSON/world mutation/player-date-paused scope, typed actor coexistence, observation failure recovery; no live CK3 access");
  return 0;
}

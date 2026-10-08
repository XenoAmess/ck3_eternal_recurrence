// SOURCE_NOTRUN. Reuse fixture-owned memory construction, never its old main.
#define main RetainedTerminalFixtureConstructionOnlyMain
#include "ck3_12004_sway_terminal_first.cpp"
#undef main
#include "xar_bridge/ck3_12004_sway_stop.hpp"
#include "xar_bridge/ck3_12002_nonwar_router.hpp"

namespace {
using actual4::SelectedEndSchemeCommand12004;
std::array<void *, 9> stop_vtable{};
std::uint32_t queue_calls = 0;
std::uint32_t queued_scheme = 0;
std::uint32_t queue_channel = 0;
int command_manager = 0;
void *DeleteStop(void *command, std::uint32_t) {
  delete static_cast<SelectedEndSchemeCommand12004 *>(command);
  return nullptr;
}
void **CloneStop(const void *source, void **storage) {
  *storage = new SelectedEndSchemeCommand12004(
      *static_cast<const SelectedEndSchemeCommand12004 *>(source));
  return storage;
}
bool QueueStop(void *manager, void **owned, std::uint32_t channel) {
  Check(manager == &command_manager && owned && *owned, "owning queue arguments");
  auto *command = static_cast<SelectedEndSchemeCommand12004 *>(*owned);
  ++queue_calls; queued_scheme = command->scheme_id; queue_channel = channel;
  delete command; *owned = nullptr;
  // The synthetic queue accepts ownership only. A later independently read
  // fixture row performs the simulated gameplay end, never this ACK.
  return true;
}
void PrepareFrame(FrameAdapter &adapter) {
  adapter.frame.date_raw = kDate; adapter.frame.paused = true;
  adapter.frame.speed = 1; adapter.frame.player_id = 0;
  adapter.frame.map_ready = true; adapter.frame.has_played_character = true;
  adapter.frame.played_character_id = kActor; adapter.frame.played_character_alive = true;
}
bool ExecuteStop(World &world, FrameAdapter &adapter,
                 actual4::SwayStopMailboxContext12004 &q) {
  MainThreadQueryMailboxV1 mailbox{};
  NonwarMailboxExecutorsV1 executors{};
  PopulateNonwarRouterExecutors12004(executors);
  Check(executors.sway_action == &actual4::ExecuteSelectedSwayStop12004 &&
        executors.sway_state == &ExecuteActiveSwayMailbox12002 &&
        executors.sway_completion == &actual4::ExecuteSwayTerminalMailbox12004,
        "dedicated actual4 action registration leaves readonly callbacks intact");
  MainThreadQueryInstallEnvironmentV1 environment{};
  RegisterNonwarMailboxExecutorsV1(environment, executors);
  mailbox.permitted_executor_octoquinquagintary = environment.permitted_executor_octoquinquagintary;
  mailbox.permitted_executor_quinquinquagintary = environment.permitted_executor_quinquinquagintary;
  mailbox.state = MainThreadQueryMailboxStateV1::idle;
  mailbox.executor_submission_enabled = true;
  mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.paused_owner_verified_pump_epochs = kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
  q.envelope.game = &adapter; q.envelope.mailbox = &mailbox;
  q.envelope.expected_snapshot = adapter.frame;
  q.envelope.expected_snapshot_revision = kRevision;
  q.envelope.typed_context = &q;
  Check(TrySubmitMainThreadQueryV1(mailbox, &actual4::ExecuteSelectedSwayStop12004,
      &q.envelope, q.envelope.ticket) == MainThreadQuerySubmitResultV1::submitted,
      "existing explicit ACTION slot admits only the selected Stop callback");
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 80; stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = reinterpret_cast<std::uintptr_t>(&world.tls_initialized);
  stamp.tls_initialized = 1;
  stamp.tls_context = reinterpret_cast<std::uintptr_t>(world.tls_context.data());
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = reinterpret_cast<std::uintptr_t>(world.jomini.data());
  stamp.game_state = reinterpret_cast<std::uintptr_t>(world.state.data());
  stamp.date_raw = kDate; stamp.paused = true;
  return actual4::ExecuteSelectedSwayStop12004(&q.envelope, stamp) &&
      q.completed && q.failure.empty() && q.envelope.frame_stable;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one unique output directory");
    const std::filesystem::path output{argv[1]};
    std::filesystem::create_directories(output);
    World world; FrameAdapter adapter; PrepareFrame(adapter);
    auto bindings = actual4::BindSwayStopImage12004(kBase, actual4::kExecutableSha256);
    Check(bindings.enabled && bindings.primary_vtable == kBase + 74902848 &&
          bindings.secondary_vtable == kBase + 74902400 &&
          actual4::kSwayStopCloneRva12004 == 43633056 &&
          actual4::kSwayStopExecuteRva12004 == 43631392,
          "Root actual paired642B profile precedes fixture-owned queue operands");
    stop_vtable[0] = reinterpret_cast<void *>(&DeleteStop);
    stop_vtable[8] = reinterpret_cast<void *>(&CloneStop);
    bindings.primary_vtable = reinterpret_cast<std::uintptr_t>(stop_vtable.data());
    bindings.terminal = world.bindings;
    bindings.commands.command_manager = &command_manager;
    bindings.commands.queue_owned_command = &QueueStop;
    SwayCompletionMailboxContextV1 current{};
    Check(Execute(world, adapter, current, 79) && current.result.available &&
          !current.result.native_terminal_state_observed && queue_calls == 0,
          "existing readonly query cannot queue selected Stop");
    Save(output, "current.json", current, adapter);
    auto request = actual4::SwayStopRequest12004{{kRevision, kActor, kTarget, kScheme}, 8, kDate};
    auto wrong = request; wrong.scheme_instance_generation = 9;
    SwayCompletionStateV1 rejected{};
    Check(actual4::SubmitSelectedSwayStop12004(bindings, wrong, rejected) ==
          CommandSubmitResult::rejected && queue_calls == 0,
          "wrong selected generation never queues another instance");
    actual4::SwayStopMailboxContext12004 q{};
    q.bindings = bindings; q.request = request; q.action_id = "stop-sway-native-first";
    Check(ExecuteStop(world, adapter, q) && q.result == CommandSubmitResult::submitted &&
          queue_calls == 1 && queued_scheme == kScheme && queue_channel == 14 &&
          q.before.native_status_raw == 0 && !q.before.native_terminal_state_observed,
          "one full-ID owning Stop remains pending");
    std::ofstream ack(output / "stop-ack.json", std::ios::binary);
    ack << actual4::SerializeSelectedSwayStop12004(q, "stop-ack.json", adapter.descriptor()) << '\n';
    Check(ack.good(), "whole new production pending ACK");
    SwayCompletionMailboxContextV1 pending{};
    Check(Execute(world, adapter, pending, 81) && pending.result.native_status_raw == 0 &&
          !pending.result.native_terminal_state_observed && queue_calls == 1,
          "independent query after ACK remains active without another Stop");
    Save(output, "pending.json", pending, adapter);
    Put(world.scheme.data(), 0x28, std::int32_t{1});
    Put(world.scheme.data(), 0x2C, std::uint32_t{0xFFFFFFFFu});
    SwayCompletionMailboxContextV1 terminal{};
    Check(Execute(world, adapter, terminal, 82) && terminal.result.native_terminal_state_observed &&
          terminal.result.exact_instance_join_ready && terminal.result.scheme_instance_generation == 8 &&
          !terminal.result.terminal_cause_observed && terminal.result.terminal_cause == "unknown" &&
          queue_calls == 1, "independent retained row establishes only unattributed end");
    Save(output, "terminated.json", terminal, adapter);
    Put(world.scheme.data(), 0x10, kScheme + 0x01000000u);
    SwayCompletionMailboxContextV1 reused{};
    Check(Execute(world, adapter, reused, 83) && reused.result.storage_slot_reused &&
          !reused.result.native_terminal_state_observed && queue_calls == 1,
          "reused index cannot end original full ID");
    Save(output, "reused.json", reused, adapter);
    Put(world.slots.data(), static_cast<std::size_t>(kIndex) * 0x10 + 8, static_cast<void *>(nullptr));
    SwayCompletionMailboxContextV1 purged{};
    Check(Execute(world, adapter, purged, 84) && !purged.result.instance_present &&
          !purged.result.native_terminal_state_observed && queue_calls == 1,
          "absence cannot stand in for observed end");
    Save(output, "purged.json", purged, adapter);
    std::ofstream manifest(output / "manifest.json", std::ios::binary);
    manifest << "{\"qualification\":\"offline synthetic new Stop FIRST, not live\","
        "\"queue_submissions\":1,\"queued_scheme\":134217986,\"queue_channel\":14,"
        "\"readonly_query_submissions\":0,\"terminal_cause\":\"unknown\","
        "\"action_slot\":58,\"state_slot\":55,\"producer\":\"ExecuteSelectedSwayStop12004\","
        "\"packets\":{\"stop_ack\":\"stop-ack.json\",\"current\":\"current.json\","
        "\"terminated\":\"terminated.json\",\"reused\":\"reused.json\",\"purged\":\"purged.json\"},"
        "\"native_packets\":[\"stop-ack.json\",\"current.json\",\"pending.json\","
        "\"terminated.json\",\"reused.json\",\"purged.json\"],\"compound_cases\":1}\n";
    Check(manifest.good(), "unique new producer manifest");
    std::cout << "PASS unique selected Sway Stop production producer compound\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}

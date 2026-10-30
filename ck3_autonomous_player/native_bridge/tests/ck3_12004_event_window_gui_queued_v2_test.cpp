#include "xar_bridge/ck3_12002_event_window_context_v2_mailbox.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include <array>
#include <atomic>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>

namespace game = xar::game;
namespace build = xar::ck3_12002;
namespace current = xar::ck3_12004;
namespace api = xar::ck3_11906;
namespace {
constexpr std::int32_t kCharacterId = 42, kEventId = 0x01000029;
constexpr std::uint64_t kRevision = 17;
unsigned checks = 0;
void Check(bool value, const char *why) { ++checks; if (!value) throw std::runtime_error(why); }
bool ReadOwnedPrefix(const build::EventWindowBindings &, game::Snapshot &out) noexcept {
  out = {}; out.date_raw = 741221; out.paused = true; out.map_ready = true;
  out.player_id = 0; out.has_played_character = true;
  out.played_character_id = kCharacterId; out.played_character_alive = true;
  out.has_active_event = true; out.active_event_instance_id = kEventId;
  return true;
}
class OwnedAdapter final : public game::GameAdapter {
public:
  DWORD owner_thread = GetCurrentThreadId();
  mutable unsigned snapshot_calls = 0, wrong_owner = 0;
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static constexpr std::array<std::string_view, 1> capabilities{"game.state.snapshot"};
    static const game::AdapterDescriptor descriptor{
        "ck3-1.20.0.4-msvc-x64", "1.20.0.4", current::kExecutableSha256,
        "owned-event-gui-request-dispatch-fixture", capabilities};
    return descriptor;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner_thread) { ++wrong_owner; return false; }
    ++snapshot_calls; build::EventWindowBindings unused{}; return ReadOwnedPrefix(unused, out);
  }
#define OFF(Type, Name, Args) game::Type Name Args const noexcept override { std::abort(); }
  OFF(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  OFF(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  bool submit_set_speed(std::int32_t) const noexcept override { std::abort(); }
  OFF(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  OFF(SaveCheckpointResult, submit_save_checkpoint, ())
  OFF(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  OFF(RaiseTroopsResult, submit_raise_troops_default, ())
  OFF(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  OFF(PreviewMoveArmyResult, preview_move_army, (std::int32_t, std::int32_t))
  OFF(DisbandArmyResult, submit_disband_army, (std::int32_t))
  OFF(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  OFF(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  OFF(StartAssaultResult, submit_start_assault, (std::int32_t))
  OFF(StopAssaultResult, submit_stop_assault, (std::int32_t))
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { std::abort(); }
  OFF(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  OFF(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  OFF(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  OFF(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  OFF(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  OFF(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  OFF(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  OFF(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  OFF(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  OFF(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  OFF(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
  OFF(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  OFF(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
#undef OFF
};
}
namespace {
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

}
namespace {
struct InstalledSlot {
  api::MainThreadQueryMailboxV1 &slot;
  bool installed = false;
  ~InstalledSlot() { if (installed) (void)api::UninstallMainThreadQueryMailboxV1(slot, 1000); }
};
}
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "fresh output root required");
    const auto out = std::filesystem::path(argv[1]) /
        ("run-" + std::to_string(GetCurrentProcessId()) + "-" + std::to_string(GetTickCount64()));
    Check(!std::filesystem::exists(out) && std::filesystem::create_directories(out), "fresh output required");
    OwnedAdapter game;
    MemoryFixture memory; g_memory = &memory;
    memory.iat = reinterpret_cast<void *>(&FakePeek);
    memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
    memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
    Store(memory.tls, 0x20, std::uint8_t{1});
    Store(memory.jomini, 0x20, std::uint8_t{1});
    Store(memory.state, 0x08, std::int32_t{741221});
    api::MainThreadQueryMailboxV1 slot;
    InstalledSlot cleanup{slot};
    std::array<api::MainThreadQueryExecutorV1, 14> no_legacy_executors{};
    auto environment = current::BindThreadRuntimeImage(
        0x140000000ULL, current::kExecutableSha256, no_legacy_executors);
    environment.permitted_executor_vigintary = &build::ExecuteEventWindowContextMailboxV2;
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
    Check(api::InstallMainThreadQueryMailboxV1(slot, environment), "owned slot install failed");
    cleanup.installed = true;
    const auto pump = [&] { return api::ObserveMainThreadPumpAndDrainV1(
        slot, current::kSdlWindowsPumpFirstPeekReturnRva, GetCurrentThreadId()); };
    (void)pump(); (void)pump();
    Check(api::ReadMainThreadQueryMailboxDiagnosticsV1(slot).ready, "owner pause proof not ready");
    build::QueryMailboxEnvelope envelope;
    envelope.game = &game; envelope.mailbox = &slot;
    envelope.expected_snapshot_revision = kRevision;
    build::EventWindowBindings unused{};
    Check(ReadOwnedPrefix(unused, envelope.expected_snapshot), "owned frame unavailable");
    bool typed_result = false;
    std::optional<bool> entered, typed, finished;
    game::EventWindowContextV1 presentation;
    game::EventWindowContextV2 gui;
    build::EventWindowMailboxContextV2 context{
        envelope, build::EventWindowMailboxKindV2::event_window, 0,
        build::EventWindowGuiRequestVersionV2::gui_v2, kEventId,
        typed_result, entered, typed, finished, presentation, gui};
    envelope.typed_context = &context;
    std::atomic<bool> published{false}, allow_wait{false}, barrier_failed{false}, done{false};
    auto submitted = api::MainThreadQuerySubmitResultV1::invalid_request;
    auto waited = api::MainThreadQueryWaitResultV1::ticket_mismatch;
    auto reclaimed = api::MainThreadQueryReclaimResultV1::not_terminal;
    api::MainThreadQueryMailboxDiagnosticsV1 completion{};
    std::jthread worker([&](std::stop_token stop) {
      submitted = api::TrySubmitMainThreadQueryV1(slot,
          &build::ExecuteEventWindowContextMailboxV2, &envelope, envelope.ticket);
      published.store(true, std::memory_order_release);
      if (submitted == api::MainThreadQuerySubmitResultV1::submitted) {
        const auto barrier_deadline = GetTickCount64() + 5000;
        while (!allow_wait.load(std::memory_order_acquire) &&
               !stop.stop_requested() && GetTickCount64() < barrier_deadline) SwitchToThread();
        if (allow_wait.load(std::memory_order_acquire) && !stop.stop_requested()) {
          waited = api::WaitForMainThreadQueryV1(slot, envelope.ticket, 1000);
          completion = api::ReadMainThreadQueryMailboxDiagnosticsV1(slot);
          reclaimed = api::ReclaimMainThreadQueryV1(slot, envelope.ticket);
        } else {
          // Do not clear non-atomic context while the owner may still inspect it.
          // The installed-slot guard owns cancellation/uninstall on this failure.
          barrier_failed.store(true, std::memory_order_release);
        }
      }
      done.store(true, std::memory_order_release);
    });
    const auto deadline = GetTickCount64() + 5000;
    while (!published.load(std::memory_order_acquire) && GetTickCount64() < deadline) SwitchToThread();
    Check(published.load(std::memory_order_acquire), "bounded publish deadline");
    Check(submitted == api::MainThreadQuerySubmitResultV1::submitted, "actual submit rejected");
    Check(envelope.ticket.sequence == 1 && slot.state.load() == api::MainThreadQueryMailboxStateV1::queued,
        "ticket was not actually queued");
    Check(slot.executor.load() == &build::ExecuteEventWindowContextMailboxV2 &&
        slot.executor_context == &envelope && envelope.typed_context == &context,
        "actual queued callback/context identity changed");
    Check(!barrier_failed.load(std::memory_order_acquire), "bounded owner identity barrier failed");
    allow_wait.store(true, std::memory_order_release);
    Check(pump(), "actual owner pump did not execute callback");
    while (!done.load(std::memory_order_acquire) && GetTickCount64() < deadline) SwitchToThread();
    Check(done.load(std::memory_order_acquire), "bounded completion deadline");
    worker.join();
    Check(waited == api::MainThreadQueryWaitResultV1::completed, "actual Wait did not observe completed");
    Check(completion.state == api::MainThreadQueryMailboxStateV1::completed &&
        completion.executed_requests == 1 && completion.executor_started_requests == 1 &&
        completion.executor_started_sequence == 1 && completion.failure_flags == 0,
        "actual completion diagnostics changed");
    Check(reclaimed == api::MainThreadQueryReclaimResultV1::reclaimed &&
        slot.state.load() == api::MainThreadQueryMailboxStateV1::idle &&
        slot.executor.load() == nullptr && slot.executor_context == nullptr,
        "actual Reclaim did not clear the owned lease");
    Check(entered == true && typed == true && finished == true && typed_result && envelope.frame_stable,
        "production callback did not Enter/read/Finish");
    Check(envelope.executor == &build::ExecuteEventWindowContextMailboxV2 &&
        envelope.execution_stamp.thread_id == game.owner_thread &&
        game.snapshot_calls == 2 && game.wrong_owner == 0,
        "callback did not preserve exact self/owner/full snapshots");
    Check(gui.presentation == presentation && presentation.status == game::EventWindowContextStatusV1::unavailable &&
        gui.gui_observations.empty(), "image0 did not yield a typed unavailable observation");
    const auto body = build::SerializeEventWindowContextV2(gui);
    Check(!body.empty() && body.find("current-event-window-context-v2") != std::string::npos &&
        body.find("\"schema_version\":2") != std::string::npos,
        "actual V2 serializer did not accept typed unavailable");
    std::ofstream file(out / "queued-v2-unavailable.inner-result.json", std::ios::binary); file << body;
    Check(file.good(), "body artifact write failed");
    Check(api::UninstallMainThreadQueryMailboxV1(slot, 1000) == api::MainThreadQueryUninstallResultV1::uninstalled,
        "owned slot uninstall failed");
    cleanup.installed = false;
    Check(memory.iat == reinterpret_cast<void *>(&FakePeek), "owned fake IAT not restored");
    std::cout << "{\"complete\":true,\"case\":\"queue-completed-typed-unavailable\",\"checks\":" << checks
        << ",\"ticket\":" << envelope.ticket.sequence
        << ",\"actual_submit_pump_wait_reclaim\":true,\"production_candidate_callback\":true,\"native_image_base\":0,"
        << "\"gui_available_credited\":false,\"complete_Bridge_dispatch_executed\":false,\"game_calls\":0,\"model_calls\":0}\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}

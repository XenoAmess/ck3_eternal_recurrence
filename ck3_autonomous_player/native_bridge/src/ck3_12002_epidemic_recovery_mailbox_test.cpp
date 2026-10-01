#include "xar_bridge/ck3_12002_epidemic_recovery_mailbox.hpp"
#include "xar_bridge/ck3_12002_thread_runtime.hpp"

// Reuse the frozen exact-layout fixture objects and callbacks. Its old main
// is compiled but never invoked: this target tests the new actual controller.
#define main FrozenRecoveryProviderFixtureMain
#include "ck3_12002_epidemic_recovery_test.cpp"
#undef main

#include <atomic>
#include <chrono>
#include <thread>

#if defined(XAR_EPIDEMIC_RECOVERY_MAILBOX_STANDALONE_NATIVE_ADAPTER)
namespace xar::ck3_12002 {
// This target supplies a bare adapter, the production unwrap's identity case.
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept {
  return adapter;
}
} // namespace xar::ck3_12002
#endif

namespace {
namespace game = xar::game;
class RecoveryAdapter final : public game::GameAdapter {
public:
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
                                   c::kExecutableSha256, "fixture", {}};
  game::Snapshot snapshot{};
  bool admitted = true;
  mutable std::atomic<int> snapshot_reads{0};
  RecoveryAdapter() {
    snapshot.date_raw = Fixture::date; snapshot.paused = true;
    snapshot.map_ready = true; snapshot.player_id = 7;
    snapshot.has_played_character = true; snapshot.played_character_alive = true;
    snapshot.played_character_id = Fixture::actor;
    snapshot.has_active_event = true; snapshot.active_event_instance_id = 73;
    snapshot.active_event_option_count = 2;
  }
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return admitted; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    ++snapshot_reads; out = snapshot; return true;
  }
#define UNAVAILABLE(Type, Method, Arguments) \
  game::Type Method Arguments const noexcept override { return game::Type::unavailable; }
  UNAVAILABLE(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  UNAVAILABLE(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  UNAVAILABLE(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  UNAVAILABLE(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
              (game::PendingInteractionReply))
  UNAVAILABLE(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  UNAVAILABLE(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE(StopAssaultResult, submit_stop_assault, (std::int32_t))
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
  UNAVAILABLE(ReadDeclarableWarsResult, read_declarable_wars_for_target,
              (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  UNAVAILABLE(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  UNAVAILABLE(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices,
              (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  UNAVAILABLE(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  UNAVAILABLE(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  UNAVAILABLE(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
              (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
              (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  UNAVAILABLE(ReadWarTerminationOptionsResult, read_war_termination_options,
              (std::int32_t, game::WarTerminationOptionsSnapshot &))
  UNAVAILABLE(ReadWarTerminationTermsResult, read_war_termination_terms,
              (std::int32_t, game::WarTerminationTermsSnapshot &))
  UNAVAILABLE(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
              (std::int32_t, game::WarTerminationExitTermsSnapshot &))
  UNAVAILABLE(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  UNAVAILABLE(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
#undef UNAVAILABLE
};

BOOL WINAPI PeekFixture(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
struct Protection { void **slot = nullptr; DWORD protection = PAGE_READONLY; };
bool QueryFixture(void *opaque, const void *address, MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &memory = *static_cast<Protection *>(opaque);
  if (address != memory.slot) return false;
  const auto page = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
  information = {}; information.BaseAddress = reinterpret_cast<void *>(page);
  information.AllocationBase = information.BaseAddress; information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = 4096; information.State = MEM_COMMIT;
  information.Protect = memory.protection; information.Type = MEM_IMAGE; return true;
}
bool ProtectFixture(void *opaque, void *, std::size_t size, DWORD protection, DWORD &before) noexcept {
  if (size != 4096) return false;
  auto &memory = *static_cast<Protection *>(opaque);
  before = memory.protection; memory.protection = protection; return true;
}
Bytes<0x28> tls{};
void *__fastcall TlsFixture() noexcept { return tls.data(); }

struct Runtime {
  old::MainThreadQueryMailboxV1 mailbox{};
  Bytes<0x18> rng{};
  std::uintptr_t rng_pointer = reinterpret_cast<std::uintptr_t>(rng.data());
  std::uintptr_t rng_wrapper = reinterpret_cast<std::uintptr_t>(&rng_pointer);
  std::uint8_t initialized = 1;
  void *iat = reinterpret_cast<void *>(&PeekFixture);
  Protection protection{&iat};
  bool Install(Fixture &material) {
    const auto thread = GetCurrentThreadId(); Put(rng, 0x10, thread); tls[0x20] = std::byte{1};
    auto env = c::BindThreadRuntimeImage(0x100000, c::kExecutableSha256);
    env.offline_fixture = true; env.executor_submission_enabled = true;
    env.permitted_executor_epidemic_recovery12002 = &c::ExecutePlayerEpidemicRecoveryMailbox12002;
    env.peek_message_iat_slot_override = &iat; env.resolved_peek_message_override = &PeekFixture;
    env.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    env.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&material.jomini_ptr);
    env.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&material.state_ptr);
    env.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&initialized);
    env.tls_context_getter_override = &TlsFixture;
    env.memory_protection_context = &protection; env.memory_query_override = &QueryFixture;
    env.memory_protect_override = &ProtectFixture; env.system_page_size_override = 4096;
    if (!old::InstallMainThreadQueryMailboxV1(mailbox, env)) return false;
    for (int i = 0; i < 3; ++i)
      old::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, thread);
    return old::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready &&
      mailbox.permitted_executor_epidemic_recovery12002 == &c::ExecutePlayerEpidemicRecoveryMailbox12002 &&
      iat == reinterpret_cast<void *>(&old::XarMainThreadPeekMessageWHookV1);
  }
};

struct Response { bool success = false; bool drained = false; std::string packet{}, failure{}; };
Response Invoke(RecoveryAdapter &adapter, Runtime &runtime, const r::Bindings &source,
                std::uint64_t revision, std::string_view step, std::string_view name) {
  Response out{}; std::atomic<bool> done{false};
  const auto payload = "{\"expected_revision\":" + std::to_string(revision) + "}";
  std::thread worker([&] {
    out.success = c::HandleEpidemicRecoveryPrivateBound12002(adapter, runtime.mailbox,
      adapter.snapshot, revision, step, payload, name, source, out.packet, out.failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (runtime.mailbox.state.load(std::memory_order_acquire) == old::MainThreadQueryMailboxStateV1::queued)
      out.drained = old::ObserveMainThreadPumpAndDrainV1(runtime.mailbox,
        runtime.mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join(); return out;
}
bool Good(const Response &response, const Runtime &runtime) {
  return response.success && response.drained && response.failure.empty() &&
    runtime.mailbox.state.load() == old::MainThreadQueryMailboxStateV1::idle &&
    response.packet.find("\"type\":\"command_result\",\"protocol_version\":1") != std::string::npos &&
    response.packet.find("\"accepted\":true") != std::string::npos &&
    response.packet.find("\"private_build\":true,\"read_only\":true,\"advertised\":false") != std::string::npos;
}
void Packet(const std::filesystem::path &directory, const char *name, const Response &response) {
  if (directory.empty()) return;
  std::ofstream stream(directory / name, std::ios::binary); stream << response.packet << '\n';
  if (!stream) throw std::runtime_error("caller packet output failed");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 3 || std::string_view(argv[1]) != "--output") return 2;
  const auto directory = std::filesystem::path(argv[2]); std::filesystem::create_directories(directory);
  Fixture material; const auto source = Bind(material); RecoveryAdapter adapter; Runtime runtime;
  if (!Check(c::IsEpidemicRecoveryPrivate12002("query-player-epidemic-recovery-v1") &&
      c::IsEpidemicRecoveryPrivate12002("query-player-epidemic-recovery-v1-title-67108866") &&
      !c::IsEpidemicRecoveryPrivate12002("query-player-epidemic-recovery-v1-extra"), "retained selector parser")) return 1;
  if (!Check(runtime.Install(material), "actual install copies named readonly executor")) return 1;
  const auto base = "query-player-epidemic-recovery-v1";
  auto out = Invoke(adapter, runtime, source, 88, base, "epidemic-recovery-pre88");
  if (!Check(Good(out, runtime) && material.getter_calls == 4 && adapter.snapshot_reads.load() == 2,
             "producer to real owner callback to actual provider and serializer")) return 1;
  Packet(directory, "pre88-two-counties.json", out);

  Put(material.context, 0x3C, std::int32_t{0}); material.minor[0] = true;
  material.tiny[0] = false; material.tiny[1] = true;
  adapter.snapshot.has_active_event = false; adapter.snapshot.active_event_instance_id = -1;
  adapter.snapshot.active_event_option_count = 0;
  out = Invoke(adapter, runtime, source, 89, "query-player-epidemic-recovery-v1-title-67108866",
               "epidemic-recovery-post89-a");
  if (!Check(Good(out, runtime) && material.getter_calls == 6, "same-day post explicit county A after list clear")) return 1;
  Packet(directory, "post89-county-a.json", out);
  out = Invoke(adapter, runtime, source, 89, "query-player-epidemic-recovery-v1-title-83886083",
               "epidemic-recovery-post89-b");
  if (!Check(Good(out, runtime) && material.getter_calls == 8, "same-day post explicit county B after list clear")) return 1;
  Packet(directory, "post89-county-b.json", out);

  std::string serialized, failure;
  const auto submitted = runtime.mailbox.next_sequence.load();
  if (!Check(!c::HandleEpidemicRecoveryPrivateBound12002(adapter, runtime.mailbox, adapter.snapshot,
      89, base, "{\"expected_revision\":89}", "no-current-event", source, serialized, failure) &&
      !failure.empty() && runtime.mailbox.next_sequence.load() == submitted,
      "list mode needs a current event; explicit post mode does not")) return 1;
  if (!Check(!c::HandleEpidemicRecoveryPrivateBound12002(adapter, runtime.mailbox, adapter.snapshot,
      89, "query-player-epidemic-recovery-v1-title-67108866", "{\"expected_revision\":88}",
      "stale-revision", source, serialized, failure) && runtime.mailbox.next_sequence.load() == submitted,
      "existing expected revision contract preserved")) return 1;
  adapter.admitted = false;
  if (!Check(!c::HandleEpidemicRecoveryPrivate12002(adapter, runtime.mailbox, adapter.snapshot,
      89, "query-player-epidemic-recovery-v1-title-67108866", "{\"expected_revision\":89}",
      "disabled-standard-caller", serialized, failure) && runtime.mailbox.next_sequence.load() == submitted,
      "standard real-image caller rejects unavailable adapter before submit")) return 1;
  adapter.admitted = true;

  adapter.snapshot.has_active_event = true; adapter.snapshot.active_event_instance_id = 74;
  out = Invoke(adapter, runtime, source, 90, base, "epidemic-recovery-empty");
  if (!Check(Good(out, runtime) && out.packet.find("\"counties\":[]") != std::string::npos &&
      material.getter_calls == 8, "actual empty collection stays known empty in full packet")) return 1;
  Packet(directory, "empty-list.json", out);
  material.context_fails = true;
  out = Invoke(adapter, runtime, source, 90, base, "epidemic-recovery-unavailable");
  if (!Check(Good(out, runtime) && out.packet.find("\"counties\":null") != std::string::npos &&
      out.packet.find("variable_list_unavailable") != std::string::npos,
      "actual native failure stays typed unavailable in full packet")) return 1;
  Packet(directory, "list-unavailable.json", out); material.context_fails = false;
  runtime.mailbox.permitted_executor_epidemic_recovery12002 = nullptr;
  out = Invoke(adapter, runtime, source, 90, base, "epidemic-recovery-not-registered");
  if (!Check(!out.success && !out.drained && out.packet.empty() && !out.failure.empty(),
      "actual unregistered named callback cannot submit")) return 1;
  runtime.mailbox.permitted_executor_epidemic_recovery12002 = &c::ExecutePlayerEpidemicRecoveryMailbox12002;
  if (!Check(runtime.mailbox.executed_requests.load() == 5 &&
      runtime.mailbox.executor_started_requests.load() == 5 && material.getter_calls == 8,
      "five actual owner executions; only material getters for nonempty counties")) return 1;
  if (!Check(old::UninstallMainThreadQueryMailboxV1(runtime.mailbox, 0) ==
      old::MainThreadQueryUninstallResultV1::uninstalled &&
      runtime.iat == reinterpret_cast<void *>(&PeekFixture), "actual fixture IAT uninstall restores own slot")) return 1;
  std::cout << "PASS checks=" << checks << " producer=true owner_callback=true actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

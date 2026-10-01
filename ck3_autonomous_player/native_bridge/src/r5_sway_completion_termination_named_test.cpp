// Use the actual typed-slot source fixture without running its prior matrix.
#define main TerminationPreviousFixtureMainNotExecuted
#include "ck3_12002_sway_completion_termination_test.cpp"
#undef main

#include "xar_bridge/ck3_12002_sway_completion_termination_mailbox.hpp"

namespace {
namespace api = xar::ck3_11906;
namespace game = xar::game;
class TerminationNamedFrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
        kExecutableSha256, "offline-sway-termination-named", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) game::Result Name Params const noexcept override { return game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

void *queue_tls_context = nullptr;
void *__fastcall QueueTls() noexcept { return queue_tls_context; }
BOOL WINAPI QueuePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
struct Protection {
  void **slot = nullptr;
  DWORD current = PAGE_READONLY;
};
bool MemoryQuery(void *opaque, const void *address,
                 MEMORY_BASIC_INFORMATION &info) noexcept {
  auto &memory = *static_cast<Protection *>(opaque);
  if (address != memory.slot) return false;
  const auto start = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
  info = {};
  info.BaseAddress = reinterpret_cast<void *>(start);
  info.AllocationBase = info.BaseAddress;
  info.AllocationProtect = PAGE_READONLY;
  info.RegionSize = 4096;
  info.State = MEM_COMMIT;
  info.Protect = memory.current;
  info.Type = MEM_IMAGE;
  return true;
}
bool MemoryProtect(void *opaque, void *, std::size_t size,
                   DWORD protection, DWORD &previous) noexcept {
  auto &memory = *static_cast<Protection *>(opaque);
  if (size != 4096) return false;
  previous = memory.current;
  memory.current = protection;
  return true;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "termination named queue artifact directory");
    const std::filesystem::path output{argv[1]};
    TerminationFixture fixture;
    Check(fixture.Install() && fixture.recorder.ObserverAttached(),
          "actual typed-slot installation attaches the source recorder");
    fixture.RunSource(0);
    Check(fixture.original_calls == std::array<std::size_t, 3>{1, 0, 0} &&
          fixture.original_arguments_match,
          "typed source original executes once with unchanged command input");
    Put(fixture.jomini.data(), 0x20, std::uint8_t{1});
    TerminationNamedFrameAdapter adapter;
    adapter.frame.date_raw = 53220000;
    adapter.frame.paused = true;
    adapter.frame.speed = 1;
    adapter.frame.player_id = 0;
    adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true;
    adapter.frame.played_character_id = actor;
    adapter.frame.played_character_alive = true;
    std::array<std::byte, 0x28> tls{};
    tls[0x20] = std::byte{1};
    queue_tls_context = tls.data();
    std::uint8_t tls_initialized = 1;
    std::uintptr_t unused_rng = 0;
    void *peek_slot = reinterpret_cast<void *>(&QueuePeek);
    Protection protection{&peek_slot};
    api::MainThreadQueryBuildProfileV1 fixture_profile{};
    fixture_profile.pump_exact_return_rva = 0x12002;
    api::MainThreadQueryInstallEnvironmentV1 environment{};
    environment.module_base = base;
    environment.exact_build_admitted = true;
    environment.offline_fixture = true;
    environment.peek_message_iat_slot_override = &peek_slot;
    environment.resolved_peek_message_override = &QueuePeek;
    environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&unused_rng);
    environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&fixture.jomini_pointer);
    environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&fixture.core_pointer);
    environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&tls_initialized);
    environment.tls_context_getter_override = &QueueTls;
    environment.memory_protection_context = &protection;
    environment.memory_query_override = &MemoryQuery;
    environment.memory_protect_override = &MemoryProtect;
    environment.system_page_size_override = 4096;
    environment.executor_submission_enabled = true;
    environment.build_profile = &fixture_profile;
    environment.permitted_executor_sway_completion_termination12002 =
        &ExecuteSwayCompletionTerminationMailboxV1;
    api::MainThreadQueryMailboxV1 mailbox;
    Check(api::InstallMainThreadQueryMailboxV1(mailbox, environment),
          "production queue Install admits the new termination callback");
    Check(mailbox.permitted_executor_sway_completion_termination12002 ==
              &ExecuteSwayCompletionTerminationMailboxV1 &&
          mailbox.permitted_executor_sway_completion12002 == nullptr &&
          mailbox.permitted_executor_sway_completion_execution12002 == nullptr &&
          mailbox.permitted_executor == nullptr,
          "Install copies only the exact named termination permit");
    for (int pump = 0; pump < 2; ++pump)
      (void)api::ObserveMainThreadPumpAndDrainV1(
          mailbox, fixture_profile.pump_exact_return_rva, GetCurrentThreadId());
    Check(api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready,
          "two actual paused owner pumps qualify termination query admission");

    SwayCompletionTerminationMailboxContextV1 query{};
    query.envelope.game = &adapter;
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 7;
    query.envelope.typed_context = &query;
    query.request = fixture.Query();
    query.recorder = &fixture.recorder;
    Check(api::TrySubmitMainThreadQueryV1(
              mailbox, &ExecuteSwayCompletionTerminationMailboxV1,
              &query.envelope, query.envelope.ticket) ==
              api::MainThreadQuerySubmitResultV1::submitted,
          "production TrySubmit admits the named termination callback");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::queued,
          "actual queued state precedes termination executor");
    Check(api::ObserveMainThreadPumpAndDrainV1(
              mailbox, fixture_profile.pump_exact_return_rva, GetCurrentThreadId()),
          "owner pump drains the exact termination query callback");
    Check(api::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 100) ==
              api::MainThreadQueryWaitResultV1::completed,
          "actual Wait sees the completed named query");
    Check(query.completed && query.envelope.frame_stable && query.failure.empty() &&
          query.result.available && query.result.observer_attached &&
          query.result.records.size() == 1 && query.result.records[0].sequence == 1 &&
          query.result.records[0].source.source_class ==
              SwayTerminationSourceClass12002::end_scheme_command_execute &&
          query.result.records[0].source.actor_character_id == actor &&
          query.result.records[0].source.target_character_id == target &&
          query.result.records[0].source.scheme_id == scheme &&
          query.result.records[0].source.pre_status == 0 &&
          query.result.records[0].source.post_status == 1 &&
          query.result.records[0].source.native_terminal_state_observed &&
          query.result.records[0].source.native_terminal_transition_observed,
          "actual named query reads the copied typed-original 0-to-1 terminal transition");
    Check(api::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket) ==
              api::MainThreadQueryReclaimResultV1::reclaimed &&
          mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
          "actual completed termination query ticket reclaimed to idle");
    const auto wire = SerializeSwayCompletionTerminationCommandResultV1(
        query.result, query.envelope.expected_snapshot_revision,
        query.envelope.execution_stamp.date_raw, "termination-named-queue");
    Check(!wire.empty(), "full production terminal command_result emitted after actual named drain");
    std::ofstream file(output / "named-terminal-command-result.json");
    file << wire << '\n';
    Check(file.good(), "actual named terminal command_result saved for SDK");
    Check(api::UninstallMainThreadQueryMailboxV1(mailbox, 100) ==
              api::MainThreadQueryUninstallResultV1::uninstalled,
          "fixture named queue released through production Uninstall");
    Check(UninstallSwayCompletionTermination12002(fixture.installation),
          "actual fixture typed-slot observer is uninstalled");
    queue_tls_context = nullptr;
    std::cout << "PASS " << checks << " checks; actual typed source original 0-to-1 capture, "
                 "named termination env/runtime Install, two paused owner pumps, "
                 "TrySubmit/drain/Wait/Reclaim, full terminal command_result and Uninstall; no CK3\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}

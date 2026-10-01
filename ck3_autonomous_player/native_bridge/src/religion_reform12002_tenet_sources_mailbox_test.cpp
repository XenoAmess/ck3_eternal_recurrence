// Reuse the frozen actual-layout backing. Its eight-case main is never run.
#define main FrozenTenetSourcesProviderMainNotExecuted
#include "religion_reform12002_tenet_sources_test.cpp"
#undef main
#include "xar_bridge/religion_reform12002_tenet_sources_mailbox.hpp"

#include <atomic>
#include <chrono>
#include <memory>
#include <stdexcept>
#include <thread>
#include <windows.h>

namespace api = xar::ck3_11906;
namespace game = xar::game;
namespace {
int mailbox_checks{};
void Require(bool ok, const char *label) {
  ++mailbox_checks;
  if (!ok) throw std::runtime_error(label);
}

// This adapter supplies only the published semantic frame. The actual Tenet
// provider and its native key copier assemble the observation from Fixture.
class TenetFrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads{};
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      c::kExecutableSha256, "tenet-sources-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    ++reads; out = frame; return true;
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

void *tenet_tls_context{};
void *__fastcall TenetFixtureTls() noexcept { return tenet_tls_context; }
struct TenetPump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng{};
  TenetPump(Fixture &backing, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tenet_tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&backing.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&backing.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &TenetFixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor = &c::ExecutePlayerReligionDraftTenetChoicesMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~TenetPump() { tenet_tls_context = nullptr; }
};
} // namespace

namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    auto backing = std::make_unique<Fixture>();
    TenetFrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = static_cast<std::int32_t>(Fixture::actor_id);
    adapter.frame.date_raw = 53175816;
    api::MainThreadQueryMailboxV1 mailbox{};
    TenetPump pump(*backing, mailbox);
    c::PlayerReligionDraftTenetChoicesMailboxContext12002 query{};
    query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 701;
    query.bindings = Bind(*backing);
    std::atomic<bool> done{false};
    bool result = false, drained = false;
    std::string serialized, failure;
    std::thread worker([&] {
      result = c::RunPlayerReligionDraftTenetChoicesMailbox12002(
          query, "draft-tenets\"mailbox-fixture", serialized, failure);
      done.store(true, std::memory_order_release);
    });
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
    while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
      if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
        drained = api::ObserveMainThreadPumpAndDrainV1(
            mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    worker.join();
    Require(drained, "actual Tenet callback drained on fixture owning thread");
    Require(mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
        "actual Tenet terminal ticket reclaimed");
    Require(result && query.completed && query.envelope.frame_stable && failure.empty() &&
        !serialized.empty() && adapter.reads == 2,
        "actual provider / Finish / complete caller wire");
    const auto &out = query.observation;
    Require(out.capture_epoch == query.envelope.execution_stamp.pump_epoch && out.capture_epoch != 701 &&
        query.envelope.execution_stamp.thread_id == adapter.owner,
        "actual owner epoch and thread stamp");
    Require(out.available && out.draft_observed && out.tenet_gates_complete &&
        out.sources.size() == 8 && out.slots.size() == 2 && out.slots[0].slot_index == 7 &&
        out.slots[1].slot_index == 11 && out.source_faith_id == Fixture::source_faith_id &&
        out.source_main_rite_id == Fixture::main_id && backing->correct_native_inputs &&
        backing->filter_calls == 8,
        "actual source/category/main-Rite/actor-Faith/TopScope inputs survive owned queue");
    Require(out.sources[0].duplicate_excluded && !out.sources[0].final_selectable &&
        out.sources[0].native_can_pick && out.sources[3].native_status_raw == 0 &&
        out.sources[3].knowledge && out.sources[3].final_selectable &&
        out.sources[4].source_can_materialize && !out.sources[4].native_can_pick &&
        !out.sources[2].final_selectable && !out.sources[6].passed_shown && out.sources[7].final_selectable,
        "actual eight-source filter and final native gates remain distinct");
    std::ofstream(directory / "actual-multiple-sources.json") << serialized << '\n';
    std::cout << "PASS checks=" << mailbox_checks << " cases=1 actual_tenet_sources_provider=true "
        "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
        "frozen_provider_main_invoked=false dedicated_production_registration_tested=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}

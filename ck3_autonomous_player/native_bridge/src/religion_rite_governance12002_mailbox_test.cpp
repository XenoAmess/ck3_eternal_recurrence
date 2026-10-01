#define XAR_RITE_GOVERNANCE_FIXTURE_ONLY 1
#include "religion_rite_governance12002_context_test.cpp"
#include "xar_bridge/religion_rite_governance12002_mailbox.hpp"

#include <atomic>
#include <chrono>
#include <thread>

#if defined(XAR_RITE_GOVERNANCE_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif

namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
class FrameAdapter final : public game::GameAdapter {
public:
  const DWORD owner = GetCurrentThreadId();
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      c::kExecutableSha256, "rite-governance-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    c::CoreSnapshotPrefix core{};
    if (!c::ReadCoreSnapshot(Core(), core)) return false;
    out = {};
    out.paused = core.clock.paused; out.date_raw = core.clock.date_raw; out.speed = core.clock.speed;
    out.player_id = core.local_player_id; out.map_ready = core.map_ready;
    out.has_played_character = core.has_played_character;
    out.played_character_id = core.played_character_id;
    out.played_character_alive = core.played_character_alive;
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

void *tls_context = nullptr;
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng = 0;
  Pump(GovernanceFixture &value, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&value.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&value.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    // The existing primary offline permit proves the runtime envelope contract.
    // Dedicated production registration is a separate central integration step.
    mailbox.permitted_executor = &c::ExecutePlayerRiteGovernanceMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(GovernanceFixture &value, const g::Bindings &bindings, FrameAdapter &adapter,
           const std::filesystem::path &directory, const char *filename, g::Context &observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(value, mailbox);
  c::PlayerRiteGovernanceMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  Check(adapter.read_snapshot(query.envelope.expected_snapshot), "actual fixture core published frame");
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = bindings;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerRiteGovernanceMailbox12002(query, "governance\"worker-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained, "actual worker executor drained on fixture owner");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual Wait/Reclaim returns mailbox idle");
  observed = query.observation;
  if (result) {
    Check(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(),
          "actual native wrapper ready for serialization");
    Check(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          query.observation.capture_epoch != query.envelope.expected_snapshot_revision,
          "owner capture epoch is distinct from published revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else {
    Check(serialized.empty() && !failure.empty(), "changed owner frame emits no success response");
    std::ofstream(directory / "frame-changed-rejection.json") <<
        "{\"success_wire_emitted\":false,\"mailbox_reclaimed\":true,\"failure\":\"" << failure << "\"}\n";
  }
  return result;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    GovernanceFixture value; auto bindings = Bind(value); FrameAdapter adapter; g::Context observed{};
    Check(Query(value, bindings, adapter, directory, "distinct-zero.json", observed), "actual worker complete distinct observations");
    CheckDistinct(observed);
    LegalAbsence(value);
    Check(Query(value, bindings, adapter, directory, "legal-absent.json", observed), "actual worker legal absence");
    CheckAbsence(observed);
    Put(value.actor, r::kCharacterRiteIdOffset, std::uint32_t{0});
    Put(value.realm_title, s::kTitleStateRiteIdOffset, GovernanceFixture::realm_rite_id);
    value.bad_head_return = true;
    Check(Query(value, bindings, adapter, directory, "heads-unavailable.json", observed), "actual worker partial component failure");
    CheckPartial(observed);
    bindings.state_rite.enabled = bindings.heads.enabled = bindings.organization.enabled = false;
    Check(Query(value, bindings, adapter, directory, "components-unavailable.json", observed) &&
          !observed.available && observed.frame_available && observed.failure == g::Failure::components_unavailable,
          "actual unavailable wrapper retains observed published frame");
    bindings = Bind(value); value.bad_head_return = false; value.change_frame_on_count = true;
    Check(!Query(value, bindings, adapter, directory, "frame-changed.json", observed),
          "actual native core changes during capture so no success wire");
    value.change_frame_on_count = false; Put(value.state, 8, GovernanceFixture::date);
    std::uint64_t revision = 0;
    Check(c::ParsePlayerRiteGovernanceRevision12002("{}", revision) && revision == 0, "optional expected revision");
    Check(c::ParsePlayerRiteGovernanceRevision12002("{\"expected_revision\":701}", revision) && revision == 701,
          "actual revision alias parser");
    Check(!c::ParsePlayerRiteGovernanceRevision12002(
          "{\"expected_snapshot_revision\":701,\"expected_revision\":702}", revision), "conflicting aliases rejected");
    api::MainThreadQueryMailboxV1 mailbox{};
    game::Snapshot published{}; Check(adapter.read_snapshot(published), "restored actual published frame");
    std::string wire, failure;
    Check(!c::HandlePlayerRiteGovernancePrivate12002(adapter, mailbox, published, 701,
          c::kPlayerRiteGovernancePrivateStep12002, "{\"expected_revision\":702}", "stale", wire, failure) &&
          wire.empty() && failure == "player_rite_governance_current_frame_unavailable" && mailbox.next_sequence == 0,
          "actual handler rejects stale request before mailbox submission");
    Check(c::IsPlayerRiteGovernancePrivateStep12002(c::kPlayerRiteGovernancePrivateStep12002) &&
          !c::IsPlayerRiteGovernancePrivateStep12002("query-player-rite-governance-v1-other"), "exact governance selector");
    std::cout << "PASS checks=" << checks << " cases=6 actual_combined_provider=true actual_mailbox_submit_drain_wait_reclaim=true actual_wrapper=true dedicated_registration=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}

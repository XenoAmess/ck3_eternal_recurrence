// Reuse the frozen owned-memory fixture. Its renamed standalone entry point is
// never invoked: this file only runs the new worker/owner transport cases.
#define main FrozenMemberProviderFixtureEntry12002
#include "religion_rite_governance12002_organization_members_test.cpp"
#undef main
#include "xar_bridge/religion_rite_governance12002_members_mailbox.hpp"

#include <atomic>
#include <chrono>
#include <stdexcept>
#include <thread>

#if defined(XAR_RITE_MEMBERS_MAILBOX_STANDALONE_ADAPTER)
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
#endif

namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
void Require(bool condition, const char *message) {
  if (!Check(condition, message)) throw std::runtime_error(message);
}
DWORD collector_owner = 0;
bool collector_wrong_thread = false;
void OwnedFaithCollector(void *self, m::ScopeArray *out, const m::ScopeRoot *root) {
  collector_wrong_thread |= GetCurrentThreadId() != collector_owner;
  FaithCollector(self, out, root);
}
void OwnedCountyCollector(void *self, m::ScopeArray *out, const m::ScopeRoot *root) {
  collector_wrong_thread |= GetCurrentThreadId() != collector_owner;
  CountyCollector(self, out, root);
}
class FrameAdapter final : public game::GameAdapter {
public:
  const DWORD owner = GetCurrentThreadId();
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      c::kExecutableSha256, "rite-members-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    c::CoreSnapshotPrefix core{};
    const auto bindings = c::CoreBindings{true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
    if (!c::ReadCoreSnapshot(bindings, core)) return false;
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
  Pump(Fixture &value, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&value.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&value.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    // Existing primary offline permit. The named production member permit is
    // registered by the central integration owner, outside this leaf package.
    mailbox.permitted_executor = &c::ExecutePlayerRiteMembersMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &value, const m::Bindings &bindings, FrameAdapter &adapter,
           const std::filesystem::path &directory, const char *filename, m::Snapshot &observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(value, mailbox);
  c::PlayerRiteMembersMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  Require(adapter.read_snapshot(query.envelope.expected_snapshot), "actual published core frame");
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = bindings;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerRiteMembersMailbox12002(query, "members\"worker-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Require(drained && !collector_wrong_thread, "actual worker drains collectors on owner");
  Require(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual Wait/Reclaim returns mailbox idle");
  observed = query.observation;
  if (result) {
    Require(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(),
            "actual native wrapper serialized");
    Require(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
            query.observation.capture_epoch != query.envelope.expected_snapshot_revision,
            "owner capture epoch differs from published revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else {
    Require(serialized.empty() && !failure.empty(), "changed frame emits no success response");
    std::ofstream(directory / "frame-changed-rejection.json") <<
        "{\"success_wire_emitted\":false,\"mailbox_reclaimed\":true,\"failure\":\"" << failure << "\"}\n";
  }
  return result;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    Fixture value; auto bindings = Bind(value); FrameAdapter adapter; m::Snapshot observed{};
    collector_owner = adapter.owner;
    bindings.faith_characters = &OwnedFaithCollector; bindings.rite_counties = &OwnedCountyCollector;
    Require(Query(value, bindings, adapter, directory, "current-members.json", observed) &&
        observed.rite_character_ids.size() == 2 && observed.faith_character_ids.size() == 3 &&
        observed.county_title_ids.size() == 1, "actual worker current member scopes");
    Put(value.data, m::kAlivePoolSizeOffset, std::int32_t{0});
    Put(value.religion, m::kReligionCountyPoolSizeOffset, std::int32_t{0});
    Require(Query(value, bindings, adapter, directory, "known-empty.json", observed) && observed.available &&
        observed.rite_character_ids.empty() && observed.county_title_ids.empty(), "actual worker observed empty");
    Put(value.data, m::kAlivePoolSizeOffset, std::int32_t{5});
    Put(value.religion, m::kReligionCountyPoolSizeOffset, std::int32_t{2});
    Put(value.titles[0], m::kTitleIdentityOffset, std::uint32_t{0x8B000002});
    Require(Query(value, bindings, adapter, directory, "title-unavailable.json", observed) &&
        !observed.available && observed.failure == m::Failure::county_title_unavailable,
        "actual worker unavailable native source");
    Put(value.titles[0], m::kTitleIdentityOffset, Fixture::title_ids[0]);
    Put(value.characters[0], r::kCharacterRiteIdOffset, r::kAbsentReference);
    Require(Query(value, bindings, adapter, directory, "legal-no-rite.json", observed) &&
        observed.available && !observed.rite_id, "actual worker legal no Rite");
    Put(value.characters[0], r::kCharacterRiteIdOffset, Fixture::rite_id);
    value.drift = true;
    Require(!Query(value, bindings, adapter, directory, "frame-changed.json", observed), "actual post-read changed frame rejection");
    value.drift = false; Put(value.state, 8, std::int32_t{53175816});
    std::uint64_t revision = 0;
    Require(c::ParsePlayerRiteMembersRevision12002("{}", revision) && revision == 0, "optional expected revision");
    Require(c::ParsePlayerRiteMembersRevision12002("{\"expected_revision\":701}", revision) && revision == 701,
            "actual expected revision alias parser");
    Require(!c::ParsePlayerRiteMembersRevision12002("{\"expected_snapshot_revision\":701,\"expected_revision\":702}", revision),
            "conflicting expected revisions rejected");
    api::MainThreadQueryMailboxV1 mailbox{};
    game::Snapshot published{}; Require(adapter.read_snapshot(published), "restored actual published frame");
    std::string wire, failure;
    Require(!c::HandlePlayerRiteMembersPrivate12002(adapter, mailbox, published, 701,
        c::kPlayerRiteMembersPrivateStep12002, "{\"expected_revision\":702}", "stale", wire, failure) &&
        wire.empty() && failure == "player_rite_members_current_frame_unavailable" && mailbox.next_sequence == 0,
        "actual handler rejects stale request before submission");
    Require(c::IsPlayerRiteMembersPrivateStep12002(c::kPlayerRiteMembersPrivateStep12002) &&
        !c::IsPlayerRiteMembersPrivateStep12002("query-player-rite-members-v1-other"), "exact member selector");
    std::cout << "PASS checks=" << checks << " cases=5 actual_provider=true actual_mailbox_submit_drain_wait_reclaim=true actual_wrapper=true component_matrix_repeated=false dedicated_registration=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}

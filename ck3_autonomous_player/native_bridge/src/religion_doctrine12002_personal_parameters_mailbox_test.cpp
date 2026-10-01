#define main PersonalParametersLibraryFixtureMain
#include "religion_doctrine12002_personal_parameters_test.cpp"
#undef main
#include "xar_bridge/religion_doctrine12002_personal_parameters_mailbox.hpp"
#include <windows.h>

#include <atomic>
#include <chrono>
#include <stdexcept>
#include <thread>

namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
int mailbox_checks = 0;
void Assert(bool condition, const char *message) {
  ++mailbox_checks;
  if (!condition) throw std::runtime_error(message);
}
class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  game::AdapterDescriptor identity{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
      c::kExecutableSha256, "personal-parameters-query-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    if (++reads > 1 && drift) ++out.date_raw;
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
  Pump(Fixture &fixture, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    // Use the existing primary fixture permit; root registers the separate deployed personal parameter permit, with fixture-owned memory.
    mailbox.permitted_executor = &c::ExecutePlayerReligionPersonalParametersMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, d::PersonalParameterContext &observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionPersonalParametersMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(fixture);
  query.parameter_bindings = BindParameters(fixture);
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionPersonalParametersMailbox12002(query, "religion\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Assert(drained, "real queued executor drained on fixture owner");
  Assert(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  observed = query.observation;
  if (result) {
    Assert(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(), "serialized-ready actual result");
    Assert(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          query.observation.capture_epoch != query.envelope.expected_snapshot_revision, "epoch differs from published revision");
    std::ofstream(directory / filename) << serialized << '\n';
  } else Assert(serialized.empty() && !failure.empty(), "unstable query has no success JSON");
  return result;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "output directory");
    const std::filesystem::path output(argv[1]);
    Fixture fixture;
    FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id;
    adapter.frame.date_raw = Get<std::int32_t>(fixture.state.data(), 8);
    d::PersonalParameterContext observation{};
    Assert(Query(fixture, adapter, output, "personal-true-and-known-missing.json", observation) &&
          observation.available && observation.has_character_extension &&
          observation.personal_tenet_keys.size() == 2 && observation.parameters.size() == 4 &&
          d::LookupPersonalParameter12002(observation, fixture.names[1]).value == true &&
          d::LookupPersonalParameter12002(observation, fixture.names[0]).state == d::PersonalParameterLookupState::Value &&
          d::LookupPersonalParameter12002(observation, fixture.names[0]).value == false,
          "actual full personal packet preserves present true and supported missing false");
    Put(fixture.character, d::kPersonalParameterCharacterExtensionOffset, static_cast<void *>(nullptr));
    Assert(Query(fixture, adapter, output, "extension-absent.json", observation) && observation.available &&
          !observation.has_character_extension && observation.personal_tenet_keys.empty() &&
          d::LookupPersonalParameter12002(observation, fixture.names[1]).value == false,
          "actual legal absent extension is observed supported false");
    Put(fixture.character, d::kPersonalParameterCharacterExtensionOffset, fixture.extension.data());
    Put(fixture.extension, d::kPersonalParameterOwnedTenetsOffset + 0xC, std::int32_t{0});
    Assert(Query(fixture, adapter, output, "empty-owned-tenets.json", observation) && observation.available &&
          observation.has_character_extension && observation.personal_tenet_keys.empty() &&
          d::LookupPersonalParameter12002(observation, fixture.names[2]).value == false,
          "actual empty personal collection preserves full supported false registry");
    fixture.database_ptr = nullptr;
    Assert(Query(fixture, adapter, output, "database-unavailable.json", observation) && !observation.available &&
          observation.failure == "parameter_registry_unavailable" &&
          observation.date_raw == adapter.frame.date_raw && observation.played_character_id == Fixture::character_id,
          "actual typed database unavailable preserves published owner frame");
    fixture.database_ptr = fixture.database.data();
    Put(fixture.extension, d::kPersonalParameterOwnedTenetsOffset + 0xC, std::int32_t{2});
    fixture.drift = true; fixture.getter_calls = 0;
    Assert(Query(fixture, adapter, output, "state-changed.json", observation) && !observation.available &&
          observation.failure == "state_changed" && observation.date_raw == adapter.frame.date_raw &&
          observation.played_character_id == Fixture::character_id,
          "actual changed personal values remain typed unavailable rather than false");
    Assert(c::IsPlayerReligionPersonalParametersPrivateStep12002("query-player-religion-personal-parameters-v1") &&
          !c::IsPlayerReligionPersonalParametersPrivateStep12002("query-player-religion-tenets-v1"),
          "separate personal parameter selector");
    std::uint64_t revision = 0;
    Assert(c::ParsePlayerReligionPersonalParametersRevision12002("{\"expected_revision\":701}", revision) && revision == 701,
          "revision alias");
    Assert(c::ParsePlayerReligionPersonalParametersRevision12002("{\"expected_snapshot_revision\":701,\"expected_revision\":701}", revision),
          "matching revision aliases");
    Assert(!c::ParsePlayerReligionPersonalParametersRevision12002("{\"expected_snapshot_revision\":701,\"expected_revision\":702}", revision),
          "different revision aliases rejected");
    std::cout << "PASS checks=" << mailbox_checks
              << " actual_domain_mailbox=true actual_personal_parameters=true actual_command_result=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}

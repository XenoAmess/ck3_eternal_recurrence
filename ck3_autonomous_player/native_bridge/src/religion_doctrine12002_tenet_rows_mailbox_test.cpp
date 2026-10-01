#define main TenetRowsLibraryFixtureMain
#include "religion_doctrine12002_tenet_rows_test.cpp"
#undef main
#include "xar_bridge/religion_doctrine12002_tenet_rows_mailbox.hpp"
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
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
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
      c::kExecutableSha256, "doctrine-query-fixture", {}};
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
    // Use the existing primary fixture permit; root registers the separate deployed doctrine permit, with fixture-owned memory.
    mailbox.permitted_executor = &c::ExecutePlayerReligionTenetsMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, d::TenetRowsContext &observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionTenetsMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(fixture);
  query.tenet_bindings = {true, &State};
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionTenetsMailbox12002(query, "religion\"mailbox-fixture", serialized, failure);
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
    d::TenetRowsContext observation{};
    Assert(Query(fixture, adapter, output, "current-main-personal.json", observation) && observation.available &&
          observation.current_rite->core_tenets[0].key == "tenet_4" &&
          observation.faith_main_rite->core_tenets[0].key == "tenet_3" &&
          observation.personal_tenets[0].current_rite_status == 0 &&
          observation.effective_tenet_states.size() == 5,
          "actual command_result keeps real Core/main/personal states");
    Put(fixture.character, d::kCharacterExtensionOffset, static_cast<void *>(nullptr));
    Assert(Query(fixture, adapter, output, "known-empty-personal.json", observation) && observation.available &&
          observation.personal_tenets.empty(), "absent extension is observed empty personal collection");
    Put(fixture.character, d::kCharacterExtensionOffset, fixture.extension.data());
    Put(fixture.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
    Assert(Query(fixture, adapter, output, "personal-without-rite.json", observation) && observation.available &&
          !observation.current_rite && !observation.personal_tenets[0].current_rite_status,
          "legal absent Rite keeps native personal definitions");
    Put(fixture.character, r::kCharacterRiteIdOffset, Fixture::current_id);
    fixture.invalid_state = true;
    Assert(Query(fixture, adapter, output, "tenet-state-unavailable.json", observation) && !observation.available &&
          observation.failure == "tenet_state_unavailable" &&
          observation.date_raw == adapter.frame.date_raw && observation.played_character_id == Fixture::character_id,
          "actual typed unavailable keeps published owner frame");
    fixture.invalid_state = false; adapter.drift = true;
    Assert(!Query(fixture, adapter, output, "frame-drift.json", observation), "actual owner drift is not success wire");
    Assert(c::IsPlayerReligionTenetsPrivateStep12002("query-player-religion-tenets-v1") &&
          !c::IsPlayerReligionTenetsPrivateStep12002("query-player-religion-doctrines-v1"), "separate Tenet selector");
    std::uint64_t revision = 0;
    Assert(c::ParsePlayerReligionTenetsRevision12002("{\"expected_revision\":701}", revision) && revision == 701,
          "revision alias");
    Assert(c::ParsePlayerReligionTenetsRevision12002("{\"expected_snapshot_revision\":701,\"expected_revision\":701}", revision),
          "matching revision aliases");
    Assert(!c::ParsePlayerReligionTenetsRevision12002("{\"expected_snapshot_revision\":701,\"expected_revision\":702}", revision),
          "different revision aliases rejected");
    std::cout << "PASS checks=" << mailbox_checks << " actual_domain_mailbox=true actual_tenet_rows=true actual_command_result=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}

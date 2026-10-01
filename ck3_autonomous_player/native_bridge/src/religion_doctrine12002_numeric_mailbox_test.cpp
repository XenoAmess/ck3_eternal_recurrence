#include "xar_bridge/religion_doctrine12002_numeric_final.hpp"

// Reuse frozen memory layout only. The old 15-check main is never executed.
#define main NumericSpecialFixtureLibraryMain
#include "religion_doctrine12002_numeric_test.cpp"
#undef main

namespace {
std::int64_t native_define = 2500000;
int threshold_calls = 0;
bool bad_return = false, threshold_drift = false;
template <typename T> T FinalLoad(const void *object, std::size_t at) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value));
  return value;
}
std::int64_t *Threshold(const void *faith, std::int64_t *output) {
  ++threshold_calls;
  if (faith != f->faith.data() ||
      FinalLoad<std::uint32_t>(faith, r::kFaithMainRiteIdOffset) != Fixture::main_id || bad_return)
    return nullptr;
  const auto adjustment = FinalLoad<std::int64_t>(f->main_rite.data(),
      d::kRiteNumericSpecialOffset + d::kNumericHeresyThresholdOffset);
  *output = native_define + adjustment;
  if (threshold_drift && threshold_calls == 2) ++*output;
  return output;
}
} // namespace
#include "xar_bridge/religion_doctrine12002_numeric_mailbox.hpp"
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
      c::kExecutableSha256, "numeric-special-query-fixture", {}};
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
    // Use the existing primary fixture permit; root registers the separate deployed numeric permit, with fixture-owned memory.
    mailbox.permitted_executor = &c::ExecutePlayerReligionNumericSpecialParametersMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

bool Query(Fixture &fixture, FrameAdapter &adapter, const std::filesystem::path &directory,
           const char *filename, d::NumericSpecialContext &observed, d::FaithNumericFinalContext &final_observed) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionNumericSpecialParametersMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(fixture);
  query.numeric_bindings = {true};
  query.final_bindings = {true, &Threshold, &native_define};
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionNumericSpecialParametersMailbox12002(query, "religion\"mailbox-fixture", serialized, failure);
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
  final_observed = query.final_observation;
  if (result) {
    Assert(failure.empty() && query.completed && query.envelope.frame_stable && !serialized.empty(), "serialized-ready actual result");
    Assert(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          query.observation.capture_epoch != query.envelope.expected_snapshot_revision &&
          query.final_observation.capture_epoch == query.observation.capture_epoch,
          "both actual observers share owner epoch distinct from published revision");
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
    d::NumericSpecialContext observation{};
    d::FaithNumericFinalContext final{};
    Assert(Query(fixture, adapter, output, "current-versus-main.json", observation, final) &&
          observation.available && final.available && threshold_calls == 2 &&
          final.current_rite_id == observation.current_rite->rite_id &&
          final.faith_id == observation.faith_id && final.main_rite_id == observation.faith_main_rite->rite_id &&
          final.main_rite_adjustment_raw == 500000 && final.native_define_raw == 2500000 &&
          final.final_heresy_threshold_raw == 3000000,
          "combined actual provider reports main-rite final30 rather than actor adjustment-5");
    native_define = -500000;
    Assert(Query(fixture, adapter, output, "known-zero-final.json", observation, final) &&
          observation.available && final.available && final.final_heresy_threshold_raw.has_value() &&
          final.final_heresy_threshold_raw == 0,
          "native final zero remains a value alongside actual five-cache DTO");
    native_define = 2500000;
    Fixture::Set(fixture.rite, -1, 0, 0, 0, 0);
    Assert(Query(fixture, adapter, output, "minimum-unset.json", observation, final) &&
          observation.available && final.available && observation.current_rite->parameters[0].unset &&
          final.final_heresy_threshold_raw == 3000000,
          "minimum sentinel preserves separate main-rite final value");
    Put(fixture.rite, r::kRiteFaithIdOffset, r::kAbsentReference); threshold_calls = 0;
    Assert(Query(fixture, adapter, output, "legal-absent-faith.json", observation, final) &&
          observation.available && final.available && !final.faith_id &&
          !final.final_heresy_threshold_raw && threshold_calls == 0 && observation.current_rite.has_value(),
          "legal absent Faith retains current cache and performs no fallback final callback");
    Put(fixture.rite, r::kRiteFaithIdOffset, Fixture::faith_id);
    Put(fixture.faith, r::kFaithMainRiteIdOffset, r::kAbsentReference);
    Assert(Query(fixture, adapter, output, "legal-absent-main-rite.json", observation, final) &&
          observation.available && final.available && final.faith_id.has_value() &&
          !final.main_rite_id && !final.final_heresy_threshold_raw && threshold_calls == 0,
          "legal absent main Rite has a typed absent final rather than fabricated numeric zero");
    Put(fixture.faith, r::kFaithMainRiteIdOffset, Fixture::main_id); bad_return = true;
    Assert(Query(fixture, adapter, output, "native-threshold-unavailable.json", observation, final) &&
          observation.available && !final.available && final.failure == "native_threshold_unavailable" &&
          final.date_raw == observation.date_raw && final.played_character_id == observation.played_character_id &&
          !final.final_heresy_threshold_raw,
          "final callback failure is independent and preserves observed five-cache DTO");
    std::cout << "PASS checks=" << mailbox_checks
              << " actual_domain_mailbox=true actual_numeric_special_parameters=true actual_faith_numeric_final=true"
              << " actual_command_result=true live=false old_cache39_executed=false old_final10_executed=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}

// Deterministic real WorkerAdapter wait/publication regression; owned DTOs only.
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/nonwar_private_snapshot_guard_diagnostics_v1.hpp"
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace xar::ck3_12002 {
struct WorkerSnapshotWaitFixtureAccess12004 {
  using Boundary = WorkerAdapter::SnapshotWaitBoundary12004;
  using Observer = WorkerAdapter::SnapshotWaitObserver12004;
  static void Bind(WorkerAdapter &adapter, void *context, Observer observer) {
    std::lock_guard lock(adapter.snapshot_mutex_);
    adapter.snapshot_wait_observer_context12004_ = context;
    adapter.snapshot_wait_observer12004_ = observer;
  }
};
}
namespace {
namespace api = xar::ck3_11906;
namespace build = xar::ck3_12002;
namespace game = xar::game;
namespace diag = xar::bridge::ck3_12004;
using Access = build::WorkerSnapshotWaitFixtureAccess12004;
using namespace std::chrono_literals;
void Need(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}

// The interface stub below is copied from the existing semantic adapter fixture.
// It never accesses CK3; the actual production WorkerAdapter performs all caching.
class FixtureAdapter final : public game::GameAdapter {
public:
  const DWORD owner = GetCurrentThreadId();
  game::Snapshot frame{};
  mutable std::atomic<std::uint32_t> raw_reads{0};
  mutable std::atomic<std::uint32_t> semantic_calls{0};
  mutable std::atomic<std::uint32_t> wrong_owner{0};
  mutable std::atomic<DWORD> queue_thread{0};
  mutable std::atomic<std::int32_t> last_event_option{-1};
  mutable std::atomic<std::int32_t> last_army{-1};
  mutable std::atomic<std::int32_t> last_province{-1};
  mutable std::atomic<std::int32_t> last_family_subject{-1};
  bool reader_available = true;
  bool declarations_available = true;
  bool family_available = true;
  bool patch3 = false;
  bool patch4 = false;
  void *raw_gate_context = nullptr;
  bool (*raw_gate)(void *) noexcept = nullptr;

  FixtureAdapter() {
    frame.date_raw = 123456;
    frame.speed = 3;
    frame.player_id = 7;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_id = 0x12000015;
    frame.played_character_alive = true;
    frame.has_active_event = true;
    frame.active_event_instance_id = 91;
    frame.active_event_option_count = 3;
    game::ArmySnapshot army{};
    army.army_id = 0x23000031;
    army.owner_character_id = frame.played_character_id;
    army.controllable = true;
    army.has_current_province = true;
    army.current_province_id = 900;
    frame.player_armies.push_back(army);
  }

  const game::AdapterDescriptor &descriptor() const noexcept override {
    if (patch4) return game::Ck3_12004AdapterDescriptor();
    if (patch3) return game::Ck3_12003AdapterDescriptor();
    static const game::AdapterDescriptor value{
      "ck3-1.20.0.2-msvc-x64", "1.20.0.2", build::kExecutableSha256,
      "fixture-only", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  void RecordSemantic() const noexcept {
    ++semantic_calls;
    if (GetCurrentThreadId() != owner) ++wrong_owner;
  }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    ++raw_reads;
    if (GetCurrentThreadId() != owner) {
      ++wrong_owner;
      output = {};
      return false;
    }
    if (raw_gate != nullptr && !raw_gate(raw_gate_context)) { output = {}; return false; }
    output = reader_available ? frame : game::Snapshot{};
    return reader_available;
  }
  game::PauseSubmitResult submit_pause_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::PauseSubmitResult::submitted;
  }
  game::ResumeSubmitResult submit_resume_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::ResumeSubmitResult::submitted;
  }
  bool submit_set_speed(std::int32_t speed) const noexcept override {
    queue_thread = GetCurrentThreadId();
    return speed == 4;
  }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    queue_thread = GetCurrentThreadId();
    return {game::SaveCheckpointStatus::submitted, 123456};
  }
  game::SelectEventOptionResult submit_select_event_option(
      std::int32_t option) const noexcept override {
    RecordSemantic();
    last_event_option = option;
    return option < 0 || option >= frame.active_event_option_count
      ? game::SelectEventOptionResult::option_out_of_range
      : game::SelectEventOptionResult::submitted;
  }
  bool read_declarable_wars(
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return false;
    output.push_back({0x14000042, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return true;
  }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t target_id,
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return game::ReadDeclarableWarsResult::unavailable;
    if (target_id != 0x14000042) return game::ReadDeclarableWarsResult::target_not_found;
    output.push_back({target_id, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return game::ReadDeclarableWarsResult::available;
  }
  game::MoveArmyResult submit_move_army(
      std::int32_t army, std::int32_t province) const noexcept override {
    RecordSemantic();
    last_army = army;
    last_province = province;
    return army == frame.player_armies.front().army_id && province == 901
      ? game::MoveArmyResult::submitted : game::MoveArmyResult::validation_failed;
  }
  game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<game::ArmyStrengthSnapshot> &output) const noexcept override {
    RecordSemantic();
    game::ArmyStrengthSnapshot row{};
    row.available = true;
    row.army_id = frame.player_armies.front().army_id;
    row.regiment_count = 2;
    row.current_soldiers = 734;
    row.maximum_soldiers = 1000;
    row.ai_base_power_raw = 123456789;
    output = {row};
    return game::ReadArmyStrengthsResult::available;
  }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<game::ArrangeMarriageChoice> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    output = {{frame.played_character_id, 0x15000011}};
    diagnostics = {};
    diagnostics.storage_capacity = 17;
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageChoicesResult::available;
  }
  game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t war_id, game::WarTerminationOptionsSnapshot &output) const noexcept override {
    RecordSemantic();
    output = {};
    if (frame.active_wars.empty() || frame.active_wars.front().war_id != war_id)
      return game::ReadWarTerminationOptionsResult::war_not_found;
    output.war_id = war_id;
    output.player_relative_war_score = frame.active_wars.front().player_relative_war_score;
    return game::ReadWarTerminationOptionsResult::available;
  }
  game::ReadArrangeMarriageFamilyCandidatesResultV1
  read_arrange_marriage_family_candidates_v1(
      std::int32_t subject_id,
      std::vector<game::ArrangeMarriageFamilyCandidateV1> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    last_family_subject = subject_id;
    output.clear();
    diagnostics = {};
    if (subject_id != 0x13000016)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::subject_not_found;
    diagnostics.storage_capacity = 17;
    diagnostics.slots_scanned = 2;
    if (!family_available)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::unavailable;
    game::ArrangeMarriageFamilyCandidateV1 row{};
    row.played_character_id = frame.played_character_id;
    row.subject_character_id = subject_id;
    row.candidate_character_id = 0x15000011;
    row.recipient_matchmaker_character_id = 0x14000042;
    row.recipient_ai_accept_raw = 2'500'000;
    row.recipient_answer_status_raw = 1;
    row.complete_can_send = true;
    row.recipient_answer_allows_send = true;
    row.heir_adult_measure_raw = std::int16_t{17};
    row.candidate_adult_measure_raw = std::int16_t{19};
    row.played_dynasty_id = 71;
    row.heir_dynasty_id = 71;
    row.candidate_dynasty_id = 72;
    row.realm_backed_actor_recipient = true;
    output.push_back(row);
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageFamilyCandidatesResultV1::available;
  }

#define UNAVAILABLE_RESULT(Result, Name, Parameters) \
  game::Result Name Parameters const noexcept override { \
    RecordSemantic(); return game::Result::unavailable; }
  UNAVAILABLE_RESULT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
                     (game::PendingInteractionReply))
  UNAVAILABLE_RESULT(AcknowledgePendingInteractionResult, submit_acknowledge_pending_interaction,
                     (std::int32_t))
  UNAVAILABLE_RESULT(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE_RESULT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE_RESULT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE_RESULT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE_RESULT(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE_RESULT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  UNAVAILABLE_RESULT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  UNAVAILABLE_RESULT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  UNAVAILABLE_RESULT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE_RESULT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  UNAVAILABLE_RESULT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationTermsResult, read_war_termination_terms,
                     (std::int32_t, game::WarTerminationTermsSnapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
                     (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef UNAVAILABLE_RESULT
  game::PreviewMoveArmyResult preview_move_army(
      std::int32_t, std::int32_t) const noexcept override {
    RecordSemantic();
    return {};
  }
};

enum class Mode { cadence_forward, same_epoch, replacement_generation, owner_drift };
struct FixtureState {
  std::mutex mutex;
  std::condition_variable changed;
  build::WorkerAdapter *adapter = nullptr;
  bool read_requested = false, before_wait = false, after_wait = false;
  bool continue_after_wait = false, shutdown = false, fixture_failed = false;
  bool raw_gate_armed = false, owner_rejected = false, unrelated_rejected = false;
  bool reader_finished = false;
  game::Snapshot expected{}, output{};
  std::string guard_error;
  std::optional<diag::WorkerSnapshotObservation12004> observation;
  unsigned read_calls = 0;
};

void WaitBoundary(void *opaque, Access::Boundary boundary,
                  std::unique_lock<std::mutex> &cache_lock) noexcept {
  auto &state = *static_cast<FixtureState *>(opaque);
  if (boundary == Access::Boundary::before_wait) {
    std::lock_guard lock(state.mutex);
    state.before_wait = true;
    state.changed.notify_all();
    return; // Keep the real cache mutex: owner commits only after CV releases it.
  }
  cache_lock.unlock();
  {
    std::unique_lock lock(state.mutex);
    state.after_wait = true;
    state.changed.notify_all();
    if (!state.changed.wait_for(lock, 2s, [&] {
          return state.continue_after_wait || state.shutdown; }))
      state.fixture_failed = true;
  }
  cache_lock.lock(); // Original after_wait guards see the real current cache.
}

bool RawReadGate(void *opaque) noexcept {
  auto &state = *static_cast<FixtureState *>(opaque);
  {
    std::unique_lock lock(state.mutex);
    if (!state.raw_gate_armed) return true;
    state.raw_gate_armed = false;
    state.read_requested = true;
    state.changed.notify_all();
    if (!state.changed.wait_for(lock, 2s, [&] {
          return state.before_wait || state.shutdown; }) || state.shutdown) {
      state.fixture_failed = true;
      return false;
    }
  }
  // The owner and an unrelated reader must not await work on the owner itself.
  game::Snapshot owner_output{};
  const bool owner_rejected = !state.adapter->read_snapshot(owner_output) &&
      owner_output == game::Snapshot{};
  bool unrelated_rejected = false;
  std::thread unrelated([&] {
    game::Snapshot output{};
    unrelated_rejected = !state.adapter->read_snapshot(output) &&
        output == game::Snapshot{};
  });
  unrelated.join();
  {
    std::lock_guard lock(state.mutex);
    state.owner_rejected = owner_rejected;
    state.unrelated_rejected = unrelated_rejected;
  }
  return owner_rejected && unrelated_rejected;
}

void PublishMailbox(api::MainThreadQueryMailboxV1 &mailbox,
                    const api::MainThreadExecutionStampV1 &stamp) {
  mailbox.pump_epochs.store(stamp.pump_epoch);
  mailbox.owner_thread_id.store(stamp.thread_id);
  mailbox.observed_current_thread_id.store(stamp.thread_id);
  mailbox.observed_date_raw.store(stamp.date_raw);
  mailbox.observed_paused.store(stamp.paused);
  mailbox.observed_tls_initialized.store(stamp.tls_initialized);
  mailbox.observed_tls_main_thread_marker.store(stamp.tls_main_thread_marker);
  mailbox.observed_stamp_read_success.store(true);
}

void RunCase(Mode mode) {
  FixtureAdapter native;
  native.patch4 = true;
  native.frame.paused = true;
  api::MainThreadQueryMailboxV1 mailbox{};
  FixtureState state;
  std::jthread reader([&] {
    build::WorkerAdapter adapter(native, mailbox, build::ConsoleFixtureBindings{});
    {
      std::unique_lock lock(state.mutex);
      state.adapter = &adapter; // Constructor runs on the actual reading worker.
      state.changed.notify_all();
      if (!state.changed.wait_for(lock, 2s, [&] {
            return state.read_requested || state.shutdown; }) || state.shutdown)
        return;
    }
    unsigned reads = 0;
    const std::optional<game::Snapshot> previous{state.expected};
    game::Snapshot output{};
    const auto error = xar::bridge::NonwarPrivateSnapshotGuardFailureV1(
        false, true, 36, 36, previous, output,
        [&](game::Snapshot &current) {
          ++reads;
          return adapter.read_snapshot(current); // Actual single producer call.
        }, true);
    {
      std::lock_guard lock(state.mutex);
      state.read_calls = reads;
      state.output = std::move(output);
      state.guard_error = error;
      state.observation = diag::detail::snapshot_read_attempt12004.worker_observation;
      state.reader_finished = true;
      state.changed.notify_all();
    }
  });
  const auto release = [&] {
    {
      std::lock_guard lock(state.mutex);
      state.shutdown = true;
      state.continue_after_wait = true;
      state.changed.notify_all();
    }
    if (reader.joinable()) reader.join();
  };
  try {
    {
      std::unique_lock lock(state.mutex);
      Need(state.changed.wait_for(lock, 2s, [&] {
        return state.adapter != nullptr; }), "worker constructor handshake");
    }
    Access::Bind(*state.adapter, &state, &WaitBoundary);
    api::MainThreadExecutionStampV1 stamp{};
    stamp.pump_epoch = 460573;
    stamp.thread_id = GetCurrentThreadId();
    stamp.tls_initialized = 1;
    stamp.tls_main_thread_marker = 1;
    stamp.date_raw = native.frame.date_raw;
    stamp.paused = true;
    PublishMailbox(mailbox, stamp);
    Need(state.adapter->Observe(stamp), "initial actual raw publication");
    Need(native.raw_reads == 1, "one initial native raw read");
    ++native.frame.date_raw; // Force the second real raw sample without sleeping.
    ++stamp.pump_epoch;
    stamp.date_raw = native.frame.date_raw;
    {
      std::lock_guard lock(state.mutex);
      state.expected = native.frame;
      state.raw_gate_armed = true;
    }
    native.raw_gate_context = &state;
    native.raw_gate = &RawReadGate;
    PublishMailbox(mailbox, stamp);
    Need(state.adapter->Observe(stamp), "gated actual raw publication");
    {
      std::unique_lock lock(state.mutex);
      Need(state.changed.wait_for(lock, 2s, [&] {return state.after_wait;}),
           "worker must reach actual CV after_wait");
    }
    Need(native.raw_reads == 2, "exact two actual raw reads before cadence");
    if (mode != Mode::same_epoch) {
      ++stamp.pump_epoch;
      if (mode == Mode::replacement_generation) {
        ++native.frame.date_raw;
        stamp.date_raw = native.frame.date_raw;
      }
      PublishMailbox(mailbox, stamp);
      Need(state.adapter->Observe(stamp), "actual subsequent owner Observe");
      if (mode == Mode::replacement_generation)
        Need(native.raw_reads == 3, "replacement is real new raw generation");
      else
        Need(native.raw_reads == 2, "setup exceeded250ms: cadence must do no raw read");
      if (mode == Mode::owner_drift)
        mailbox.owner_thread_id.store(stamp.thread_id + 1U);
    }
    {
      std::lock_guard lock(state.mutex);
      state.continue_after_wait = true;
      state.changed.notify_all();
    }
    reader.join();
    Need(!state.fixture_failed && state.reader_finished && state.before_wait &&
         state.after_wait, "bounded real waiting path completed");
    Need(state.owner_rejected && state.unrelated_rejected,
         "owner and unrelated reader never wait on active raw owner");
    Need(state.read_calls == 1 && native.semantic_calls == 0 &&
         native.wrong_owner == 0, "one real snapshot read; no semantics or wrong owner");
    Need(state.observation.has_value() &&
         state.observation->expected_wait_ticket.has_value() &&
         state.observation->wait_terminal == std::optional<bool>{true},
         "actual production wait ticket and terminal receipt");
    if (mode == Mode::replacement_generation || mode == Mode::owner_drift) {
      Need(!state.guard_error.empty() && state.output == game::Snapshot{},
           "raw generation/owner drift remains RED with empty output");
      return;
    }
    if (!state.guard_error.empty())
      std::fprintf(stderr, "actual wait RED: %s\n", state.guard_error.c_str());
    Need(state.guard_error.empty() && state.output == state.expected,
         "successful raw ticket survives same-frame cadence in actual FullSnapshot guard");
    const auto &view = *state.observation;
    Need(view.last_committed_raw_generation == view.expected_wait_ticket->generation &&
         view.raw_publish_epoch == std::optional<std::uint64_t>{460574} &&
         view.raw_publisher_thread_id == std::optional<std::uint32_t>{stamp.thread_id} &&
         view.current_cache_epoch == stamp.pump_epoch,
         "immutable raw ticket and exact live freshness are separately observed");
  } catch (...) {
    release();
    throw;
  }
  release();
}
} // namespace

namespace xar::native_test {
bool RunWorkerSnapshotPublicationWaitFixture12004() noexcept {
  try {
    RunCase(Mode::cadence_forward); // Original guard must RED here before the fix.
    RunCase(Mode::same_epoch);
    RunCase(Mode::replacement_generation);
    RunCase(Mode::owner_drift);
    std::puts("PASS4 real WorkerAdapter wait/publication cases; owner/unrelated no-wait; no Game");
    return true;
  } catch (const std::exception &error) {
    std::fprintf(stderr, "worker publication fixture failed: %s\n", error.what());
    return false;
  }
}
}

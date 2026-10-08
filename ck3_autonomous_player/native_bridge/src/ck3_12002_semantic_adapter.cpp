#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/army_strength_query_diagnostic_v1.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_adapter.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_marriage_probe.hpp"
#include <atomic>
#include <utility>

namespace xar::ck3_12002 {
namespace {
bool ReadTimelineCommandObservation(
    const game::GameAdapter &native,
    const ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    game::Snapshot &output) noexcept {
  output = {};
  const auto stamp = ck3_11906::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
  if (!stamp.observed_stamp_read_success ||
      stamp.observed_tls_initialized != 1 ||
      stamp.observed_tls_main_thread_marker != 1) return false;
  game::Snapshot observed{};
  if (!game::ReadCk3_12002TimelineCoreSnapshot(native, observed) ||
      observed.date_raw != stamp.observed_date_raw ||
      observed.paused != stamp.observed_paused) return false;
  output = std::move(observed);
  return true;
}

enum class SemanticOperation {
  select_event, reply, acknowledge, raise, move, halt, disband, split, merge, assault_start, assault_stop, declare, marriage, enforce, surrender, white_peace,
  preview, declarations, declarations_for_target, marriage_choices, family_candidates, strengths, combat_v2, combat_v3,
  player_claims, title_own_laws, title_holder, occupation_targets, termination_options, termination_terms, exit_terms, marriage_diagnostic,
  fixture_run_inbox
};

std::string SerializeInboxFixture(ConsoleFixtureResult result) {
  std::string json = "{\"query_status\":\"";
  switch (result) {
  case ConsoleFixtureResult::executed: json += "executed"; break;
  case ConsoleFixtureResult::command_rejected: json += "command_rejected"; break;
  case ConsoleFixtureResult::console_unavailable: json += "console_unavailable"; break;
  case ConsoleFixtureResult::unavailable: json += "unavailable"; break;
  }
  json += "\",\"native_executed\":";
  json += result == ConsoleFixtureResult::executed ? "true" : "false";
  json += ",\"fixed_command\":\"run xar_mcp_inbox.txt\",\"marker_confirmed\":false}";
  return json;
}
} // namespace

struct WorkerAdapter::SemanticRequest {
  QueryMailboxEnvelope envelope{};
  SemanticOperation operation = SemanticOperation::declarations;
  std::int32_t id = -1;
  std::int32_t other_id = -1;
  game::PendingInteractionReply reply{};
  game::DeclarableWarSnapshot declaration{};
  game::ArrangeMarriageChoice choice{};
  game::CombatSimulationInputsRequest combat_request{};
  std::int32_t result = 0;
  bool bool_result = false;
  game::PreviewMoveArmyResult preview{};
  std::vector<game::DeclarableWarSnapshot> declarations;
  std::vector<game::ArrangeMarriageChoice> marriage_choices;
  std::vector<game::ArrangeMarriageFamilyCandidateV1> family_candidates;
  game::ArrangeMarriageQueryDiagnostics marriage_diagnostics{};
  std::vector<game::ArmyStrengthSnapshot> strengths;
  game::CombatSimulationInputsSnapshot combat_v2{};
  game::CombatSimulationInputsV3Snapshot combat_v3{};
  std::vector<std::int32_t> player_claim_title_ids;
  game::PlayerClaimsV1 player_claims{};
  std::uint32_t title_own_laws_title_id = UINT32_MAX;
  game::TitleOwnLawsV1 title_own_laws{};
  game::TitleHolderV1 title_holder{};
  game::WarOccupationTargetsV1 occupation_targets{};
  game::WarTerminationOptionsSnapshot termination_options{};
  game::WarTerminationTermsSnapshot termination_terms{};
  game::WarTerminationExitTermsSnapshot exit_terms{};
  std::string diagnostic_json;
  ConsoleFixtureBindings console_fixture{};
  ConsoleFixtureResult console_result = ConsoleFixtureResult::unavailable;
};

WorkerAdapter::WorkerAdapter(const game::GameAdapter &native_adapter,
                             ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept
    : WorkerAdapter(native_adapter, mailbox,
          BindConsoleFixtureImage(
              reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
              game::ReviewedCrozierAbiSha256(native_adapter.descriptor()))) {}
WorkerAdapter::WorkerAdapter(const game::GameAdapter &native_adapter,
                             ck3_11906::MainThreadQueryMailboxV1 &mailbox,
                             const ConsoleFixtureBindings &console_fixture) noexcept
    : native_(&native_adapter), mailbox_(&mailbox), console_fixture_(console_fixture) {}
const game::GameAdapter &WorkerAdapter::native_adapter() const noexcept { return *native_; }
const game::AdapterDescriptor &WorkerAdapter::descriptor() const noexcept { return native_->descriptor(); }
bool WorkerAdapter::enabled() const noexcept { return native_->enabled(); }

SnapshotObserverDiagnostics12002 WorkerAdapter::snapshot_observer_diagnostics() const noexcept {
  SnapshotObserverDiagnostics12002 result{};
  result.started_ms = observer_started_ms_.load();
  result.completed_ms = observer_completed_ms_.load();
  result.last_read_ms = observer_last_read_ms_.load();
  result.last_read_available = observer_last_read_available_.load();
  try {
    std::lock_guard guard(snapshot_mutex_);
    result.snapshot_cached = snapshot_.has_value() && snapshot_epoch_ != 0;
  } catch (...) {}
  return result;
}

bool WorkerAdapter::read_snapshot(game::Snapshot &output) const noexcept {
  output = {};
  try {
    const auto diagnostics = ck3_11906::ReadMainThreadQueryMailboxDiagnosticsV1(*mailbox_);
    std::lock_guard guard(snapshot_mutex_);
    if (!snapshot_.has_value() || !diagnostics.observed_stamp_read_success ||
        diagnostics.observed_tls_initialized != 1 ||
        diagnostics.observed_tls_main_thread_marker != 1 ||
        snapshot_epoch_ == 0 ||
        snapshot_->date_raw != diagnostics.observed_date_raw ||
        snapshot_->paused != diagnostics.observed_paused) return false;
    output = *snapshot_;
    return true;
  } catch (...) { return false; }
}

bool WorkerAdapter::Observe(const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  try {
    const bool actual4 = game::IsCk3_12004Descriptor(descriptor()) &&
        supports_snapshot();
    if (!enabled() || (!game::IsReviewedCrozierAdapter(*this) && !actual4) ||
        GetCurrentThreadId() != stamp.thread_id || stamp.tls_initialized != 1 ||
        stamp.tls_main_thread_marker != 1) return false;
    {
      std::lock_guard guard(snapshot_mutex_);
      // Match the bridge heartbeat cadence. Date/pause transitions sample
      // immediately; typed requests still read a fresh raw frame on owner.
      if (snapshot_.has_value() && snapshot_epoch_ != 0 &&
          snapshot_->date_raw == stamp.date_raw && snapshot_->paused == stamp.paused &&
          GetTickCount64() < next_snapshot_sample_ms_) {
        snapshot_epoch_ = stamp.pump_epoch;
        return true;
      }
      snapshot_epoch_ = 0;
    }
    game::Snapshot observed{};
    const auto read_started_ms = GetTickCount64();
    observer_started_ms_.store(read_started_ms);
    const bool available = native_->read_snapshot(observed) &&
        observed.date_raw == stamp.date_raw && observed.paused == stamp.paused;
    const auto read_completed_ms = GetTickCount64();
    observer_last_read_ms_.store(read_completed_ms - read_started_ms);
    observer_last_read_available_.store(available);
    observer_completed_ms_.store(read_completed_ms);
    std::lock_guard guard(snapshot_mutex_);
    if (!available) {
      snapshot_.reset();
      return false;
    }
    if (!snapshot_.has_value() || *snapshot_ != observed) ++snapshot_revision_;
    snapshot_ = std::move(observed);
    snapshot_epoch_ = stamp.pump_epoch;
    next_snapshot_sample_ms_ = GetTickCount64() + 250;
    return true;
  } catch (...) {
    observer_last_read_available_.store(false);
    observer_completed_ms_.store(GetTickCount64());
    try { std::lock_guard guard(snapshot_mutex_); snapshot_.reset(); snapshot_epoch_ = 0; }
    catch (...) {}
    return false;
  }
}

bool ObserveAdapterSnapshot12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *adapter = static_cast<WorkerAdapter *>(opaque);
  return adapter != nullptr && adapter->Observe(stamp);
}

const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept {
  const auto *worker = dynamic_cast<const WorkerAdapter *>(&adapter);
  return worker == nullptr ? adapter : worker->native_adapter();
}

ck3_11906::VerifiedOwnerWakeDiagnosticsV1 WorkerAdapter::owner_wake_diagnostics() const noexcept {
  return owner_wake_counters_.Read();
}
void WorkerAdapter::WakeAfterDirectControlSubmit() const noexcept {
  owner_wake_counters_.Record(ck3_11906::WakeVerifiedApplicationMainOwnerV1(*mailbox_));
}

game::PauseSubmitResult WorkerAdapter::submit_pause_map(
    game::Snapshot *observed_snapshot) const noexcept {
  if (observed_snapshot == nullptr) {
    const auto result = native_->submit_pause_map();
    if (result == game::PauseSubmitResult::submitted) WakeAfterDirectControlSubmit();
    return result;
  }
  *observed_snapshot = {};
  game::Snapshot observed{};
  if (!ReadTimelineCommandObservation(*native_, *mailbox_, observed))
    return game::PauseSubmitResult::unavailable;
  const auto result = game::SubmitCk3_12002PauseMapObserved(*native_, observed);
  if (result == game::PauseSubmitResult::submitted) WakeAfterDirectControlSubmit();
  if (result != game::PauseSubmitResult::unavailable)
    *observed_snapshot = std::move(observed);
  return result;
}
game::ResumeSubmitResult WorkerAdapter::submit_resume_map(
    game::Snapshot *observed_snapshot) const noexcept {
  if (observed_snapshot == nullptr) {
    const auto result = native_->submit_resume_map();
    if (result == game::ResumeSubmitResult::submitted) WakeAfterDirectControlSubmit();
    return result;
  }
  *observed_snapshot = {};
  game::Snapshot observed{};
  if (!ReadTimelineCommandObservation(*native_, *mailbox_, observed))
    return game::ResumeSubmitResult::unavailable;
  const auto result = game::SubmitCk3_12002ResumeMapObserved(*native_, observed);
  if (result == game::ResumeSubmitResult::submitted) WakeAfterDirectControlSubmit();
  if (result != game::ResumeSubmitResult::unavailable)
    *observed_snapshot = std::move(observed);
  return result;
}
bool WorkerAdapter::submit_set_speed(std::int32_t speed) const noexcept {
  const bool submitted = native_->submit_set_speed(speed);
  if (submitted) WakeAfterDirectControlSubmit();
  return submitted;
}
game::SaveCheckpointResult WorkerAdapter::submit_save_checkpoint() const noexcept { return native_->submit_save_checkpoint(); }

bool WorkerAdapter::Run(SemanticRequest &request) const noexcept {
  auto *diagnostic = request.operation == SemanticOperation::strengths
      ? &g_army_strength_query_diagnostic_v1 : nullptr;
  try {
    request.envelope.game = native_;
    request.envelope.mailbox = mailbox_;
    request.envelope.typed_context = &request;
    if (diagnostic != nullptr) diagnostic->worker.store("pre_snapshot");
    const bool pre_snapshot = read_snapshot(request.envelope.expected_snapshot);
    if (diagnostic != nullptr) {
      diagnostic->pre_snapshot.store(pre_snapshot);
      diagnostic->paused.store(request.envelope.expected_snapshot.paused);
      diagnostic->map_ready.store(request.envelope.expected_snapshot.map_ready);
    }
    if (!pre_snapshot || !request.envelope.expected_snapshot.paused ||
        !request.envelope.expected_snapshot.map_ready) return false;
    {
      std::lock_guard guard(snapshot_mutex_);
      request.envelope.expected_snapshot_revision = snapshot_revision_;
    }
    if (diagnostic != nullptr) diagnostic->worker.store("submit");
    const auto submitted = ck3_11906::TrySubmitMainThreadQueryV1(
        *mailbox_, &ExecuteSemanticAdapter12002, &request.envelope, request.envelope.ticket);
    if (diagnostic != nullptr) diagnostic->submit.store(static_cast<std::int64_t>(submitted));
    if (submitted != ck3_11906::MainThreadQuerySubmitResultV1::submitted) return false;
    if (diagnostic != nullptr) diagnostic->worker.store("wait");
    auto wait = ck3_11906::WaitForMainThreadQueryV1(*mailbox_, request.envelope.ticket, 30'000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(*mailbox_, request.envelope.ticket, 2'000);
    if (diagnostic != nullptr) {
      diagnostic->wait.store(static_cast<std::int64_t>(wait));
      diagnostic->worker.store("reclaim");
    }
    const auto reclaimed = ck3_11906::ReclaimMainThreadQueryV1(*mailbox_, request.envelope.ticket);
    const bool success = wait == ck3_11906::MainThreadQueryWaitResultV1::completed &&
        reclaimed == ck3_11906::MainThreadQueryReclaimResultV1::reclaimed &&
        request.envelope.frame_stable;
    if (diagnostic != nullptr) {
      diagnostic->reclaim.store(static_cast<std::int64_t>(reclaimed));
      diagnostic->entered.store(request.envelope.entered);
      diagnostic->frame_stable.store(request.envelope.frame_stable);
      diagnostic->run_success.store(success);
      diagnostic->worker.store(success ? "returned" : "failed");
    }
    return success;
  } catch (...) {
    if (diagnostic != nullptr) diagnostic->worker.store("catch");
    return false;
  }
}

bool ExecuteSemanticAdapter12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return false;
  auto &request = *static_cast<WorkerAdapter::SemanticRequest *>(envelope->typed_context);
  auto *diagnostic = request.operation == SemanticOperation::strengths
      ? &g_army_strength_query_diagnostic_v1 : nullptr;
  if (diagnostic != nullptr) diagnostic->native.store("enter");
  const bool enter_result = EnterQueryMailbox(*envelope, stamp, &ExecuteSemanticAdapter12002);
  if (diagnostic != nullptr) {
    diagnostic->enter_result.store(enter_result);
    diagnostic->entered.store(envelope->entered);
  }
  if (!enter_result) return false;
  const auto &native = *envelope->game;
  try {
    switch (request.operation) {
    case SemanticOperation::select_event: request.result = static_cast<std::int32_t>(native.submit_select_event_option(request.id)); break;
    case SemanticOperation::reply: request.result = static_cast<std::int32_t>(native.submit_reply_to_pending_interaction(request.reply)); break;
    case SemanticOperation::acknowledge: request.result = static_cast<std::int32_t>(native.submit_acknowledge_pending_interaction(request.id)); break;
    case SemanticOperation::raise: request.result = static_cast<std::int32_t>(native.submit_raise_troops_default()); break;
    case SemanticOperation::move: request.result = static_cast<std::int32_t>(native.submit_move_army(request.id, request.other_id)); break;
    case SemanticOperation::halt: request.result = static_cast<std::int32_t>(native.submit_halt_army(request.id)); break;
    case SemanticOperation::disband: request.result = static_cast<std::int32_t>(native.submit_disband_army(request.id)); break;
    case SemanticOperation::split: request.result = static_cast<std::int32_t>(native.submit_split_army_half(request.id)); break;
    case SemanticOperation::merge: request.result = static_cast<std::int32_t>(native.submit_merge_armies(request.id, request.other_id)); break;
    case SemanticOperation::assault_start: request.result = static_cast<std::int32_t>(native.submit_start_assault(request.id)); break;
    case SemanticOperation::assault_stop: request.result = static_cast<std::int32_t>(native.submit_stop_assault(request.id)); break;
    case SemanticOperation::declare: request.result = static_cast<std::int32_t>(native.submit_declare_war(request.declaration)); break;
    case SemanticOperation::marriage: request.result = static_cast<std::int32_t>(native.submit_arrange_marriage(request.choice)); break;
    case SemanticOperation::enforce: request.result = static_cast<std::int32_t>(native.submit_enforce_demands(request.id)); break;
    case SemanticOperation::surrender: request.result = static_cast<std::int32_t>(native.submit_surrender_war(request.id)); break;
    case SemanticOperation::white_peace: request.result = static_cast<std::int32_t>(native.submit_offer_white_peace(request.id)); break;
    case SemanticOperation::preview: request.preview = native.preview_move_army(request.id, request.other_id); break;
    case SemanticOperation::declarations: request.bool_result = native.read_declarable_wars(request.declarations); break;
    case SemanticOperation::declarations_for_target: request.result = static_cast<std::int32_t>(native.read_declarable_wars_for_target(request.id, request.declarations)); break;
    case SemanticOperation::marriage_choices: request.result = static_cast<std::int32_t>(native.read_arrange_marriage_choices(request.marriage_choices, request.marriage_diagnostics)); break;
    case SemanticOperation::family_candidates: request.result = static_cast<std::int32_t>(native.read_arrange_marriage_family_candidates_v1(request.id, request.family_candidates, request.marriage_diagnostics)); break;
    case SemanticOperation::strengths:
      diagnostic->native.store("dispatch");
      request.result = static_cast<std::int32_t>(native.read_army_strengths(request.strengths));
      diagnostic->native_returned.store(1);
      break;
    case SemanticOperation::combat_v2: request.result = static_cast<std::int32_t>(native.read_combat_simulation_inputs(request.combat_request, request.combat_v2)); break;
    case SemanticOperation::combat_v3: request.result = static_cast<std::int32_t>(native.read_combat_simulation_inputs_v3(request.combat_request, request.combat_v3)); break;
    case SemanticOperation::player_claims: request.result = static_cast<std::int32_t>(
        native.read_player_claims_v1(request.player_claim_title_ids, request.player_claims)); break;
    case SemanticOperation::title_own_laws: request.result = static_cast<std::int32_t>(
        native.read_title_own_laws_v1(request.title_own_laws_title_id, request.title_own_laws)); break;
    case SemanticOperation::title_holder: request.result = static_cast<std::int32_t>(native.read_title_holder_v1(request.id, request.title_holder)); break;
    case SemanticOperation::occupation_targets: request.result = static_cast<std::int32_t>(native.read_war_occupation_targets_v1(request.id, request.occupation_targets)); break;
    case SemanticOperation::termination_options: request.result = static_cast<std::int32_t>(native.read_war_termination_options(request.id, request.termination_options)); break;
    case SemanticOperation::termination_terms: request.result = static_cast<std::int32_t>(native.read_war_termination_terms(request.id, request.termination_terms)); break;
    case SemanticOperation::exit_terms: request.result = static_cast<std::int32_t>(native.read_war_termination_exit_terms(request.id, request.exit_terms)); break;
    case SemanticOperation::marriage_diagnostic:
      request.bool_result = CollectMarriageProbe12002(
          BindContextImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), kExecutableSha256),
          request.diagnostic_json);
      break;
    case SemanticOperation::fixture_run_inbox:
      request.console_result = RunPrivateInboxFixture(request.console_fixture);
      request.diagnostic_json = SerializeInboxFixture(request.console_result);
      break;
    }
    if (diagnostic != nullptr) diagnostic->native.store("finish");
    const bool finish_result = FinishQueryMailbox(*envelope);
    if (diagnostic != nullptr) {
      diagnostic->finish_result.store(finish_result);
      diagnostic->frame_stable.store(envelope->frame_stable);
      diagnostic->native.store(finish_result ? "returned" : "finish_failed");
    }
    return finish_result;
  } catch (...) {
    if (diagnostic != nullptr) diagnostic->native.store("catch");
    return false;
  }
}

bool WorkerAdapter::read_marriage_diagnostic(std::string &output) const noexcept {
  output.clear();
  SemanticRequest request{};
  request.operation = SemanticOperation::marriage_diagnostic;
  if (!Run(request)) return false;
  output = std::move(request.diagnostic_json);
  return !output.empty();
}
bool WorkerAdapter::run_inbox_fixture(std::string &output) const noexcept {
  output.clear();
  SemanticRequest request{};
  request.operation = SemanticOperation::fixture_run_inbox;
  request.console_fixture = console_fixture_;
  request.envelope.snapshot_comparison =
      QuerySnapshotComparison12002::fixture_inbox_mutation;
  if (!Run(request)) return false;
  output = std::move(request.diagnostic_json);
  return request.console_result == ConsoleFixtureResult::executed;
}
game::SelectEventOptionResult WorkerAdapter::submit_select_event_option(std::int32_t option_index) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::select_event;
  request.id = option_index;
  return Run(request) ? static_cast<game::SelectEventOptionResult>(request.result) : game::SelectEventOptionResult::unavailable;
}
game::ReplyPendingInteractionResult WorkerAdapter::submit_reply_to_pending_interaction(game::PendingInteractionReply reply) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::reply;
  request.reply = reply;
  return Run(request) ? static_cast<game::ReplyPendingInteractionResult>(request.result) : game::ReplyPendingInteractionResult::unavailable;
}
game::AcknowledgePendingInteractionResult WorkerAdapter::submit_acknowledge_pending_interaction(std::int32_t pending_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::acknowledge;
  request.id = pending_id;
  return Run(request) ? static_cast<game::AcknowledgePendingInteractionResult>(request.result) : game::AcknowledgePendingInteractionResult::unavailable;
}
game::RaiseTroopsResult WorkerAdapter::submit_raise_troops_default() const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::raise;

  return Run(request) ? static_cast<game::RaiseTroopsResult>(request.result) : game::RaiseTroopsResult::unavailable;
}
game::HaltArmyResult WorkerAdapter::submit_halt_army(std::int32_t army_id) const noexcept {
  SemanticRequest request; request.operation = SemanticOperation::halt;
  request.id = army_id;
  return Run(request) ? static_cast<game::HaltArmyResult>(request.result) : game::HaltArmyResult::unavailable;
}
game::MoveArmyResult WorkerAdapter::submit_move_army(std::int32_t army_id, std::int32_t province_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::move;
  request.id = army_id; request.other_id = province_id;
  return Run(request) ? static_cast<game::MoveArmyResult>(request.result) : game::MoveArmyResult::unavailable;
}
game::DisbandArmyResult WorkerAdapter::submit_disband_army(std::int32_t army_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::disband;
  request.id = army_id;
  return Run(request) ? static_cast<game::DisbandArmyResult>(request.result) : game::DisbandArmyResult::unavailable;
}
game::SplitArmyHalfResult WorkerAdapter::submit_split_army_half(std::int32_t army_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::split;
  request.id = army_id;
  return Run(request) ? static_cast<game::SplitArmyHalfResult>(request.result) : game::SplitArmyHalfResult::unavailable;
}
game::MergeArmiesResult WorkerAdapter::submit_merge_armies(std::int32_t destination, std::int32_t source) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::merge;
  request.id = destination; request.other_id = source;
  return Run(request) ? static_cast<game::MergeArmiesResult>(request.result) : game::MergeArmiesResult::unavailable;
}
game::StartAssaultResult WorkerAdapter::submit_start_assault(std::int32_t siege_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::assault_start;
  request.id = siege_id;
  return Run(request) ? static_cast<game::StartAssaultResult>(request.result) : game::StartAssaultResult::unavailable;
}
game::StopAssaultResult WorkerAdapter::submit_stop_assault(std::int32_t siege_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::assault_stop;
  request.id = siege_id;
  return Run(request) ? static_cast<game::StopAssaultResult>(request.result) : game::StopAssaultResult::unavailable;
}
game::DeclareWarResult WorkerAdapter::submit_declare_war(const game::DeclarableWarSnapshot &declaration) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::declare;
  request.declaration = declaration;
  return Run(request) ? static_cast<game::DeclareWarResult>(request.result) : game::DeclareWarResult::unavailable;
}
game::ArrangeMarriageResult WorkerAdapter::submit_arrange_marriage(const game::ArrangeMarriageChoice &choice) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::marriage;
  request.choice = choice;
  return Run(request) ? static_cast<game::ArrangeMarriageResult>(request.result) : game::ArrangeMarriageResult::unavailable;
}
game::EnforceDemandsResult WorkerAdapter::submit_enforce_demands(std::int32_t war_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::enforce;
  request.id = war_id;
  return Run(request) ? static_cast<game::EnforceDemandsResult>(request.result) : game::EnforceDemandsResult::unavailable;
}
game::SurrenderWarResult WorkerAdapter::submit_surrender_war(std::int32_t war_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::surrender;
  request.id = war_id;
  return Run(request) ? static_cast<game::SurrenderWarResult>(request.result) : game::SurrenderWarResult::unavailable;
}
game::OfferWhitePeaceResult WorkerAdapter::submit_offer_white_peace(std::int32_t war_id) const noexcept {
  SemanticRequest request{};
  request.operation = SemanticOperation::white_peace;
  request.id = war_id;
  return Run(request) ? static_cast<game::OfferWhitePeaceResult>(request.result) : game::OfferWhitePeaceResult::unavailable;
}
game::PreviewMoveArmyResult WorkerAdapter::preview_move_army(std::int32_t army, std::int32_t province) const noexcept {
  SemanticRequest request{}; request.operation = SemanticOperation::preview;
  request.id = army; request.other_id = province;
  return Run(request) ? request.preview : game::PreviewMoveArmyResult{};
}
bool WorkerAdapter::read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &output) const noexcept {
  output.clear(); SemanticRequest request{}; request.operation = SemanticOperation::declarations;
  if (!Run(request)) return false;
  output = std::move(request.declarations); return request.bool_result;
}
game::ReadDeclarableWarsResult WorkerAdapter::read_declarable_wars_for_target(
    std::int32_t target_character_id,
    std::vector<game::DeclarableWarSnapshot> &output) const noexcept {
  output.clear();
  SemanticRequest request{};
  request.operation = SemanticOperation::declarations_for_target;
  request.id = target_character_id;
  if (!Run(request)) return game::ReadDeclarableWarsResult::unavailable;
  output = std::move(request.declarations);
  return static_cast<game::ReadDeclarableWarsResult>(request.result);
}
game::ReadArrangeMarriageChoicesResult WorkerAdapter::read_arrange_marriage_choices(
    std::vector<game::ArrangeMarriageChoice> &output, game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept {
  output.clear(); diagnostics = {};
  SemanticRequest request{}; request.operation = SemanticOperation::marriage_choices;
  if (!Run(request)) return game::ReadArrangeMarriageChoicesResult::unavailable;
  output = std::move(request.marriage_choices); diagnostics = std::move(request.marriage_diagnostics);
  return static_cast<game::ReadArrangeMarriageChoicesResult>(request.result);
}
game::ReadArmyStrengthsResult WorkerAdapter::read_army_strengths(std::vector<game::ArmyStrengthSnapshot> &output) const noexcept {
  output.clear(); SemanticRequest request{}; request.operation = SemanticOperation::strengths;
  if (!Run(request)) return game::ReadArmyStrengthsResult::unavailable;
  output = std::move(request.strengths); return static_cast<game::ReadArmyStrengthsResult>(request.result);
}
game::ReadArrangeMarriageFamilyCandidatesResultV1
WorkerAdapter::read_arrange_marriage_family_candidates_v1(
    std::int32_t subject_character_id,
    std::vector<game::ArrangeMarriageFamilyCandidateV1> &output,
    game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept {
  output.clear();
  diagnostics = {};
  SemanticRequest request{};
  request.operation = SemanticOperation::family_candidates;
  request.id = subject_character_id;
  if (!Run(request)) return game::ReadArrangeMarriageFamilyCandidatesResultV1::unavailable;
  output = std::move(request.family_candidates);
  diagnostics = std::move(request.marriage_diagnostics);
  return static_cast<game::ReadArrangeMarriageFamilyCandidatesResultV1>(request.result);
}
game::ReadCombatSimulationInputsResult WorkerAdapter::read_combat_simulation_inputs(const game::CombatSimulationInputsRequest &input, game::CombatSimulationInputsSnapshot &output) const noexcept {
  output = {}; SemanticRequest request{}; request.operation = SemanticOperation::combat_v2;
  request.combat_request = input;
  if (!Run(request)) return game::ReadCombatSimulationInputsResult::unavailable;
  output = std::move(request.combat_v2); return static_cast<game::ReadCombatSimulationInputsResult>(request.result);
}
game::ReadCombatSimulationInputsV3Result WorkerAdapter::read_combat_simulation_inputs_v3(const game::CombatSimulationInputsRequest &input, game::CombatSimulationInputsV3Snapshot &output) const noexcept {
  output = {}; SemanticRequest request{}; request.operation = SemanticOperation::combat_v3;
  request.combat_request = input;
  if (!Run(request)) return game::ReadCombatSimulationInputsV3Result::unavailable;
  output = std::move(request.combat_v3); return static_cast<game::ReadCombatSimulationInputsV3Result>(request.result);
}
game::ReadPlayerClaimsV1Result WorkerAdapter::read_player_claims_v1(
    const std::vector<std::int32_t> &ids, game::PlayerClaimsV1 &output) const noexcept {
  output = {};
  try {
    SemanticRequest request{};
    request.operation = SemanticOperation::player_claims;
    request.player_claim_title_ids = ids;
    if (!Run(request)) return game::ReadPlayerClaimsV1Result::unavailable;
    output = std::move(request.player_claims);
    return static_cast<game::ReadPlayerClaimsV1Result>(request.result);
  } catch (...) { return game::ReadPlayerClaimsV1Result::unavailable; }
}
game::ReadTitleOwnLawsV1Result WorkerAdapter::read_title_own_laws_v1(
    std::uint32_t title_id, game::TitleOwnLawsV1 &output) const noexcept {
  output = {};
  try {
    SemanticRequest request{};
    request.operation = SemanticOperation::title_own_laws;
    request.title_own_laws_title_id = title_id;
    if (!Run(request)) return game::ReadTitleOwnLawsV1Result::unavailable;
    output = std::move(request.title_own_laws);
    return static_cast<game::ReadTitleOwnLawsV1Result>(request.result);
  } catch (...) { return game::ReadTitleOwnLawsV1Result::unavailable; }
}
game::ReadTitleHolderV1Result WorkerAdapter::read_title_holder_v1(
    std::int32_t title_id, game::TitleHolderV1 &output) const noexcept {
  output = {};
  SemanticRequest request{};
  request.operation = SemanticOperation::title_holder;
  request.id = title_id;
  if (!Run(request)) return game::ReadTitleHolderV1Result::unavailable;
  output = std::move(request.title_holder);
  return static_cast<game::ReadTitleHolderV1Result>(request.result);
}
game::ReadWarOccupationTargetsV1Result WorkerAdapter::read_war_occupation_targets_v1(
    std::int32_t war_id, game::WarOccupationTargetsV1 &output) const noexcept {
  output = {};
  SemanticRequest request{};
  request.operation = SemanticOperation::occupation_targets;
  request.id = war_id;
  if (!Run(request)) return game::ReadWarOccupationTargetsV1Result::unavailable;
  output = std::move(request.occupation_targets);
  return static_cast<game::ReadWarOccupationTargetsV1Result>(request.result);
}
game::ReadWarTerminationOptionsResult WorkerAdapter::read_war_termination_options(std::int32_t war_id, game::WarTerminationOptionsSnapshot &output) const noexcept {
  output = {}; SemanticRequest request{}; request.operation = SemanticOperation::termination_options;
  request.envelope.snapshot_comparison = QuerySnapshotComparison12002::war_termination_options;
  request.id = war_id;
  if (!Run(request)) return game::ReadWarTerminationOptionsResult::unavailable;
  output = std::move(request.termination_options); return static_cast<game::ReadWarTerminationOptionsResult>(request.result);
}
game::ReadWarTerminationTermsResult WorkerAdapter::read_war_termination_terms(std::int32_t war_id, game::WarTerminationTermsSnapshot &output) const noexcept {
  output = {}; SemanticRequest request{}; request.operation = SemanticOperation::termination_terms;
  request.id = war_id;
  if (!Run(request)) return game::ReadWarTerminationTermsResult::unavailable;
  output = std::move(request.termination_terms); return static_cast<game::ReadWarTerminationTermsResult>(request.result);
}
game::ReadWarTerminationExitTermsResult WorkerAdapter::read_war_termination_exit_terms(std::int32_t war_id, game::WarTerminationExitTermsSnapshot &output) const noexcept {
  output = {}; SemanticRequest request{}; request.operation = SemanticOperation::exit_terms;
  request.id = war_id;
  if (!Run(request)) return game::ReadWarTerminationExitTermsResult::unavailable;
  output = std::move(request.exit_terms); return static_cast<game::ReadWarTerminationExitTermsResult>(request.result);
}
} // namespace xar::ck3_12002

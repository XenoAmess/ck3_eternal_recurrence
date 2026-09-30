#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include <atomic>
#include <utility>

namespace xar::ck3_12002 {
namespace {
enum class SemanticOperation {
  select_event, reply, acknowledge, raise, move, disband, split, merge, assault_start, assault_stop, declare, marriage, enforce, surrender, white_peace,
  preview, declarations, marriage_choices, strengths, combat_v2, combat_v3,
  termination_options, termination_terms, exit_terms
};
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
  game::ArrangeMarriageQueryDiagnostics marriage_diagnostics{};
  std::vector<game::ArmyStrengthSnapshot> strengths;
  game::CombatSimulationInputsSnapshot combat_v2{};
  game::CombatSimulationInputsV3Snapshot combat_v3{};
  game::WarTerminationOptionsSnapshot termination_options{};
  game::WarTerminationTermsSnapshot termination_terms{};
  game::WarTerminationExitTermsSnapshot exit_terms{};
};

WorkerAdapter::WorkerAdapter(const game::GameAdapter &native_adapter,
                             ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept
    : native_(&native_adapter), mailbox_(&mailbox) {}
const game::GameAdapter &WorkerAdapter::native_adapter() const noexcept { return *native_; }
const game::AdapterDescriptor &WorkerAdapter::descriptor() const noexcept { return native_->descriptor(); }
bool WorkerAdapter::enabled() const noexcept { return native_->enabled(); }

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
    if (!enabled() || descriptor().executable_sha256 != kExecutableSha256 ||
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
    const bool available = native_->read_snapshot(observed) &&
        observed.date_raw == stamp.date_raw && observed.paused == stamp.paused;
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

game::PauseSubmitResult WorkerAdapter::submit_pause_map() const noexcept { return native_->submit_pause_map(); }
game::ResumeSubmitResult WorkerAdapter::submit_resume_map() const noexcept { return native_->submit_resume_map(); }
bool WorkerAdapter::submit_set_speed(std::int32_t speed) const noexcept { return native_->submit_set_speed(speed); }
game::SaveCheckpointResult WorkerAdapter::submit_save_checkpoint() const noexcept { return native_->submit_save_checkpoint(); }

bool WorkerAdapter::Run(SemanticRequest &request) const noexcept {
  try {
    request.envelope.game = native_;
    request.envelope.mailbox = mailbox_;
    request.envelope.typed_context = &request;
    if (!read_snapshot(request.envelope.expected_snapshot) ||
        !request.envelope.expected_snapshot.paused ||
        !request.envelope.expected_snapshot.map_ready) return false;
    {
      std::lock_guard guard(snapshot_mutex_);
      request.envelope.expected_snapshot_revision = snapshot_revision_;
    }
    const auto submitted = ck3_11906::TrySubmitMainThreadQueryV1(
        *mailbox_, &ExecuteSemanticAdapter12002, &request.envelope, request.envelope.ticket);
    if (submitted != ck3_11906::MainThreadQuerySubmitResultV1::submitted) return false;
    auto wait = ck3_11906::WaitForMainThreadQueryV1(*mailbox_, request.envelope.ticket, 8'000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(*mailbox_, request.envelope.ticket, 2'000);
    const auto reclaimed = ck3_11906::ReclaimMainThreadQueryV1(*mailbox_, request.envelope.ticket);
    return wait == ck3_11906::MainThreadQueryWaitResultV1::completed &&
        reclaimed == ck3_11906::MainThreadQueryReclaimResultV1::reclaimed &&
        request.envelope.frame_stable;
  } catch (...) { return false; }
}

bool ExecuteSemanticAdapter12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !EnterQueryMailbox(*envelope, stamp, &ExecuteSemanticAdapter12002)) return false;
  auto &request = *static_cast<WorkerAdapter::SemanticRequest *>(envelope->typed_context);
  const auto &native = *envelope->game;
  try {
    switch (request.operation) {
    case SemanticOperation::select_event: request.result = static_cast<std::int32_t>(native.submit_select_event_option(request.id)); break;
    case SemanticOperation::reply: request.result = static_cast<std::int32_t>(native.submit_reply_to_pending_interaction(request.reply)); break;
    case SemanticOperation::acknowledge: request.result = static_cast<std::int32_t>(native.submit_acknowledge_pending_interaction(request.id)); break;
    case SemanticOperation::raise: request.result = static_cast<std::int32_t>(native.submit_raise_troops_default()); break;
    case SemanticOperation::move: request.result = static_cast<std::int32_t>(native.submit_move_army(request.id, request.other_id)); break;
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
    case SemanticOperation::marriage_choices: request.result = static_cast<std::int32_t>(native.read_arrange_marriage_choices(request.marriage_choices, request.marriage_diagnostics)); break;
    case SemanticOperation::strengths: request.result = static_cast<std::int32_t>(native.read_army_strengths(request.strengths)); break;
    case SemanticOperation::combat_v2: request.result = static_cast<std::int32_t>(native.read_combat_simulation_inputs(request.combat_request, request.combat_v2)); break;
    case SemanticOperation::combat_v3: request.result = static_cast<std::int32_t>(native.read_combat_simulation_inputs_v3(request.combat_request, request.combat_v3)); break;
    case SemanticOperation::termination_options: request.result = static_cast<std::int32_t>(native.read_war_termination_options(request.id, request.termination_options)); break;
    case SemanticOperation::termination_terms: request.result = static_cast<std::int32_t>(native.read_war_termination_terms(request.id, request.termination_terms)); break;
    case SemanticOperation::exit_terms: request.result = static_cast<std::int32_t>(native.read_war_termination_exit_terms(request.id, request.exit_terms)); break;
    }
    return FinishQueryMailbox(*envelope);
  } catch (...) { return false; }
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
game::ReadWarTerminationOptionsResult WorkerAdapter::read_war_termination_options(std::int32_t war_id, game::WarTerminationOptionsSnapshot &output) const noexcept {
  output = {}; SemanticRequest request{}; request.operation = SemanticOperation::termination_options;
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

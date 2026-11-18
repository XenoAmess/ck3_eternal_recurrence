#include "xar_bridge/ck3_1210_personal_cash_frame_v1.hpp"

// Reuse the already-qualified RAM model and independent JSON reader without
// changing its frozen source or inventing another monthly implementation.
#define main PersonalCashProviderColdFixtureMainV1
#include "ck3_1210_personal_cash_v1_test.cpp"
#undef main

#include <windows.h>
#include "fresh_bridge_personal_cash_result1210.inc"

namespace {
using namespace xar::game;
using namespace xar::ck3_11906;
constexpr std::array<std::string_view, 3> kCashFrameCapabilities{
    kPersonalCashCapabilityV1, "game.state.snapshot", "game.query.fresh-full-state.v1"};
constexpr std::array<std::string_view, 2> kNoCashCapabilities{
    "game.state.snapshot", "game.query.fresh-full-state.v1"};
class CashFrameAdapter final : public GameAdapter {
public:
  using Reader = bool (*)(void *, Snapshot &) noexcept;
  CashFrameAdapter(const AdapterDescriptor &d, Reader reader = nullptr, void *context = nullptr)
      : descriptor_(d), reader_(reader), context_(context) {}
  mutable unsigned snapshot_calls = 0;
  bool adapter_enabled = true;
  const AdapterDescriptor &descriptor() const noexcept override {
    return descriptor_;
  }
  bool enabled() const noexcept override { return adapter_enabled; }
  bool read_snapshot(xar::game::Snapshot &output) const noexcept override {
    ++snapshot_calls;
    if (reader_ == nullptr) { output = {}; return false; }
    return reader_(context_, output);
  }
  xar::game::PauseSubmitResult
  submit_pause_map(xar::game::Snapshot *observed_snapshot) const noexcept override {
    if (observed_snapshot != nullptr) {
      *observed_snapshot = {};
    }
    return xar::game::PauseSubmitResult::unavailable;
  }
  xar::game::ResumeSubmitResult
  submit_resume_map(xar::game::Snapshot *observed_snapshot) const noexcept override {
    if (observed_snapshot != nullptr) {
      *observed_snapshot = {};
    }
    return xar::game::ResumeSubmitResult::unavailable;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  xar::game::SelectEventOptionResult
  submit_select_event_option(std::int32_t) const noexcept override {
    return xar::game::SelectEventOptionResult::unavailable;
  }
  xar::game::SaveCheckpointResult
  submit_save_checkpoint() const noexcept override {
    return {};
  }
  xar::game::ReplyPendingInteractionResult
  submit_reply_to_pending_interaction(
      xar::game::PendingInteractionReply) const noexcept override {
    return xar::game::ReplyPendingInteractionResult::unavailable;
  }
  xar::game::RaiseTroopsResult
  submit_raise_troops_default() const noexcept override {
    return xar::game::RaiseTroopsResult::unavailable;
  }
  xar::game::MoveArmyResult
  submit_move_army(std::int32_t, std::int32_t) const noexcept override {
    return xar::game::MoveArmyResult::unavailable;
  }
  xar::game::PreviewMoveArmyResult
  preview_move_army(std::int32_t, std::int32_t) const noexcept override {
    return {};
  }
  xar::game::DisbandArmyResult
  submit_disband_army(std::int32_t) const noexcept override {
    return xar::game::DisbandArmyResult::unavailable;
  }
  xar::game::SplitArmyHalfResult
  submit_split_army_half(std::int32_t) const noexcept override {
    return xar::game::SplitArmyHalfResult::unavailable;
  }
  xar::game::MergeArmiesResult
  submit_merge_armies(std::int32_t, std::int32_t) const noexcept override {
    return xar::game::MergeArmiesResult::unavailable;
  }
  xar::game::StartAssaultResult
  submit_start_assault(std::int32_t) const noexcept override {
    return xar::game::StartAssaultResult::unavailable;
  }
  xar::game::StopAssaultResult
  submit_stop_assault(std::int32_t) const noexcept override {
    return xar::game::StopAssaultResult::unavailable;
  }
  bool read_declarable_wars(
      std::vector<xar::game::DeclarableWarSnapshot> &output) const noexcept override {
    output.clear();
    return false;
  }
  xar::game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t, std::vector<xar::game::DeclarableWarSnapshot> &output)
      const noexcept override {
    output.clear();
    return xar::game::ReadDeclarableWarsResult::unavailable;
  }
  xar::game::DeclareWarResult submit_declare_war(
      const xar::game::DeclarableWarSnapshot &) const noexcept override {
    return xar::game::DeclareWarResult::unavailable;
  }
  xar::game::ReadArrangeMarriageChoicesResult
  read_arrange_marriage_choices(
      std::vector<xar::game::ArrangeMarriageChoice> &output,
      xar::game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    output.clear();
    diagnostics = {};
    return xar::game::ReadArrangeMarriageChoicesResult::unavailable;
  }
  xar::game::ArrangeMarriageResult submit_arrange_marriage(
      const xar::game::ArrangeMarriageChoice &) const noexcept override {
    return xar::game::ArrangeMarriageResult::unavailable;
  }
  xar::game::EnforceDemandsResult
  submit_enforce_demands(std::int32_t) const noexcept override {
    return xar::game::EnforceDemandsResult::unavailable;
  }
  xar::game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<xar::game::ArmyStrengthSnapshot> &output) const noexcept override {
    output.clear();
    return xar::game::ReadArmyStrengthsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsResult
  read_combat_simulation_inputs(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadCombatSimulationInputsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsV3Result
  read_combat_simulation_inputs_v3(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsV3Snapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadCombatSimulationInputsV3Result::unavailable;
  }
  xar::game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t,
      xar::game::WarTerminationOptionsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationOptionsResult::unavailable;
  }
  xar::game::ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t,
      xar::game::WarTerminationTermsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationTermsResult::unavailable;
  }
  xar::game::ReadWarTerminationExitTermsResult
  read_war_termination_exit_terms(
      std::int32_t,
      xar::game::WarTerminationExitTermsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationExitTermsResult::unavailable;
  }
  xar::game::SurrenderWarResult
  submit_surrender_war(std::int32_t) const noexcept override {
    return xar::game::SurrenderWarResult::unavailable;
  }
  xar::game::OfferWhitePeaceResult
  submit_offer_white_peace(std::int32_t) const noexcept override {
    return xar::game::OfferWhitePeaceResult::unavailable;
  }
private:
  const AdapterDescriptor &descriptor_;
  Reader reader_ = nullptr;
  void *context_ = nullptr;
};

enum class FrameMode { normal, raw_fail_first, raw_fail_second, raw_fault,
    revision_during_read, stop_after_read, snapshot_scope_change,
    adapter_identity_after_second_full, revision_source_after_second_full };

struct CashFrameFixture;
bool ReadRawCashFull(void *, Snapshot &) noexcept;

struct CashFrameFixture {
  Fixture ram;
  AdapterDescriptor parent_descriptor{kAdapterId, kGameVersion, kExecutableSha256,
      "xar_checkpoint", kCashFrameCapabilities};
  AdapterDescriptor raw_descriptor = parent_descriptor;
  CashFrameAdapter parent_adapter{parent_descriptor};
  CashFrameAdapter raw_adapter{raw_descriptor, &ReadRawCashFull, this};
  MainThreadQueryMailboxV1 mailbox{};
  PersonalGoldMailboxContextV1 parent{};
  PersonalCashMailboxContextV1 cash{};
  MainThreadExecutionStampV1 stamp{};
  FrameMode mode = FrameMode::normal;
  bool reset_proof_after_read=false,advance_epoch_after_read=false,drain_hook_after_read=false;
  std::uint64_t foreign_revision = 0;

  CashFrameFixture() {
    cash.bindings = ram.bindings;
    cash.bindings.integration_native_calls_permitted = false;
    cash.bindings.monthly.integration_native_calls_permitted = false;
    cash.native_full_adapter = &raw_adapter;
    cash.expected_full = ram.published;
    cash.expected_native_revision = ram.revision;
    cash.current_published_revision = &ram.revision;
    parent.kind = ActorObservationKindV1::personal_cash;
    parent.game = &parent_adapter; parent.bindings = ram.bindings.gold;
    parent.mailbox = &mailbox; parent.ticket.sequence = 41; parent.cash = &cash;
    stamp.thread_id = GetCurrentThreadId(); stamp.pump_epoch = 9;
    stamp.tls_initialized = 1; stamp.tls_main_thread_marker = 1;
    stamp.tls_context = 0x123400; stamp.paused = true; stamp.date_raw = ram.world.date_raw;
    stamp.game_state = reinterpret_cast<std::uintptr_t>(ram.state_pointer);
    stamp.jomini_state = reinterpret_cast<std::uintptr_t>(ram.jomini_pointer);
    mailbox.offline_fixture=true; // RAM model is never actual-module qualification.
    mailbox.iat_hook_installed.store(true); mailbox.owner_thread_id.store(stamp.thread_id);
    mailbox.paused_owner_verified_pump_epochs.store(kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
    mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
    mailbox.pump_epochs.store(stamp.pump_epoch);mailbox.active_hook_calls.store(1);
    mailbox.published_sequence.store(parent.ticket.sequence);
    mailbox.executor_started_sequence.store(parent.ticket.sequence);
    mailbox.executor_started_pump_epoch.store(stamp.pump_epoch);
    mailbox.executor_context = &parent;
    mailbox.executor.store(&ExecutePersonalGoldMailboxV1);
    // The real MQ writes execution_stamp only AFTER the callback. Leaving it
    // empty ensures this fixture exercises the actual pre-callback contract.
    ram.ResetCalls();
  }
  bool Invoke(bool direct = false) {
    return direct ? ExecutePersonalCashOnActorOwnerV1(parent, stamp) :
        ExecutePersonalGoldMailboxV1(&parent, stamp);
  }
  void ClosedSharedGates() const {
    Require(!cash.bindings.integration_native_calls_permitted &&
        !cash.bindings.monthly.integration_native_calls_permitted &&
        cash.bindings.monthly.native_call_admission == nullptr &&
        cash.bindings.monthly.native_call_admission_context == nullptr,
        "only an admitted local binding copy opens gates and retains owner callback");
  }
};

bool ReadRawCashFull(void *opaque, Snapshot &out) noexcept {
  auto &f = *static_cast<CashFrameFixture *>(opaque);
  f.ClosedSharedGates();
  const auto calls = f.raw_adapter.snapshot_calls;
  if ((f.mode == FrameMode::raw_fail_first && calls == 1) ||
      (f.mode == FrameMode::raw_fail_second && calls == 2)) return false;
  if (f.mode == FrameMode::raw_fault) { Fault(); return false; }
  if (f.mode == FrameMode::revision_during_read) --f.ram.revision;
  std::uint64_t ignored_fixture_revision = 0;
  const bool result = CurrentFull(&f.ram, out, ignored_fixture_revision);
  if (f.mode == FrameMode::stop_after_read) f.mailbox.stop_requested.store(true);
  if(f.reset_proof_after_read)f.mailbox.proof_reset_requested.store(true);
  if(f.advance_epoch_after_read)f.mailbox.pump_epochs.store(f.stamp.pump_epoch+1);
  if(f.drain_hook_after_read)f.mailbox.active_hook_calls.store(0);
  if (f.mode == FrameMode::snapshot_scope_change && calls == 2)
    out.active_wars[0].war_id = 66;
  if (calls == 2 && f.mode == FrameMode::adapter_identity_after_second_full)
    f.cash.native_full_adapter = &f.parent_adapter; // Same tuple/caps; different physical producer.
  if (calls == 2 && f.mode == FrameMode::revision_source_after_second_full) {
    f.foreign_revision = f.ram.revision; // Same value; different physical published source.
    f.cash.current_published_revision = &f.foreign_revision;
  }
  return result;
}

Json CashFrameJson(const CashFrameFixture &f) {
  const auto root = JsonReader(SerializePersonalCashFrameResultV1(f.cash)).Document();
  Require(root.At("step").Text() == kPersonalCashStepV1 &&
      root.At("private_build").Flag() && root.At("read_only").Flag(),
      "frame emits existing original inner CASH result");
  return root.At("war_cash_current_resources");
}
void CashFrameFailure(CashFrameFixture &f, bool zero_calls, bool direct = false) {
  f.cash.observation.completed = f.cash.observation.same_frame_ready = true;
  f.cash.observation.personal_gold_raw = 99;
  f.cash.observation.monthly_gross_income_raw = 99;
  f.cash.observation.monthly_total_expenses_raw = 99;
  f.cash.observation.monthly_net_income_raw = 99;
  f.cash.observation.current_full_call_attempts = 99;
  f.cash.observation.context_call_attempts = 99;
  f.cash.application_main_observed = true;
  Require(f.Invoke(direct), "unavailable DATA remains completed Actor infrastructure");
  const auto &o = f.cash.observation;
  Require(!o.completed && !o.same_frame_ready && !o.personal_gold_raw &&
      !o.monthly_gross_income_raw && !o.monthly_total_expenses_raw && !o.monthly_net_income_raw,
      "Actor admission/frame failure clears every stale monetary value");
  Require(o.current_full_call_attempts == f.raw_adapter.snapshot_calls &&
      o.context_call_attempts == f.ram.context_calls &&
      o.gross_call_attempted == (f.ram.gross_calls != 0) &&
      o.expenses_call_attempted == (f.ram.expense_calls != 0) &&
      f.parent_adapter.snapshot_calls == 0, "real attempts retained; never nested Worker/parent read");
  if (zero_calls) {
    Require(f.ram.core_calls == 0 && f.raw_adapter.snapshot_calls == 0 &&
        f.ram.context_calls == 0 && f.ram.gross_calls == 0 && f.ram.expense_calls == 0 &&
        !f.cash.application_main_observed && !f.parent.application_main_observed,
        "unqualified owner makes zero native reads");
  }
  f.ClosedSharedGates();
  const auto cash = CashFrameJson(f);
  Require(cash.At("current_treasury").IsNull() &&
      cash.At("player_monthly_gross_income").IsNull() &&
      cash.At("player_monthly_total_expenses").IsNull() &&
      cash.At("player_monthly_net_income").IsNull() &&
      !cash.At("readiness").At("same_frame_ready").Flag(),
      "failed Actor frame serializes only explicit unknown amounts");
  UnknownScope(o, cash);
}
void CashFrameSuccess(CashFrameFixture &f) {
  Require(f.Invoke() && f.cash.application_main_observed && f.parent.application_main_observed &&
      f.cash.observation.completed && f.cash.observation.same_frame_ready,
      "existing Actor MQ branch invokes admitted personal CASH");
  const auto &o = f.cash.observation;
  Require(o.current_full_call_attempts == 2 && f.raw_adapter.snapshot_calls == 2 &&
      f.parent_adapter.snapshot_calls == 0 && f.ram.context_calls == 2 &&
      f.ram.gross_calls == 1 && f.ram.expense_calls == 1,
      "only raw native Full adapter and existing monthly seam execute");
  Require(o.context_call_attempts == 2 && o.gross_call_attempted && o.expenses_call_attempted,
      "actual monthly attempts copied through owner layer");
  Require(f.mailbox.execution_stamp.thread_id == 0,
      "callback does not require the post-callback execution_stamp");
  f.ClosedSharedGates();
  const auto cash = CashFrameJson(f);
  Fixed(cash, "current_treasury", f.ram.wallet);
  Fixed(cash, "player_monthly_gross_income", f.ram.gross);
  Fixed(cash, "player_monthly_total_expenses", f.ram.expenses);
  Fixed(cash, "player_monthly_net_income", f.ram.gross - f.ram.expenses);
  Require(cash.At("status").Text() == "partial" &&
      cash.At("snapshot_revision").Number() == "18446744073709551615" &&
      cash.At("played_character_id").Number() == std::to_string(kActor) &&
      cash.At("active_war_ids").elements.size() == f.ram.world.active_wars.size() &&
      cash.At("player_army_ids").elements.size() == f.ram.world.player_armies.size(),
      "partial source preserves original signed actor/revision/actual scope");
  UnknownScope(o, cash);
}
constexpr std::array<std::string_view, 4> kV2CashFrameCapabilities{
    kPersonalCashCapabilityV1, kPersonalCashCapabilityV2,
    "game.state.snapshot", "game.query.fresh-full-state.v1"};
void PrepareCashScopeV2(CashFrameFixture &f) {
  f.cash.scope_version = PersonalCashScopeVersion::florin_unit_full_id_v2;
  f.parent_descriptor.capabilities = kV2CashFrameCapabilities;
  f.raw_descriptor.capabilities = kV2CashFrameCapabilities;
  f.ram.world.player_armies[0].army_id = (std::numeric_limits<std::int32_t>::min)();
  f.ram.world.player_armies[1].army_id = -2;
  f.ram.published = f.ram.world; f.cash.expected_full = f.ram.published;
}
std::string RunCashQueryCase(std::string_view mode) {
  CashFrameFixture f; PrepareCashScopeV2(f);
  const bool no_context = mode == "--emit-query-v2-monthly-unknown";
  const bool owner_after_gross = mode == "--emit-query-v2-owner-after-gross";
  if (owner_after_gross) {
    f.ram.gross_before_return = +[](void *opaque) noexcept {
      static_cast<CashFrameFixture *>(opaque)->mailbox.stop_requested.store(true);
    };
    f.ram.gross_hook_context = &f;
  } else if (mode == "--emit-query-v2-wallet-drift") f.ram.mode = Mode::wallet_after;
  else if (no_context) f.ram.mode = Mode::null_context;
  else if (mode == "--emit-query-v2-net-overflow") {
    f.ram.gross = (std::numeric_limits<std::int64_t>::min)(); f.ram.expenses = 1;
  } else if (mode == "--emit-query-v2-adapter-drift")
    f.mode = FrameMode::adapter_identity_after_second_full;
  else if (mode == "--emit-query-v2-revision-source-drift")
    f.mode = FrameMode::revision_source_after_second_full;
  else Require(mode == "--emit-query-v2-partial", "known real post-getter query case");
  Require(f.Invoke() && f.raw_adapter.snapshot_calls == (owner_after_gross ? 1U : 2U) &&
      f.parent_adapter.snapshot_calls == 0 &&
      f.ram.context_calls == (no_context || owner_after_gross ? 1U : 2U) &&
      f.ram.gross_calls == (no_context ? 0U : 1U) &&
      f.ram.expense_calls == (no_context || owner_after_gross ? 0U : 1U),
      "actual Actor callback and existing monthly getters produce query result");
  f.ClosedSharedGates();
  return PersonalCashCommandResult1210("cash-v2-actor-query-original", f.cash,
      PersonalCashScopeVersion::florin_unit_full_id_v2);
}
bool OtherCashFrameExecutor(void *, const MainThreadExecutionStampV1 &) noexcept { return false; }
} // namespace

int main(int argc, char **argv) {
  if (argc == 2) {
    const std::string_view mode = argv[1];
    if (mode.starts_with("--emit-query-v2-")) {
      std::cout << RunCashQueryCase(mode) << '\n'; return 0;
    }
    CashFrameFixture f;
    Require(mode == "--emit-json", "known Actor CASH emission mode");
    CashFrameSuccess(f);
    std::cout << SerializePersonalCashFrameResultV1(f.cash) << '\n'; return 0;
  }
  Require(argc == 1, "no unexpected Actor CASH arguments");
  { CashFrameFixture f; CashFrameSuccess(f); }
  for (const auto change : {
      +[](CashFrameFixture &f) { f.parent.game = nullptr; },
      +[](CashFrameFixture &f) { f.mailbox.offline_fixture = false; },
      +[](CashFrameFixture &f) { f.parent_adapter.adapter_enabled = false; },
      +[](CashFrameFixture &f) { f.raw_adapter.adapter_enabled = false; },
      +[](CashFrameFixture &f) { f.parent_descriptor.game_version = "1.20.0.4"; },
      +[](CashFrameFixture &f) { f.raw_descriptor.executable_sha256 = "old"; },
      +[](CashFrameFixture &f) { f.parent_descriptor.capabilities = kNoCashCapabilities; },
      +[](CashFrameFixture &f) { f.raw_descriptor.capabilities = kNoCashCapabilities; },
      +[](CashFrameFixture &f) { f.cash.native_full_adapter = nullptr; },
      +[](CashFrameFixture &f) { f.parent.mailbox = nullptr; },
      +[](CashFrameFixture &f) { f.parent.ticket.sequence = 0; },
      +[](CashFrameFixture &f) { f.parent.bindings.exact_build_admitted = false; },
      +[](CashFrameFixture &f) { f.cash.bindings.exact_build_admitted = false; },
      +[](CashFrameFixture &f) { f.cash.bindings.gold.exact_build_admitted = false; },
      +[](CashFrameFixture &f) { f.cash.bindings.monthly.exact_build_admitted = false; },
      +[](CashFrameFixture &f) { f.cash.bindings.gold.core.jomini_state_slot = nullptr; },
      +[](CashFrameFixture &f) { f.cash.bindings.monthly.core.get_local_player = nullptr; },
      +[](CashFrameFixture &f) { f.cash.bindings.monthly.core.character_storage_slot = nullptr; },
      +[](CashFrameFixture &f) { f.cash.expected_native_revision = 0; },
      +[](CashFrameFixture &f) { f.cash.current_published_revision = nullptr; },
      +[](CashFrameFixture &f) { --f.ram.revision; },
      +[](CashFrameFixture &f) { f.stamp.thread_id = 0; },
      +[](CashFrameFixture &f) { f.stamp.pump_epoch = 0; },
      +[](CashFrameFixture &f) { f.stamp.tls_initialized = 0; },
      +[](CashFrameFixture &f) { f.stamp.tls_main_thread_marker = 0; },
      +[](CashFrameFixture &f) { f.stamp.tls_context = 0; },
      +[](CashFrameFixture &f) { f.stamp.paused = false; },
      +[](CashFrameFixture &f) { f.stamp.game_state = 0; },
      +[](CashFrameFixture &f) { ++f.stamp.jomini_state; },
      +[](CashFrameFixture &f) { f.mailbox.iat_hook_installed.store(false); },
      +[](CashFrameFixture &f) { f.mailbox.owner_thread_id.store(0); },
      +[](CashFrameFixture &f) { f.mailbox.failure_flags.store(1); },
      +[](CashFrameFixture &f) { f.mailbox.stop_requested.store(true); },
      +[](CashFrameFixture &f) { f.mailbox.proof_reset_requested.store(true); },
      +[](CashFrameFixture &f) { f.mailbox.pump_epochs.store(f.stamp.pump_epoch+1); },
      +[](CashFrameFixture &f) { f.mailbox.active_hook_calls.store(0); },
      +[](CashFrameFixture &f) { f.mailbox.paused_owner_verified_pump_epochs.store(1); },
      +[](CashFrameFixture &f) { f.mailbox.state.store(MainThreadQueryMailboxStateV1::queued); },
      +[](CashFrameFixture &f) { f.mailbox.published_sequence.store(42); },
      +[](CashFrameFixture &f) { f.mailbox.executor_started_sequence.store(42); },
      +[](CashFrameFixture &f) { f.mailbox.executor_started_pump_epoch.store(8); },
      +[](CashFrameFixture &f) { f.mailbox.executor_context = &f.cash; },
      +[](CashFrameFixture &f) { f.mailbox.executor.store(&OtherCashFrameExecutor); },
      +[](CashFrameFixture &f) { f.ram.state_pointer = nullptr; },
      +[](CashFrameFixture &f) { ++f.cash.expected_full.date_raw; },
      +[](CashFrameFixture &f) { f.cash.expected_full.paused = false; },
      +[](CashFrameFixture &f) { f.cash.expected_full.map_ready = false; },
      +[](CashFrameFixture &f) { f.cash.expected_full.played_character_alive = false; }}) {
    CashFrameFixture f; change(f); CashFrameFailure(f, true);
  }
  {
    CashFrameFixture f; f.parent.kind = ActorObservationKindV1::personal_gold;
    CashFrameFailure(f, true, true);
  }
  {
    CashFrameFixture f; f.parent.cash = nullptr;
    Require(f.Invoke() && f.ram.core_calls == 0 && f.raw_adapter.snapshot_calls == 0,
        "null typed cash context cannot dispatch native code");
  }
  for (const auto mode : {FrameMode::raw_fail_first, FrameMode::raw_fail_second,
      FrameMode::raw_fault, FrameMode::revision_during_read,
      FrameMode::stop_after_read, FrameMode::snapshot_scope_change}) {
    CashFrameFixture f; f.mode = mode; CashFrameFailure(f, false);
    Require(f.cash.observation.current_full_call_attempts > 0,
        "raw adapter failure retains attempted Full call");
  }
  for (const auto mode : {Mode::wallet_after, Mode::wallet_after_full, Mode::date_gross,
      Mode::pause_gross, Mode::actor_generation, Mode::war_after, Mode::army_after}) {
    CashFrameFixture f; f.ram.mode = mode; CashFrameFailure(f, false);
    Require(f.cash.observation.gross_call_attempted,
        "post-native drift retains actual monthly attempt");
  }
  {
    CashFrameFixture f; f.ram.mode = Mode::null_context;
    Require(f.Invoke() && f.cash.observation.completed && f.cash.observation.same_frame_ready &&
        f.cash.application_main_observed && f.cash.observation.personal_gold_raw == f.ram.wallet &&
        !f.cash.observation.monthly_gross_income_raw && !f.cash.observation.monthly_total_expenses_raw &&
        !f.cash.observation.monthly_net_income_raw && f.ram.context_calls == 1 &&
        f.raw_adapter.snapshot_calls == 2 && f.parent_adapter.snapshot_calls == 0,
        "real stable owner preserves wallet-only partial on unavailable context");
    const auto cash = CashFrameJson(f); Fixed(cash, "current_treasury", f.ram.wallet);
    Require(cash.At("status").Text() == "partial" &&
        !cash.At("readiness").At("monthly_net_income_ready").Flag(),
        "wallet-only Actor partial never becomes NET-ready");
    UnknownScope(f.cash.observation, cash); f.ClosedSharedGates();
  }
  {
    CashFrameFixture f;
    f.ram.gross = (std::numeric_limits<std::int64_t>::min)(); f.ram.expenses = 1;
    Require(f.Invoke() && f.cash.observation.completed && !f.cash.observation.monthly_net_income_raw,
        "owning Actor path preserves overflow NET unknown");
    const auto cash = CashFrameJson(f);
    Require(cash.At("monthly_net_income_unavailable_reason").Text() ==
        "war_cash_monthly_net_income_overflow", "Actor path retains exact legacy overflow reason");
    Fixed(cash, "player_monthly_gross_income", f.ram.gross); f.ClosedSharedGates();
  }
  {
    CashFrameFixture f; CashFrameSuccess(f);
    f.cash.application_main_observed = false;
    const auto cash = CashFrameJson(f);
    Require(cash.At("current_treasury").IsNull() &&
        !cash.At("readiness").At("same_frame_ready").Flag() &&
        f.cash.observation.personal_gold_raw == f.ram.wallet,
        "pure frame serializer refuses unowned copied values without mutating source");
  }
  const auto v2_setup = &PrepareCashScopeV2;
  {
    CashFrameFixture f; v2_setup(f);
    Require(f.Invoke() && f.cash.application_main_observed && f.cash.observation.completed,
        "explicit V2 Actor path retains signed UnitFullId");
    const auto result = JsonReader(SerializePersonalCashFrameResultV2(f.cash)).Document();
    const auto &cash = result.At("war_cash_current_resources");
    Require(result.At("step").Text() == kPersonalCashStepV2 &&
        cash.At("schema").Text() == kPersonalCashSchemaV2 &&
        cash.At("player_army_ids").elements[0].Number() == "-2147483648" &&
        cash.At("player_army_ids").elements[1].Number() == "-2",
        "V2 owner binds signed scope to its independent wire");
    Fixed(cash, "current_treasury", f.ram.wallet); UnknownScope(f.cash.observation, cash);
    const auto legacy = JsonReader(SerializePersonalCashFrameResultV1(f.cash)).Document();
    Require(legacy.At("war_cash_current_resources").At("current_treasury").IsNull(),
        "V2 owner receipt cannot revive V1 amounts");
    f.cash.application_main_observed = false;
    const auto unowned = JsonReader(SerializePersonalCashFrameResultV2(f.cash)).Document();
    Require(unowned.At("war_cash_current_resources").At("current_treasury").IsNull(),
        "V2 serializer retains owner qualification");
    f.ClosedSharedGates();
  }
  for (unsigned missing = 0; missing != 2; ++missing) {
    CashFrameFixture f; v2_setup(f);
    if (missing == 0) f.parent_descriptor.capabilities = kCashFrameCapabilities;
    else f.raw_descriptor.capabilities = kCashFrameCapabilities;
    Require(f.Invoke() && !f.cash.observation.completed &&
        f.raw_adapter.snapshot_calls == 0 && f.ram.context_calls == 0 &&
        f.ram.gross_calls == 0 && f.ram.expense_calls == 0,
        "V1 capability on either adapter cannot admit V2 native calls");
    f.ClosedSharedGates();
  }
  {
    CashFrameFixture f; v2_setup(f);
    f.cash.scope_version = PersonalCashScopeVersion::legacy_nonnegative_v1;
    Require(f.Invoke() && !f.cash.observation.completed && f.ram.context_calls == 0 &&
        f.cash.observation.unavailable_reason == "personal_cash_full_scope_unrepresentable",
        "advertising V2 never broadens the V1 reader");
  }
  for (const bool signed_scope : {false, true}) {
    for (const auto mode : {FrameMode::adapter_identity_after_second_full,
        FrameMode::revision_source_after_second_full}) {
      CashFrameFixture f;
      if (signed_scope) v2_setup(f);
      f.mode = mode;
      Require(f.Invoke() && f.raw_adapter.snapshot_calls == 2 && f.parent_adapter.snapshot_calls == 0 &&
          f.ram.context_calls == 2 && f.ram.gross_calls == 1 && f.ram.expense_calls == 1,
          "source changes only after actual second Full and all monthly getters");
      const auto &observed = f.cash.observation;
      Require(!observed.completed && !observed.same_frame_ready && !observed.personal_gold_raw &&
          !observed.monthly_gross_income_raw && !observed.monthly_total_expenses_raw &&
          !observed.monthly_net_income_raw && observed.current_full_call_attempts == 2 &&
          observed.context_call_attempts == 2 && observed.gross_call_attempted &&
          observed.expenses_call_attempted, "Full source drift clears money and retains attempts");
      if (mode == FrameMode::adapter_identity_after_second_full)
        Require(f.cash.native_full_adapter == &f.parent_adapter,
            "same-capability replacement producer really occurred");
      else Require(f.cash.current_published_revision == &f.foreign_revision &&
          f.foreign_revision == f.ram.revision, "same-valued revision source replacement occurred");
      const auto result = JsonReader(signed_scope ? SerializePersonalCashFrameResultV2(f.cash) :
          SerializePersonalCashFrameResultV1(f.cash)).Document();
      const auto &cash = result.At("war_cash_current_resources");
      Require(cash.At("status").Text() == "unavailable" && cash.At("current_treasury").IsNull() &&
          cash.At("player_monthly_gross_income").IsNull() &&
          cash.At("player_monthly_total_expenses").IsNull() &&
          cash.At("player_monthly_net_income").IsNull() &&
          !cash.At("readiness").At("same_frame_ready").Flag(),
          "custody failure cannot downgrade to wallet-known partial");
      UnknownScope(observed, cash); f.ClosedSharedGates();
    }
  }
  for (const std::string_view mode : {"--emit-query-v2-partial", "--emit-query-v2-wallet-drift",
      "--emit-query-v2-monthly-unknown", "--emit-query-v2-net-overflow",
      "--emit-query-v2-adapter-drift", "--emit-query-v2-revision-source-drift",
      "--emit-query-v2-owner-after-gross"}) {
    const auto outer = JsonReader(RunCashQueryCase(mode)).Document();
    const bool rejected = mode == "--emit-query-v2-wallet-drift" ||
        mode == "--emit-query-v2-adapter-drift" || mode == "--emit-query-v2-revision-source-drift" ||
        mode == "--emit-query-v2-owner-after-gross";
    Require(outer.At("type").Text() == "command_result" &&
        outer.At("request_id").Text() == "cash-v2-actor-query-original" &&
        outer.At("ok").Flag() == !rejected, "actual bridge formatter preserves query gate");
    if (rejected) Require(!outer.members.contains("result") && !outer.At("error").Text().empty(),
        "real outer reject has error and no accepted inner DATA");
    else {
      const auto &inner = outer.At("result"); const auto &cash = inner.At("war_cash_current_resources");
      Require(inner.At("step").Text() == kPersonalCashStepV2 && cash.At("status").Text() == "partial" &&
          !cash.At("current_treasury").IsNull() && !cash.At("formal_action_ready").Flag(),
          "stable wallet-known partial is an actual successful outer query");
      if (mode == "--emit-query-v2-monthly-unknown")
        Require(cash.At("player_monthly_gross_income").IsNull() &&
            cash.At("player_monthly_total_expenses").IsNull() &&
            cash.At("player_monthly_net_income").IsNull(), "getter unknown is not observed zero");
      if (mode == "--emit-query-v2-net-overflow")
        Require(!cash.At("player_monthly_gross_income").IsNull() &&
            !cash.At("player_monthly_total_expenses").IsNull() &&
            cash.At("player_monthly_net_income").IsNull(), "overflow loses NET only");
    }
  }
  {
    CashFrameFixture f; Require(f.Invoke() && f.cash.observation.completed, "legacy Actor result available");
    const auto outer = JsonReader(PersonalCashCommandResult1210("cash-v1-query-original", f.cash,
        PersonalCashScopeVersion::legacy_nonnegative_v1)).Document();
    Require(outer.At("ok").Flag() && outer.At("result").At("step").Text() == kPersonalCashStepV1 &&
        outer.At("result").At("war_cash_current_resources").At("schema").Text() == kPersonalCashSchemaV1,
        "real outer query formatter retains V1 wire identity");
  }
  for (const auto version : {PersonalCashScopeVersion::legacy_nonnegative_v1,
      static_cast<PersonalCashScopeVersion>(99)}) {
    CashFrameFixture f; PrepareCashScopeV2(f);
    Require(f.Invoke() && f.cash.observation.completed, "real V2 observation precedes wrong-version request");
    const auto outer = JsonReader(PersonalCashCommandResult1210("cash-version-mismatch", f.cash, version)).Document();
    Require(!outer.At("ok").Flag() && !outer.members.contains("result") &&
        outer.At("error").Text() == "personal_cash_scope_version_mismatch",
        "actual post-getter gate rejects cross-version wrapping before inner serialization");
  }
  for(int event=0;event<3;++event) {
    CashFrameFixture f;f.reset_proof_after_read=event==0;
    f.advance_epoch_after_read=event==1;f.drain_hook_after_read=event==2;
    CashFrameFailure(f,false);
    Require(f.cash.observation.current_full_call_attempts==1 &&
        f.raw_adapter.snapshot_calls==1 && f.ram.context_calls==0 &&
        !f.cash.observation.personal_gold_raw &&
        !f.cash.observation.monthly_gross_income_raw,
        "owner lifecycle change inside real Full callback keeps one attempt, closes later getters");
  }
  for (const bool signed_scope : {false, true}) {
    for (const unsigned loss : {0U, 1U, 2U}) {
      CashFrameFixture f; if (signed_scope) PrepareCashScopeV2(f);
      struct GrossLoss { CashFrameFixture *frame; unsigned kind; } loss_context{&f, loss};
      f.ram.gross_hook_context = &loss_context;
      f.ram.gross_before_return = +[](void *opaque) noexcept {
        auto &event = *static_cast<GrossLoss *>(opaque); auto &frame = *event.frame;
        if (event.kind == 0) frame.mailbox.stop_requested.store(true);
        else if (event.kind == 1) frame.cash.native_full_adapter = &frame.parent_adapter;
        else {
          frame.foreign_revision = frame.ram.revision;
          frame.cash.current_published_revision = &frame.foreign_revision;
        }
      };
      Require(f.Invoke() && f.raw_adapter.snapshot_calls == 1 && f.parent_adapter.snapshot_calls == 0 &&
          f.ram.context_calls == 1 && f.ram.gross_calls == 1 && f.ram.expense_calls == 0,
          "actual post-Gross owner/source loss blocks expense and confirmation native calls");
      const auto &observed = f.cash.observation;
      Require(!observed.completed && !observed.same_frame_ready && !observed.personal_gold_raw &&
          !observed.monthly_gross_income_raw && !observed.monthly_total_expenses_raw &&
          !observed.monthly_net_income_raw && observed.current_full_call_attempts == 1 &&
          observed.context_call_attempts == 1 && observed.gross_call_attempted &&
          !observed.expenses_call_attempted, "owner loss latches whole Cash failure without post-loss Full reads");
      f.ClosedSharedGates();
    }
  }
  std::cout << "ck3_1210_personal_cash_frame_v1 Actor MQ NoGame fixture PASS\n";
  return 0;
}

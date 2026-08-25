#include "xar_bridge/ck3_11906_adapter.hpp"
#include "xar_bridge/combat_simulation_inputs_v3_mailbox.hpp"
#include "xar_bridge/game_adapter.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace {

using xar::game::AdapterDescriptor;
using xar::game::GameAdapter;

constexpr std::array<std::string_view, 1> kPreferredCapabilities{
    "fixture.preferred",
};
constexpr AdapterDescriptor kPreferredDescriptor{
    "fixture-preferred",
    "fixture.1",
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "fixture_checkpoint",
    kPreferredCapabilities,
};

constexpr std::array<std::string_view, 8> kFutureCapabilities{
    "game.state.snapshot",
    "game.command.pause-map",
    "game.command.preview-move-army-N-to-N",
    "game.command.split-army-half-N",
    "game.command.merge-armies-N-with-N",
    "game.state.war-objective-assault",
    "game.command.start-assault-N",
    "game.command.stop-assault-N",
};
constexpr AdapterDescriptor kFutureDescriptor{
    "fixture-future",
    "fixture.2",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "fixture_checkpoint_v2",
    kFutureCapabilities,
};

class StubAdapter final : public GameAdapter {
public:
  StubAdapter(const AdapterDescriptor &descriptor, bool enabled) noexcept
      : descriptor_(descriptor), enabled_(enabled) {}

  const AdapterDescriptor &descriptor() const noexcept override {
    return descriptor_;
  }
  bool enabled() const noexcept override { return enabled_; }
  bool read_snapshot(xar::game::Snapshot &) const noexcept override {
    return false;
  }
  xar::game::PauseSubmitResult submit_pause_map() const noexcept override {
    return xar::game::PauseSubmitResult::unavailable;
  }
  xar::game::ResumeSubmitResult submit_resume_map() const noexcept override {
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
      std::vector<xar::game::DeclarableWarSnapshot> &) const noexcept override {
    return false;
  }
  xar::game::DeclareWarResult submit_declare_war(
      const xar::game::DeclarableWarSnapshot &) const noexcept override {
    return xar::game::DeclareWarResult::unavailable;
  }
  xar::game::ReadArrangeMarriageChoicesResult
  read_arrange_marriage_choices(
      std::vector<xar::game::ArrangeMarriageChoice> &,
      xar::game::ArrangeMarriageQueryDiagnostics &) const noexcept override {
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
      std::vector<xar::game::ArmyStrengthSnapshot> &) const noexcept override {
    return xar::game::ReadArmyStrengthsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsResult
  read_combat_simulation_inputs(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsSnapshot &) const noexcept override {
    return xar::game::ReadCombatSimulationInputsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsV3Result
  read_combat_simulation_inputs_v3(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsV3Snapshot &) const noexcept override {
    return xar::game::ReadCombatSimulationInputsV3Result::unavailable;
  }
  xar::game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t,
      xar::game::WarTerminationOptionsSnapshot &) const noexcept override {
    return xar::game::ReadWarTerminationOptionsResult::unavailable;
  }
  xar::game::ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t,
      xar::game::WarTerminationTermsSnapshot &) const noexcept override {
    return xar::game::ReadWarTerminationTermsResult::unavailable;
  }
  xar::game::ReadWarTerminationExitTermsResult
  read_war_termination_exit_terms(
      std::int32_t,
      xar::game::WarTerminationExitTermsSnapshot &) const noexcept override {
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
  bool enabled_;
};

std::unique_ptr<GameAdapter>
CreateDisabledPreferred(std::string_view) noexcept {
  return std::make_unique<StubAdapter>(kPreferredDescriptor, false);
}

std::unique_ptr<GameAdapter>
CreateDisabledFuture(std::string_view) noexcept {
  return std::make_unique<StubAdapter>(kFutureDescriptor, false);
}

std::unique_ptr<GameAdapter>
CreateEnabledFuture(std::string_view executable_sha256) noexcept {
  return std::make_unique<StubAdapter>(
      kFutureDescriptor, executable_sha256 == "fixture-future-hash");
}

int Fail(std::string_view message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

bool Contains(std::span<const std::string_view> values,
              std::string_view expected) {
  return std::find(values.begin(), values.end(), expected) != values.end();
}

} // namespace

int main() {
  const auto &known = xar::game::Ck3_11906AdapterDescriptor();
  if (known.adapter_id != "ck3-1.19.0.6-msvc-x64" ||
      known.game_version != "1.19.0.6" ||
      known.executable_sha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86" ||
      known.checkpoint_save_name != "xar_checkpoint") {
    return Fail("known CK3 build descriptor drifted");
  }
  if (!Contains(known.capabilities, "game.state.snapshot") ||
      !Contains(known.capabilities,
                "game.state.xar-one-life-settlement") ||
      !Contains(known.capabilities, "game.state.war-primary-opponent") ||
      !Contains(known.capabilities, "game.state.war-objectives") ||
      !Contains(known.capabilities,
                "game.state.war-objective-occupation") ||
      !Contains(known.capabilities,
                "game.state.war-objective-fort-level") ||
      !Contains(known.capabilities,
                "game.state.war-objective-garrison") ||
      !Contains(known.capabilities,
                "game.state.war-objective-siege-progress") ||
      !Contains(known.capabilities,
                "game.state.war-objective-assault") ||
      !Contains(known.capabilities, "game.state.army-routes") ||
      !Contains(known.capabilities,
                "game.command.preview-move-army-N-to-N") ||
      !Contains(known.capabilities,
                "game.command.query-route-contact-horizon-v1-N") ||
      !Contains(known.capabilities,
                "game.command.query-actual-contact-scope-v1-N") ||
      !Contains(known.capabilities, "game.command.split-army-half-N") ||
      !Contains(known.capabilities,
                "game.command.merge-armies-N-with-N") ||
      !Contains(known.capabilities, "game.command.start-assault-N") ||
      !Contains(known.capabilities, "game.command.stop-assault-N") ||
      !Contains(known.capabilities, "game.command.declare-war-N") ||
      !Contains(known.capabilities,
                "game.command.query-army-strengths-v1") ||
      !Contains(known.capabilities,
                "game.command.query-combat-simulation-inputs-v2-N") ||
      !Contains(known.capabilities,
                "game.command.query-combat-simulation-inputs-v3-N") ||
      !Contains(known.capabilities,
                "game.command.query-war-termination-options-N") ||
      !Contains(known.capabilities,
                "game.command.query-war-termination-terms-v1-N") ||
      !Contains(known.capabilities, "game.command.surrender-war-N") ||
      !Contains(known.capabilities,
                "game.command.offer-white-peace-N") ||
      !Contains(known.capabilities,
                "game.command.query-arrange-marriage-choices") ||
      !Contains(known.capabilities, "game.adapter.minimized-headless")) {
    return Fail("known adapter omitted a required semantic capability");
  }
  if (Contains(known.capabilities,
               "game.command.query-war-termination-exit-terms-v2-N")) {
    return Fail("known adapter advertised the crash-disabled exit-v2 query");
  }
  for (auto left = known.capabilities.begin(); left != known.capabilities.end();
       ++left) {
    if (std::find(left + 1, known.capabilities.end(), *left) !=
        known.capabilities.end()) {
      return Fail("known adapter advertised a duplicate capability");
    }
  }

  xar::game::CombatSimulationInputsRequest combat_request{};
  constexpr std::string_view canonical_combat_step =
      "query-combat-simulation-inputs-v2-900-899-a-2-22-12-d-1-13";
  if (!xar::game::ParseCombatSimulationInputsStep(
          canonical_combat_step, combat_request) ||
      combat_request.target_province_id != 900 ||
      combat_request.attacker_entry_province_id != 899 ||
      combat_request.attacker_army_ids !=
          std::vector<std::int32_t>{22, 12} ||
      combat_request.defender_army_ids != std::vector<std::int32_t>{13}) {
    return Fail("canonical hypothetical-contact combat query did not parse");
  }
  constexpr std::string_view canonical_v3_combat_step =
      "query-combat-simulation-inputs-v3-900-899-a-2-22-12-d-1-13";
  if (!xar::game::ParseCombatSimulationInputsV3Step(
          canonical_v3_combat_step, combat_request) ||
      combat_request.target_province_id != 900 ||
      combat_request.attacker_entry_province_id != 899 ||
      combat_request.attacker_army_ids !=
          std::vector<std::int32_t>{22, 12} ||
      combat_request.defender_army_ids != std::vector<std::int32_t>{13} ||
      xar::game::ParseCombatSimulationInputsStep(canonical_v3_combat_step,
                                                 combat_request)) {
    return Fail("canonical production v3 combat literal did not parse");
  }
  std::uint64_t combat_v3_revision = 0;
  if (!xar::ck3_11906::ParseCombatSimulationInputsV3ExpectedRevision(
          "{\"expected_revision\":4294967297}", combat_v3_revision) ||
      combat_v3_revision != 4'294'967'297ULL ||
      xar::ck3_11906::ParseCombatSimulationInputsV3ExpectedRevision(
          "{\"expected_revision\":7,\"expected_revision\":8}",
          combat_v3_revision) ||
      xar::ck3_11906::ParseCombatSimulationInputsV3ExpectedRevision(
          "{\"expected_revision\":0}", combat_v3_revision)) {
    return Fail("combat-v3 revision parser lost strict uint64 binding");
  }
  xar::ck3_11906::CombatSimulationInputsV3MailboxContext
      forged_combat_query{};
  xar::ck3_11906::MainThreadExecutionStampV1 forged_combat_stamp{};
  if (xar::ck3_11906::ExecuteCombatSimulationInputsV3MailboxQuery(
          &forged_combat_query, forged_combat_stamp) ||
      forged_combat_query.completion !=
          xar::ck3_11906::CombatSimulationInputsV3MailboxCompletion::
              infrastructure_rejected) {
    return Fail("combat-v3 executor accepted a direct worker-thread call");
  }
  constexpr auto combat_v3_runtime_slot_base =
      xar::ck3_11906::kCombatSimulationInputsV3AccoladeTypeDatabaseSlotRva;
  constexpr auto combat_v3_scripted_rules_slot_delta =
      xar::ck3_11906::
          kCombatSimulationInputsV3AccoladeScriptedRulesSingletonSlotRva -
      combat_v3_runtime_slot_base;
  constexpr auto combat_v3_type_database_slot_delta =
      xar::ck3_11906::kCombatSimulationInputsV3AccoladeTypeDatabaseSlotRva -
      combat_v3_runtime_slot_base;
  constexpr auto combat_v3_owner_key_delta =
      xar::ck3_11906::kCombatSimulationInputsV3AccoladeOwnerNamedKeyIdRva -
      combat_v3_runtime_slot_base;
  std::vector<std::byte> combat_v3_runtime_slots(
      combat_v3_owner_key_delta + sizeof(std::int32_t));
  const auto fake_combat_v3_module =
      reinterpret_cast<std::uintptr_t>(combat_v3_runtime_slots.data()) -
      combat_v3_runtime_slot_base;
  std::uintptr_t fake_singleton = 1;
  std::int32_t missing_named_key = -1;
  std::memcpy(combat_v3_runtime_slots.data() + combat_v3_owner_key_delta,
              &missing_named_key, sizeof(missing_named_key));
  if (xar::ck3_11906::ReadCombatSimulationInputsV3PhaseRuntimeStatus(0) !=
          xar::ck3_11906::CombatSimulationInputsV3PhaseRuntimeStatus::
              module_unavailable ||
      xar::ck3_11906::ReadCombatSimulationInputsV3PhaseRuntimeStatus(
          fake_combat_v3_module) !=
          xar::ck3_11906::CombatSimulationInputsV3PhaseRuntimeStatus::
              accolade_scripted_rules_uninitialized) {
    return Fail(
        "combat-v3 accolade rules gate accepted an empty singleton");
  }
  std::memcpy(combat_v3_runtime_slots.data() +
                  combat_v3_scripted_rules_slot_delta,
              &fake_singleton, sizeof(fake_singleton));
  if (xar::ck3_11906::ReadCombatSimulationInputsV3PhaseRuntimeStatus(
      fake_combat_v3_module) !=
      xar::ck3_11906::CombatSimulationInputsV3PhaseRuntimeStatus::
          accolade_type_database_uninitialized) {
    return Fail("combat-v3 accolade type gate accepted an empty database");
  }
  std::memcpy(
      combat_v3_runtime_slots.data() + combat_v3_type_database_slot_delta,
      &fake_singleton, sizeof(fake_singleton));
  if (xar::ck3_11906::ReadCombatSimulationInputsV3PhaseRuntimeStatus(
          fake_combat_v3_module) !=
      xar::ck3_11906::CombatSimulationInputsV3PhaseRuntimeStatus::
          accolade_owner_named_key_unregistered) {
    return Fail("combat-v3 accolade owner gate accepted an unregistered key");
  }
  std::int32_t registered_named_key = 0;
  std::memcpy(combat_v3_runtime_slots.data() + combat_v3_owner_key_delta,
              &registered_named_key, sizeof(registered_named_key));
  if (xar::ck3_11906::ReadCombatSimulationInputsV3PhaseRuntimeStatus(
          fake_combat_v3_module) !=
      xar::ck3_11906::CombatSimulationInputsV3PhaseRuntimeStatus::ready) {
    return Fail("combat-v3 phase runtime gate rejected initialized singletons");
  }
  constexpr std::array<std::string_view, 15> invalid_combat_steps{
      "query-combat-simulation-inputs-v1-900-22-12",
      "query-combat-simulation-inputs-v2-900",
      "query-combat-simulation-inputs-v2-0900-899-a-1-22-d-1-13",
      "query-combat-simulation-inputs-v2-900-900-a-1-22-d-1-13",
      "query-combat-simulation-inputs-v2-900-899-a-0-d-1-13",
      "query-combat-simulation-inputs-v2-900-899-a-2-22-d-1-13",
      "query-combat-simulation-inputs-v2-900-899-a-1-22-x-1-13",
      "query-combat-simulation-inputs-v2-900-899-a-1-22-d-0",
      "query-combat-simulation-inputs-v2-900-899-a-1-22-d-1-22",
      "query-combat-simulation-inputs-v2-900-899-a-64-22-d-1-13",
      "query-combat-simulation-inputs-v2-900-899-a-1-2147483648-d-1-13",
      "query-combat-simulation-inputs-v2-900-899-a-1-22-d-1-13-",
      "query-combat-simulation-inputs-v2-900-899-a-1-22-d-2-13",
      "game.command.query-combat-simulation-inputs-v2-N",
      "game.command.query-combat-simulation-inputs-v3-N",
  };
  constexpr std::string_view v2_prefix =
      "query-combat-simulation-inputs-v2-";
  constexpr std::string_view v3_prefix =
      "query-combat-simulation-inputs-v3-";
  for (const auto invalid : invalid_combat_steps) {
    if (xar::game::ParseCombatSimulationInputsStep(invalid, combat_request) ||
        xar::game::ParseCombatSimulationInputsV3Step(invalid,
                                                     combat_request)) {
      return Fail("noncanonical combat query step was accepted");
    }
    if (invalid.starts_with(v2_prefix)) {
      const std::string invalid_v3 =
          std::string(v3_prefix) + std::string(invalid.substr(v2_prefix.size()));
      if (xar::game::ParseCombatSimulationInputsV3Step(invalid_v3,
                                                       combat_request)) {
        return Fail("noncanonical production v3 combat query was accepted");
      }
    }
  }
  auto exact_adapter =
      xar::game::CreateCk3_11906Adapter(known.executable_sha256);
  if (exact_adapter == nullptr || !exact_adapter->enabled() ||
      !exact_adapter->supports_step(canonical_combat_step) ||
      !exact_adapter->supports_step(canonical_v3_combat_step) ||
      !exact_adapter->supports_step(
          "query-route-contact-horizon-v1-16777217-to-3-h-2-16777218-33554433") ||
      exact_adapter->supports_step(
          "query-route-contact-horizon-v1-16777217-to-3-h-2-16777218-16777218") ||
      !exact_adapter->supports_step(
          "query-actual-contact-scope-v1-16777217-at-3") ||
      exact_adapter->supports_step(
          "query-actual-contact-scope-v1-016777217-at-3") ||
      exact_adapter->supports_step(
          "query-actual-contact-scope-v1-16777217-at-0") ||
      !exact_adapter->supports_step(
          "query-war-termination-terms-v1-16777290") ||
      exact_adapter->supports_step(
          "query-war-termination-exit-terms-v2-16777290") ||
      !exact_adapter->supports_step("offer-white-peace-16777290") ||
      exact_adapter->supports_step(
          "query-war-termination-terms-v1-016777290") ||
      exact_adapter->supports_step(
          "query-war-termination-terms-v1-2147483648") ||
      exact_adapter->supports_step(
          "query-war-termination-exit-terms-v2-016777290") ||
      exact_adapter->supports_step(
          "query-war-termination-exit-terms-v2-2147483648") ||
      exact_adapter->supports_step("offer-white-peace-016777290")) {
    return Fail("exact adapter did not map the strict combat query step");
  }
  for (const auto invalid : invalid_combat_steps) {
    if (exact_adapter->supports_step(invalid)) {
      return Fail("exact adapter advertised a malformed combat query step");
    }
  }

  StubAdapter partial(kFutureDescriptor, true);
  if (!partial.supports("game.state.snapshot") ||
      !partial.supports("game.command.pause-map") ||
      partial.supports("game.state.war-primary-opponent") ||
      partial.supports("game.state.war-objectives") ||
      partial.supports("game.state.war-objective-siege-progress") ||
      partial.supports("game.command.declare-war-N") ||
      partial.supports_step("query-army-strengths-v1") ||
      partial.supports_step("query-war-termination-options-16777217") ||
      partial.supports_step(
          "query-war-termination-terms-v1-16777217") ||
      partial.supports_step(
          "query-war-termination-exit-terms-v2-16777217") ||
      partial.supports_step("surrender-war-16777217") ||
      partial.supports_step("offer-white-peace-16777217") ||
      !partial.supports_snapshot() || !partial.supports_step("pause-map") ||
      !partial.supports_step("preview-move-army-1-to-2") ||
      !partial.supports_step("split-army-half-1") ||
      !partial.supports_step("merge-armies-1-with-2") ||
      !partial.supports_step("start-assault-16777217") ||
      !partial.supports_step("stop-assault-16777217") ||
      partial.supports_step("declare-war-99-1-0") ||
      partial.supports_step("unsupported-step")) {
    return Fail("capability lookup did not use the selected adapter set");
  }
  StubAdapter disabled(kFutureDescriptor, false);
  if (disabled.supports("game.state.snapshot")) {
    return Fail("disabled adapter exposed gameplay capabilities");
  }

  constexpr std::array<xar::game::AdapterFactory, 2> with_future{
      &CreateDisabledPreferred,
      &CreateEnabledFuture,
  };
  auto selected =
      xar::game::SelectAdapter("fixture-future-hash", with_future);
  if (selected == nullptr || !selected->enabled() ||
      selected->descriptor().adapter_id != "fixture-future") {
    return Fail("registry did not select a later enabled build adapter");
  }
  selected = xar::game::SelectAdapter("unknown-fixture-hash", with_future);
  if (selected == nullptr || selected->enabled() ||
      selected->descriptor().adapter_id != "fixture-preferred") {
    return Fail("registry did not pass executable identity to adapters");
  }

  constexpr std::array<xar::game::AdapterFactory, 2> unknown_build{
      &CreateDisabledPreferred,
      &CreateDisabledFuture,
  };
  selected = xar::game::SelectAdapter("fixture-hash", unknown_build);
  if (selected == nullptr || selected->enabled() ||
      selected->descriptor().adapter_id != "fixture-preferred" ||
      selected->supports("fixture.preferred")) {
    return Fail("unknown build did not retain an unsupported preferred adapter");
  }

  constexpr std::array<xar::game::AdapterFactory, 0> no_adapters{};
  if (xar::game::SelectAdapter("fixture-hash", no_adapters) != nullptr) {
    return Fail("empty adapter registry did not return null");
  }

  auto current = xar::game::SelectCurrentProcessAdapter();
  if (current == nullptr || current->enabled() ||
      current->descriptor().adapter_id != known.adapter_id ||
      current->supports("game.state.snapshot")) {
    return Fail("unknown current test executable exposed CK3 gameplay");
  }

  std::cout << "PASS: known_descriptor=1 adapter_capability_set=1 "
               "unknown_build_unsupported=1 future_adapter_registry=1 "
               "empty_registry=1 combat_v3_mailbox_gate=1\n";
  return 0;
}

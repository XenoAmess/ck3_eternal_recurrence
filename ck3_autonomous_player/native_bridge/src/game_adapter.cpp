#include "xar_bridge/game_adapter.hpp"

#include "xar_bridge/war_entry_assessments_v1.hpp"
#include "xar_bridge/route_contact_horizon_v1_mailbox.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"
#include "xar_bridge/actual_contact_scope_v1_mailbox.hpp"
#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"
#include "xar_bridge/battle_reinforcement_assignment_v1_mailbox.hpp"
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"
#include "xar_bridge/battle_transition_v1_mailbox.hpp"
#include "xar_bridge/campaign_root_context_v1_mailbox.hpp"
#include "xar_bridge/event_window_context_v1.hpp"
#include "xar_bridge/loaded_feature_manifest_v1_mailbox.hpp"
#include "xar_bridge/pending_character_interaction_context_v1_mailbox.hpp"
#include "xar_bridge/title_map_navigation_v1.hpp"
#include "xar_bridge/zhongguo_ai_owned_case_snapshot_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_case_snapshot_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_b2_pip_snapshot_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_incident_snapshot_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_manager_governance_snapshot_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_career_hc_workforce_postcondition_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_projects_metrics_postcondition_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_promotion_compensation_postcondition_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_workforce_collective_snapshot_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.hpp"
#include "xar_bridge/zhongguo_result_case_snapshot_v1_mailbox.hpp"

#include "xar_bridge/ck3_11906_adapter.hpp"

#include <windows.h>
#include <bcrypt.h>

#include <array>
#include <charconv>
#include <cstdint>
#include <limits>
#include <memory>
#include <string>
#include <vector>

namespace xar::game {
namespace {

constexpr std::string_view kCombatInputsV2StepPrefix =
    "query-combat-simulation-inputs-v2-";
constexpr std::string_view kCombatInputsV3StepPrefix =
    "query-combat-simulation-inputs-v3-";
constexpr std::size_t kMaximumCombatInputArmyIds = 64;

bool IsCanonicalPositiveIdStep(std::string_view step,
                               std::string_view prefix) noexcept {
  if (!step.starts_with(prefix)) {
    return false;
  }
  const auto value_text = step.substr(prefix.size());
  if (value_text.empty() || value_text.front() == '0') {
    return false;
  }
  std::int32_t value = 0;
  const auto [end, error] =
      std::from_chars(value_text.data(), value_text.data() + value_text.size(),
                      value);
  return error == std::errc{} && end == value_text.data() + value_text.size() &&
         value > 0;
}

std::string CurrentExecutableSha256() noexcept {
  std::array<wchar_t, 32'768> path{};
  const DWORD path_length =
      GetModuleFileNameW(nullptr, path.data(), static_cast<DWORD>(path.size()));
  if (path_length == 0 || path_length >= path.size()) {
    return {};
  }

  HANDLE file = CreateFileW(path.data(), GENERIC_READ, FILE_SHARE_READ, nullptr,
                            OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (file == INVALID_HANDLE_VALUE) {
    return {};
  }

  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<std::uint8_t> object;
  std::array<std::uint8_t, 32> digest{};
  bool ok = false;
  do {
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                    nullptr, 0) < 0) {
      break;
    }
    DWORD object_size = 0;
    DWORD copied = 0;
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_size),
                          sizeof(object_size), &copied, 0) < 0 ||
        object_size == 0) {
      break;
    }
    object.resize(object_size);
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr,
                         0, 0) < 0) {
      break;
    }

    std::array<std::uint8_t, 64U * 1024U> buffer{};
    while (true) {
      DWORD read = 0;
      if (!ReadFile(file, buffer.data(), static_cast<DWORD>(buffer.size()),
                    &read, nullptr)) {
        break;
      }
      if (read == 0) {
        ok = BCryptFinishHash(hash, digest.data(),
                              static_cast<ULONG>(digest.size()), 0) >= 0;
        break;
      }
      if (BCryptHashData(hash, buffer.data(), read, 0) < 0) {
        break;
      }
    }
  } while (false);

  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  if (algorithm != nullptr) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
  }
  CloseHandle(file);
  if (!ok) {
    return {};
  }

  constexpr char digits[] = "0123456789ABCDEF";
  std::array<char, 65> encoded{};
  for (std::size_t index = 0; index < digest.size(); ++index) {
    encoded[index * 2] = digits[digest[index] >> 4U];
    encoded[index * 2 + 1] = digits[digest[index] & 0x0fU];
  }
  return encoded.data();
}

} // namespace

namespace {

bool ParseCombatSimulationInputsStepWithPrefix(
    std::string_view step, std::string_view prefix,
    CombatSimulationInputsRequest &request) noexcept {
  request = {};
  if (!step.starts_with(prefix)) {
    return false;
  }
  auto suffix = step.substr(prefix.size());
  std::array<std::string_view, kMaximumCombatInputArmyIds + 6> tokens{};
  std::size_t token_count = 0;
  while (!suffix.empty()) {
    if (token_count >= tokens.size()) {
      return false;
    }
    const auto delimiter = suffix.find('-');
    const auto token = suffix.substr(0, delimiter);
    if (token.empty()) {
      return false;
    }
    tokens[token_count++] = token;
    if (delimiter == std::string_view::npos) {
      suffix = {};
    } else {
      suffix.remove_prefix(delimiter + 1);
      if (suffix.empty()) {
        return false;
      }
    }
  }
  if (token_count < 8 || tokens[2] != "a") {
    return false;
  }

  const auto parse_positive = [](std::string_view token,
                                 std::int32_t &value) noexcept {
    value = -1;
    if (token.empty() || token.front() < '1' || token.front() > '9') {
      return false;
    }
    for (const char character : token) {
      if (character < '0' || character > '9') {
        return false;
      }
    }
    std::int64_t parsed = 0;
    const auto conversion =
        std::from_chars(token.data(), token.data() + token.size(), parsed);
    if (conversion.ec != std::errc{} ||
        conversion.ptr != token.data() + token.size() || parsed <= 0 ||
        parsed > std::numeric_limits<std::int32_t>::max()) {
      return false;
    }
    value = static_cast<std::int32_t>(parsed);
    return true;
  };

  std::int32_t attacker_count_value = -1;
  if (!parse_positive(tokens[0], request.target_province_id) ||
      !parse_positive(tokens[1], request.attacker_entry_province_id) ||
      request.target_province_id == request.attacker_entry_province_id ||
      !parse_positive(tokens[3], attacker_count_value) ||
      attacker_count_value > 63) {
    request = {};
    return false;
  }
  const auto attacker_count = static_cast<std::size_t>(attacker_count_value);
  const auto defender_marker_index = 4 + attacker_count;
  if (defender_marker_index + 2 >= token_count ||
      tokens[defender_marker_index] != "d") {
    request = {};
    return false;
  }
  std::int32_t defender_count_value = -1;
  if (!parse_positive(tokens[defender_marker_index + 1],
                      defender_count_value) ||
      defender_count_value > 63 ||
      attacker_count + static_cast<std::size_t>(defender_count_value) >
          kMaximumCombatInputArmyIds ||
      token_count != defender_marker_index + 2 +
                         static_cast<std::size_t>(defender_count_value)) {
    request = {};
    return false;
  }

  std::array<std::int32_t, kMaximumCombatInputArmyIds> army_ids{};
  const auto total_army_count =
      attacker_count + static_cast<std::size_t>(defender_count_value);
  for (std::size_t index = 0; index < total_army_count; ++index) {
    const auto token_index = index < attacker_count
                                 ? 4 + index
                                 : defender_marker_index + 2 +
                                       (index - attacker_count);
    if (!parse_positive(tokens[token_index], army_ids[index])) {
      request = {};
      return false;
    }
    for (std::size_t previous = 0; previous < index; ++previous) {
      if (army_ids[index] == army_ids[previous]) {
        request = {};
        return false;
      }
    }
  }
  try {
    request.attacker_army_ids.assign(army_ids.begin(),
                                     army_ids.begin() + attacker_count);
    request.defender_army_ids.assign(
        army_ids.begin() + attacker_count,
        army_ids.begin() + total_army_count);
  } catch (...) {
    request = {};
    return false;
  }
  return true;
}

} // namespace

bool ParseCombatSimulationInputsStep(
    std::string_view step, CombatSimulationInputsRequest &request) noexcept {
  return ParseCombatSimulationInputsStepWithPrefix(
      step, kCombatInputsV2StepPrefix, request);
}

bool ParseCombatSimulationInputsV3Step(
    std::string_view step, CombatSimulationInputsRequest &request) noexcept {
  return ParseCombatSimulationInputsStepWithPrefix(
      step, kCombatInputsV3StepPrefix, request);
}

bool GameAdapter::supports(std::string_view capability) const noexcept {
  if (!enabled()) {
    return false;
  }
  for (const auto candidate : descriptor().capabilities) {
    if (candidate == capability) {
      return true;
    }
  }
  return false;
}

bool GameAdapter::supports_snapshot() const noexcept {
  return supports("game.state.snapshot");
}

bool GameAdapter::supports_step(std::string_view step) const noexcept {
  std::string_view capability;
  if (step == "pause-map") {
    capability = "game.command.pause-map";
  } else if (step == "resume-map") {
    capability = "game.command.resume-map";
  } else if (step == "save-checkpoint") {
    capability = "game.command.save-checkpoint";
  } else if (step == "accept-pending-character-interaction") {
    capability = "game.command.accept-pending-character-interaction";
  } else if (step == "reject-pending-character-interaction") {
    capability = "game.command.reject-pending-character-interaction";
  } else if (step == "acknowledge-pending-character-interaction") {
    capability = "game.command.acknowledge-pending-character-interaction";
  } else if (step == "query-arrange-marriage-choices") {
    capability = "game.command.query-arrange-marriage-choices";
  } else if (step.starts_with("arrange-marriage-")) {
    capability = "game.command.arrange-marriage-N";
  } else if (step == "query-declarable-wars") {
    capability = "game.command.query-declarable-wars";
  } else if (step.starts_with("declare-war-")) {
    capability = "game.command.declare-war-N";
  } else if (step.starts_with("enforce-demands-")) {
    capability = "game.command.enforce-demands-N";
  } else if (step == "query-army-strengths-v1") {
    capability = "game.command.query-army-strengths-v1";
  } else if (ck3_11906::ParseCampaignRootContextV1Step(step)) {
    capability = ck3_11906::kCampaignRootContextV1Capability;
  } else if (ck3_11906::ParseZhongguoCaseSnapshotV1Step(step)) {
    capability = ck3_11906::kZhongguoCaseSnapshotV1Capability;
  } else if (ck3_11906::ParseZhongguoResultCaseSnapshotV1Step(step)) {
    capability = ck3_11906::kZhongguoResultCaseSnapshotV1Capability;
  } else if (ck3_11906::ParseZhongguoB2PipSnapshotV1Step(step)) {
    capability = ck3_11906::kZhongguoB2PipSnapshotV1Capability;
  } else if (ck3_11906::ParseZhongguoIncidentSnapshotV1Step(step)) {
    capability = ck3_11906::kZhongguoIncidentSnapshotV1Capability;
  } else if (
      ck3_11906::ParseZhongguoManagerGovernanceSnapshotV1Step(step)) {
    capability =
        ck3_11906::kZhongguoManagerGovernanceSnapshotV1Capability;
  } else if (
      ck3_11906::ParseZhongguoManagerSubordinateSelectorV1Step(step)) {
    capability =
        ck3_11906::kZhongguoManagerSubordinateSelectorV1Capability;
  } else if (
      ck3_11906::ParseZhongguoPromotionCompensationPostconditionV1Step(step)) {
    capability = ck3_11906::kZhongguoPromotionCompensationPostconditionV1Capability;
  } else if (
      ck3_11906::ParseZhongguoProjectsMetricsPostconditionV1Step(step)) {
    capability = ck3_11906::kZhongguoProjectsMetricsPostconditionV1Capability;
  } else if (
      ck3_11906::ParseZhongguoCareerHcWorkforcePostconditionV1Step(step)) {
    capability =
        ck3_11906::kZhongguoCareerHcWorkforcePostconditionV1Capability;
  } else if (ck3_11906::ParseZhongguoScoreboardStateV1Step(step)) {
    capability = ck3_11906::kZhongguoScoreboardStateV1Capability;
  } else if (ck3_11906::ParseZhongguoScoreboardActionV1Step(step)) {
    // Transport-only registration.  The descriptor deliberately does not
    // advertise kZhongguoScoreboardActionV1Capability until the provider-owned
    // observed-state revision has independent paused live evidence.  Exact
    // shortcut-manager dispatch, effective visibility/enabled and global
    // modal admission are wired, but an ACK is still verification-pending.
    capability = ck3_11906::kZhongguoScoreboardActionV1TransportCapability;
  } else if (
      ck3_11906::ParseZhongguoWorkforceCollectiveSnapshotV1Step(step)) {
    capability =
        ck3_11906::kZhongguoWorkforceCollectiveSnapshotV1Capability;
  } else if (
      ck3_11906::ParseZhongguoAiOwnedCaseSnapshotV1Step(step)) {
    capability = ck3_11906::kZhongguoAiOwnedCaseSnapshotV1Capability;
  } else if (ck3_11906::
                 ParseZhongguoWorkforceNormalExitSnapshotV1Step(step)) {
    capability =
        ck3_11906::kZhongguoWorkforceNormalExitSnapshotV1Capability;
  } else if (ck3_11906::ParseLoadedFeatureManifestV1Step(step)) {
    capability = ck3_11906::kLoadedFeatureManifestV1Capability;
  } else if (ck3_11906::
                 ParsePendingCharacterInteractionContextV1Step(step)) {
    capability =
        ck3_11906::kPendingCharacterInteractionContextV1Capability;
  } else if (step == ck3_11906::kEventWindowContextV1Step) {
    capability = ck3_11906::kEventWindowContextV1Capability;
  } else if (step == ck3_11906::kTitleMapNavigationV1Step) {
    capability = ck3_11906::kTitleMapNavigationV1Capability;
  } else {
    std::vector<std::int32_t> war_entry_targets;
    if (ck3_11906::ParseWarEntryAssessmentsV1Step(step,
                                                   war_entry_targets)) {
      capability = ck3_11906::kWarEntryAssessmentsV1Capability;
    }
  }
  if (capability.empty()) {
    BattleControlRequest battle_request{};
    if (ck3_11906::ParseBattleControlSnapshotV1Step(step,
                                                    battle_request)) {
      capability = ck3_11906::kBattleControlSnapshotV1Capability;
    }
  }
  if (capability.empty()) {
    BattleReinforcementAssignmentRequest reinforcement_request{};
    if (ck3_11906::ParseBattleReinforcementAssignmentV1Step(
            step, reinforcement_request)) {
      capability = ck3_11906::kBattleReinforcementAssignmentV1Capability;
    }
  }
  if (capability.empty()) {
    BattleTerminalTransitionRequestV1 terminal_request{};
    if (ck3_11906::ParseBattleTerminalTransitionV1Step(
            step, terminal_request)) {
      capability = ck3_11906::kBattleTerminalTransitionV1Capability;
    }
  }
  if (capability.empty()) {
    BattleTransitionRequest transition_request{};
    if (ck3_11906::ParseBattleTransitionV1Step(
            step, transition_request)) {
      capability = ck3_11906::kBattleTransitionV1Capability;
    }
  }
  if (capability.empty()) {
    ActualContactScopeRequest actual_contact_request{};
    if (ck3_11906::ParseActualContactScopeV1Step(
            step, actual_contact_request)) {
      capability = ck3_11906::kActualContactScopeV1Capability;
    }
  }
  if (capability.empty()) {
    RouteContactHorizonRequest route_request{};
    if (ck3_11906::ParseRouteContactHorizonV1Step(step, route_request)) {
      capability = "game.command.query-route-contact-horizon-v1-N";
    }
  }
  if (capability.empty()) {
    CombatSimulationInputsRequest request{};
    if (ParseCombatSimulationInputsV3Step(step, request)) {
      capability = "game.command.query-combat-simulation-inputs-v3-N";
    } else if (ParseCombatSimulationInputsStep(step, request)) {
      capability = "game.command.query-combat-simulation-inputs-v2-N";
    }
  }
  if (capability.empty()) {
    ck3_11906::TacticalDailySentinelArmRequestV1 request{};
    std::uint64_t cancel_generation = 0;
    if (ck3_11906::ParseTacticalDailySentinelArmStepV1(step, request)) {
      capability = ck3_11906::kTacticalDailySentinelCapabilityV1;
    } else if (ck3_11906::ParseTacticalDailySentinelCancelStepV1(
                   step, cancel_generation)) {
      capability = ck3_11906::kTacticalDailySentinelCancelCapabilityV1;
    } else if (step == ck3_11906::kTacticalDailySentinelStatusStepV1) {
      capability = ck3_11906::kTacticalDailySentinelStatusCapabilityV1;
    }
  }
  if (capability.empty() &&
      step.starts_with("query-war-termination-options-")) {
    capability = "game.command.query-war-termination-options-N";
  } else if (capability.empty() && IsCanonicalPositiveIdStep(
             step, "query-war-termination-terms-v1-")) {
    capability = "game.command.query-war-termination-terms-v1-N";
  } else if (capability.empty() && step.starts_with("surrender-war-")) {
    capability = "game.command.surrender-war-N";
  } else if (capability.empty() &&
             IsCanonicalPositiveIdStep(step, "offer-white-peace-")) {
    capability = "game.command.offer-white-peace-N";
  } else if (step == "raise-troops-default") {
    capability = "game.command.raise-troops-default";
  } else if (step.starts_with("preview-move-army-")) {
    capability = "game.command.preview-move-army-N-to-N";
  } else if (step.starts_with("move-army-")) {
    capability = "game.command.move-army-N-to-N";
  } else if (step.starts_with("disband-army-")) {
    capability = "game.command.disband-army-N";
  } else if (step.starts_with("split-army-half-")) {
    capability = "game.command.split-army-half-N";
  } else if (step.starts_with("merge-armies-")) {
    capability = "game.command.merge-armies-N-with-N";
  } else if (step.starts_with("start-assault-")) {
    capability = "game.command.start-assault-N";
  } else if (step.starts_with("stop-assault-")) {
    capability = "game.command.stop-assault-N";
  } else if (step.starts_with("select-event-option-")) {
    capability = "game.command.select-event-option-N";
  } else if (step.size() == 11 && step.starts_with("set-speed-") &&
             step.back() >= '1' && step.back() <= '5') {
    constexpr std::array<std::string_view, 5> speed_capabilities{
        "game.command.set-speed-1", "game.command.set-speed-2",
        "game.command.set-speed-3", "game.command.set-speed-4",
        "game.command.set-speed-5"};
    capability = speed_capabilities[static_cast<std::size_t>(step.back() - '1')];
  }
  return !capability.empty() && supports(capability);
}

const AdapterDescriptor &PreferredAdapterDescriptor() noexcept {
  return Ck3_11906AdapterDescriptor();
}

std::unique_ptr<GameAdapter>
SelectAdapter(std::string_view executable_sha256,
              std::span<const AdapterFactory> factories) noexcept {
  std::unique_ptr<GameAdapter> preferred;
  for (const auto factory : factories) {
    auto candidate = factory(executable_sha256);
    if (candidate == nullptr) {
      continue;
    }
    if (candidate->enabled()) {
      return candidate;
    }
    if (preferred == nullptr) {
      preferred = std::move(candidate);
    }
  }
  return preferred;
}

std::unique_ptr<GameAdapter> SelectCurrentProcessAdapter() noexcept {
  // Add one factory for each exact CK3 build. Order controls the preferred
  // diagnostic descriptor only; the first exact enabled match always wins.
  constexpr std::array<AdapterFactory, 1> factories{
      &CreateCk3_11906Adapter,
  };
  const std::string executable_sha256 = CurrentExecutableSha256();
  return SelectAdapter(executable_sha256, factories);
}

} // namespace xar::game

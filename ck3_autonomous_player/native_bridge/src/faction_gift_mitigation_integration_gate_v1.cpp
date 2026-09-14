#include "xar_bridge/faction_gift_mitigation_integration_gate_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using GateResult = FactionGiftMitigationIntegrationGateResultV1;
using GateTerminal = FactionGiftMitigationIntegrationGateTerminalV1;
using MembershipRole = game::FactionGiftMembershipRoleV1;
using Observation = game::FactionGiftMitigationObservationV1;
using ProbeBinding = bridge::FactionTargetingRowProbeBindingV1;
using ProbeFaction = bridge::FactionTargetingRowProbeFactionV1;
using ProbeResult = bridge::FactionTargetingRowProbeResultV1;

void AddRed(GateResult &result, std::uint32_t flag) {
  result.red_flags |= flag;
  if (result.first_red_reason.empty()) {
    result.first_red_reason.assign(
        FactionGiftMitigationIntegrationGateRedKeyV1(flag));
  }
}

bool SameBinding(const ProbeBinding &left,
                 const ProbeBinding &right) noexcept {
  return left.paused == right.paused &&
         left.proof_epoch == right.proof_epoch &&
         left.snapshot_revision == right.snapshot_revision &&
         left.date_raw == right.date_raw &&
         left.player_character_id == right.player_character_id;
}

bool ValidProbe(const ProbeResult &probe) noexcept {
  if (probe.terminal != bridge::FactionTargetingRowProbeTerminalV1::ready ||
      probe.unavailable_reasons !=
          bridge::faction_targeting_row_probe_unavailable_none ||
      probe.observer_failure_flags !=
          bridge::faction_targeting_row_observer_failure_none ||
      probe.published_generation == 0 ||
      (probe.published_generation & 1ULL) != 0 ||
      !SameBinding(probe.required_binding, probe.observed_binding) ||
      !probe.observed_binding.paused ||
      probe.observed_binding.proof_epoch == 0 ||
      probe.observed_binding.snapshot_revision == 0 ||
      probe.observed_binding.player_character_id == 0 ||
      probe.faction_count == 0 ||
      probe.faction_count > probe.factions.size()) {
    return false;
  }
  for (std::size_t index = 0; index < probe.faction_count; ++index) {
    const auto &row = probe.factions[index];
    if (row.faction_id == 0 || row.target_character_id == 0 ||
        row.character_member_count > row.character_member_ids.size()) {
      return false;
    }
    if (row.leader_present && row.leader_character_id == 0) return false;
    std::uint32_t previous = 0;
    for (std::size_t member_index = 0;
         member_index < row.character_member_count; ++member_index) {
      const auto member = row.character_member_ids[member_index];
      if (member == 0 || (member_index != 0 && previous >= member)) {
        return false;
      }
      previous = member;
    }
  }
  return true;
}

bool SameFaction(const ProbeFaction &left,
                 const ProbeFaction &right) noexcept {
  if (left.faction_id != right.faction_id ||
      left.target_character_id != right.target_character_id ||
      left.leader_present != right.leader_present ||
      left.leader_character_id != right.leader_character_id ||
      left.leader_present_in_character_members !=
          right.leader_present_in_character_members ||
      left.character_member_count != right.character_member_count) {
    return false;
  }
  for (std::size_t index = 0; index < left.character_member_count; ++index) {
    if (left.character_member_ids[index] !=
        right.character_member_ids[index]) {
      return false;
    }
  }
  return true;
}

bool SameProbe(const ProbeResult &left, const ProbeResult &right) noexcept {
  if (left.terminal != right.terminal ||
      left.unavailable_reasons != right.unavailable_reasons ||
      left.observer_failure_flags != right.observer_failure_flags ||
      left.published_generation != right.published_generation ||
      !SameBinding(left.required_binding, right.required_binding) ||
      !SameBinding(left.observed_binding, right.observed_binding) ||
      left.faction_count != right.faction_count) {
    return false;
  }
  for (std::size_t index = 0; index < left.faction_count; ++index) {
    if (!SameFaction(left.factions[index], right.factions[index])) {
      return false;
    }
  }
  return true;
}

const ProbeFaction *FindUniqueFaction(const ProbeResult &probe,
                                      std::uint32_t faction_id) noexcept {
  const ProbeFaction *found = nullptr;
  for (std::size_t index = 0; index < probe.faction_count; ++index) {
    if (probe.factions[index].faction_id != faction_id) continue;
    if (found != nullptr) return nullptr;
    found = &probe.factions[index];
  }
  return found;
}

bool Contains(const std::vector<std::uint32_t> &values,
              std::uint32_t value) noexcept {
  return std::binary_search(values.begin(), values.end(), value);
}

bool ValidRequestShape(
    const game::FactionGiftMitigationRequestV1 &request) noexcept {
  const bool role_valid = request.membership_role == MembershipRole::leader ||
                          request.membership_role ==
                              MembershipRole::character_member;
  return request.expected_revision != 0 &&
         request.expected_native_revision != 0 &&
         request.player_character_id != 0 && request.source_faction_id != 0 &&
         request.recipient_character_id != 0 &&
         request.player_character_id != request.recipient_character_id &&
         role_valid &&
         request.expected_definition_key ==
             kFactionGiftMitigationActionV1DefinitionKey &&
         request.expected_definition_stable_hash != 0 &&
         request.expected_gold_cost_raw > 0 &&
         request.expected_gold_scale ==
             kFactionGiftMitigationActionV1GoldScale &&
         request.expected_opinion_delta > 0 &&
         request.minimum_gold_reserve_raw >= 0 &&
         request.minimum_gold_reserve_scale == request.expected_gold_scale;
}

void CheckSemanticBindings(
    const ProbeResult &probe, const Observation &observation,
    const game::FactionGiftMitigationRequestV1 &request,
    GateResult &result) {
  const auto *row = FindUniqueFaction(probe, request.source_faction_id);
  if (!ValidRequestShape(request) || !observation.available ||
      !observation.paused ||
      observation.snapshot_revision != request.expected_revision ||
      observation.native_snapshot_revision !=
          request.expected_native_revision ||
      observation.observed_date_raw != request.expected_date_raw ||
      probe.observed_binding.snapshot_revision !=
          observation.snapshot_revision ||
      probe.observed_binding.date_raw != observation.observed_date_raw ||
      probe.observed_binding.player_character_id !=
          observation.player_character_id) {
    AddRed(result, faction_gift_gate_red_snapshot_binding);
  }

  bool membership_matches = false;
  if (request.membership_role == MembershipRole::leader) {
    membership_matches =
        observation.source_faction_leader_character_id ==
        request.recipient_character_id;
  } else if (request.membership_role == MembershipRole::character_member) {
    membership_matches = Contains(
        observation.source_faction_member_character_ids,
        request.recipient_character_id);
  }
  if (observation.player_character_id != request.player_character_id ||
      !observation.recipient_identity_resolved ||
      observation.recipient_character_id != request.recipient_character_id ||
      !membership_matches || !observation.recipient_alive ||
      !observation.recipient_is_ai ||
      !observation.recipient_is_direct_landed_vassal ||
      !observation.recipient_opinion_query_complete ||
      observation.gift_opinion_present) {
    AddRed(result, faction_gift_gate_red_identity_binding);
  }

  if (row == nullptr || !observation.source_faction_requery_complete ||
      observation.queried_source_faction_id != request.source_faction_id ||
      !observation.source_faction_present ||
      observation.source_faction_target_character_id !=
          request.player_character_id ||
      !observation.source_faction_targeting_player ||
      observation.source_faction_at_war ||
      !observation.source_faction_metrics_available ||
      observation.source_faction_metric_scale == 0) {
    AddRed(result, faction_gift_gate_red_faction_binding);
  }

  if (!observation.player_resources_query_complete ||
      observation.player_gold_scale != request.expected_gold_scale) {
    AddRed(result, faction_gift_gate_red_resource_binding);
  }

  const auto &preview = observation.gift_preview;
  if (!preview.available ||
      preview.definition_key != request.expected_definition_key ||
      preview.definition_stable_hash !=
          request.expected_definition_stable_hash ||
      !preview.interaction_legal || !preview.auto_accept ||
      preview.gold_cost_raw != request.expected_gold_cost_raw ||
      preview.gold_scale != request.expected_gold_scale ||
      preview.opinion_delta != request.expected_opinion_delta) {
    AddRed(result, faction_gift_gate_red_preview_binding);
  }

  if (request.expected_gold_cost_raw <= 0 ||
      request.minimum_gold_reserve_raw < 0 ||
      observation.player_gold_raw < request.expected_gold_cost_raw ||
      observation.player_gold_raw - request.expected_gold_cost_raw <
          request.minimum_gold_reserve_raw) {
    AddRed(result, faction_gift_gate_red_budget);
  }
}

GateTerminal Finish(GateResult &result) noexcept {
  result.ready_for_single_submit =
      result.red_flags == faction_gift_gate_red_none;
  result.terminal = result.ready_for_single_submit ? GateTerminal::ready
                                                   : GateTerminal::red;
  return result.terminal;
}

std::string Escape(std::string_view value) {
  std::string output;
  output.reserve(value.size() + 8);
  for (const char character : value) {
    if (character == '\\' || character == '"') output.push_back('\\');
    output.push_back(character);
  }
  return output;
}

std::string Quote(std::string_view value) {
  return "\"" + Escape(value) + "\"";
}

} // namespace

GateTerminal EvaluateFactionGiftMitigationIntegrationGateV1(
    FactionGiftMitigationNativeBinderStateV1 &binder,
    const game::FactionGiftMitigationRequestV1 &request,
    GateResult &result) noexcept {
  result = {};
  try {
    if (!binder.bound || binder.module_base == 0 ||
        binder.upstream.read_targeting_rows == nullptr) {
      AddRed(result, faction_gift_gate_red_binder_unavailable);
      return Finish(result);
    }
    if (binder.idempotency_claim_attempted || binder.submit_attempted) {
      AddRed(result, faction_gift_gate_red_action_already_consumed);
      return Finish(result);
    }
    const bool claim_before = binder.idempotency_claim_attempted;
    const bool submit_before = binder.submit_attempted;
    const auto sources =
        MakeFactionGiftMitigationNativeSourceActionAccessV1(binder);

    ProbeResult row_before{};
    if (sources.read_targeting_rows == nullptr ||
        !sources.read_targeting_rows(sources.context, row_before) ||
        !ValidProbe(row_before)) {
      AddRed(result, faction_gift_gate_red_row_before_unavailable);
      return Finish(result);
    }

    Observation first{};
    if (!CaptureFactionGiftMitigationObservationFromSourcesV1(
            sources, request.source_faction_id,
            request.recipient_character_id, first)) {
      AddRed(result, faction_gift_gate_red_first_capture_unavailable);
      return Finish(result);
    }
    Observation second{};
    if (!CaptureFactionGiftMitigationObservationFromSourcesV1(
            sources, request.source_faction_id,
            request.recipient_character_id, second)) {
      AddRed(result, faction_gift_gate_red_second_capture_unavailable);
      return Finish(result);
    }

    ProbeResult row_after{};
    if (!sources.read_targeting_rows(sources.context, row_after) ||
        !ValidProbe(row_after)) {
      AddRed(result, faction_gift_gate_red_row_after_unavailable);
      return Finish(result);
    }

    result.row_published_generation = row_after.published_generation;
    result.proof_epoch = row_after.observed_binding.proof_epoch;
    result.snapshot_revision = second.snapshot_revision;
    result.native_snapshot_revision = second.native_snapshot_revision;
    result.date_raw = second.observed_date_raw;
    result.player_character_id = second.player_character_id;
    result.source_faction_id = request.source_faction_id;
    result.recipient_character_id = second.recipient_character_id;
    result.player_gold_raw = second.player_gold_raw;
    result.gift_gold_cost_raw = request.expected_gold_cost_raw;
    result.minimum_gold_reserve_raw = request.minimum_gold_reserve_raw;

    if (!SameProbe(row_before, row_after)) {
      AddRed(result, faction_gift_gate_red_publication_drift);
    }
    if (first != second) {
      AddRed(result, faction_gift_gate_red_observation_drift);
    }
    CheckSemanticBindings(row_after, second, request, result);

    if (binder.idempotency_claim_attempted != claim_before ||
        binder.submit_attempted != submit_before) {
      result.action_callbacks_invoked = true;
      AddRed(result, faction_gift_gate_red_forbidden_action_mutation);
    }
    return Finish(result);
  } catch (...) {
    AddRed(result, faction_gift_gate_red_binder_unavailable);
    return Finish(result);
  }
}

std::string_view FactionGiftMitigationIntegrationGateRedKeyV1(
    std::uint32_t single_flag) noexcept {
  switch (single_flag) {
  case faction_gift_gate_red_none: return "none";
  case faction_gift_gate_red_binder_unavailable:
    return "binder_unavailable";
  case faction_gift_gate_red_action_already_consumed:
    return "action_already_consumed";
  case faction_gift_gate_red_row_before_unavailable:
    return "row_before_unavailable";
  case faction_gift_gate_red_first_capture_unavailable:
    return "first_capture_unavailable";
  case faction_gift_gate_red_second_capture_unavailable:
    return "second_capture_unavailable";
  case faction_gift_gate_red_row_after_unavailable:
    return "row_after_unavailable";
  case faction_gift_gate_red_publication_drift:
    return "publication_drift";
  case faction_gift_gate_red_observation_drift:
    return "observation_drift";
  case faction_gift_gate_red_snapshot_binding:
    return "snapshot_binding";
  case faction_gift_gate_red_identity_binding:
    return "identity_binding";
  case faction_gift_gate_red_faction_binding:
    return "faction_binding";
  case faction_gift_gate_red_resource_binding:
    return "resource_binding";
  case faction_gift_gate_red_preview_binding:
    return "preview_binding";
  case faction_gift_gate_red_budget: return "budget";
  case faction_gift_gate_red_forbidden_action_mutation:
    return "forbidden_action_mutation";
  }
  return "unknown";
}

std::string SerializeFactionGiftMitigationIntegrationGateResultV1(
    const GateResult &result) {
  const auto terminal = result.terminal == GateTerminal::ready ? "ready"
                                                               : "red";
  return "{\"schema_version\":1,\"contract_stage\":" +
         Quote(kFactionGiftMitigationIntegrationGateV1ContractStage) +
         ",\"terminal\":" + Quote(terminal) +
         ",\"red_flags\":" + std::to_string(result.red_flags) +
         ",\"first_red_reason\":" +
         (result.first_red_reason.empty() ?
              "null" : Quote(result.first_red_reason)) +
         ",\"row_published_generation\":" +
         std::to_string(result.row_published_generation) +
         ",\"proof_epoch\":" + std::to_string(result.proof_epoch) +
         ",\"snapshot_revision\":" +
         std::to_string(result.snapshot_revision) +
         ",\"native_snapshot_revision\":" +
         std::to_string(result.native_snapshot_revision) +
         ",\"date_raw\":" + std::to_string(result.date_raw) +
         ",\"player_character_id\":" +
         std::to_string(result.player_character_id) +
         ",\"source_faction_id\":" +
         std::to_string(result.source_faction_id) +
         ",\"recipient_character_id\":" +
         std::to_string(result.recipient_character_id) +
         ",\"player_gold_raw\":" +
         std::to_string(result.player_gold_raw) +
         ",\"gift_gold_cost_raw\":" +
         std::to_string(result.gift_gold_cost_raw) +
         ",\"minimum_gold_reserve_raw\":" +
         std::to_string(result.minimum_gold_reserve_raw) +
         ",\"action_callbacks_invoked\":" +
         (result.action_callbacks_invoked ? "true" : "false") +
         ",\"ready_for_single_submit\":" +
         (result.ready_for_single_submit ? "true" : "false") + "}";
}

} // namespace xar::ck3_11906

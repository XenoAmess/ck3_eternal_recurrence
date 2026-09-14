#include "xar_bridge/faction_gift_mitigation_source_action_adapter_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using AckStatus = game::FactionGiftMitigationAckStatusV1;
using Observation = game::FactionGiftMitigationObservationV1;
using ProbeBinding = bridge::FactionTargetingRowProbeBindingV1;
using ProbeFaction = bridge::FactionTargetingRowProbeFactionV1;
using ProbeResult = bridge::FactionTargetingRowProbeResultV1;
using ReceiptStatus = game::FactionGiftMitigationReceiptStatusV1;

bool SameProbeBinding(const ProbeBinding &left,
                      const ProbeBinding &right) noexcept {
  return left.paused == right.paused &&
         left.proof_epoch == right.proof_epoch &&
         left.snapshot_revision == right.snapshot_revision &&
         left.date_raw == right.date_raw &&
         left.player_character_id == right.player_character_id;
}

bool ValidProbeEnvelope(const ProbeResult &probe) noexcept {
  const bool terminal_valid =
      probe.terminal == bridge::FactionTargetingRowProbeTerminalV1::ready ||
      probe.terminal ==
          bridge::FactionTargetingRowProbeTerminalV1::known_empty;
  if (!terminal_valid ||
      probe.unavailable_reasons !=
          bridge::faction_targeting_row_probe_unavailable_none ||
      probe.observer_failure_flags !=
          bridge::faction_targeting_row_observer_failure_none ||
      probe.published_generation == 0 ||
      (probe.published_generation & 1ULL) != 0 ||
      !SameProbeBinding(probe.required_binding, probe.observed_binding) ||
      !probe.observed_binding.paused ||
      probe.observed_binding.proof_epoch == 0 ||
      probe.observed_binding.snapshot_revision == 0 ||
      probe.observed_binding.player_character_id == 0 ||
      probe.faction_count > probe.factions.size()) {
    return false;
  }
  if (probe.terminal ==
      bridge::FactionTargetingRowProbeTerminalV1::known_empty) {
    return probe.faction_count == 0;
  }
  return probe.faction_count != 0;
}

FactionGiftMitigationSourceFrameV1 FrameFromProbe(
    const ProbeResult &probe) noexcept {
  FactionGiftMitigationSourceFrameV1 frame{};
  frame.paused = probe.observed_binding.paused;
  frame.row_published_generation = probe.published_generation;
  frame.proof_epoch = probe.observed_binding.proof_epoch;
  frame.snapshot_revision = probe.observed_binding.snapshot_revision;
  frame.date_raw = probe.observed_binding.date_raw;
  frame.player_character_id =
      probe.observed_binding.player_character_id;
  return frame;
}

bool DetailsMatchProbeFrame(
    const FactionGiftMitigationSourceFrameV1 &required,
    const FactionGiftMitigationSourceFrameV1 &observed) noexcept {
  return observed.paused == required.paused &&
         observed.row_published_generation ==
             required.row_published_generation &&
         observed.proof_epoch == required.proof_epoch &&
         observed.snapshot_revision == required.snapshot_revision &&
         observed.native_snapshot_revision != 0 &&
         observed.date_raw == required.date_raw &&
         observed.player_character_id == required.player_character_id;
}

const ProbeFaction *FindUniqueFaction(const ProbeResult &probe,
                                      std::uint32_t faction_id,
                                      bool &duplicate) noexcept {
  const ProbeFaction *found = nullptr;
  duplicate = false;
  for (std::size_t index = 0; index < probe.faction_count; ++index) {
    if (probe.factions[index].faction_id != faction_id) continue;
    if (found != nullptr) {
      duplicate = true;
      return nullptr;
    }
    found = &probe.factions[index];
  }
  return found;
}

void CopyFactionRow(const ProbeFaction *row, Observation &output) {
  if (row == nullptr) return;
  output.source_faction_target_character_id = row->target_character_id;
  output.source_faction_targeting_player =
      row->target_character_id == output.player_character_id;
  if (row->leader_present) {
    output.source_faction_leader_character_id =
        row->leader_character_id;
  }
  if (row->character_member_count > row->character_member_ids.size()) {
    output.available = false;
    return;
  }
  output.source_faction_member_character_ids.assign(
      row->character_member_ids.begin(),
      row->character_member_ids.begin() + row->character_member_count);
}

struct AdapterExecutionContextV1 {
  const FactionGiftMitigationSourceActionAccessV1 *sources = nullptr;
  std::uint32_t player_character_id = 0;
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  std::uint64_t definition_stable_hash = 0;
  bool claim_attempted = false;
  bool submit_attempted = false;
};

bool CaptureForAction(void *context, Observation &output) noexcept {
  auto &adapter = *static_cast<AdapterExecutionContextV1 *>(context);
  return CaptureFactionGiftMitigationObservationFromSourcesV1(
      *adapter.sources, adapter.source_faction_id,
      adapter.recipient_character_id, output);
}

bool ValidateForAction(void *context, std::uint32_t player_character_id,
                       std::uint32_t recipient_character_id,
                       std::string_view definition_key, bool &valid,
                       std::string &native_reason_key) noexcept {
  auto &adapter = *static_cast<AdapterExecutionContextV1 *>(context);
  if (player_character_id != adapter.player_character_id ||
      recipient_character_id != adapter.recipient_character_id ||
      definition_key != kFactionGiftMitigationActionV1DefinitionKey ||
      adapter.sources->validate_native == nullptr) {
    valid = false;
    native_reason_key = "adapter_identity_binding_failed";
    return true;
  }
  return adapter.sources->validate_native(
      adapter.sources->context, player_character_id,
      recipient_character_id, definition_key, valid, native_reason_key);
}

bool ClaimForAction(void *context,
                    std::string_view idempotency_key) noexcept {
  auto &adapter = *static_cast<AdapterExecutionContextV1 *>(context);
  if (adapter.claim_attempted ||
      adapter.sources->claim_idempotency_key == nullptr) {
    return false;
  }
  adapter.claim_attempted = true;
  return adapter.sources->claim_idempotency_key(
      adapter.sources->context, idempotency_key);
}

bool SubmitForAction(void *context, std::uint32_t player_character_id,
                     std::uint32_t recipient_character_id,
                     std::uint64_t definition_stable_hash) noexcept {
  auto &adapter = *static_cast<AdapterExecutionContextV1 *>(context);
  if (adapter.submit_attempted ||
      player_character_id != adapter.player_character_id ||
      recipient_character_id != adapter.recipient_character_id ||
      definition_stable_hash != adapter.definition_stable_hash ||
      adapter.sources->submit_native == nullptr) {
    return false;
  }
  adapter.submit_attempted = true;
  return adapter.sources->submit_native(
      adapter.sources->context, player_character_id,
      recipient_character_id, definition_stable_hash);
}

} // namespace

bool CaptureFactionGiftMitigationObservationFromSourcesV1(
    const FactionGiftMitigationSourceActionAccessV1 &sources,
    std::uint32_t source_faction_id, std::uint32_t recipient_character_id,
    Observation &output) noexcept {
  output = {};
  try {
    if (source_faction_id == 0 || recipient_character_id == 0 ||
        sources.read_targeting_rows == nullptr ||
        sources.read_details == nullptr) {
      return false;
    }

    ProbeResult probe{};
    if (!sources.read_targeting_rows(sources.context, probe) ||
        !ValidProbeEnvelope(probe)) {
      return false;
    }
    const auto required_frame = FrameFromProbe(probe);
    FactionGiftMitigationSourceDetailsV1 details{};
    if (!sources.read_details(sources.context, required_frame,
                              source_faction_id, recipient_character_id,
                              details) ||
        !details.available ||
        !DetailsMatchProbeFrame(required_frame, details.frame)) {
      return false;
    }

    bool duplicate = false;
    const auto *row = FindUniqueFaction(probe, source_faction_id, duplicate);
    if (duplicate || details.source_faction_present != (row != nullptr)) {
      return false;
    }

    output.available = true;
    output.paused = details.frame.paused;
    output.snapshot_revision = details.frame.snapshot_revision;
    output.native_snapshot_revision =
        details.frame.native_snapshot_revision;
    output.observed_date_raw = details.frame.date_raw;
    output.player_resources_query_complete =
        details.player_resources_query_complete;
    output.player_character_id = details.frame.player_character_id;
    output.player_gold_raw = details.player_gold_raw;
    output.player_gold_scale = details.player_gold_scale;
    output.source_faction_requery_complete =
        details.source_faction_query_complete;
    output.queried_source_faction_id =
        details.queried_source_faction_id;
    output.source_faction_present = details.source_faction_present;
    output.source_faction_at_war = details.source_faction_at_war;
    output.source_faction_metrics_available =
        details.source_faction_metrics_available;
    output.source_faction_power_raw = details.source_faction_power_raw;
    output.source_faction_discontent_raw =
        details.source_faction_discontent_raw;
    output.source_faction_metric_scale =
        details.source_faction_metric_scale;
    output.recipient_identity_resolved =
        details.recipient_identity_resolved;
    output.recipient_character_id = details.recipient_character_id;
    output.recipient_alive = details.recipient_alive;
    output.recipient_is_ai = details.recipient_is_ai;
    output.recipient_is_direct_landed_vassal =
        details.recipient_is_direct_landed_vassal;
    output.recipient_opinion_query_complete =
        details.recipient_opinion_query_complete;
    output.recipient_opinion_of_player =
        details.recipient_opinion_of_player;
    output.gift_opinion_present = details.gift_opinion_present;
    output.gift_opinion_modifier_value =
        details.gift_opinion_modifier_value;
    output.gift_preview = details.gift_preview;
    CopyFactionRow(row, output);
    return output.available;
  } catch (...) {
    output = {};
    return false;
  }
}

AckStatus ExecuteFactionGiftMitigationSourceActionAdapterV1(
    const FactionGiftMitigationNativeEnvironmentV1 &environment,
    const FactionGiftMitigationSourceActionAccessV1 &sources,
    const game::FactionGiftMitigationRequestV1 &request,
    game::FactionGiftMitigationAckV1 &ack) noexcept {
  AdapterExecutionContextV1 context{};
  context.sources = &sources;
  context.player_character_id = request.player_character_id;
  context.source_faction_id = request.source_faction_id;
  context.recipient_character_id = request.recipient_character_id;
  context.definition_stable_hash =
      request.expected_definition_stable_hash;
  const FactionGiftMitigationActionAccessV1 access{
      &context, &CaptureForAction, &ValidateForAction, &ClaimForAction,
      &SubmitForAction};
  return ExecuteFactionGiftMitigationActionV1(environment, access, request,
                                              ack);
}

ReceiptStatus VerifyFactionGiftMitigationSourceActionReceiptV1(
    const FactionGiftMitigationSourceActionAccessV1 &sources,
    const game::FactionGiftMitigationAckV1 &ack,
    game::FactionGiftMitigationReceiptV1 &receipt) noexcept {
  Observation post{};
  if (ack.status == AckStatus::submitted_verification_pending) {
    CaptureFactionGiftMitigationObservationFromSourcesV1(
        sources, ack.source_faction_id, ack.recipient_character_id, post);
  }
  return VerifyFactionGiftMitigationReceiptV1(ack, post, receipt);
}

} // namespace xar::ck3_11906

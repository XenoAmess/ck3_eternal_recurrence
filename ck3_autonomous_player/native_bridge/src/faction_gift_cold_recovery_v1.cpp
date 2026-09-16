#include "xar_bridge/faction_gift_cold_recovery_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

bool Digest(std::string_view value) noexcept {
  if (value.size() != 64) return false;
  return std::all_of(value.begin(), value.end(), [](char character) {
    return (character >= '0' && character <= '9') ||
           (character >= 'a' && character <= 'f');
  });
}

bool NewProcess(const FactionGiftColdRecoveryRequestV1 &request,
                const FactionGiftColdRecoveryPostV1 &post) noexcept {
  return post.new_process_confirmed && !post.new_round_id.empty() &&
         post.new_round_id != request.source_round_id &&
         post.new_bridge_pid != 0 && !post.new_bridge_creation_date.empty() &&
         (post.new_bridge_pid != request.source_bridge_pid ||
          post.new_bridge_creation_date !=
              request.source_bridge_creation_date);
}

bool BaseFacts(const FactionGiftColdRecoveryRequestV1 &request,
               const FactionGiftColdRecoveryPostV1 &post) noexcept {
  const auto &value = post.observation;
  return !request.request_id.empty() && !request.episode_run_id.empty() &&
         !request.source_round_id.empty() && request.source_bridge_pid != 0 &&
         !request.source_bridge_creation_date.empty() &&
         Digest(request.checkpoint_sha256_before_submit) &&
         request.pre_snapshot_revision != 0 &&
         request.pre_native_snapshot_revision != 0 &&
         request.player_character_id != 0 && request.source_faction_id != 0 &&
         request.recipient_character_id != 0 &&
         request.pre_player_gold_raw >= 0 &&
         request.expected_gold_cost_raw > 0 &&
         request.expected_opinion_delta > 0 &&
         request.pre_player_gold_raw >= request.expected_gold_cost_raw &&
         NewProcess(request, post) &&
         post.episode_run_id == request.episode_run_id &&
         post.independent_faction_storage_lookup_complete &&
         post.independent_recipient_lookup_complete &&
         !post.selected_from_current_targeting_vector &&
         value.available && value.paused && value.snapshot_revision != 0 &&
         value.native_snapshot_revision != 0 &&
         // Revisions are local to each CK3 process; they may restart at one.
         value.observed_date_raw == request.pre_date_raw &&
         value.player_resources_query_complete &&
         value.player_character_id == request.player_character_id &&
         value.source_faction_requery_complete &&
         value.queried_source_faction_id == request.source_faction_id &&
         value.recipient_identity_resolved &&
         value.recipient_character_id == request.recipient_character_id &&
         value.recipient_alive && value.recipient_opinion_query_complete;
}

bool MemberPresent(const game::FactionGiftMitigationObservationV1 &value,
                   std::uint32_t recipient) noexcept {
  return value.source_faction_leader_character_id == recipient ||
         std::find(value.source_faction_member_character_ids.begin(),
                   value.source_faction_member_character_ids.end(),
                   recipient) != value.source_faction_member_character_ids.end();
}

} // namespace

FactionGiftColdRecoveryTerminalV1 EvaluateFactionGiftColdRecoveryV1(
    const FactionGiftColdRecoveryRequestV1 &request,
    const FactionGiftColdRecoveryPostV1 &post,
    FactionGiftColdRecoveryResultV1 &result) noexcept {
  result = {};
  const auto unresolved = [&](std::string_view reason) {
    result.terminal = FactionGiftColdRecoveryTerminalV1::unresolved;
    result.reason.assign(reason);
    result.action_retry_allowed = false;
    return result.terminal;
  };
  if (!BaseFacts(request, post))
    return unresolved("process_or_independent_entity_facts_unproven");
  const auto &value = post.observation;
  if (value.player_gold_raw ==
          request.pre_player_gold_raw - request.expected_gold_cost_raw &&
      value.gift_opinion_present &&
      value.gift_opinion_modifier_value == request.expected_opinion_delta &&
      (!value.source_faction_present ||
       (value.source_faction_metrics_available &&
        value.source_faction_metric_scale != 0))) {
    auto &receipt = result.receipt;
    receipt.status = game::FactionGiftMitigationReceiptStatusV1::mitigated;
    receipt.request_id = request.request_id;
    receipt.post_snapshot_revision = value.snapshot_revision;
    receipt.post_native_snapshot_revision = value.native_snapshot_revision;
    receipt.post_observed_date_raw = value.observed_date_raw;
    receipt.player_character_id = value.player_character_id;
    receipt.source_faction_id = request.source_faction_id;
    receipt.recipient_character_id = request.recipient_character_id;
    receipt.post_player_gold_raw = value.player_gold_raw;
    receipt.post_recipient_opinion_of_player =
        value.recipient_opinion_of_player;
    receipt.post_gift_opinion_present = true;
    receipt.post_gift_opinion_modifier_value =
        value.gift_opinion_modifier_value;
    receipt.source_faction_present = value.source_faction_present;
    receipt.recipient_still_in_source_faction =
        value.source_faction_present &&
        MemberPresent(value, request.recipient_character_id);
    receipt.faction_dissolved = !value.source_faction_present;
    receipt.recipient_left = value.source_faction_present &&
                             !receipt.recipient_still_in_source_faction;
    receipt.mitigation_applied = true;
    receipt.threat_resolved = receipt.faction_dissolved ||
                              receipt.recipient_left ||
                              !value.source_faction_targeting_player;
    if (receipt.threat_resolved)
      receipt.status = game::FactionGiftMitigationReceiptStatusV1::left;
    receipt.postcondition_verified = true;
    result.terminal = FactionGiftColdRecoveryTerminalV1::applied;
    result.reason = "independent_gold_gift_and_faction_readback";
    return result.terminal;
  }
  if (post.save_is_pre_action_checkpoint &&
      post.selected_save_sha256 ==
          request.checkpoint_sha256_before_submit &&
      value.player_gold_raw == request.pre_player_gold_raw &&
      !value.gift_opinion_present &&
      !value.gift_opinion_modifier_value.has_value() &&
      value.recipient_opinion_of_player ==
          request.pre_recipient_opinion_of_player &&
      value.source_faction_present &&
      value.source_faction_targeting_player &&
      value.source_faction_metrics_available &&
      value.source_faction_power_raw ==
          request.pre_source_faction_power_raw &&
      value.source_faction_discontent_raw ==
          request.pre_source_faction_discontent_raw &&
      value.source_faction_member_character_ids ==
          request.pre_source_faction_member_character_ids &&
      MemberPresent(value, request.recipient_character_id)) {
    result.terminal = FactionGiftColdRecoveryTerminalV1::unchanged;
    result.reason = "pre_action_save_and_independent_world_facts_match";
    result.action_retry_allowed = true;
    return result.terminal;
  }
  return unresolved("material_outcome_not_distinguishable");
}

} // namespace xar::ck3_11906

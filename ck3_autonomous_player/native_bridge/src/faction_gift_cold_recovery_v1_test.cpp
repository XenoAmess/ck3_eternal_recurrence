#include "xar_bridge/faction_gift_cold_recovery_v1.hpp"

#include <cstdlib>

namespace {

void Check(bool condition) {
  if (!condition) std::abort();
}

xar::ck3_11906::FactionGiftColdRecoveryRequestV1 Request() {
  xar::ck3_11906::FactionGiftColdRecoveryRequestV1 request{};
  request.request_id = "gift-real-1";
  request.episode_run_id = "native-32904-a";
  request.source_round_id = "R742";
  request.source_bridge_pid = 12345;
  request.source_bridge_creation_date = "2026-09-16T12:00:00Z";
  request.checkpoint_sha256_before_submit = std::string(64, 'a');
  request.pre_snapshot_revision = 412;
  request.pre_native_snapshot_revision = 414;
  request.pre_date_raw = 53'789'952;
  request.player_character_id = 32904;
  request.source_faction_id = 771;
  request.recipient_character_id = 33011;
  request.pre_player_gold_raw = 25'000'000;
  request.expected_gold_cost_raw = 7'500'000;
  request.expected_opinion_delta = 25;
  request.pre_recipient_opinion_of_player = -40;
  request.pre_source_faction_power_raw = 65'000'000;
  request.pre_source_faction_discontent_raw = 45'000'000;
  request.pre_source_faction_member_character_ids = {33011};
  return request;
}

xar::ck3_11906::FactionGiftColdRecoveryPostV1 Post() {
  xar::ck3_11906::FactionGiftColdRecoveryPostV1 post{};
  post.new_round_id = "R744";
  post.new_bridge_pid = 23456;
  post.new_bridge_creation_date = "2026-09-16T12:30:00Z";
  post.episode_run_id = "native-32904-a";
  post.new_process_confirmed = true;
  post.independent_faction_storage_lookup_complete = true;
  post.independent_recipient_lookup_complete = true;
  post.selected_from_current_targeting_vector = false;
  post.selected_save_sha256 = std::string(64, 'b');
  auto &value = post.observation;
  value.available = true;
  value.paused = true;
  // A new process has its own revision counters; no comparison with 412/414.
  value.snapshot_revision = 1;
  value.native_snapshot_revision = 2;
  value.observed_date_raw = 53'789'952;
  value.player_resources_query_complete = true;
  value.player_character_id = 32904;
  value.player_gold_raw = 17'500'000;
  value.source_faction_requery_complete = true;
  value.queried_source_faction_id = 771;
  value.source_faction_present = false;
  value.recipient_identity_resolved = true;
  value.recipient_character_id = 33011;
  value.recipient_alive = true;
  value.recipient_opinion_query_complete = true;
  value.recipient_opinion_of_player = -15;
  value.gift_opinion_present = true;
  value.gift_opinion_modifier_value = 25;
  return post;
}

} // namespace

int main() {
  using namespace xar::ck3_11906;
  using Terminal = FactionGiftColdRecoveryTerminalV1;
  const auto request = Request();
  auto post = Post();
  FactionGiftColdRecoveryResultV1 result{};
  Check(EvaluateFactionGiftColdRecoveryV1(request, post, result) ==
        Terminal::applied);
  Check(result.receipt.postcondition_verified &&
        result.receipt.faction_dissolved &&
        !result.action_retry_allowed);
  post.independent_faction_storage_lookup_complete = false;
  Check(EvaluateFactionGiftColdRecoveryV1(request, post, result) ==
        Terminal::unresolved);
  post.independent_faction_storage_lookup_complete = true;
  post.new_round_id = "R742";
  Check(EvaluateFactionGiftColdRecoveryV1(request, post, result) ==
        Terminal::unresolved);
  post.new_round_id = "R744";
  post.save_is_pre_action_checkpoint = true;
  post.selected_save_sha256 = std::string(64, 'a');
  auto &value = post.observation;
  value.player_gold_raw = 25'000'000;
  value.gift_opinion_present = false;
  value.gift_opinion_modifier_value.reset();
  value.recipient_opinion_of_player = -40;
  value.source_faction_present = true;
  value.source_faction_targeting_player = true;
  value.source_faction_metrics_available = true;
  value.source_faction_power_raw = 65'000'000;
  value.source_faction_discontent_raw = 45'000'000;
  value.source_faction_member_character_ids = {33011};
  Check(EvaluateFactionGiftColdRecoveryV1(request, post, result) ==
        Terminal::unchanged);
  Check(result.action_retry_allowed);
  value.source_faction_member_character_ids.clear();
  Check(EvaluateFactionGiftColdRecoveryV1(request, post, result) ==
        Terminal::unresolved);
  return 0;
}

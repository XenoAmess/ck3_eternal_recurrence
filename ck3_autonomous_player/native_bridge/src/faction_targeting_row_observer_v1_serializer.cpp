#include "xar_bridge/faction_targeting_row_observer_v1_serializer.hpp"

#include <string>

namespace xar::bridge {
namespace {

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

} // namespace

std::string SerializeFactionTargetingRowObserverV1(
    const FactionTargetingRowObserverDiagnosticsV1 &diagnostics) {
  const auto &capture = diagnostics.observation;
  const bool captured = capture.accepted_capture_count != 0;
  std::string output;
  output.reserve(4096 +
                 capture.last_faction_count *
                     (96 +
                      kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1 *
                          12));
  output += "{\"schema_version\":1,\"private_key\":\"";
  output += kFactionTargetingRowObserverPrivateKeyV1;
  output += "\",\"artifact_stem\":\"";
  output += kFactionTargetingRowObserverArtifactStemV1;
  output += "\",\"status\":\"";
  output += captured
      ? (diagnostics.offline_fixture
             ? "fixture-captured-private-leader-member-vector"
             : "production-captured-private-leader-member-vector")
      : "waiting-for-paused-application-main";
  output += "\",\"exact_build\":{\"product_version\":\"1.19.0.6\",";
  output += "\"executable_sha256\":\"";
  output += kFactionTargetingRowObserverExecutableSha256V1;
  output += "\",\"patch_rva\":\"0x1395F0E\",";
  output += "\"get_targeting_factions_rva\":\"0xF6F790\",";
  output += "\"faction_identity_resolver_rva\":\"0xE6F440\",";
  output += "\"character_identity_resolver_rva\":\"0x82B270\",";
  output += "\"faction_leader_character_id_offset\":\"0x44\",";
  output += "\"character_member_container_offset\":\"0x48\",";
  output += "\"character_member_count_offset\":\"0x54\",";
  output += "\"character_member_stride\":\"0x20\"}";
  output += ",\"installed\":";
  AppendBool(output, diagnostics.installed);
  output += ",\"offline_fixture\":";
  AppendBool(output, diagnostics.offline_fixture);
  output += ",\"failure_flags\":" +
      std::to_string(diagnostics.failure_flags);
  output += ",\"readiness\":{\"exact_targeting_span\":true,";
  output += "\"stable_faction_identity\":true,";
  output += "\"same_frame_identity_copy\":";
  AppendBool(output, captured);
  output += ",\"target_character_identity\":";
  AppendBool(output, captured);
  output += ",\"campaign_root_count_equivalence\":";
  AppendBool(output, captured);
  output += ",\"canonical_nullable_leader\":";
  AppendBool(output, captured);
  output += ",\"character_member_vector\":";
  AppendBool(output, captured);
  output += ",\"member_identity\":";
  AppendBool(output, captured);
  output += ",\"member_ownership\":";
  AppendBool(output, captured);
  output += ",\"same_admission_leader_member\":";
  AppendBool(output, captured);
  output += ",\"public_targeting_rows\":false}";
  output += ",\"counters\":{\"callback_calls\":" +
      std::to_string(capture.callback_count);
  output += ",\"rejected_application_main\":" +
      std::to_string(capture.rejected_application_main_count);
  output += ",\"rejected_paused\":" +
      std::to_string(capture.rejected_paused_count);
  output += ",\"rejected_state_change\":" +
      std::to_string(capture.rejected_state_change_count);
  output += ",\"span_read_failures\":" +
      std::to_string(capture.span_read_failure_count);
  output += ",\"span_stability_failures\":" +
      std::to_string(capture.span_stability_failure_count);
  output += ",\"identity_failures\":" +
      std::to_string(capture.identity_failure_count);
  output += ",\"target_character_failures\":" +
      std::to_string(capture.target_character_failure_count);
  output += ",\"count_equivalence_failures\":" +
      std::to_string(capture.count_equivalence_failure_count);
  output += ",\"leader_character_failures\":" +
      std::to_string(capture.leader_character_failure_count);
  output += ",\"leader_stability_failures\":" +
      std::to_string(capture.leader_stability_failure_count);
  output += ",\"member_span_failures\":" +
      std::to_string(capture.member_span_failure_count);
  output += ",\"member_stability_failures\":" +
      std::to_string(capture.member_stability_failure_count);
  output += ",\"member_identity_failures\":" +
      std::to_string(capture.member_identity_failure_count);
  output += ",\"member_ownership_failures\":" +
      std::to_string(capture.member_ownership_failure_count);
  output += ",\"accepted_captures\":" +
      std::to_string(capture.accepted_capture_count) + "}";
  output += ",\"capture\":{\"published_generation\":" +
      std::to_string(capture.published_generation);
  output += ",\"proof_epoch\":" +
      std::to_string(capture.last_proof_epoch);
  output += ",\"snapshot_revision\":" +
      std::to_string(capture.last_snapshot_revision);
  output += ",\"date_raw\":" + std::to_string(capture.last_date_raw);
  output += ",\"player_character_id\":" +
      std::to_string(capture.last_player_character_id);
  output += ",\"campaign_root_targeting_faction_count\":" +
      std::to_string(capture.last_campaign_root_targeting_faction_count);
  output += ",\"thread_id\":" +
      std::to_string(capture.last_thread_id);
  output += ",\"timestamp_qpc\":" +
      std::to_string(capture.last_timestamp_qpc);
  output += ",\"faction_count\":" +
      std::to_string(capture.last_faction_count);
  output += ",\"faction_ids\":[";
  for (std::size_t index = 0;
       index < capture.last_faction_count &&
       index < capture.last_faction_ids.size(); ++index) {
    if (index != 0) output.push_back(',');
    output += std::to_string(capture.last_faction_ids[index]);
  }
  output += "],\"target_character_ids\":[";
  for (std::size_t index = 0;
       index < capture.last_faction_count &&
       index < capture.last_target_character_ids.size(); ++index) {
    if (index != 0) output.push_back(',');
    output += std::to_string(capture.last_target_character_ids[index]);
  }
  output += "],\"factions\":[";
  for (std::size_t index = 0;
       index < capture.last_faction_count &&
       index < capture.last_faction_ids.size(); ++index) {
    if (index != 0) output.push_back(',');
    output += "{\"faction_id\":" +
        std::to_string(capture.last_faction_ids[index]);
    output += ",\"target_character_id\":" +
        std::to_string(capture.last_target_character_ids[index]);
    output += ",\"leader_character_id\":";
    if (capture.last_leader_present[index] != 0) {
      output += std::to_string(capture.last_leader_character_ids[index]);
    } else {
      output += "null";
    }
    output += ",\"leader_present_in_character_members\":";
    AppendBool(output,
               capture.last_leader_present_in_character_members[index] != 0);
    output += ",\"character_member_ids\":[";
    const auto member_count = static_cast<std::size_t>(
        capture.last_character_member_counts[index]);
    const auto member_base =
        index *
        kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
    for (std::size_t member_index = 0;
         member_index < member_count &&
         member_index <
             kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
         ++member_index) {
      if (member_index != 0) output.push_back(',');
      output += std::to_string(
          capture.last_character_member_ids[member_base + member_index]);
    }
    output += "]}";
  }
  output += "]}";
  output += ",\"raw_pointer_fields_persisted\":false,";
  output += "\"raw_row_bytes_persisted\":false,";
  output += "\"raw_member_row_bytes_persisted\":false,";
  output += "\"public_abi_changed\":false,";
  output += "\"public_readiness_changed\":false,";
  output += "\"next_reverse_engineering_entry\":\"";
  output += kFactionTargetingRowObserverNextReverseEngineeringEntryV1;
  output += "\"}";
  return output;
}

} // namespace xar::bridge

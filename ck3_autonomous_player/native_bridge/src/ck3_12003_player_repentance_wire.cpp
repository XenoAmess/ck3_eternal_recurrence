#include "xar_bridge/ck3_12003_player_repentance_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
namespace xar::ck3_12003 {
namespace {
namespace rep = religion::repentance;
std::string Quote(std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
std::string OrdinaryDecisionReadiness(const PlayerRepentanceMailboxContext12003 &query) {
  const auto &candidate = query.candidate_observation;
  const bool complete = candidate.fallback_sources_sampled &&
      candidate.source_candidate_evaluation_complete;
  const bool ready = query.observation.player_excommunication.available &&
      query.recovery_observation.available && query.pam_observation.available && complete;
  const bool legal = candidate.first_observed_ordinary_legal_recipient_character_id.has_value();
  std::string out = "{\"schema\":\"ck3_12003_ordinary_repentance_decision_readiness_v1\""
      ",\"read_only\":true,\"capture_epoch\":" + std::to_string(candidate.capture_epoch) +
      ",\"date_raw\":" + std::to_string(candidate.date_raw) +
      ",\"played_character_id\":" + std::to_string(candidate.played_character_id) +
      ",\"ordinary_candidate_collection_complete\":" + (complete ? "true" : "false") +
      ",\"ordinary_recovery_decision_inputs_ready\":" + (ready ? "true" : "false") +
      ",\"any_observed_ordinary_request_terms_ready\":" + (legal ? "true" : "false") +
      ",\"ordinary_request_route_currently_absent\":";
  out += ready ? (legal ? "false" : "true") : "null";
  out += ",\"first_observed_ordinary_legal_recipient_character_id\":";
  out += legal ? std::to_string(*candidate.first_observed_ordinary_legal_recipient_character_id) : "null";
  out += ",\"selected_repentance_petition_terms_ready\":false"
      ",\"scope\":\"ordinary_request_candidate_set_and_current_route_inputs\"}";
  return out;
}
} // namespace

std::string SerializePlayerRepentanceResult12003(
    const PlayerRepentanceMailboxContext12003 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  auto observation = rep::SerializeRepentanceContext12003(query.observation);
  if (query.candidate_observation.capture_epoch != 0) {
    observation.pop_back();
    observation += ",\"recipient_candidates\":" +
        religion::repentance_candidates::SerializeRepentanceRecipientCandidates12003(query.candidate_observation);
    if (query.fallback_observation.capture_epoch != 0)
      observation += ",\"repentance_fallback_sources\":" +
          religion::repentance_fallback::SerializeRepentanceFallback12003(query.fallback_observation);
    if (query.recovery_observation.capture_epoch != 0)
      observation += ",\"repentance_recovery_inputs\":" +
          religion::repentance_recovery_inputs::SerializePlayerRepentanceRecoveryInputs12003(query.recovery_observation);
    if (query.pam_observation.capture_epoch != 0)
      observation += ",\"repentance_pam_route\":" +
          religion::repentance_pam_route::SerializeRepentancePamRoute12003(query.pam_observation);
    if (query.petition_observation.capture_epoch != 0)
      observation += ",\"petition_decision_terms\":" +
          religion::repentance_petition::SerializePlayerRepentancePetitionDecisionTerms12003(query.petition_observation);
    if (query.recovery_observation.capture_epoch != 0 && query.pam_observation.capture_epoch != 0)
      observation += ",\"ordinary_recovery_readiness\":" + OrdinaryDecisionReadiness(query);
    observation += "}";
  }
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerRepentancePrivateStep12003) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":" + Quote(rep::kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerRepentanceDomainKey12003) +
      ",\"backend_id\":" + Quote(kPlayerRepentanceBackend12003) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_repentance_context\":" + observation + "}}";
}

} // namespace xar::ck3_12003
#endif

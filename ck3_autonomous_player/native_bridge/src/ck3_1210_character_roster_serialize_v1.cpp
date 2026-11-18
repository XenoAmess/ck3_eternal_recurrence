#include "xar_bridge/ck3_1210_character_roster_frame_v1.hpp"
namespace xar::ck3_1210 {
namespace {
void Quote(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef"; out += char(34);
  for (const unsigned char c : value) {
    if (c == 34 || c == 92) { out += char(92); out += char(c); }
    else if (c < 32) { out += char(92); out += "u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += char(c);
  }
  out += char(34);
}
void Decimal(std::string &out, std::uint64_t value) { Quote(out, std::to_string(value)); }
} // namespace
std::string SerializeCharacterRosterResultV1(const CharacterRosterMailboxContextV1 &q) {
  std::string data; std::string_view reason{};
  const bool valid_data = SerializeCharacterManagerCandidateDataV1(q.observation, data, reason);
  const auto invalid_reason = reason;
  if (!valid_data) {
    CharacterManagerObservationV1 failed{}; failed.unavailable_reason = reason;
    if (!SerializeCharacterManagerCandidateDataV1(failed, data, reason)) return {};
  }
  const auto &p = q.source;
  const bool custody = q.application_main_observed && p.custody_available && !p.offline_fixture &&
    p.native_revision && p.connection_generation && p.mailbox_sequence && p.pump_epoch && p.owner_thread_id &&
    p.played_character_id != -1 && p.native_revision == q.expected_native_revision &&
    p.connection_generation == q.expected_connection_generation &&
    (!q.observation.available || (p.date_raw == q.observation.frame.clock.date_raw &&
      p.played_character_id == q.observation.frame.played_character_id));
  const bool available = valid_data && custody && q.observation.available && q.observation.same_frame_ready;
  std::string out = R"({"schema":)"; Quote(out, kCharacterRosterSchemaV1);
  out += R"(,"step":)"; Quote(out, kCharacterRosterStepV1);
  out += R"(,"game_version":)"; Quote(out, kGameVersion);
  out += R"(,"executable_sha256":)"; Quote(out, kExecutableSha256);
  out += R"(,"adapter_id":)"; Quote(out, kAdapterId);
  out += R"(,"source_role":"actor_readonly_manager_roster","read_only":true,"roster_available":)";
  out += available ? "true" : "false";
  out += R"(,"application_main_observed":)"; out += custody ? "true" : "false";
  out += R"(,"source_kind":)"; Quote(out, p.offline_fixture ? "offline_fixture" : custody ? "owned_actor" : "unqualified");
  out += R"(,"model_source_observed":false,"model_source":null,"same_owner_family_join_available":false,"all_living_complete":false,"interaction_candidates_complete":false,"source_proof":)";
  if (!custody) out += "null";
  else {
    out += R"({"source_domain":"character_manager_maintained_members","native_revision":)"; Decimal(out, p.native_revision);
    out += R"(,"connection_generation":)"; Decimal(out, p.connection_generation);
    out += R"(,"mailbox_sequence":)"; Decimal(out, p.mailbox_sequence);
    out += R"(,"pump_epoch":)"; Decimal(out, p.pump_epoch);
    out += R"(,"owner_thread_id":)" + std::to_string(p.owner_thread_id);
    out += R"(,"date_raw":)" + std::to_string(p.date_raw);
    out += R"(,"played_character_id":)" + std::to_string(p.played_character_id) + '}';
  }
  out += R"(,"data":)" + data;
  out += R"(,"unavailable_reason":)";
  if (available) out += "null";
  else Quote(out, !valid_data ? invalid_reason : custody ? q.observation.unavailable_reason :
    p.offline_fixture ? "offline_fixture_is_not_actual_owner_proof" : "character_roster_owner_unqualified");
  out += '}'; return out;
}
std::string SerializeCharacterRosterCommandResultV1(std::string_view id,
    const CharacterRosterMailboxContextV1 &q) {
  std::string out = R"({"type":"command_result","protocol_version":1,"request_id":)";
  Quote(out, id); out += R"(,"ok":true,"result":)" + SerializeCharacterRosterResultV1(q) + '}'; return out;
}
} // namespace xar::ck3_1210

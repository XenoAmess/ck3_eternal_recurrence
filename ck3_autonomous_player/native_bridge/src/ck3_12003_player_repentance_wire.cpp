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
} // namespace

std::string SerializePlayerRepentanceResult12003(
    const PlayerRepentanceMailboxContext12003 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerRepentancePrivateStep12003) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":" + Quote(rep::kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerRepentanceDomainKey12003) +
      ",\"backend_id\":" + Quote(kPlayerRepentanceBackend12003) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_repentance_context\":" + rep::SerializeRepentanceContext12003(query.observation) + "}}";
}

} // namespace xar::ck3_12003
#endif

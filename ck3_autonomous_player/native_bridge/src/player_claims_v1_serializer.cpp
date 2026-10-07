#include "xar_bridge/player_claims_v1_serializer.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <charconv>
#include <system_error>

namespace xar::game {
namespace {
std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
const char *Bool(bool value) noexcept { return value ? "true" : "false"; }
std::string Ids(std::span<const std::int32_t> ids) {
  std::string out = "[";
  for (const auto id : ids) { if (out.size() > 1) out += ','; out += std::to_string(id); }
  return out + ']';
}
} // namespace


std::string SerializePlayerClaimsV1(const PlayerClaimsV1 &o,
    ReadPlayerClaimsV1Result read_result, std::uint64_t sequence,
    std::uint64_t revision, std::string_view step) {
  const bool available = read_result == ReadPlayerClaimsV1Result::available && o.available;
  const auto status = available ? "available" : "unavailable";
  std::string rows = "null";
  if (available) {
    rows = "[";
    for (const auto &row : o.claims) {
      if (rows.size() > 1) rows += ',';
      rows += "{\"title_id\":" + std::to_string(row.title_id) +
          ",\"present\":" + Bool(row.present) + ",\"state\":" + Quote(row.state) +
          ",\"strong\":" + (row.present ? Bool(row.strong) : "null") +
          ",\"implicit\":" + (row.present ? Bool(row.implicit) : "null") + '}';
    }
    rows += ']';
  }
  const auto reason = available ? std::string("null") : Quote(
      o.unavailable_reason.empty() ? "native_reader_unavailable" : o.unavailable_reason);
  return "{\"step\":" + Quote(step) + ",\"accepted\":true,\"read_only\":true,"
      "\"status\":" + Quote(status) + ",\"query_sequence\":" + std::to_string(sequence) +
      ",\"snapshot_revision\":" + std::to_string(revision) +
      ",\"date_raw\":" + std::to_string(o.date_raw) +
      ",\"backend_id\":\"native-headless\",\"player_claims\":{"
      "\"schema\":\"xar.ck3.player-claims.v1\",\"schema_version\":1,"
      "\"game_version\":" + Quote(ck3_12004::kGameVersion) +
      ",\"executable_sha256\":" + Quote(ck3_12004::kExecutableSha256) +
      ",\"status\":" + Quote(status) + ",\"available\":" + Bool(available) +
      ",\"snapshot_revision\":" + std::to_string(revision) +
      ",\"date_raw\":" + std::to_string(o.date_raw) +
      ",\"actor_character_id\":" + std::to_string(o.actor_character_id) +
      ",\"title_ids\":" + Ids(o.title_ids) + ",\"claims\":" + rows +
      ",\"unavailable_reason\":" + reason + "}}";
}
} // namespace xar::game

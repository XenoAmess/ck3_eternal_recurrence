#include "xar_bridge/title_own_laws_v1_serializer.hpp"
#include "xar_bridge/ck3_12004.hpp"

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
bool Complete(const TitleOwnLawsV1 &o) noexcept {
  return o.title_id != UINT32_MAX && o.native_law_count.has_value() &&
      *o.native_law_count >= 0 && o.laws.has_value() &&
      static_cast<std::size_t>(*o.native_law_count) == o.laws->size() &&
      o.single_heir_member.has_value();
}
} // namespace

std::string SerializeTitleOwnLawsV1(const TitleOwnLawsV1 &o,
    ReadTitleOwnLawsV1Result read_result, std::uint64_t sequence,
    std::uint64_t revision, std::string_view step) {
  const bool available = read_result == ReadTitleOwnLawsV1Result::available &&
      o.available && Complete(o);
  const auto status = available ? "available" : "unavailable";
  std::string rows = "null";
  if (available) {
    rows = "[";
    for (const auto &row : *o.laws) {
      if (rows.size() > 1) rows += ',';
      rows += "{\"native_definition_id\":" + std::to_string(row.native_definition_id) +
          ",\"key\":" + Quote(row.key) + '}';
    }
    rows += ']';
  }
  const auto reason = available ? std::string("null") : Quote(
      o.unavailable_reason.empty() ? "native_reader_unavailable" : o.unavailable_reason);
  return "{\"step\":" + Quote(step) + ",\"accepted\":true,\"read_only\":true,"
      "\"status\":" + Quote(status) + ",\"query_sequence\":" + std::to_string(sequence) +
      ",\"snapshot_revision\":" + std::to_string(revision) +
      ",\"date_raw\":" + std::to_string(o.date_raw) +
      ",\"backend_id\":\"native-headless\",\"title_own_laws\":{"
      "\"schema\":" + Quote(kTitleOwnLawsV1Schema) + ",\"schema_version\":1,"
      "\"game_version\":" + Quote(ck3_12004::kGameVersion) +
      ",\"executable_sha256\":" + Quote(ck3_12004::kExecutableSha256) +
      ",\"status\":" + Quote(status) + ",\"available\":" + Bool(available) +
      ",\"snapshot_revision\":" + std::to_string(revision) +
      ",\"date_raw\":" + std::to_string(o.date_raw) +
      ",\"actor_character_id\":" + std::to_string(o.actor_character_id) +
      ",\"title_id\":" + std::to_string(o.title_id) +
      ",\"native_law_count\":" + (available ? std::to_string(*o.native_law_count) : "null") +
      ",\"laws\":" + rows + ",\"single_heir_member\":" +
      (available ? Bool(*o.single_heir_member) : "null") +
      ",\"unavailable_reason\":" + reason + "}}";
}
} // namespace xar::game

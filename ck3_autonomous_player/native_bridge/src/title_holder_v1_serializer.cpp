#include "xar_bridge/title_holder_v1_serializer.hpp"
#include "xar_bridge/ck3_12003.hpp"

namespace xar::game {
namespace {

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') {
      out += '\\';
      out += static_cast<char>(byte);
    } else if (byte < 0x20) {
      out += "\\u00";
      out += hex[byte >> 4];
      out += hex[byte & 15];
    } else {
      out += static_cast<char>(byte);
    }
  }
  return out + '"';
}

const char *Bool(bool value) noexcept { return value ? "true" : "false"; }

std::string NullableId(std::optional<std::int32_t> value) {
  return value.has_value() ? std::to_string(*value) : std::string("null");
}

std::string FrameId(std::int32_t value) {
  return value == -1 ? std::string("null") : std::to_string(value);
}

} // namespace

std::string SerializeTitleHolderV1(
    const TitleHolderV1 &observation, ReadTitleHolderV1Result read_result,
    std::uint64_t query_sequence, std::uint64_t snapshot_revision,
    std::string_view step) {
  const bool available = read_result == ReadTitleHolderV1Result::available &&
      observation.available;
  const auto status = available ? "available" : "unavailable";
  const auto reason = available ? std::string("null") : Quote(
      observation.unavailable_reason.empty()
          ? std::string_view("native_reader_unavailable")
          : observation.unavailable_reason);
  return "{\"step\":" + Quote(step) +
      ",\"accepted\":true,\"status\":" + Quote(status) +
      ",\"read_only\":true,\"query_sequence\":" +
      std::to_string(query_sequence) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(observation.date_raw) +
      ",\"backend_id\":\"native-headless\",\"title_holder\":{"
      "\"schema\":\"xar.ck3.title-holder.v1\",\"schema_version\":1,"
      "\"game_version\":\"1.20.0.3\",\"executable_sha256\":" +
      Quote(ck3_12003::kExecutableSha256) +
      ",\"status\":" + Quote(status) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(observation.date_raw) +
      ",\"actor_character_id\":" + FrameId(observation.actor_character_id) +
      ",\"title_id\":" + FrameId(observation.title_id) +
      ",\"title_tier_raw\":" + (available
          ? std::to_string(observation.title_tier_raw) : std::string("null")) +
      ",\"title_tier_key\":" + (available
          ? Quote(observation.title_tier_key) : std::string("null")) +
      ",\"holder_character_id\":" + (available
          ? NullableId(observation.holder_character_id) : std::string("null")) +
      ",\"holder_is_player\":" + (available
          ? Bool(observation.holder_is_player) : "null") +
      ",\"holder_in_player_realm\":" + (available
          ? Bool(observation.holder_in_player_realm) : "null") +
      ",\"holder_immediate_liege_character_id\":" + (available
          ? NullableId(observation.holder_immediate_liege_character_id)
          : std::string("null")) +
      ",\"holder_top_liege_character_id\":" + (available
          ? NullableId(observation.holder_top_liege_character_id)
          : std::string("null")) +
      ",\"available\":" + Bool(available) +
      ",\"unavailable_reason\":" + reason + "}}";
}

} // namespace xar::game

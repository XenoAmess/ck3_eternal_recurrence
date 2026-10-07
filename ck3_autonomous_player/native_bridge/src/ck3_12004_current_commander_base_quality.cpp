#include "xar_bridge/ck3_12004_current_commander_base_quality.hpp"

#include "xar_bridge/ck3_12003_current_commander_martial_serializer.hpp"

namespace xar::ck3_12004 {

CurrentCommanderNativeBaseQualitySnapshot
ReadCurrentCommanderNativeBaseQuality(
    std::int32_t actual_character_id, void *validated_current_character,
    CurrentCommanderNativeBaseQualityReader get_native_ai_base_quality) noexcept {
  CurrentCommanderNativeBaseQualitySnapshot output{};
  if (actual_character_id == -1) {
    output.unavailable_reason = "current_commander_absent";
    return output;
  }
  output.source_character_id = actual_character_id;
  if (validated_current_character == nullptr) {
    output.unavailable_reason = "current_commander_identity_unavailable";
    return output;
  }
  if (get_native_ai_base_quality == nullptr) {
    output.unavailable_reason = "current_commander_quality_reader_unavailable";
    return output;
  }
  output.value = get_native_ai_base_quality(validated_current_character);
  output.status = "available";
  output.unavailable_reason = {};
  return output;
}

std::string SerializeCurrentCommanderNativeBaseQuality(
    const CurrentCommanderNativeBaseQualitySnapshot &quality) {
  const auto quote = ck3_12003::current_commander_martial_detail::Quote;
  return "{\"status\":" + quote(quality.status) +
      ",\"source\":" + quote(quality.source) +
      ",\"source_character_id\":" +
      (quality.source_character_id
           ? std::to_string(*quality.source_character_id) : std::string("null")) +
      ",\"value\":" +
      (quality.status == "available" && quality.value
           ? std::to_string(*quality.value) : std::string("null")) +
      ",\"unavailable_reason\":" +
      (quality.unavailable_reason.empty() ? std::string("null")
                                         : quote(quality.unavailable_reason)) + '}';
}

} // namespace xar::ck3_12004

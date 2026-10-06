#pragma once

#include "xar_bridge/ck3_12003_commander_target_roll_dto.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12003 {
namespace commander_target_roll_detail {

inline std::string Quote(std::string_view value) {
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

} // namespace commander_target_roll_detail

inline std::string SerializeCommanderCandidateTargetRollBounds(
    const CommanderCandidateTargetRollBoundsSnapshot &bounds) {
  const auto quote = commander_target_roll_detail::Quote;
  return "{\"status\":" + quote(bounds.status) +
      ",\"source\":" + quote(bounds.source) +
      ",\"source_target_province_id\":" +
      std::to_string(bounds.source_target_province_id) +
      ",\"effective_min_roll\":" +
      (bounds.status == "available" && bounds.effective_min_roll
           ? std::to_string(*bounds.effective_min_roll) : std::string("null")) +
      ",\"effective_max_roll\":" +
      (bounds.status == "available" && bounds.effective_max_roll
           ? std::to_string(*bounds.effective_max_roll) : std::string("null")) +
      ",\"unavailable_reason\":" +
      (bounds.unavailable_reason.empty() ? std::string("null")
                                        : quote(bounds.unavailable_reason)) + '}';
}

} // namespace xar::ck3_12003

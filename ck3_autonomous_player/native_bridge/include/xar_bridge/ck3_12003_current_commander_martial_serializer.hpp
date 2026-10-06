#pragma once

#include "xar_bridge/ck3_12003_current_commander_martial_dto.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12003 {
namespace current_commander_martial_detail {

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

} // namespace current_commander_martial_detail

inline std::string SerializeCurrentCommanderTotalMartial(
    const CurrentCommanderTotalMartialSnapshot &martial) {
  const auto quote = current_commander_martial_detail::Quote;
  return "{\"status\":" + quote(martial.status) +
      ",\"source\":" + quote(martial.source) +
      ",\"source_character_id\":" +
      (martial.source_character_id ? std::to_string(*martial.source_character_id)
                                   : std::string("null")) +
      ",\"skill_index\":" + std::to_string(martial.skill_index) +
      ",\"value\":" +
      (martial.status == "available" && martial.value
           ? std::to_string(*martial.value) : std::string("null")) +
      ",\"unavailable_reason\":" +
      (martial.unavailable_reason.empty() ? std::string("null")
                                         : quote(martial.unavailable_reason)) + '}';
}

} // namespace xar::ck3_12003

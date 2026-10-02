#pragma once

#include <charconv>
#include <cstdint>
#include <string_view>

namespace xar::game {
// Public ArmySnapshot IDs are full CUnit handles: slot/generation zero is
// valid. Other native entity namespaces keep their own ID contracts.
inline bool ParsePublicCUnitIdV1(std::string_view text,
                                std::int32_t &output) noexcept {
  output = -1;
  if (text.empty() || (text.size() > 1 && text.front() == '0')) {
    return false;
  }
  for (const char c : text) {
    if (c < '0' || c > '9') return false;
  }
  std::int32_t value = -1;
  const auto parsed =
      std::from_chars(text.data(), text.data() + text.size(), value);
  if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size() ||
      value < 0) {
    return false;
  }
  output = value;
  return true;
}
} // namespace xar::game

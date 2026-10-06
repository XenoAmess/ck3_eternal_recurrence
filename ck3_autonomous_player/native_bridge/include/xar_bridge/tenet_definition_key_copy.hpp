#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>

namespace xar::ck3_12002::religion::doctrine12002::detail {
// Same source-closed key copier used by the existing Core/personal reader.
inline bool CopyTenetDefinitionKeySource(const void *definition, std::string &out) {
  const auto load = []<typename T>(const void *object, std::size_t offset) {
    T value{};
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
    return value;
  };
  if (!definition || load.operator()<std::uint32_t>(definition, 0x38) != 0x4744624F) return false;
  const auto *text = static_cast<const std::byte *>(definition) + 0x18;
  const auto size = load.operator()<std::uint64_t>(text, 0x10);
  const auto capacity = load.operator()<std::uint64_t>(text, 0x18);
  if (!size || size > capacity || size > 4096) return false;
  const auto *data = capacity < 16 ? reinterpret_cast<const char *>(text) : load.operator()<const char *>(text, 0);
  if (!data) return false;
  out.assign(data, static_cast<std::size_t>(size));
  return true;
}
} // namespace xar::ck3_12002::religion::doctrine12002::detail

#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>

namespace xar::ck3_12002::combat_effect_detail {
template<class T> inline T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
inline bool ReadKey(void *object, std::string &key) {
  if (!object) return false;
  const auto length = Load<std::size_t>(object, 0x28);
  const auto capacity = Load<std::size_t>(object, 0x30);
  if (length == 0 || length > 512 || capacity < length) return false;
  const auto *data = capacity < 16 ? static_cast<const char *>(object) + 0x18
                                  : Load<const char *>(object, 0x18);
  if (!data) return false;
  key.assign(data, length);
  return true;
}
inline bool ValidEffect(void *effect) noexcept {
  return effect && Load<std::uint32_t>(effect, 0x38) == 0x4744624FU;
}
} // namespace xar::ck3_12002::combat_effect_detail

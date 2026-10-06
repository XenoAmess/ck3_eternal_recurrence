#pragma once

#include "xar_bridge/religion_doctrine12002_tenet.hpp"
#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion::doctrine12002::detail {
template <typename T> inline T LoadRiteBoolean(const void *object,
                                             std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
inline bool CopyRiteBooleanKey(const void *native_string, std::string &out) {
  if (!native_string) return false;
  const auto size = LoadRiteBoolean<std::uint64_t>(native_string, 0x10);
  const auto capacity = LoadRiteBoolean<std::uint64_t>(native_string, 0x18);
  if (!size || size > capacity || size > 4096) return false;
  const auto *data = capacity < 16 ? static_cast<const char *>(native_string)
                                 : LoadRiteBoolean<const char *>(native_string, 0);
  if (!data) return false;
  out.assign(data, static_cast<std::size_t>(size));
  return true;
}

// Extracted unchanged from the existing played-Rite reader's internal ReadRite.
// The caller selects an actual Rite; this copier never changes the actor root.
inline std::string CopyRiteBooleanParameters(
    const TenetParameterBindings &b, const void *rite, std::uint32_t id,
    RiteBooleanParameters &out) {
  if (!rite || LoadRiteBoolean<std::uint32_t>(rite, religion::kReferenceIdentityOffset) != id)
    return "rite_unavailable";
  const auto *collection = static_cast<const std::byte *>(rite) + kRiteBooleanParameterOffset;
  const auto count = LoadRiteBoolean<std::int32_t>(collection, kArrayCountOffset);
  const auto *data = LoadRiteBoolean<const std::int32_t *>(collection, kArrayDataOffset);
  if (count < 0 || count > 8192 || (count && !data)) return "parameter_collection_unavailable";
  out.rite_id = id;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto token = LoadRiteBoolean<std::int32_t>(data, static_cast<std::size_t>(i) * sizeof(std::int32_t));
    if (!b.contains_boolean_parameter(collection, &token)) return "parameter_membership_unavailable";
    std::string key;
    if (!CopyRiteBooleanKey(b.parameter_key(token), key)) return "parameter_key_unavailable";
    out.parameters.push_back({std::move(key), true});
  }
  if (LoadRiteBoolean<const std::int32_t *>(collection, kArrayDataOffset) != data ||
      LoadRiteBoolean<std::int32_t>(collection, kArrayCountOffset) != count ||
      LoadRiteBoolean<std::uint32_t>(rite, religion::kReferenceIdentityOffset) != id)
    return "state_changed";
  return {};
}
} // namespace xar::ck3_12002::religion::doctrine12002::detail

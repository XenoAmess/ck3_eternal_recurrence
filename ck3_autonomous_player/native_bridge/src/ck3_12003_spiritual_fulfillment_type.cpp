#include "xar_bridge/ck3_12003_spiritual_fulfillment_type.hpp"

#include <cstring>

namespace xar::ck3_12003::religion::fulfillment_type {
namespace {
template <typename T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool CopyTypeKey(const void *type, std::string &out) {
  // The exact .3 SSpiritualFulfillmentType constructor copies its stable key
  // into this+18 (MSVC string); this is not the localized GetName result.
  const auto *key = static_cast<const std::byte *>(type) + 0x18;
  const auto size = Load<std::size_t>(key, 0x10);
  const auto capacity = Load<std::size_t>(key, 0x18);
  if (size > capacity) return false;
  const auto *text = capacity <= 15 ? reinterpret_cast<const char *>(key) : Load<const char *>(key);
  if (size && !text) return false;
  if (size) out.assign(text, size); else out.clear();
  return true;
}
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
} // namespace

bool ReadPlayerSpiritualFulfillmentType12003(const Bindings &b,
    void *actor, const CurrentContext &current, Type &out) noexcept {
  out = {};
  out.capture_epoch = current.capture_epoch;
  out.date_raw = current.date_raw;
  out.played_character_id = current.played_character_id;
  if (!b.enabled || !b.database_slot || !b.type_for_character) return false;
  if (!current.available) {
    out.unavailable_reason = "current_context_unavailable"; return false;
  }
  if (!actor || current.played_character_id <= 0 ||
      Load<std::int32_t>(actor, 0x18) != current.played_character_id) {
    out.unavailable_reason = "played_character_mismatch"; return false;
  }
  try {
    auto *database = Load<void *>(b.database_slot);
    if (!database) { out.unavailable_reason = "database_unavailable"; return false; }
    const auto *type = b.type_for_character(database, actor);
    if (!type) { out.unavailable_reason = "fulfillment_type_unavailable"; return false; }
    std::string key;
    if (!CopyTypeKey(type, key)) {
      out.unavailable_reason = "fulfillment_type_key_unavailable"; return false;
    }
    out.has_christian_fulfillment_type = key == kChristianType;
    out.spiritual_fulfillment_type_key = std::move(key);
    out.available = true; out.unavailable_reason.clear();
    return true;
  } catch (...) { out.unavailable_reason = "fulfillment_type_copy_exception"; return false; }
}

std::string SerializePlayerSpiritualFulfillmentType12003(const Type &t) {
  return "{\"schema\":" + Quote(kSchema) + ",\"read_only\":true,\"available\":" +
      (t.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (t.available ? "null" : Quote(t.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(t.capture_epoch) +
      ",\"date_raw\":" + std::to_string(t.date_raw) +
      ",\"played_character_id\":" + std::to_string(t.played_character_id) +
      ",\"spiritual_fulfillment_type_key\":" +
      (t.spiritual_fulfillment_type_key ? Quote(*t.spiritual_fulfillment_type_key) : "null") +
      ",\"has_christian_fulfillment_type\":" +
      (t.has_christian_fulfillment_type ? (*t.has_christian_fulfillment_type ? "true" : "false") : "null") + "}";
}

} // namespace xar::ck3_12003::religion::fulfillment_type

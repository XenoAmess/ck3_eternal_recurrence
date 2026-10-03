#include "xar_bridge/ck3_12003_pilgrimage_activity_type_terms.hpp"

#include <array>
#include <cstring>
#include <sstream>
#include <utility>

namespace xar::ck3_12003::religion::pilgrimage {
namespace {
template <typename T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <typename T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
bool KeyEquals(const void *type) noexcept {
  const auto *key = static_cast<const std::byte *>(type) + 0x18;
  const auto size = Load<std::size_t>(key, 0x10);
  const auto capacity = Load<std::size_t>(key, 0x18);
  if (size != kActivityId.size() || capacity < size) return false;
  const auto *bytes = capacity < 16 ? reinterpret_cast<const char *>(key) : Load<const char *>(key);
  return bytes && std::memcmp(bytes, kActivityId.data(), size) == 0;
}
const void *FindPilgrimage(const Bindings &b, const void *database) noexcept {
  const auto *rows = Load<const void *const *>(database, 0x50);
  const auto count = Load<std::int32_t>(database, 0x5C);
  if (!rows || count <= 0) return nullptr;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *type = rows[index];
    if (type && Load<std::uintptr_t>(type) == b.activity_type_vtable && KeyEquals(type)) return type;
  }
  return nullptr;
}
class NativeReason {
public:
  explicit NativeReason(const Bindings &b) noexcept : b_(b) {
    // The callable tooltip also initializes this native canonical empty state.
    // Its native append owns any heap allocation; copy before native destruction.
    Store<std::size_t>(bytes_.data(), 0x18, 15);
  }
  ~NativeReason() { b_.reason_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &out) const {
    const auto size = Load<std::size_t>(bytes_.data(), 0x10);
    const auto capacity = Load<std::size_t>(bytes_.data(), 0x18);
    if (size > capacity) return false;
    const char *text = capacity < 16 ? reinterpret_cast<const char *>(bytes_.data()) : Load<const char *>(bytes_.data());
    if (size && !text) return false;
    if (size == 0) out.clear(); else out.assign(text, size);
    return true;
  }
  NativeReason(const NativeReason &) = delete;
  NativeReason &operator=(const NativeReason &) = delete;
private:
  alignas(8) std::array<std::byte, 0x20> bytes_{};
  const Bindings &b_;
};
std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string result = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') { result += '\\'; result += static_cast<char>(byte); }
    else if (byte < 0x20) { result += "\\u00"; result += hex[byte >> 4]; result += hex[byte & 15]; }
    else result += static_cast<char>(byte);
  }
  return result + '"';
}
} // namespace

Bindings BindPlayerPilgrimageActivityTypeTermsImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.activity_type_database = reinterpret_cast<void **>(base + 0x5C67208);
  b.activity_type_vtable = base + 0x48BFE50;
  b.can_plan = reinterpret_cast<ActivityCanPlan>(base + 0x9DC990);
  b.can_plan_tooltip = reinterpret_cast<ActivityCanPlanTooltip>(base + 0x9DCC40);
  b.reason_destroy = reinterpret_cast<ReasonDestroy>(base + 0x856050);
  return b;
}

bool ReadPlayerPilgrimageActivityTypeTerms12003(const Bindings &b, void *character,
    std::int32_t id, std::int32_t date, std::uint64_t epoch, Terms &out) noexcept {
  out = {};
  out.capture_epoch = epoch; out.date_raw = date; out.played_character_id = id;
  if (!b.enabled || !b.activity_type_database || !b.activity_type_vtable ||
      !b.can_plan || !b.can_plan_tooltip || !b.reason_destroy) return false;
  if (!character || id <= 0 || Load<std::int32_t>(character, 0x18) != id) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  try {
    const auto *database = *b.activity_type_database;
    if (!database) { out.unavailable_reason = "activity_type_database_unavailable"; return false; }
    const auto *type = FindPilgrimage(b, database);
    if (!type) { out.unavailable_reason = "activity_type_definition_unavailable"; return false; }
    // These two exact wrappers each construct and destroy their own player scope.
    // Tooltip internally calls the native predicate with mode0/detailfalse.
    out.can_plan = b.can_plan(type, character);
    NativeReason reason(b);
    (void)b.can_plan_tooltip(reason.get(), type, character);
    std::string owned;
    out.reasons_available = reason.copy(owned);
    if (out.reasons_available) out.can_plan_reasons = std::move(owned);
    else { out.unavailable_reason = "activity_can_plan_reasons_unavailable"; return false; }
    out.available = true; out.unavailable_reason.clear();
    return true;
  } catch (...) { out.unavailable_reason = "activity_can_plan_native_copy_exception"; return false; }
}

std::string SerializePlayerPilgrimageActivityTypeTerms12003(const Terms &t) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":" << Quote(kSchema)
      << ",\"read_only\":true,\"available\":" << t.available
      << ",\"unavailable_reason\":" << (t.available ? "null" : Quote(t.unavailable_reason))
      << ",\"capture_epoch\":" << t.capture_epoch << ",\"date_raw\":" << t.date_raw
      << ",\"played_character_id\":" << t.played_character_id << ",\"activity_id\":" << Quote(kActivityId)
      << ",\"can_plan\":" << (t.can_plan ? (*t.can_plan ? "true" : "false") : "null")
      << ",\"reasons_available\":" << t.reasons_available << ",\"can_plan_reasons\":";
  if (t.can_plan_reasons) out << Quote(*t.can_plan_reasons); else out << "null";
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12003::religion::pilgrimage

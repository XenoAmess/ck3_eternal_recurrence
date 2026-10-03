#include "xar_bridge/ck3_12003_confession_decision_terms.hpp"

#include <array>
#include <cstring>
#include <sstream>
#include <utility>

namespace xar::ck3_12003::religion::confession {
namespace {
template <typename T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <typename T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
bool IsFixedDefinition(const void *definition) noexcept {
  const auto *key = static_cast<const std::byte *>(definition) + 0x18;
  const auto size = Load<std::size_t>(key, 0x10), capacity = Load<std::size_t>(key, 0x18);
  if (size != kDecisionId.size() || capacity < size) return false;
  const auto *text = capacity < 16 ? reinterpret_cast<const char *>(key) : Load<const char *>(key);
  return text && std::memcmp(text, kDecisionId.data(), size) == 0;
}
class CharacterScope {
public:
  CharacterScope(const Bindings &b, std::int32_t id) noexcept : bindings_(b) {
    b.root_construct(bytes_.data());
    Store<std::uint16_t>(bytes_.data(), 0, 4);
    Store<std::int64_t>(bytes_.data(), 8, id);
  }
  ~CharacterScope() { bindings_.root_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  CharacterScope(const CharacterScope &) = delete;
  CharacterScope &operator=(const CharacterScope &) = delete;
private:
  alignas(16) std::array<std::byte, 0x168> bytes_{};
  const Bindings &bindings_;
};
class FinalReason {
public:
  explicit FinalReason(const Bindings &b) noexcept : bindings_(b) {
    Store<std::size_t>(bytes_.data(), 0x18, 15);
  }
  ~FinalReason() { bindings_.reason_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &out) const {
    const auto size = Load<std::size_t>(bytes_.data(), 0x10);
    const auto capacity = Load<std::size_t>(bytes_.data(), 0x18);
    if (size > capacity) return false;
    const char *text = capacity < 16 ? reinterpret_cast<const char *>(bytes_.data()) : Load<const char *>(bytes_.data());
    if (size && !text) return false;
    if (size) out.assign(text, size); else out.clear();
    return true;
  }
  FinalReason(const FinalReason &) = delete;
  FinalReason &operator=(const FinalReason &) = delete;
private:
  alignas(8) std::array<std::byte, 0x20> bytes_{};
  const Bindings &bindings_;
};
std::string Quote(std::string_view value) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
std::string Bool(const std::optional<bool> &value) {
  return value ? (*value ? "true" : "false") : "null";
}
} // namespace

Bindings BindPlayerConfessionDecisionTermsImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  // v27 already closes these exact .3 methods, scope layout and native sink ABI.
  return mystical_communion::BindPlayerMysticalCommunionDecisionTermsImage12003(base, sha);
}

bool ReadPlayerConfessionDecisionTerms12003(const Bindings &b, void *character,
    std::int32_t id, std::int32_t date, std::uint64_t epoch, Terms &out) noexcept {
  out = {};
  out.capture_epoch = epoch; out.date_raw = date; out.played_character_id = id;
  if (!b.enabled || !b.decision_database || !b.decision_fallback || !b.decision_hash ||
      !b.decision_lookup || !b.root_construct || !b.root_destroy || !b.decision_shown ||
      !b.decision_can_take || !b.decision_cost || !b.cost_evaluate ||
      !b.cost_affordable || !b.reason_destroy) return false;
  if (!character || id <= 0 || Load<std::int32_t>(character, 0x18) != id) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  try {
    auto *database = *b.decision_database;
    if (!database) { out.unavailable_reason = "decision_database_unavailable"; return false; }
    const auto hash = b.decision_hash(database, kDecisionId.data(), static_cast<std::uint32_t>(kDecisionId.size()));
    const auto *definition = b.decision_lookup(database, hash);
    if (!definition || definition == *b.decision_fallback || !IsFixedDefinition(definition)) {
      out.unavailable_reason = "decision_definition_unavailable"; return false;
    }
    CharacterScope scope(b, id);
    const auto *cost = b.decision_cost(definition);
    if (!cost) { out.unavailable_reason = "decision_cost_unavailable"; return false; }
    std::array<std::int64_t, 10> resources{};
    // The production method returns void; only its out10 buffer carries costs.
    b.cost_evaluate(cost, scope.get(), resources.data());
    out.costs_raw = ResourceCost{resources[0], resources[6], resources[1], resources[2]};
    out.is_shown = b.decision_shown(definition, character);
    FinalReason reason(b);
    out.can_take = b.decision_can_take(definition, character, scope.get(), nullptr, reason.get());
    std::string text;
    out.reasons_available = reason.copy(text);
    if (out.reasons_available) out.can_take_reasons = std::move(text);
    out.affordable = b.cost_affordable(cost, scope.get(), character, nullptr);
    if (!out.reasons_available) {
      out.unavailable_reason = "decision_reasons_unavailable"; return false;
    }
    out.available = true; out.unavailable_reason.clear();
    return true;
  } catch (...) { out.unavailable_reason = "decision_native_copy_exception"; return false; }
}

std::string SerializePlayerConfessionDecisionTerms12003(const Terms &t) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":" << Quote(kSchema) << ",\"read_only\":true,\"available\":" << t.available
      << ",\"unavailable_reason\":" << (t.available ? "null" : Quote(t.unavailable_reason))
      << ",\"capture_epoch\":" << t.capture_epoch << ",\"date_raw\":" << t.date_raw
      << ",\"played_character_id\":" << t.played_character_id << ",\"decision_id\":" << Quote(kDecisionId)
      << ",\"is_shown\":" << Bool(t.is_shown) << ",\"can_take\":" << Bool(t.can_take)
      << ",\"affordable\":" << Bool(t.affordable) << ",\"costs_raw\":{\"gold\":";
  if (t.costs_raw) out << t.costs_raw->gold; else out << "null";
  out << ",\"treasury\":"; if (t.costs_raw) out << t.costs_raw->treasury; else out << "null";
  out << ",\"prestige\":"; if (t.costs_raw) out << t.costs_raw->prestige; else out << "null";
  out << ",\"piety\":"; if (t.costs_raw) out << t.costs_raw->piety; else out << "null";
  out << "},\"raw_scale\":100000,\"reasons_available\":" << t.reasons_available << ",\"can_take_reasons\":";
  if (t.can_take_reasons) out << Quote(*t.can_take_reasons); else out << "null";
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12003::religion::confession

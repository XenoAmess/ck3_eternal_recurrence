#include "xar_bridge/ck3_12003_repentance_petition_decision_terms.hpp"

#include <cstring>
#include <sstream>
#include <utility>

namespace xar::ck3_12003::religion::repentance_petition {
namespace {
template <typename T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <typename T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
bool KeyEquals(const void *definition, std::string_view expected) noexcept {
  const auto *key = static_cast<const std::byte *>(definition) + 0x18;
  const auto size = Load<std::size_t>(key, 0x10), capacity = Load<std::size_t>(key, 0x18);
  if (size != expected.size() || capacity < size) return false;
  const auto *text = capacity < 16 ? reinterpret_cast<const char *>(key) : Load<const char *>(key);
  return text && std::memcmp(text, expected.data(), size) == 0;
}
class CharacterRoot {
public:
  CharacterRoot(const Bindings &b, std::int32_t id) noexcept : b_(b) {
    b_.root_construct(bytes_.data());
    Store<std::uint16_t>(bytes_.data(), 0, 4);
    Store<std::int64_t>(bytes_.data(), 8, id);
  }
  ~CharacterRoot() { b_.root_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  CharacterRoot(const CharacterRoot &) = delete;
  CharacterRoot &operator=(const CharacterRoot &) = delete;
private:
  alignas(16) std::array<std::byte, 0x168> bytes_{};
  const Bindings &b_;
};
class NativeReason {
public:
  explicit NativeReason(const Bindings &b) noexcept : b_(b) {
    Store<std::size_t>(bytes_.data(), 0x18, 15);
  }
  ~NativeReason() { b_.reason_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &out) const {
    const auto size = Load<std::size_t>(bytes_.data(), 0x10);
    const auto capacity = Load<std::size_t>(bytes_.data(), 0x18);
    if (size > capacity) return false;
    const auto *text = capacity < 16 ? reinterpret_cast<const char *>(bytes_.data()) : Load<const char *>(bytes_.data());
    if (size && !text) return false;
    if (size) out.assign(text, size); else out.clear();
    return true;
  }
  NativeReason(const NativeReason &) = delete;
  NativeReason &operator=(const NativeReason &) = delete;
private:
  alignas(8) std::array<std::byte, 0x20> bytes_{};
  const Bindings &b_;
};
bool HasBindings(const Bindings &b) noexcept {
  return b.enabled && b.decision_database && b.decision_fallback && b.decision_hash &&
      b.decision_lookup && b.root_construct && b.root_destroy && b.decision_shown &&
      b.decision_can_take && b.decision_cost && b.cost_evaluate && b.cost_affordable &&
      b.reason_destroy;
}
bool ReadOne(const Bindings &b, void *character, std::int32_t id,
    std::string_view key, DecisionTerms &out) {
  auto *database = *b.decision_database;
  if (!database) { out.unavailable_reason = "decision_database_unavailable"; return false; }
  const auto hash = b.decision_hash(database, key.data(), static_cast<std::uint32_t>(key.size()));
  const auto *definition = b.decision_lookup(database, hash);
  if (!definition || definition == *b.decision_fallback || !KeyEquals(definition, key)) {
    out.unavailable_reason = "decision_definition_unavailable"; return false;
  }
  CharacterRoot scope(b, id);
  const auto *cost = b.decision_cost(definition);
  if (!cost) { out.unavailable_reason = "decision_cost_unavailable"; return false; }
  std::array<std::int64_t, 10> resources{};
  b.cost_evaluate(cost, scope.get(), resources.data());
  out.costs_raw = resources;
  out.is_shown = b.decision_shown(definition, character);
  NativeReason reason(b);
  out.can_take = b.decision_can_take(definition, character, scope.get(), nullptr, reason.get());
  std::string owned;
  out.reasons_available = reason.copy(owned);
  if (out.reasons_available) out.can_take_reasons = std::move(owned);
  out.affordable = b.cost_affordable(cost, scope.get(), character, nullptr);
  if (!out.reasons_available) {
    out.unavailable_reason = "decision_reasons_unavailable"; return false;
  }
  out.available = true; out.unavailable_reason.clear();
  return true;
}
bool ReadGuarded(const Bindings &b, void *character, std::int32_t id,
    std::string_view key, DecisionTerms &out) noexcept {
  try { return ReadOne(b, character, id, key, out); }
  catch (...) { out.unavailable_reason = "decision_native_copy_exception"; return false; }
}
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
void Row(std::ostream &out, std::string_view key, const DecisionTerms &t) {
  out << "{\"decision_id\":" << Quote(key) << ",\"available\":" << t.available
      << ",\"unavailable_reason\":" << (t.available ? "null" : Quote(t.unavailable_reason))
      << ",\"is_shown\":" << Bool(t.is_shown) << ",\"can_take\":" << Bool(t.can_take)
      << ",\"affordable\":" << Bool(t.affordable)
      << ",\"quote_context\":\"unselected_player_root\",\"repentance_option_quote_ready\":false,\"costs_raw\":";
  if (!t.costs_raw) out << "null";
  else {
    out << '[';
    for (std::size_t i = 0; i < t.costs_raw->size(); ++i) {
      if (i) out << ',';
      out << (*t.costs_raw)[i];
    }
    out << ']';
  }
  out << ",\"reasons_available\":" << t.reasons_available << ",\"can_take_reasons\":";
  if (t.can_take_reasons) out << Quote(*t.can_take_reasons); else out << "null";
  out << '}';
}
} // namespace

Bindings BindPlayerRepentancePetitionDecisionTermsImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  return mystical_communion::BindPlayerMysticalCommunionDecisionTermsImage12003(base, sha);
}

bool ReadPlayerRepentancePetitionDecisionTerms12003(const Bindings &b, void *character,
    std::int32_t id, std::int32_t date, std::uint64_t epoch, Terms &out) noexcept {
  out = {};
  out.capture_epoch = epoch; out.date_raw = date; out.played_character_id = id;
  if (!HasBindings(b)) return false;
  if (!character || id <= 0 || Load<std::int32_t>(character, 0x18) != id) {
    out.unavailable_reason = "played_character_unavailable";
    out.head_of_faith.unavailable_reason = out.antipope.unavailable_reason = out.unavailable_reason;
    return false;
  }
  const bool head = ReadGuarded(b, character, id, kHeadOfFaithDecisionId, out.head_of_faith);
  const bool challenger = ReadGuarded(b, character, id, kAntipopeDecisionId, out.antipope);
  out.available = head && challenger;
  out.unavailable_reason = out.available ? "" : "one_or_more_decisions_unavailable";
  return out.available;
}

std::string SerializePlayerRepentancePetitionDecisionTerms12003(const Terms &t) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":" << Quote(kSchema) << ",\"read_only\":true,\"available\":" << t.available
      << ",\"unavailable_reason\":" << (t.available ? "null" : Quote(t.unavailable_reason))
      << ",\"capture_epoch\":" << t.capture_epoch << ",\"date_raw\":" << t.date_raw
      << ",\"played_character_id\":" << t.played_character_id
      << ",\"selection_context\":\"unselected_player_root\",\"raw_scale\":" << Terms::raw_scale
      << ",\"resource_order\":[\"gold\",\"prestige\",\"piety\",\"renown\",\"influence\",\"herd\","
         "\"treasury\",\"treasury_or_gold\",\"merit\",\"barter_goods\"],\"head_of_faith\":";
  Row(out, kHeadOfFaithDecisionId, t.head_of_faith);
  out << ",\"antipope\":"; Row(out, kAntipopeDecisionId, t.antipope);
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12003::religion::repentance_petition

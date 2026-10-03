#include "xar_bridge/ck3_12003_vow_of_poverty_terms.hpp"

#include <array>
#include <cstring>
#include <sstream>
#include <utility>

namespace xar::ck3_12003::religion::vow_of_poverty_terms12003 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof(result));
  return result;
}
template <typename T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
bool KeyEquals(const void *definition) noexcept {
  const auto *key = static_cast<const std::byte *>(definition) + 0x18;
  const auto size = Load<std::size_t>(key, 0x10);
  const auto capacity = Load<std::size_t>(key, 0x18);
  if (size != kDecisionId.size() || capacity < size) return false;
  const auto *text = capacity < 16 ? reinterpret_cast<const char *>(key) : Load<const char *>(key);
  return text != nullptr && std::memcmp(text, kDecisionId.data(), size) == 0;
}
class RootScope {
public:
  RootScope(const Bindings &b, std::int32_t id) noexcept : b_(b) {
    b_.root_construct(bytes_.data());
    Store<std::uint16_t>(bytes_.data(), 0, 4);
    Store<std::int64_t>(bytes_.data(), 8, id);
  }
  ~RootScope() { b_.root_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  RootScope(const RootScope &) = delete;
  RootScope &operator=(const RootScope &) = delete;
private:
  alignas(16) std::array<std::byte, 0x168> bytes_{};
  const Bindings &b_;
};
class NativeReason {
public:
  explicit NativeReason(const Bindings &b) noexcept : b_(b) {
    // Reproduce native 0x856050's canonical empty UTF-8 small-string state:
    // data[0]=0, size=0, capacity15. Native appends own later heap data.
    Store<std::size_t>(bytes_.data(), 0x18, 15);
  }
  ~NativeReason() { b_.reason_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &out) const {
    const auto size = Load<std::size_t>(bytes_.data(), 0x10);
    const auto capacity = Load<std::size_t>(bytes_.data(), 0x18);
    if (size > capacity) return false;
    const char *text = capacity < 16 ? reinterpret_cast<const char *>(bytes_.data()) : Load<const char *>(bytes_.data());
    if (size != 0 && text == nullptr) return false;
    if (size == 0) out.clear();
    else out.assign(text, size);
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
std::string Bool(const std::optional<bool> &value) {
  return value.has_value() ? *value ? "true" : "false" : "null";
}
} // namespace

Bindings BindVowOfPovertyTermsImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.decision_database = reinterpret_cast<void **>(base + 0x5D1DEF0);
  b.decision_fallback = reinterpret_cast<const void **>(base + 0x5D1F7E8);
  b.decision_hash = reinterpret_cast<DecisionHash>(base + 0x3F7E240);
  b.decision_lookup = reinterpret_cast<DecisionLookup>(base + 0xCAA8D0);
  b.root_construct = reinterpret_cast<RootConstruct>(base + 0x889F60);
  b.root_destroy = reinterpret_cast<RootDestroy>(base + 0x87E0E0);
  b.decision_shown = reinterpret_cast<DecisionShown>(base + 0x3103400);
  b.decision_can_take = reinterpret_cast<DecisionCanTake>(base + 0x3103510);
  b.decision_cost = reinterpret_cast<DecisionCost>(base + 0x14706D0);
  b.cost_evaluate = reinterpret_cast<CostEvaluate>(base + 0x310CE70);
  b.cost_affordable = reinterpret_cast<CostAffordable>(base + 0x310B3B0);
  b.reason_destroy = reinterpret_cast<ReasonDestroy>(base + 0x856050);
  return b;
}

bool ReadVowOfPovertyTerms12003(const Bindings &b, void *character,
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
    if (!definition || definition == *b.decision_fallback || !KeyEquals(definition)) {
      out.unavailable_reason = "decision_definition_unavailable"; return false;
    }
    RootScope scope(b, id);
    const auto *cost = b.decision_cost(definition);
    if (!cost) { out.unavailable_reason = "decision_cost_unavailable"; return false; }
    std::array<std::int64_t, 10> resources{};
    b.cost_evaluate(cost, scope.get(), resources.data());
    out.costs_raw = ResourceCost{resources[0], resources[6], resources[1], resources[2]};
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
  } catch (...) { out.unavailable_reason = "decision_native_copy_exception"; return false; }
}

std::string SerializeVowOfPovertyTerms12003(const Terms &t) {
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

} // namespace xar::ck3_12003::religion::vow_of_poverty_terms12003

#include "xar_bridge/ck3_12003_holy_order_selected_title_terms.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"

#include <cstddef>
#include <cstring>
#include <sstream>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::holy_order::selected_title_terms {
namespace {
template <typename T> bool Read(const void *object, std::size_t offset, T &value) noexcept {
  if (object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename Fn, typename Result, typename... Args>
bool Call(Fn fn, Result &result, Args... args) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename Fn, typename... Args>
bool CallVoid(Fn fn, Args... args) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool KeyEquals(const void *definition, std::string_view key) {
  std::size_t size = 0, capacity = 0;
  const auto *native = static_cast<const std::byte *>(definition) + 0x18;
  if (!Read(native, 0x10, size) || !Read(native, 0x18, capacity) ||
      size != key.size() || capacity < size) return false;
  const char *text = reinterpret_cast<const char *>(native);
  if (capacity >= 16 && !Read(native, 0, text)) return false;
  if (text == nullptr) return false;
  for (std::size_t i = 0; i < size; ++i) {
    char actual = 0;
    if (!Read(text, i, actual) || actual != key[i]) return false;
  }
  return true;
}
class NativeReason {
 public:
  explicit NativeReason(mystical_communion::ReasonDestroy destroy) noexcept : destroy_(destroy) {
    const std::size_t capacity = 15;
    std::memcpy(bytes_.data() + 0x18, &capacity, sizeof(capacity));
  }
  ~NativeReason() { (void)CallVoid(destroy_, static_cast<void *>(bytes_.data())); }
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &out) const {
    std::size_t size = 0, capacity = 0;
    if (!Read(bytes_.data(), 0x10, size) || !Read(bytes_.data(), 0x18, capacity) || size > capacity)
      return false;
    const char *text = reinterpret_cast<const char *>(bytes_.data());
    if (capacity >= 16 && !Read(bytes_.data(), 0, text)) return false;
    if (size != 0 && text == nullptr) return false;
    out.clear();
    for (std::size_t i = 0; i < size; ++i) {
      char value = 0;
      if (!Read(text, i, value)) return false;
      out.push_back(value);
    }
    return true;
  }
 private:
  alignas(8) std::array<std::byte, 0x20> bytes_{};
  mystical_communion::ReasonDestroy destroy_ = nullptr;
};

void ReadTitleTerms(const Bindings &b, const void *definition, const void *cost,
    const selected_candidates::Widget &widget, void *player,
    selected_parameters::NativeSelectedTitleParameters &parameters, TitleTerms &out) {
  out.unavailable_reason = "selected_title_evaluation_unavailable";
  if (!parameters.SelectTitle(widget.selected_name_key, out.title_id) ||
      !parameters.ExportPlayerScope()) {
    out.unavailable_reason = parameters.failure(); return;
  }
  bool title_valid = false;
  if (selected_candidates::ReadSelectedTitleValid12003(
      b.candidates, widget, parameters.parameters(), title_valid)) out.title_valid = title_valid;
  NativeReason take_reason(b.decision.reason_destroy), afford_reason(b.decision.reason_destroy);
  bool can_take = false;
  if (Call(b.decision.decision_can_take, can_take, definition, player,
      parameters.evaluation_scope(), static_cast<const void *>(parameters.parameters()), take_reason.get())) {
    out.can_take = can_take;
    std::string literal;
    out.can_take_reasons_available = take_reason.copy(literal);
    if (out.can_take_reasons_available) out.can_take_reason_literal = std::move(literal);
  }
  std::array<std::int64_t, 10> costs{};
  if (CallVoid(b.decision.cost_evaluate, cost, parameters.evaluation_scope(), costs.data())) {
    out.resource_costs_raw = costs;
    bool affordable = false;
    if (Call(b.decision.cost_affordable, affordable, cost, parameters.evaluation_scope(),
        player, afford_reason.get())) {
      out.can_afford = affordable;
      std::string literal;
      out.can_afford_reasons_available = afford_reason.copy(literal);
      if (out.can_afford_reasons_available) out.can_afford_reason_literal = std::move(literal);
    }
  }
  out.available = out.title_valid.has_value() && out.can_take.has_value() &&
      out.can_afford.has_value() && out.resource_costs_raw.has_value() &&
      out.can_take_reasons_available && out.can_afford_reasons_available;
  if (out.available) out.unavailable_reason.clear();
}

void ReadDecision(const Bindings &b, void *database, const void *fallback,
    void *player, std::uint32_t actor, std::size_t index, DecisionTerms &out) {
  out.decision_id = kDecisionIds[index];
  out.selected_scope_name = index == 2 ? "title" : "barony";
  out.unavailable_reason = "decision_definition_unavailable";
  std::uint32_t hash = 0;
  const void *definition = nullptr;
  const auto key = kDecisionIds[index];
  if (!Call(b.decision.decision_hash, hash, database, key.data(),
      static_cast<std::uint32_t>(key.size())) ||
      !Call(b.decision.decision_lookup, definition, database, hash) ||
      definition == nullptr || definition == fallback || !KeyEquals(definition, key)) return;
  bool shown = false;
  if (Call(b.decision.decision_shown, shown, definition, player)) out.is_shown = shown;
  selected_candidates::Widget widget{};
  if (!selected_candidates::GetHolyOrderDecisionWidget12003(b.candidates, definition, widget)) {
    out.unavailable_reason = "decision_widget_unavailable"; return;
  }
  out.selected_title_tier = widget.expected_tier;
  selected_parameters::NativeSelectedTitleParameters parameters(b.parameters, actor);
  if (!parameters.available()) { out.unavailable_reason = parameters.failure(); return; }
  std::vector<std::uint32_t> candidates;
  if (!selected_candidates::CollectHolyOrderTitleCandidates12003(
      b.candidates, widget, player, parameters.parameters(), candidates)) {
    out.unavailable_reason = "decision_title_candidates_unavailable"; return;
  }
  out.candidates_available = true;
  const void *cost = nullptr;
  if (!Call(b.decision.decision_cost, cost, definition) || cost == nullptr) {
    out.unavailable_reason = "decision_cost_unavailable"; return;
  }
  bool titles_available = true;
  for (const auto id : candidates) {
    TitleTerms terms{};
    terms.title_id = id;
    ReadTitleTerms(b, definition, cost, widget, player, parameters, terms);
    titles_available = titles_available && terms.available;
    out.candidates.push_back(std::move(terms));
  }
  out.available = out.is_shown.has_value() && titles_available;
  if (out.available) out.unavailable_reason.clear();
  else out.unavailable_reason = "decision_selected_terms_unavailable";
}
void Quote(std::ostream &out, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char value : text) {
    if (value == '"' || value == '\\') out << '\\' << static_cast<char>(value);
    else if (value < 0x20) out << "\\u00" << hex[value >> 4] << hex[value & 15];
    else out << static_cast<char>(value);
  }
  out << '"';
}
template <typename T> void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value; else out << "null";
}
void Optional(std::ostream &out, const std::optional<std::string> &value) {
  if (value) Quote(out, *value); else out << "null";
}
void TitleJson(std::ostream &out, const TitleTerms &t) {
  out << "{\"title_id\":" << t.title_id << ",\"available\":" << t.available
      << ",\"unavailable_reason\":";
  if (t.available) out << "null"; else Quote(out, t.unavailable_reason);
  out << ",\"title_valid\":"; Optional(out, t.title_valid);
  out << ",\"can_take\":"; Optional(out, t.can_take);
  out << ",\"can_afford\":"; Optional(out, t.can_afford);
  out << ",\"resource_costs_raw\":";
  if (t.resource_costs_raw) {
    out << '[';
    for (std::size_t i = 0; i < t.resource_costs_raw->size(); ++i) {
      if (i != 0) out << ',';
      out << (*t.resource_costs_raw)[i];
    }
    out << ']';
  } else out << "null";
  out << ",\"resource_scale\":" << kRawScale
      << ",\"can_take_reasons_available\":" << t.can_take_reasons_available
      << ",\"can_take_reason_literal\":"; Optional(out, t.can_take_reason_literal);
  out << ",\"can_afford_reasons_available\":" << t.can_afford_reasons_available
      << ",\"can_afford_reason_literal\":"; Optional(out, t.can_afford_reason_literal);
  out << '}';
}
} // namespace

Bindings BindHolyOrderSelectedTitleTermsImage12003(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != holy_order::kExecutableSha256) return b;
  b.decision = mystical_communion::BindPlayerMysticalCommunionDecisionTermsImage12003(base, sha);
  b.parameters = selected_parameters::BindSelectedTitleParametersImage12003(base, sha);
  b.candidates = selected_candidates::BindHolyOrderSelectedCandidatesImage12003(base, sha);
  b.enabled = b.decision.enabled && b.parameters.enabled && b.candidates.available;
  return b;
}

bool ReadHolyOrderSelectedTitleTerms12003(const Bindings &b, void *player,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch, Context &out) noexcept {
  out = {};
  out.played_character_id = actor; out.date_raw = date; out.capture_epoch = epoch;
  const auto &d = b.decision;
  if (!b.enabled || !d.enabled || !b.parameters.enabled || !b.candidates.available ||
      d.decision_database == nullptr || d.decision_fallback == nullptr ||
      d.decision_hash == nullptr || d.decision_lookup == nullptr ||
      d.decision_shown == nullptr || d.decision_can_take == nullptr ||
      d.decision_cost == nullptr || d.cost_evaluate == nullptr ||
      d.cost_affordable == nullptr || d.reason_destroy == nullptr) return false;
  std::int32_t actual = -1;
  if (!Read(player, 0x18, actual) || actual != actor || actor <= 0) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  void *database = nullptr;
  const void *fallback = nullptr;
  if (!Read(d.decision_database, 0, database) || database == nullptr ||
      !Read(d.decision_fallback, 0, fallback)) {
    out.unavailable_reason = "decision_database_unavailable"; return false;
  }
  try {
    bool complete = true;
    for (std::size_t i = 0; i < kDecisionIds.size(); ++i) {
      DecisionTerms terms{};
      ReadDecision(b, database, fallback, player, static_cast<std::uint32_t>(actor), i, terms);
      complete = complete && terms.available;
      out.decisions.push_back(std::move(terms));
    }
    out.available = complete;
    out.unavailable_reason = complete ? "" : "selected_decision_terms_unavailable";
    return complete;
  } catch (...) {
    out.unavailable_reason = "selected_decision_native_copy_exception"; return false;
  }
}

std::string SerializeHolyOrderSelectedTitleTerms12003(const Context &c) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":"; Quote(out, kSchema);
  out << ",\"read_only\":true,\"game_version\":\"1.20.0.3\",\"executable_sha256\":";
  Quote(out, holy_order::kExecutableSha256);
  out << ",\"available\":" << c.available << ",\"unavailable_reason\":";
  if (c.available) out << "null"; else Quote(out, c.unavailable_reason);
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"date_raw\":" << c.date_raw
      << ",\"played_character_id\":" << c.played_character_id
      << ",\"raw_scale\":" << kRawScale << ",\"decisions\":[";
  for (std::size_t i = 0; i < c.decisions.size(); ++i) {
    if (i != 0) out << ',';
    const auto &d = c.decisions[i];
    out << "{\"decision_id\":"; Quote(out, d.decision_id);
    out << ",\"selected_scope_name\":"; Quote(out, d.selected_scope_name);
    out << ",\"selected_title_tier\":" << d.selected_title_tier << ",\"available\":" << d.available
        << ",\"unavailable_reason\":";
    if (d.available) out << "null"; else Quote(out, d.unavailable_reason);
    out << ",\"is_shown\":"; Optional(out, d.is_shown);
    out << ",\"candidates_available\":" << d.candidates_available << ",\"candidates\":[";
    for (std::size_t j = 0; j < d.candidates.size(); ++j) {
      if (j != 0) out << ',';
      TitleJson(out, d.candidates[j]);
    }
    out << "]}";
  }
  out << "]}";
  return out.str();
}
} // namespace xar::ck3_12003::religion::holy_order::selected_title_terms

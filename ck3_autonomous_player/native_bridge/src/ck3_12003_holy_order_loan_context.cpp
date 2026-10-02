#include "xar_bridge/ck3_12003_holy_order_loan_context.hpp"
#include "xar_bridge/ck3_12003_holy_order_loan_amount.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <sstream>

namespace xar::ck3_12003::religion::loan {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset,
              sizeof(result));
  return result;
}
template <typename T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
bool KeyEquals(const void *object, std::string_view expected) noexcept {
  if (!object) return false;
  const auto *key = static_cast<const std::byte *>(object) + 0x18;
  auto size = Load<std::size_t>(key, 0x10);
  auto capacity = Load<std::size_t>(key, 0x18);
  if (size != expected.size() || capacity < size) return false;
  const char *data = capacity < 16 ? reinterpret_cast<const char *>(key)
                                  : Load<const char *>(key, 0);
  return data && std::memcmp(data, expected.data(), size) == 0;
}
const void *FindDecision(const Bindings &b, std::string_view key) noexcept {
  auto *database = *b.decision_database;
  if (!database) return nullptr;
  auto hash = b.decision_hash(database, key.data(), static_cast<std::uint32_t>(key.size()));
  const void *decision = b.decision_lookup(database, hash);
  return decision && decision != *b.decision_fallback && KeyEquals(decision, key)
             ? decision : nullptr;
}

class RootScope {
 public:
  explicit RootScope(const Bindings &b, std::int32_t character_id) noexcept : b_(b) {
    b_.root_construct(storage_.data());
    Store<std::uint16_t>(storage_.data(), 0, 4);
    Store<std::int64_t>(storage_.data(), 8, character_id);
  }
  ~RootScope() { b_.root_destroy(storage_.data()); }
  RootScope(const RootScope &) = delete;
  RootScope &operator=(const RootScope &) = delete;
  void *get() noexcept { return storage_.data(); }
 private:
  alignas(16) std::array<std::byte, 0x168> storage_{};
  const Bindings &b_;
};

bool ReadVariable(const Bindings &b, std::int32_t character_id, std::string_view key,
                  std::uint16_t expected_kind, bool &present,
                  std::optional<std::int64_t> &payload) noexcept {
  present = false;
  payload.reset();
  std::int32_t variable_id = -1;
  if (!ck3_12002::ResolvePhaseVariableIdentifier(b.variable_identifiers, key, variable_id))
    return false;
  ck3_12002::PhaseVariableTarget target{4, {}, character_id};
  auto *context = b.variable_identifiers.variable_context(&target);
  if (!context) return false;
  const void *rows = Load<const void *>(context, 0x10);
  auto count = Load<std::int32_t>(context, 0x1C);
  if (count < 0 || count > 65'536 || (count && !rows)) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *row = static_cast<const std::byte *>(rows) + static_cast<std::size_t>(i) * 0x20;
    if (Load<std::int32_t>(row, 8) != variable_id) continue;
    if (Load<std::uint16_t>(row, 0x10) != expected_kind) return false;
    present = true;
    payload = Load<std::int64_t>(row, 0x18);
    return true;
  }
  return true;
}
void *ResolveHolder(const Bindings &b, std::int32_t id) noexcept {
  if (!b.character_store || !*b.character_store) return nullptr;
  auto *store = *b.character_store;
  auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  auto capacity = Load<std::int32_t>(store, 0x2C);
  auto *slots = Load<const void *>(store, 0x20);
  if (capacity < 0 || index >= static_cast<std::uint32_t>(capacity) || !slots) return nullptr;
  auto *character = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  if (!character || (b.character_fallback && character == *b.character_fallback) ||
      Load<std::int32_t>(character, 0x18) != id) return nullptr;
  return character;
}
bool ReadDecision(const Bindings &b, void *character, void *scope,
                  Decision &output) noexcept {
  auto *definition = FindDecision(b, output.decision_id);
  if (!definition) return false;
  auto *cost = b.decision_cost(definition);
  if (!cost) return false;
  std::array<std::int64_t, 10> resources{};
  b.cost_evaluate(cost, scope, resources.data());
  output.is_shown = b.decision_shown(definition, character);
  output.can_take = b.decision_can_take(definition, character, scope, nullptr, nullptr);
  output.affordable = b.cost_affordable(cost, scope, character, nullptr);
  output.costs_raw = {resources[0], resources[6], resources[1], resources[2]};
  return true;
}

// The plain fixed-point registry already owns the compiled stock expression.
bool ReadAmountRaw(std::uintptr_t base, void *scope, std::int64_t &raw) noexcept {
  constexpr std::string_view key = "holy_order_gold_value";
  auto *entry = xar::holy_order_amount_recipe::FindFixedPointScriptValue(base, key);
  return entry && xar::holy_order_amount_recipe::EvaluateFixedPointScriptValue(
                      base, entry, scope, raw);
}

template <typename T> void Optional(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void DecisionJson(std::ostringstream &out, const Decision &d) {
  out << "{\"decision_id\":\"" << d.decision_id << "\",\"is_shown\":" << d.is_shown
      << ",\"can_take\":" << d.can_take << ",\"affordable\":" << d.affordable
      << ",\"costs_raw\":{\"gold\":" << d.costs_raw.gold
      << ",\"treasury\":" << d.costs_raw.treasury
      << ",\"prestige\":" << d.costs_raw.prestige
      << ",\"piety\":" << d.costs_raw.piety << "}}";
}
} // namespace

Bindings BindHolyOrderLoanImage12003(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.module_base = base;
  // The existing reviewed .2 helper is an internal ABI identity. Actual .3
  // identity is admitted above; the reused identifier RVAs are closed by proof.
  b.variable_identifiers = ck3_12002::BindPhaseDefinitionsImage(base, ck3_12002::kExecutableSha256);
  b.character_store = reinterpret_cast<void **>(base + 0x5C67568);
  b.character_fallback = reinterpret_cast<void **>(base + 0x5C67570);
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
  b.amount_evaluate = &ReadAmountRaw;
  return b;
}

bool ReadHolyOrderLoanContext12003(const Bindings &b, void *character,
                                  std::int32_t character_id, std::int32_t date,
                                  std::uint64_t epoch, Context &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.date_raw = date;
  out.played_character_id = character_id;
  if (!b.enabled || !b.variable_identifiers.enabled || !b.variable_identifiers.variable_context ||
      !b.decision_database || !b.decision_fallback || !b.decision_hash || !b.decision_lookup ||
      !b.root_construct || !b.root_destroy || !b.decision_shown || !b.decision_can_take ||
      !b.decision_cost || !b.cost_evaluate || !b.cost_affordable || !b.amount_evaluate) return false;
  if (!character || Load<std::int32_t>(character, 0x18) != character_id) {
    out.unavailable_reason = "played_character_unavailable";
    return false;
  }
  if (!ReadVariable(b, character_id, "loan_amount_owed", 1,
                    out.loan_amount_owed_present, out.loan_amount_owed_raw) ||
      !ReadVariable(b, character_id, "years_since_loan", 1,
                    out.borrower_years_present, out.borrower_years_raw)) {
    out.unavailable_reason = "borrower_variables_unavailable";
    return false;
  }
  std::optional<std::int64_t> holder;
  if (!ReadVariable(b, character_id, "loan_holder", 4, out.loan_holder_present, holder)) {
    out.unavailable_reason = "loan_holder_unavailable";
    return false;
  }
  if (holder) {
    if (*holder <= 0 || *holder > std::numeric_limits<std::int32_t>::max()) {
      out.unavailable_reason = "loan_holder_unavailable";
      return false;
    }
    out.loan_holder_character_id = static_cast<std::int32_t>(*holder);
    out.loan_holder_resolved = ResolveHolder(b, *out.loan_holder_character_id) != nullptr;
    if (out.loan_holder_resolved &&
        !ReadVariable(b, *out.loan_holder_character_id, "years_since_loan", 1,
                      out.lender_years_present, out.lender_years_raw)) {
      out.unavailable_reason = "lender_years_unavailable";
      return false;
    }
  }
  RootScope scope(b, character_id);
  std::int64_t amount = 0;
  if (!b.amount_evaluate(b.module_base, scope.get(), amount)) {
    out.unavailable_reason = "loan_amount_expression_unavailable";
    return false;
  }
  out.loan_amount_quote_raw = amount;
  if (!ReadDecision(b, character, scope.get(), out.borrow_decision) ||
      !ReadDecision(b, character, scope.get(), out.repay_decision)) {
    out.unavailable_reason = "decision_evaluation_unavailable";
    return false;
  }
  out.available = true;
  out.unavailable_reason.clear();
  return true;
}

std::string SerializeHolyOrderLoanContext12003(const Context &c) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":\"" << kSchema << "\",\"game_version\":\"1.20.0.3\","
      << "\"executable_sha256\":\"" << kExecutableSha256 << "\",\"available\":" << c.available
      << ",\"unavailable_reason\":";
  if (c.available) out << "null";
  else out << '\"' << c.unavailable_reason << '\"';
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"date_raw\":" << c.date_raw
      << ",\"played_character_id\":" << c.played_character_id << ",\"raw_scale\":" << c.raw_scale
      << ",\"loan_amount_quote_raw\":"; Optional(out, c.loan_amount_quote_raw);
  out << ",\"loan_amount_owed_present\":" << c.loan_amount_owed_present
      << ",\"loan_amount_owed_raw\":"; Optional(out, c.loan_amount_owed_raw);
  out << ",\"loan_holder_present\":" << c.loan_holder_present
      << ",\"loan_holder_character_id\":"; Optional(out, c.loan_holder_character_id);
  out << ",\"loan_holder_resolved\":" << c.loan_holder_resolved
      << ",\"borrower_years_present\":" << c.borrower_years_present
      << ",\"borrower_years_raw\":"; Optional(out, c.borrower_years_raw);
  out << ",\"lender_years_present\":" << c.lender_years_present
      << ",\"lender_years_raw\":"; Optional(out, c.lender_years_raw);
  out << ",\"borrow_decision\":"; DecisionJson(out, c.borrow_decision);
  out << ",\"repay_decision\":"; DecisionJson(out, c.repay_decision);
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12003::religion::loan

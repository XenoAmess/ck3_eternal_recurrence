#include "holy_order_loan_decision_costs_12004.hpp"
#include "xar_bridge/ck3_12004_religion_context_addons.hpp"

#include <cstring>
#include <sstream>

namespace xar::ck3_12004::religion::loan_decision_costs {
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

// Identity checks are the exact .4 Decision RTTI/key checks already used by
// ck3_12004_holy_site_decision_cooldown.cpp, rather than a hash-only match.
bool ExactDefinition(std::uintptr_t base, const void *definition,
                     std::string_view key) noexcept {
  if (!definition) return false;
  const auto vt = Load<std::uintptr_t>(definition, 0);
  if (vt != base + 0x48BD150) return false;
  const auto col = Load<std::uintptr_t>(reinterpret_cast<const void *>(vt - 8), 0);
  if (!col) return false;
  const auto *rtti = reinterpret_cast<const void *>(col);
  if (Load<std::uint32_t>(rtti, 0) != 1 ||
      Load<std::uint32_t>(rtti, 12) != 0x5586B90 ||
      col != base + Load<std::uint32_t>(rtti, 20) ||
      Load<std::uint32_t>(definition, 0x38) != 0x4744624FU) return false;
  const auto *text = static_cast<const std::byte *>(definition) + 0x18;
  const auto size = Load<std::size_t>(text, 16);
  const auto capacity = Load<std::size_t>(text, 24);
  if (size != key.size() || size > capacity ||
      (capacity < 16 && capacity != 15)) return false;
  const char *bytes = capacity < 16 ? reinterpret_cast<const char *>(text)
                                  : Load<const char *>(text, 0);
  return bytes && std::memcmp(bytes, key.data(), size) == 0 && bytes[size] == 0;
}

struct Resolution {
  void *database = nullptr;
  const void *fallback = nullptr, *definition = nullptr;
  bool operator==(const Resolution &) const = default;
};
bool Resolve(const Bindings &b, std::string_view key, Resolution &out) noexcept {
  const auto &d = b.decisions;
  out.database = *d.decision_database;
  out.fallback = *d.decision_fallback;
  if (!out.database) return false;
  const auto hash = d.decision_hash(out.database, key.data(),
      static_cast<std::uint32_t>(key.size()));
  out.definition = d.decision_lookup(out.database, hash);
  return out.definition && out.definition != out.fallback &&
      ExactDefinition(b.image_base, out.definition, key) &&
      out.database == *d.decision_database &&
      out.fallback == *d.decision_fallback;
}

class RootScope {
 public:
  RootScope(const DecisionBindings &b, std::int32_t id) noexcept : b_(b) {
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
  const DecisionBindings &b_;
};

bool ReadDecision(const Bindings &b, void *character, void *scope,
                  DecisionCosts &out) noexcept {
  Resolution before{}, after{};
  if (!Resolve(b, out.decision_id, before)) return false;
  const auto &d = b.decisions;
  const auto *cost = d.decision_cost(before.definition);
  if (!cost) return false;
  std::array<std::int64_t, kResourceSlotCount> costs{};
  d.cost_evaluate(cost, scope, costs.data());
  const bool shown = d.decision_shown(before.definition, character);
  const bool can_take = d.decision_can_take(before.definition, character,
      scope, nullptr, nullptr);
  const bool affordable = d.cost_affordable(cost, scope, character, nullptr);
  if (!Resolve(b, out.decision_id, after) || before != after) return false;
  out.is_shown = shown;
  out.can_take = can_take;
  out.affordable = affordable;
  out.costs_raw_by_native_index = costs;
  return true;
}

bool PausedPlayer(const Bindings &b, CoreSnapshotPrefix &frame) noexcept {
  return ck3_12004::ReadCoreSnapshot(b.core, frame) && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.clock.paused && frame.played_character_id > 0 &&
      ck3_12004::ResolveCoreCharacter(b.core, frame.played_character_id);
}

std::string Quote(std::string_view text) {
  std::string result = "\"";
  for (const unsigned char c : text) {
    if (c == '"' || c == '\\') result += '\\';
    result += static_cast<char>(c);
  }
  return result + '"';
}
void DecisionJson(std::ostringstream &json, const DecisionCosts &d, bool available) {
  const auto flag = [&](const std::optional<bool> &v) {
    if (available && v) json << (*v ? "true" : "false");
    else json << "null";
  };
  json << "{\"decision_id\":" << Quote(d.decision_id) << ",\"is_shown\":";
  flag(d.is_shown); json << ",\"can_take\":"; flag(d.can_take);
  json << ",\"affordable\":"; flag(d.affordable);
  json << ",\"costs_raw_by_native_index\":";
  if (!available || !d.costs_raw_by_native_index) json << "null";
  else {
    json << '[';
    for (std::size_t i = 0; i < kResourceSlotCount; ++i) {
      if (i) json << ',';
      json << (*d.costs_raw_by_native_index)[i];
    }
    json << ']';
  }
  json << '}';
}
} // namespace

Bindings BindHolyOrderLoanDecisionCostsImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != ck3_12004::kExecutableSha256) return b;
  b.image_base = base;
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.decisions = BindReligionContextAddonsImage12004(base, sha).mystical_communion_bindings;
  b.enabled = b.core.enabled && b.decisions.enabled;
  return b;
}

namespace {
bool ReadPlayerCostsImpl(
    const Bindings &b, std::uint64_t epoch, Observation &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  const auto fail = [&](const char *reason) {
    // Discard partial successful reads. Unknown is never emitted as false/zero.
    out.borrow = DecisionCosts{"borrow_from_holy_order_decision"};
    out.repay = DecisionCosts{"repay_loan_decision"};
    out.unavailable_reason = reason;
    return false;
  };
  const auto &d = b.decisions;
  if (!b.enabled || !b.image_base || !epoch || !b.core.enabled || !d.enabled ||
      !d.decision_database || !d.decision_fallback || !d.decision_hash ||
      !d.decision_lookup || !d.root_construct || !d.root_destroy ||
      !d.decision_shown || !d.decision_can_take || !d.decision_cost ||
      !d.cost_evaluate || !d.cost_affordable) return fail("bindings_or_epoch_unavailable");
  try {
    CoreSnapshotPrefix before{}, after{};
    if (!PausedPlayer(b, before)) return fail("paused_player_unavailable");
    out.date_raw = before.clock.date_raw;
    out.played_character_id = before.played_character_id;
    auto *character = ck3_12004::ResolveCoreCharacter(b.core, before.played_character_id);
    RootScope scope(d, before.played_character_id);
    if (!ReadDecision(b, character, scope.get(), out.borrow) ||
        !ReadDecision(b, character, scope.get(), out.repay))
      return fail("loan_decision_definition_or_cost_unavailable");
    if (!PausedPlayer(b, after) || before.clock.date_raw != after.clock.date_raw ||
        before.played_character_id != after.played_character_id ||
        character != ck3_12004::ResolveCoreCharacter(b.core, after.played_character_id))
      return fail("paused_player_frame_changed");
    out.available = true;
    out.unavailable_reason.clear();
    return true;
  } catch (...) { return fail("loan_decision_capture_exception"); }
}
bool NativeReadFailure(Observation &out) noexcept {
  // Kept out of the SEH wrapper because Observation owns C++ strings.
  out = {};
  out.unavailable_reason = "loan_decision_native_read_exception";
  return false;
}
} // namespace

bool ReadPlayerHolyOrderLoanDecisionCosts12004(
    const Bindings &b, std::uint64_t epoch, Observation &out) noexcept {
#if defined(_WIN32) && defined(_MSC_VER)
  __try { return ReadPlayerCostsImpl(b, epoch, out); }
  __except (1) { return NativeReadFailure(out); }
#else
  return ReadPlayerCostsImpl(b, epoch, out);
#endif
}

std::string SerializeHolyOrderLoanDecisionCosts12004(const Observation &v) {
  std::ostringstream json;
  json << std::boolalpha << "{\"schema\":" << Quote(kSchema)
       << ",\"game_version\":" << Quote(ck3_12004::kGameVersion)
       << ",\"executable_sha256\":" << Quote(ck3_12004::kExecutableSha256)
       << ",\"read_only\":true,\"scope\":\"decision_gates_and_costs_only\""
       << ",\"available\":" << v.available << ",\"unavailable_reason\":"
       << (v.available ? "null" : Quote(v.unavailable_reason))
       << ",\"capture_epoch\":" << v.capture_epoch << ",\"date_raw\":" << v.date_raw
       << ",\"played_character_id\":" << v.played_character_id
       << ",\"raw_scale\":" << v.raw_scale
       << ",\"resource_slot_count\":" << kResourceSlotCount
       << ",\"complete_loan_terms\":false,\"principal_quote_raw\":null"
       << ",\"typed_debt\":null,\"funding_credit_raw\":0,\"submit_planned\":false"
       << ",\"borrow_decision\":";
  DecisionJson(json, v.borrow, v.available);
  json << ",\"repay_decision\":"; DecisionJson(json, v.repay, v.available);
  return json.str() + '}';
}

} // namespace xar::ck3_12004::religion::loan_decision_costs

#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"

#include <cstddef>
#include <cstring>
#include <sstream>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::holy_order {
namespace {
template <typename T>
bool Read(const void *object, std::size_t offset, T &value) noexcept {
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
void DestroyReason(ReasonDestroy fn, void *sink) noexcept {
  if (fn == nullptr) return;
#if defined(_MSC_VER)
  __try {
#endif
    fn(sink);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {}
#endif
}
class NativeReason {
 public:
  explicit NativeReason(ReasonDestroy destroy) noexcept : destroy_(destroy) {
    // The existing .3 reason sink ABI is a 32-byte small UTF-8 string.
    // Empty state matches native capacity15; native appends own heap data.
    const std::size_t capacity = 15;
    std::memcpy(bytes_.data() + 0x18, &capacity, sizeof(capacity));
  }
  ~NativeReason() { DestroyReason(destroy_, bytes_.data()); }
  NativeReason(const NativeReason &) = delete;
  NativeReason &operator=(const NativeReason &) = delete;
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &text) const {
    std::size_t size = 0, capacity = 0;
    if (!Read(bytes_.data(), 0x10, size) || !Read(bytes_.data(), 0x18, capacity) ||
        size > capacity) return false;
    const char *data = reinterpret_cast<const char *>(bytes_.data());
    if (capacity >= 16 && !Read(bytes_.data(), 0, data)) return false;
    if (size != 0 && data == nullptr) return false;
    text.clear();
    for (std::size_t i = 0; i < size; ++i) {
      char value = 0;
      if (!Read(data, i, value)) return false;
      text.push_back(value);
    }
    return true;
  }
 private:
  alignas(8) std::array<std::byte, 0x20> bytes_{};
  ReasonDestroy destroy_ = nullptr;
};
std::optional<std::uint32_t> Identity(std::uint32_t raw) noexcept {
  return raw == UINT32_MAX ? std::nullopt : std::optional{raw};
}
bool ReadIdentity(const Bindings &b, void *order, Row &row) {
  std::uint32_t type = 0, founder = UINT32_MAX, employer = UINT32_MAX;
  const void *leases = nullptr;
  std::int32_t count = -1;
  if (!Read(order, 0x10, row.holy_order_id) ||
      !Read(order, 0x14, type) || type != 0x486F4F72U ||
      !Read(order, 0x24, row.rite_id) ||
      !Read(order, 0x40, founder) || !Read(order, 0x80, employer) ||
      !Read(order, 0x50, leases) || !Read(order, 0x5C, count) ||
      count < 0 || (count != 0 && leases == nullptr) ||
      !Call(b.is_military, row.is_military, order)) return false;
  row.founder_id = Identity(founder);
  row.employer_id = Identity(employer);
  row.leased_title_ids.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i) {
    std::uint32_t id = UINT32_MAX;
    if (!Read(leases, static_cast<std::size_t>(i) * sizeof(id), id)) return false;
    row.leased_title_ids.push_back(id);
  }
  // Patron is derived from current leased-title holders by the engine.
  // It must not be replaced with the historical founder.
  void *patron = nullptr;
  if (!Call(b.patron, patron, order)) return false;
  if (patron != nullptr) {
    std::uint32_t id = UINT32_MAX;
    if (!Read(patron, 0x18, id)) return false;
    row.patron_id = Identity(id);
  }
  return true;
}
void ReadMilitaryTerms(const Bindings &b, void *order, void *player,
                       MilitaryTerms &terms) {
  terms.unavailable_reason = "native_evaluation_unavailable";
  terms.troop_strength.unavailable_reason = "native_current_soldiers_unavailable";
  std::int32_t current_soldiers = 0;
  if (Call(b.current_soldiers, current_soldiers, order)) {
    terms.troop_strength.current_soldiers = current_soldiers;
    terms.troop_strength.available = true;
    terms.troop_strength.unavailable_reason.clear();
  }
  NativeReason hire_reason(b.reason_destroy), afford_reason(b.reason_destroy);
  bool can_hire = false;
  if (Call(b.can_hire, can_hire, order, player, hire_reason.get())) {
    terms.can_hire = can_hire;
    std::string literal;
    terms.can_hire_reasons_available = hire_reason.copy(literal);
    if (terms.can_hire_reasons_available)
      terms.can_hire_reason_literal = std::move(literal);
  }
  std::array<std::int64_t, 10> cost{};
  std::int64_t *returned = nullptr;
  if (Call(b.cost, returned, order, cost.data(), player) && returned == cost.data()) {
    terms.resource_costs_raw = cost;
    bool affordable = false;
    if (Call(b.can_afford, affordable, static_cast<const std::int64_t *>(cost.data()),
             player, afford_reason.get())) {
      terms.can_afford = affordable;
      std::string literal;
      terms.can_afford_reasons_available = afford_reason.copy(literal);
      if (terms.can_afford_reasons_available)
        terms.can_afford_reason_literal = std::move(literal);
    }
  }
  terms.available = terms.can_hire.has_value() && terms.can_afford.has_value() &&
      terms.resource_costs_raw.has_value() && terms.can_hire_reasons_available &&
      terms.can_afford_reasons_available;
  if (terms.available) terms.unavailable_reason.clear();
}
void Quote(std::ostream &out, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char value : text) {
    if (value == '"' || value == '\\') out << '\\' << static_cast<char>(value);
    else if (value < 0x20)
      out << "\\u00" << hex[value >> 4] << hex[value & 15];
    else out << static_cast<char>(value);
  }
  out << '"';
}
template <typename T> void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void Optional(std::ostream &out, const std::optional<std::string> &value) {
  if (value) Quote(out, *value);
  else out << "null";
}
void TermsJson(std::ostream &out, const MilitaryTerms &terms) {
  out << "{\"available\":" << terms.available << ",\"unavailable_reason\":";
  if (terms.available) out << "null";
  else Quote(out, terms.unavailable_reason);
  out << ",\"can_hire\":"; Optional(out, terms.can_hire);
  out << ",\"can_afford\":"; Optional(out, terms.can_afford);
  out << ",\"resource_costs_raw\":";
  if (terms.resource_costs_raw) {
    out << '[';
    for (std::size_t i = 0; i < terms.resource_costs_raw->size(); ++i) {
      if (i != 0) out << ',';
      out << (*terms.resource_costs_raw)[i];
    }
    out << ']';
  } else out << "null";
  out << ",\"resource_scale\":" << kRawScale
      << ",\"can_hire_reasons_available\":" << terms.can_hire_reasons_available
      << ",\"can_hire_reason_literal\":"; Optional(out, terms.can_hire_reason_literal);
  out << ",\"can_afford_reasons_available\":" << terms.can_afford_reasons_available
      << ",\"can_afford_reason_literal\":"; Optional(out, terms.can_afford_reason_literal);
  out << ",\"troop_strength\":{\"available\":" << terms.troop_strength.available
      << ",\"unavailable_reason\":";
  if (terms.troop_strength.available) out << "null";
  else Quote(out, terms.troop_strength.unavailable_reason);
  out << ",\"current_soldiers\":"; Optional(out, terms.troop_strength.current_soldiers);
  out << "}}";
}
} // namespace

Bindings BindPlayerHolyOrderImage12003(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.manager_slot = reinterpret_cast<void **>(base + 0x5D1DF10);
  b.fallback_slot = reinterpret_cast<void **>(base + 0x5D1DF00);
  b.patron = reinterpret_cast<Patron>(base + 0x2618D80);
  b.is_military = reinterpret_cast<IsMilitary>(base + 0x261C490);
  b.can_hire = reinterpret_cast<CanHire>(base + 0x2619C50);
  b.cost = reinterpret_cast<Cost>(base + 0x26198E0);
  b.can_afford = reinterpret_cast<CanAfford>(base + 0x310E710);
  b.reason_destroy = reinterpret_cast<ReasonDestroy>(base + 0x856050);
  b.current_soldiers = reinterpret_cast<CurrentSoldiers>(base + 0x261AD10);
  return b;
}

bool ReadPlayerHolyOrderContext12003(const Bindings &b, void *player,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch,
    Context &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.date_raw = date;
  out.played_character_id = actor;
  if (!b.enabled || b.manager_slot == nullptr || b.fallback_slot == nullptr ||
      b.patron == nullptr || b.is_military == nullptr || b.can_hire == nullptr ||
      b.cost == nullptr || b.can_afford == nullptr || b.reason_destroy == nullptr)
    return false;
  std::int32_t actual_actor = -1;
  if (!Read(player, 0x18, actual_actor) || actual_actor != actor) {
    out.unavailable_reason = "played_character_unavailable";
    return false;
  }
  void *manager = nullptr, *fallback = nullptr;
  if (!Read(b.manager_slot, 0, manager) || manager == nullptr ||
      !Read(b.fallback_slot, 0, fallback)) {
    out.unavailable_reason = "holy_order_manager_unavailable";
    return false;
  }
  const void *entries = nullptr;
  std::int32_t range_bound = -1;
  if (!Read(manager, 0x20, entries) || !Read(manager, 0x2C, range_bound) ||
      range_bound < 0 || (range_bound != 0 && entries == nullptr)) {
    out.unavailable_reason = "holy_order_entries_unavailable";
    return false;
  }
  try {
    // +2C is a slot range bound, not an active-object count. Hole slots are
    // expected: inspect every entry and copy each real organisation once.
    for (std::int32_t i = 0; i < range_bound; ++i) {
      void *order = nullptr;
      if (!Read(entries, static_cast<std::size_t>(i) * 0x10 + 8, order)) {
        out.unavailable_reason = "holy_order_entry_unavailable";
        return false;
      }
      if (order == nullptr || (fallback != nullptr && order == fallback)) continue;
      Row row{};
      if (!ReadIdentity(b, order, row)) {
        out.unavailable_reason = "holy_order_identity_unavailable";
        return false;
      }
      if (row.is_military) {
        row.military_terms.emplace();
        ReadMilitaryTerms(b, order, player, *row.military_terms);
      }
      out.rows.push_back(std::move(row));
    }
    out.available = true;
    out.unavailable_reason.clear();
    return true;
  } catch (...) {
    out.unavailable_reason = "holy_order_native_copy_exception";
    return false;
  }
}

std::string SerializePlayerHolyOrderContext12003(const Context &c) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":"; Quote(out, kSchema);
  out << ",\"read_only\":true,\"game_version\":\"1.20.0.3\",\"executable_sha256\":";
  Quote(out, kExecutableSha256);
  out << ",\"available\":" << c.available << ",\"unavailable_reason\":";
  if (c.available) out << "null";
  else Quote(out, c.unavailable_reason);
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"date_raw\":" << c.date_raw
      << ",\"played_character_id\":" << c.played_character_id
      << ",\"raw_scale\":" << kRawScale << ",\"rows\":[";
  for (std::size_t i = 0; i < c.rows.size(); ++i) {
    if (i != 0) out << ',';
    const auto &row = c.rows[i];
    out << "{\"holy_order_id\":" << row.holy_order_id << ",\"rite_id\":" << row.rite_id
        << ",\"is_military\":" << row.is_military << ",\"founder_id\":";
    Optional(out, row.founder_id);
    out << ",\"patron_id\":"; Optional(out, row.patron_id);
    out << ",\"employer_id\":"; Optional(out, row.employer_id);
    out << ",\"leased_title_ids\":[";
    for (std::size_t j = 0; j < row.leased_title_ids.size(); ++j) {
      if (j != 0) out << ',';
      out << row.leased_title_ids[j];
    }
    out << "],\"military_terms\":";
    if (row.military_terms) TermsJson(out, *row.military_terms);
    else out << "null";
    out << '}';
  }
  out << "]}";
  return out.str();
}
} // namespace xar::ck3_12003::religion::holy_order

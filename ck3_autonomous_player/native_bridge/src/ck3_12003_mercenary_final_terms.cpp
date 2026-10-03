#include "xar_bridge/ck3_12003_mercenary_final_terms.hpp"

#include <cstddef>
#include <cstring>
#include <sstream>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::mercenary {
namespace {
template <typename T>
bool Read(const void *object, std::size_t offset, T &value) noexcept {
  if (object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
                sizeof(T));
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
// Same accepted exact .3 owned native-string ABI as the holy-order reader.
class NativeReason {
 public:
  explicit NativeReason(ReasonDestroy destroy) noexcept : destroy_(destroy) {
    const std::size_t capacity = 15;
    std::memcpy(bytes_.data() + 0x18, &capacity, sizeof(capacity));
  }
  ~NativeReason() { DestroyReason(destroy_, bytes_.data()); }
  NativeReason(const NativeReason &) = delete;
  NativeReason &operator=(const NativeReason &) = delete;
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &text) const {
    std::size_t size = 0, capacity = 0;
    if (!Read(bytes_.data(), 0x10, size) ||
        !Read(bytes_.data(), 0x18, capacity) || size > capacity) return false;
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
template <typename T>
void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void Optional(std::ostream &out, const std::optional<std::string> &value) {
  if (value) Quote(out, *value);
  else out << "null";
}
} // namespace

FinalTermsBindings BindMercenaryFinalTermsImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  FinalTermsBindings b{};
  if (base == 0 || sha != kFinalTermsExecutableSha256) return b;
  b.enabled = true;
  b.can_hire = reinterpret_cast<CanHire>(base + 0x26242D0);
  b.cost = reinterpret_cast<Cost>(base + 0x26253B0);
  b.payment_status = reinterpret_cast<PaymentStatus>(base + 0x2625470);
  b.can_afford = reinterpret_cast<CanAfford>(base + 0x310E710);
  b.hire_duration = reinterpret_cast<HireDuration>(base + 0x2625580);
  b.reason_destroy = reinterpret_cast<ReasonDestroy>(base + 0x856050);
  return b;
}

bool ReadMercenaryFinalTerms12003(const FinalTermsBindings &b, void *company,
                                void *player, FinalTerms &out) noexcept {
  out = {};
  out.unavailable_reason = "native_evaluation_unavailable";
  if (!b.enabled || company == nullptr || player == nullptr ||
      b.can_hire == nullptr || b.cost == nullptr || b.payment_status == nullptr ||
      b.can_afford == nullptr || b.hire_duration == nullptr ||
      b.reason_destroy == nullptr) return false;
  try {
    const void *landstate = nullptr;
    std::int32_t current_landstate_value = 0;
    if (!Read(player, 0x1C0, landstate) ||
        (landstate != nullptr &&
         !Read(landstate, 0x1D0, current_landstate_value))) {
      out.unavailable_reason = "played_character_quote_input_unavailable";
      return false;
    }
    NativeReason hire_reason(b.reason_destroy), afford_reason(b.reason_destroy);
    bool can_hire = false;
    if (Call(b.can_hire, can_hire, company, player, kNormalHireMode,
             hire_reason.get())) {
      out.can_hire = can_hire;
      std::string literal;
      out.can_hire_reasons_available = hire_reason.copy(literal);
      if (out.can_hire_reasons_available)
        out.can_hire_reason_literal = std::move(literal);
    }
    std::int32_t payment_status = 0;
    if (Call(b.payment_status, payment_status, company, player, kNormalHireMode))
      out.payment_status = payment_status;
    std::array<std::int64_t, 10> cost{};
    std::int64_t *returned = nullptr;
    if (Call(b.cost, returned, company, cost.data(), player,
             current_landstate_value) && returned == cost.data()) {
      out.resource_costs_raw = cost;
      bool can_afford = false;
      if (Call(b.can_afford, can_afford,
               static_cast<const std::int64_t *>(cost.data()), player,
               afford_reason.get())) {
        out.can_afford = can_afford;
        std::string literal;
        out.can_afford_reasons_available = afford_reason.copy(literal);
        if (out.can_afford_reasons_available)
          out.can_afford_reason_literal = std::move(literal);
      }
    }
    std::int64_t months = 0;
    if (Call(b.hire_duration, months, company, player))
      out.hire_duration_months = months;
    out.available = out.can_hire.has_value() && out.can_afford.has_value() &&
        out.payment_status.has_value() && out.resource_costs_raw.has_value() &&
        out.hire_duration_months.has_value() &&
        out.can_hire_reasons_available && out.can_afford_reasons_available;
    if (out.available) out.unavailable_reason.clear();
    return out.available;
  } catch (...) {
    out.unavailable_reason = "mercenary_final_terms_copy_exception";
    return false;
  }
}

std::string SerializeMercenaryFinalTerms12003(const FinalTerms &terms) {
  std::ostringstream out;
  out << std::boolalpha << "{\"available\":" << terms.available
      << ",\"unavailable_reason\":";
  if (terms.available) out << "null";
  else Quote(out, terms.unavailable_reason);
  out << ",\"can_hire\":"; Optional(out, terms.can_hire);
  out << ",\"can_afford\":"; Optional(out, terms.can_afford);
  out << ",\"payment_status\":"; Optional(out, terms.payment_status);
  out << ",\"resource_costs_raw\":";
  if (terms.resource_costs_raw) {
    out << '[';
    for (std::size_t i = 0; i < terms.resource_costs_raw->size(); ++i) {
      if (i != 0) out << ',';
      out << (*terms.resource_costs_raw)[i];
    }
    out << ']';
  } else out << "null";
  out << ",\"resource_scale\":" << kFinalTermsResourceScale
      << ",\"hire_duration_months\":"; Optional(out, terms.hire_duration_months);
  out << ",\"can_hire_reasons_available\":" << terms.can_hire_reasons_available
      << ",\"can_hire_reason_literal\":";
  Optional(out, terms.can_hire_reason_literal);
  out << ",\"can_afford_reasons_available\":"
      << terms.can_afford_reasons_available << ",\"can_afford_reason_literal\":";
  Optional(out, terms.can_afford_reason_literal);
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12003::mercenary

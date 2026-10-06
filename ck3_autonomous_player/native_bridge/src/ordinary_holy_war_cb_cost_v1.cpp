#include "xar_bridge/ordinary_holy_war_cb_cost_v1.hpp"
#include <cstddef>
#include <sstream>
#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12002 {
namespace {
template <typename Fn, typename... Args> bool Call(Fn fn, Args... args) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try {
#endif
    fn(args...); return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
class Scope {
 public:
  explicit Scope(const OrdinaryHolyWarCbCostBindingsV1 &b) noexcept : bindings_(b) {
    constructed_ = Call(b.construct_scope, static_cast<void *>(bytes_.data()));
  }
  ~Scope() { if (constructed_) (void)Call(bindings_.destroy_scope, static_cast<void *>(bytes_.data())); }
  bool constructed() const noexcept { return constructed_; }
  void *get() noexcept { return bytes_.data(); }
 private:
  const OrdinaryHolyWarCbCostBindingsV1 &bindings_;
  alignas(16) std::array<std::byte, kOrdinaryHolyWarScopeSizeV1> bytes_{};
  bool constructed_ = false;
};
void Quote(std::ostream &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
    else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 15];
    else out << static_cast<char>(c);
  }
  out << '"';
}
template <typename T> void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value; else out << "null";
}
} // namespace
bool IsOrdinaryHolyWarKeyV1(std::string_view key) noexcept {
  return key == "minor_religious_war" || key == "religious_war" || key == "major_religious_war";
}
OrdinaryHolyWarCbCostBindingsV1 BindOrdinaryHolyWarCbCostImageV1(std::uintptr_t base, std::string_view sha) noexcept {
  OrdinaryHolyWarCbCostBindingsV1 b{};
  if (!base || sha != kOrdinaryHolyWarExactSha12003) return b;
  b.enabled = true;
  b.construct_scope = reinterpret_cast<OrdinaryHolyWarScopeCtorV1>(base + kOrdinaryHolyWarScopeCtorRvaV1);
  b.populate_scope = reinterpret_cast<OrdinaryHolyWarScopePopulateV1>(base + kOrdinaryHolyWarScopePopulateRvaV1);
  b.destroy_scope = reinterpret_cast<OrdinaryHolyWarScopeDtorV1>(base + kOrdinaryHolyWarScopeDtorRvaV1);
  b.evaluate_cost = reinterpret_cast<OrdinaryHolyWarCostEvaluatorV1>(base + kOrdinaryHolyWarCostEvaluatorRvaV1);
  b.native_character_fallback_slot = reinterpret_cast<void **>(base + kOrdinaryHolyWarFallbackSlotRvaV1);
  return b;
}
bool ReadOrdinaryHolyWarCbCostV1(const OrdinaryHolyWarCbCostBindingsV1 &b, const void *cb,
    void *additional, void *recipient, void *claimant, const void *titles, OrdinaryHolyWarCbCostV1 &out) noexcept {
  out = {};
  if (!b.enabled || !b.construct_scope || !b.populate_scope || !b.destroy_scope ||
      !b.evaluate_cost || !cb || !additional || !recipient || !claimant || !titles) return false;
  Scope scope(b);
  if (!scope.constructed() || !Call(b.populate_scope, scope.get(), additional, recipient, claimant, titles, std::int32_t{0})) {
    out.unavailable_reason = "cb_scope_capture_unavailable"; return false;
  }
  std::array<std::int64_t, 10> native{};
  if (!Call(b.evaluate_cost, static_cast<const std::byte *>(cb) + kOrdinaryHolyWarCompiledCostOffsetV1,
      static_cast<const void *>(scope.get()), native.data())) {
    out.unavailable_reason = "cb_native_cost_evaluation_unavailable"; return false;
  }
  out.resource_costs_raw = native; // A successfully evaluated zero vector is available.
  out.available = true; out.unavailable_reason.clear(); return true;
}
std::string SerializeOrdinaryHolyWarDeclarationContextV1(const OrdinaryHolyWarDeclarationContextV1 &c) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":"; Quote(out, kOrdinaryHolyWarDeclarationContextSchemaV1);
  out << ",\"read_only\":true,\"game_version\":\"1.20.0.3\",\"executable_sha256\":"; Quote(out, kOrdinaryHolyWarExactSha12003);
  out << ",\"available\":" << c.available << ",\"unavailable_reason\":";
  if (c.available) out << "null"; else Quote(out, c.unavailable_reason);
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"native_revision\":" << c.native_revision
      << ",\"public_revision\":" << c.public_revision << ",\"date_raw\":" << c.date_raw
      << ",\"played_character_id\":" << c.played_character_id << ",\"declaration_id\":"; Quote(out, c.declaration_id);
  const auto &s = c.selected;
  out << ",\"selected_declaration\":{\"target_character_id\":" << s.target_character_id
      << ",\"casus_belli_index\":" << s.casus_belli_index << ",\"casus_belli_key\":"; Quote(out, s.casus_belli_key);
  out << ",\"configuration_index\":" << s.configuration_index << ",\"claimant_character_id\":" << s.claimant_character_id << ",\"target_title_ids\":[";
  for (std::size_t i = 0; i < s.target_title_ids.size(); ++i) { if (i) out << ','; out << s.target_title_ids[i]; }
  out << "]},\"context_actor_character_id\":"; Optional(out, c.context_actor_character_id);
  out << ",\"context_recipient_character_id\":"; Optional(out, c.context_recipient_character_id);
  out << ",\"context_additional_role_character_id\":"; Optional(out, c.context_additional_role_character_id);
  out << ",\"context_claimant_character_id\":"; Optional(out, c.context_claimant_character_id);
  out << ",\"recipient_uses_native_fallback\":" << c.recipient_uses_native_fallback
      << ",\"additional_role_uses_native_fallback\":" << c.additional_role_uses_native_fallback
      << ",\"claimant_uses_native_fallback\":" << c.claimant_uses_native_fallback << ",\"final_can_send\":"; Optional(out, c.final_can_send);
  out << ",\"cb_cost\":{\"available\":" << c.cb_cost.available << ",\"unavailable_reason\":";
  if (c.cb_cost.available) out << "null"; else Quote(out, c.cb_cost.unavailable_reason);
  out << ",\"resource_costs_raw\":";
  if (c.cb_cost.resource_costs_raw) {
    out << '[';
    for (std::size_t i = 0; i < c.cb_cost.resource_costs_raw->size(); ++i) { if (i) out << ','; out << (*c.cb_cost.resource_costs_raw)[i]; }
    out << ']';
  } else out << "null";
  out << ",\"raw_scale\":" << kOrdinaryHolyWarRawScaleV1 << ",\"resource_keys\":[";
  for (std::size_t i = 0; i < kOrdinaryHolyWarResourceKeysV1.size(); ++i) { if (i) out << ','; Quote(out, kOrdinaryHolyWarResourceKeysV1[i]); }
  out << "]},\"generic_interaction_cost_raw\":null,\"total_declaration_cost_raw\":null,\"total_cost_ready\":false}";
  return out.str();
}
} // namespace xar::ck3_12002

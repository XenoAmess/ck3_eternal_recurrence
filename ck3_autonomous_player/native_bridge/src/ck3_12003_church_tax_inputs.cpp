#include "xar_bridge/ck3_12003_church_tax_inputs.hpp"

#include <cstring>

namespace xar::ck3_12003::religion::church_tax_inputs {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Fail(Terms &out, const char *reason) {
  out.unavailable_reason = reason;
  return false;
}
std::string Quoted(std::string_view value) {
  std::string result = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const auto c : value) {
    const auto byte = static_cast<unsigned char>(c);
    if (c == '\\' || c == '"') { result += '\\'; result += c; }
    else if (byte < 32) {
      result += "\\u00"; result += hex[byte >> 4]; result += hex[byte & 15];
    } else result += c;
  }
  return result + '"';
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
struct OwnedNativeString {
  NativeString32 value{};
  StringDestroy destroy;
  ~OwnedNativeString() { destroy(&value); }
};
} // namespace

Bindings BindPlayerChurchTaxInputsImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != ck3_12003::kExecutableSha256) return b;
  b.enabled = true;
  b.core.enabled = true;
  b.core.character_storage_slot = reinterpret_cast<void **>(base + kCharacterStorageSlotRva);
  b.game_state_slot = reinterpret_cast<void **>(base + kGameStateSlotRva);
  b.income_context = reinterpret_cast<ObjectGetter>(base + kIncomeContextRva);
  b.character_faith = reinterpret_cast<ObjectGetter>(base + kCharacterFaithRva);
  b.faith_lease_contract = reinterpret_cast<ObjectGetter>(base + kFaithLeaseContractRva);
  b.lease_liege = reinterpret_cast<LeaseLiege>(base + kLeaseLiegeRva);
  b.top_lease_liege_direct = reinterpret_cast<TopLeaseLiegeDirect>(base + kTopLeaseLiegeDirectRva);
  b.prior_share = reinterpret_cast<PriorShare>(base + kPriorShareRva);
  b.ruler_share = reinterpret_cast<RulerShare>(base + kRulerShareRva);
  b.income_rules = reinterpret_cast<IncomeRules>(base + kIncomeRulesRva);
  b.string_destroy = reinterpret_cast<StringDestroy>(base + kStringDestroyRva);
  b.lease_liege_label = reinterpret_cast<const void *>(base + kLeaseLiegeLabelRva);
  b.top_lease_liege_direct_label = reinterpret_cast<const void *>(base + kTopLeaseLiegeDirectLabelRva);
  return b;
}

bool ReadPlayerChurchTaxInputs12003(const Bindings &b, void *ruler,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch, Terms &out) noexcept {
  out = {};
  out.capture_epoch = epoch; out.date_raw = date; out.played_character_id = actor;
  if (!b.enabled || !b.core.enabled || !b.core.character_storage_slot ||
      !b.game_state_slot || !b.income_context || !b.character_faith ||
      !b.faith_lease_contract || !b.lease_liege || !b.top_lease_liege_direct ||
      !b.prior_share || !b.ruler_share || !b.income_rules || !b.string_destroy ||
      !b.lease_liege_label || !b.top_lease_liege_direct_label) return false;
  if (!ruler || actor == -1 || Load<std::int32_t>(ruler, 0x18) != actor)
    return Fail(out, "played_character_unavailable");

  auto *context = b.income_context(ruler);
  if (!context) return Fail(out, "income_context_unavailable");
  out.income_context_character_id = Load<std::int32_t>(context, 0x18);
  auto *faith = b.character_faith(context);
  if (!faith) return Fail(out, "income_context_faith_unavailable");
  out.income_context_faith_id = Load<std::uint32_t>(faith, 0x8);
  auto *whole_contract = b.faith_lease_contract(faith);
  if (!whole_contract) return Fail(out, "income_tax_rule_unavailable");
  auto *rule = static_cast<std::byte *>(whole_contract) + 0x68;
  out.native_configured_ruler_tax_ceiling_raw = Load<std::int64_t>(rule, 0x2F8);

  auto *land = Load<void *>(ruler, 0x1C0);
  const auto lessee_id = land ? Load<std::int32_t>(land, 0x1B8) : -1;
  out.actual_lessee_character_id = lessee_id;
  if (lessee_id == -1) return Fail(out, "actual_direct_lessee_absent");
  auto *lessee = ck3_12002::ResolveCoreCharacter(b.core, lessee_id);
  if (!lessee) return Fail(out, "actual_direct_lessee_unavailable");
  auto *game = *b.game_state_slot;
  auto *game_data = game ? Load<void *>(game, 0xA0) : nullptr;
  if (!game_data) return Fail(out, "lease_manager_unavailable");
  auto *manager = static_cast<std::byte *>(game_data) + 0x1F1E0;

  std::int32_t superior = -1, top = -1;
  if (b.lease_liege(manager, &superior, lessee_id) != &superior)
    return Fail(out, "lease_liege_unavailable");
  if (superior == -1) {
    if (b.top_lease_liege_direct(&superior, lessee_id) != &superior)
      return Fail(out, "lease_liege_unavailable");
    if (superior == lessee_id) superior = -1;
  }
  out.lease_liege_character_id = superior;
  if (b.top_lease_liege_direct(&top, lessee_id) != &top)
    return Fail(out, "top_lease_liege_direct_unavailable");
  out.top_lease_liege_direct_character_id = top;

  std::int64_t first = 0, second = 0, current = 0;
  if (b.prior_share(rule, &first, rule + 0x108,
      Load<std::int64_t>(rule, 0x8), Load<std::int64_t>(rule, 0x2E8),
      lessee_id, superior, Terms::raw_scale, b.lease_liege_label, nullptr) != &first)
    return Fail(out, "lease_liege_share_unavailable");
  out.lease_liege_share_raw = first;
  if (b.prior_share(rule, &second, rule + 0x1F8,
      Load<std::int64_t>(rule, 0x10), Load<std::int64_t>(rule, 0x2F0),
      lessee_id, top, Terms::raw_scale - first,
      b.top_lease_liege_direct_label, nullptr) != &second)
    return Fail(out, "top_lease_liege_direct_share_unavailable");
  out.top_lease_liege_direct_share_raw = second;
  const auto remaining = Terms::raw_scale - first - second;
  out.remaining_before_ruler_share_raw = remaining;
  if (b.ruler_share(rule, &current, ruler, lessee_id, false, remaining, nullptr) != &current)
    return Fail(out, "effective_ruler_tax_share_unavailable");
  out.effective_ruler_tax_share_raw = current;

  // The selected-rule formatter constructs a fresh owned string. Copy before
  // calling its native destructor once; GUI variant wrappers are unnecessary.
  OwnedNativeString text{{}, b.string_destroy};
  if (b.income_rules(rule, &text.value, ruler, lessee) != &text.value)
    return Fail(out, "income_rules_unavailable");
  const auto size = Load<std::uint64_t>(&text.value, 0x10);
  const auto capacity = Load<std::uint64_t>(&text.value, 0x18);
  const auto *data = capacity < 16 ? reinterpret_cast<const char *>(&text.value)
                                 : Load<const char *>(&text.value, 0);
  if (size > capacity || (!data && size)) return Fail(out, "income_rules_unavailable");
  out.income_rules_text = size ? std::string(data, static_cast<std::size_t>(size)) : std::string{};
  out.available = true;
  out.unavailable_reason.clear();
  return true;
}

std::string SerializePlayerChurchTaxInputs12003(const Terms &c) {
  return "{\"schema\":" + Quoted(kSchema) + ",\"read_only\":true,\"available\":" +
      (c.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (c.available ? "null" : Quoted(c.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"income_context_character_id\":" + Number(c.income_context_character_id) +
      ",\"income_context_faith_id\":" + Number(c.income_context_faith_id) +
      ",\"actual_lessee_character_id\":" + Number(c.actual_lessee_character_id) +
      ",\"lease_liege_character_id\":" + Number(c.lease_liege_character_id) +
      ",\"top_lease_liege_direct_character_id\":" + Number(c.top_lease_liege_direct_character_id) +
      ",\"lease_liege_share_raw\":" + Number(c.lease_liege_share_raw) +
      ",\"top_lease_liege_direct_share_raw\":" + Number(c.top_lease_liege_direct_share_raw) +
      ",\"remaining_before_ruler_share_raw\":" + Number(c.remaining_before_ruler_share_raw) +
      ",\"effective_ruler_tax_share_raw\":" + Number(c.effective_ruler_tax_share_raw) +
      ",\"native_configured_ruler_tax_ceiling_raw\":" + Number(c.native_configured_ruler_tax_ceiling_raw) +
      ",\"income_rules_text\":" + (c.income_rules_text ? Quoted(*c.income_rules_text) : "null") +
      ",\"raw_scale\":100000,\"share_unit\":\"fraction\","
      "\"scope\":\"income-selected-direct-ruler-tax-rule\"}";
}
} // namespace xar::ck3_12003::religion::church_tax_inputs

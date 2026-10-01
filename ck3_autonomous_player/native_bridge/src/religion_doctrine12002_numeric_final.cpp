#include "xar_bridge/religion_doctrine12002_numeric_final.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Same(const NumericSpecialContext &a, const NumericSpecialContext &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.faith_id == b.faith_id && a.current_rite == b.current_rite && a.faith_main_rite == b.faith_main_rite;
}
std::string Quote(std::string_view value) {
  std::string result = "\"";
  for (char c : value) {
    if (c == '"' || c == '\\') result += '\\';
    result += c;
  }
  return result + '"';
}
template <typename T> std::string Raw(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string Value(const std::optional<std::int64_t> &raw) {
  if (!raw) return "null";
  const auto magnitude = *raw < 0 ? std::uint64_t{0} - static_cast<std::uint64_t>(*raw)
                                 : static_cast<std::uint64_t>(*raw);
  auto fraction = std::to_string(magnitude % 100000);
  fraction.insert(0, 5 - fraction.size(), '0');
  return (*raw < 0 ? "-" : "") + std::to_string(magnitude / 100000) + '.' + fraction;
}
} // namespace

FaithNumericFinalBindings BindFaithNumericFinal12002(std::uintptr_t base, std::string_view sha) noexcept {
  if (!base || sha != kExecutableSha256) return {};
  return {true, reinterpret_cast<FaithHeresyThresholdGetter>(base + kFaithHeresyThresholdGetterRva),
                reinterpret_cast<const std::int64_t *>(base + kFaithHeresyThresholdDefineRva)};
}
bool ReadPlayedFaithNumericFinal12002(const religion::Bindings &r, const NumericSpecialBindings &n,
                                     const FaithNumericFinalBindings &b, std::uint64_t epoch,
                                     FaithNumericFinalContext &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !b.faith_heresy_threshold || !b.heresy_threshold_define) return false;
  NumericSpecialContext before{}, after{};
  if (!ReadPlayedNumericSpecialParameters12002(r, n, epoch, before)) {
    out.failure = before.failure;
    return false;
  }
  FaithNumericFinalContext result{};
  result.capture_epoch = epoch;
  result.date_raw = before.date_raw;
  result.played_character_id = before.played_character_id;
  result.faith_id = before.faith_id;
  if (before.current_rite) result.current_rite_id = before.current_rite->rite_id;
  if (before.faith_main_rite) result.main_rite_id = before.faith_main_rite->rite_id;
  if (before.faith_id && before.faith_main_rite) {
    auto *character = ResolveCoreCharacter(r.core, static_cast<std::int32_t>(before.played_character_id));
    auto *faith = character ? r.character_faith(character) : nullptr;
    if (!faith || Load<std::uint32_t>(faith, religion::kReferenceIdentityOffset) != *before.faith_id) {
      out.failure = "faith_unavailable";
      return false;
    }
    const auto adjustment = LookupNumericSpecialParameter12002(before, true, "heresy_threshold");
    if (!adjustment.parameter || adjustment.state != NumericParameterLookupState::Value) {
      out.failure = "main_rite_adjustment_unavailable";
      return false;
    }
    std::int64_t first{}, second{};
    const auto base_define = Load<std::int64_t>(b.heresy_threshold_define, 0);
    if (b.faith_heresy_threshold(faith, &first) != &first ||
        b.faith_heresy_threshold(faith, &second) != &second) {
      out.failure = "native_threshold_unavailable";
      return false;
    }
    if (first != second || Load<std::int64_t>(b.heresy_threshold_define, 0) != base_define) {
      out.failure = "state_changed";
      return false;
    }
    result.main_rite_adjustment_raw = adjustment.parameter->raw;
    result.native_define_raw = base_define;
    result.final_heresy_threshold_raw = first;
  }
  if (!ReadPlayedNumericSpecialParameters12002(r, n, epoch, after) || !Same(before, after)) {
    out.failure = after.available ? "state_changed" : after.failure;
    return false;
  }
  result.available = true;
  result.failure = "none";
  out = std::move(result);
  return true;
}
std::string SerializeFaithNumericFinal12002(const FaithNumericFinalContext &c) {
  const auto value_state = !c.available ? "unavailable" : !c.faith_id ? "legal_absent_faith" :
      !c.main_rite_id ? "legal_absent_main_rite" : "value";
  return "{\"schema\":\"ck3_12002_faith_numeric_final_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : Quote(c.failure)) +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"current_rite_id\":" + Raw(c.current_rite_id) + ",\"faith_id\":" + Raw(c.faith_id) +
      ",\"main_rite_id\":" + Raw(c.main_rite_id) + ",\"value_state\":" + Quote(value_state) +
      ",\"main_rite_adjustment_raw\":" + Raw(c.main_rite_adjustment_raw) +
      ",\"native_define_raw\":" + Raw(c.native_define_raw) +
      ",\"final_heresy_threshold_raw\":" + Raw(c.final_heresy_threshold_raw) +
      ",\"final_heresy_threshold\":" + Value(c.final_heresy_threshold_raw) +
      ",\"scale\":100000,\"unit\":\"fervor_points\",\"source\":\"faith_main_rite\","
      "\"native_getter_rva\":\"0x2440920\",\"native_define_rva\":\"0x5C68D88\"}";
}
} // namespace xar::ck3_12002::religion::doctrine12002

#include "xar_bridge/religion_doctrine12002_numeric.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Matches(const void *object, std::uint32_t id) noexcept {
  return object && Load<std::uint32_t>(object, religion::kReferenceIdentityOffset) == id;
}
std::string ReadRite(const void *rite, std::uint32_t id, RiteNumericSpecialParameters &out) {
  if (!Matches(rite, id)) return "rite_unavailable";
  const auto *special = static_cast<const std::byte *>(rite) + kRiteNumericSpecialOffset;
  const auto minimum = Load<std::int32_t>(special, kNumericMinimumFervorOffset);
  out.rite_id = id;
  out.parameters = {
      {"minimum_fervor", minimum, 1, "fervor_points", minimum == -1},
      {"fervor_per_holy_site", Load<std::int64_t>(special, kNumericHolySiteGainOffset),
       100000, "yearly_fervor_per_controlled_holy_site", false},
      {"bonus_fervor_gain", Load<std::int64_t>(special, kNumericFervorGainOffset),
       100000, "yearly_fervor_gain_bonus", false},
      {"bonus_heresy_protection", Load<std::int32_t>(special, kNumericHeresyProtectionOffset),
       1, "heresy_protection_count_bonus", false},
      {"heresy_threshold", Load<std::int64_t>(special, kNumericHeresyThresholdOffset),
       100000, "fervor_threshold_adjustment", false}};
  return Matches(rite, id) ? std::string{} : "state_changed";
}
std::string ReadOnce(const religion::Bindings &r, std::uint64_t epoch, NumericSpecialContext &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(r.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return "played_character_unavailable";
  if (!frame.clock.paused) return "frame_not_paused";
  auto *character = ResolveCoreCharacter(r.core, frame.played_character_id);
  if (!character) return "played_character_unavailable";
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
  const auto rite_id = Load<std::uint32_t>(character, religion::kCharacterRiteIdOffset);
  if (rite_id != religion::kAbsentReference) {
    auto *rite = r.character_rite(character);
    RiteNumericSpecialParameters current{};
    auto failure = ReadRite(rite, rite_id, current);
    if (!failure.empty()) return failure;
    out.current_rite = std::move(current);
    const auto faith_id = Load<std::uint32_t>(rite, religion::kRiteFaithIdOffset);
    if (faith_id != religion::kAbsentReference) {
      auto *faith = r.rite_faith(rite);
      if (!Matches(faith, faith_id) || r.character_faith(character) != faith)
        return "faith_unavailable";
      out.faith_id = faith_id;
      const auto main_id = Load<std::uint32_t>(faith, religion::kFaithMainRiteIdOffset);
      if (main_id != religion::kAbsentReference) {
        RiteNumericSpecialParameters main{};
        failure = ReadRite(r.faith_main_rite(faith), main_id, main);
        if (!failure.empty()) return failure == "rite_unavailable" ? "main_rite_unavailable" : failure;
        out.faith_main_rite = std::move(main);
      }
    }
  }
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(r.core, after) || after.clock.date_raw != frame.clock.date_raw ||
      !after.clock.paused || after.played_character_id != frame.played_character_id ||
      ResolveCoreCharacter(r.core, frame.played_character_id) != character)
    return "state_changed";
  return {};
}
bool Same(const NumericSpecialContext &a, const NumericSpecialContext &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.faith_id == b.faith_id && a.current_rite == b.current_rite &&
      a.faith_main_rite == b.faith_main_rite;
}
std::string Quote(std::string_view value) {
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
std::string Number(const NumericSpecialParameter &p) {
  if (p.unset) return "null";
  if (p.scale == 1) return std::to_string(p.raw);
  const auto magnitude = p.raw < 0 ? std::uint64_t{0} - static_cast<std::uint64_t>(p.raw)
                                  : static_cast<std::uint64_t>(p.raw);
  auto fraction = std::to_string(magnitude % 100000);
  fraction.insert(0, 5 - fraction.size(), '0');
  return (p.raw < 0 ? "-" : "") + std::to_string(magnitude / 100000) + '.' + fraction;
}
std::string RiteJson(const std::optional<RiteNumericSpecialParameters> &rite) {
  if (!rite) return "null";
  std::string result = "{\"rite_id\":" + std::to_string(rite->rite_id) +
      ",\"observed_special_parameters_complete\":true,\"parameters\":[";
  for (std::size_t i = 0; i < rite->parameters.size(); ++i) {
    if (i) result += ',';
    const auto &p = rite->parameters[i];
    result += "{\"key\":" + Quote(p.key) + ",\"raw\":" + std::to_string(p.raw) +
        ",\"scale\":" + std::to_string(p.scale) + ",\"value\":" + Number(p) +
        ",\"state\":" + Quote(p.unset ? "unset" : "value") + ",\"unit\":" + Quote(p.unit) + '}';
  }
  return result + "]}";
}
} // namespace

NumericSpecialBindings BindNumericSpecialParameters12002(std::uintptr_t base, std::string_view sha) noexcept {
  return {base != 0 && sha == kExecutableSha256};
}
bool ReadPlayedNumericSpecialParameters12002(const religion::Bindings &r, const NumericSpecialBindings &b,
                                            std::uint64_t epoch, NumericSpecialContext &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !r.enabled || !r.core.enabled || !r.character_rite || !r.character_faith ||
      !r.rite_faith || !r.faith_main_rite) return false;
  NumericSpecialContext first{}, second{};
  auto failure = ReadOnce(r, epoch, first);
  if (failure.empty()) failure = ReadOnce(r, epoch, second);
  if (failure.empty() && !Same(first, second)) failure = "state_changed";
  if (!failure.empty()) { out.failure = std::move(failure); return false; }
  out = std::move(first);
  out.available = true;
  out.failure = "none";
  return true;
}
NumericParameterLookup LookupNumericSpecialParameter12002(const NumericSpecialContext &context,
                                                          bool faith_main_rite, std::string_view key) {
  if (!context.available) return {};
  const auto &rite = faith_main_rite ? context.faith_main_rite : context.current_rite;
  if (!rite) return {};
  for (const auto &parameter : rite->parameters) {
    if (parameter.key == key)
      return {parameter.unset ? NumericParameterLookupState::Unset : NumericParameterLookupState::Value,
              parameter};
  }
  return {NumericParameterLookupState::UnsupportedKey, std::nullopt};
}
std::string SerializeNumericSpecialParameters12002(const NumericSpecialContext &c) {
  return "{\"schema\":\"ck3_12002_rite_numeric_special_parameters_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : Quote(c.failure)) +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"faith_id\":" + (c.faith_id ? std::to_string(*c.faith_id) : "null") +
      ",\"faith_numeric_consumer_source\":\"faith_main_rite\","
      "\"authored_presence_provenance_observed\":false,"
      "\"supported_key_count\":5,\"current_rite\":" + RiteJson(c.current_rite) +
      ",\"faith_main_rite\":" + RiteJson(c.faith_main_rite) + "}";
}
} // namespace xar::ck3_12002::religion::doctrine12002

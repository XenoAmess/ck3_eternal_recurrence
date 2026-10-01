#include "xar_bridge/religion_doctrine12002_tenet.hpp"

#include <cstring>
#include <limits>

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
bool CopyKey(const void *native_string, std::string &out) {
  if (!native_string) return false;
  const auto size = Load<std::uint64_t>(native_string, 0x10);
  const auto capacity = Load<std::uint64_t>(native_string, 0x18);
  if (!size || size > capacity || size > 4096) return false;
  const auto *data = capacity < 16 ? static_cast<const char *>(native_string)
                                 : Load<const char *>(native_string, 0);
  if (!data) return false;
  out.assign(data, static_cast<std::size_t>(size));
  return true;
}
std::string ReadRite(const TenetParameterBindings &b, const void *rite,
                     std::uint32_t id, RiteBooleanParameters &out) {
  if (!Matches(rite, id)) return "rite_unavailable";
  const auto *collection = static_cast<const std::byte *>(rite) + kRiteBooleanParameterOffset;
  const auto count = Load<std::int32_t>(collection, kArrayCountOffset);
  const auto *data = Load<const std::int32_t *>(collection, kArrayDataOffset);
  if (count < 0 || count > 8192 || (count && !data)) return "parameter_collection_unavailable";
  out.rite_id = id;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto token = Load<std::int32_t>(data, static_cast<std::size_t>(i) * sizeof(std::int32_t));
    if (!b.contains_boolean_parameter(collection, &token)) return "parameter_membership_unavailable";
    std::string key;
    if (!CopyKey(b.parameter_key(token), key)) return "parameter_key_unavailable";
    out.parameters.push_back({std::move(key), true});
  }
  if (Load<const std::int32_t *>(collection, kArrayDataOffset) != data ||
      Load<std::int32_t>(collection, kArrayCountOffset) != count || !Matches(rite, id))
    return "state_changed";
  return {};
}
std::string ReadOnce(const religion::Bindings &r, const TenetParameterBindings &b,
                     std::uint64_t epoch, TenetParameterContext &out) {
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
    RiteBooleanParameters current{};
    auto failure = ReadRite(b, rite, rite_id, current);
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
        RiteBooleanParameters main{};
        failure = ReadRite(b, r.faith_main_rite(faith), main_id, main);
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
bool Same(const TenetParameterContext &a, const TenetParameterContext &b) {
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
std::string RiteJson(const std::optional<RiteBooleanParameters> &rite) {
  if (!rite) return "null";
  std::string result = "{\"rite_id\":" + std::to_string(rite->rite_id) +
      ",\"boolean_parameters_complete\":true,\"parameters\":[";
  for (std::size_t i = 0; i < rite->parameters.size(); ++i) {
    if (i) result += ',';
    result += "{\"key\":" + Quote(rite->parameters[i].key) + ",\"value\":true}";
  }
  return result + "]}";
}
} // namespace

TenetParameterBindings BindTenetParameters12002(std::uintptr_t base, std::string_view sha) noexcept {
  if (!base || sha != kExecutableSha256) return {};
  return {true, reinterpret_cast<BooleanParameterMembership>(base + kBooleanParameterMembershipRva),
                reinterpret_cast<ParameterTokenKey>(base + kParameterTokenKeyRva)};
}

bool ReadPlayedTenetParameters12002(const religion::Bindings &r, const TenetParameterBindings &b,
                                  std::uint64_t epoch, TenetParameterContext &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !r.enabled || !r.core.enabled || !b.contains_boolean_parameter ||
      !b.parameter_key || !r.character_rite || !r.character_faith ||
      !r.rite_faith || !r.faith_main_rite) return false;
  TenetParameterContext first{}, second{};
  auto failure = ReadOnce(r, b, epoch, first);
  if (failure.empty()) failure = ReadOnce(r, b, epoch, second);
  if (failure.empty() && !Same(first, second)) failure = "state_changed";
  if (!failure.empty()) { out.failure = std::move(failure); return false; }
  out = std::move(first);
  out.available = true;
  out.failure = "none";
  return true;
}

std::string SerializeTenetParameters12002(const TenetParameterContext &c) {
  return "{\"schema\":\"ck3_12002_rite_boolean_parameters_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : Quote(c.failure)) +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"faith_id\":" + (c.faith_id ? std::to_string(*c.faith_id) : "null") +
      ",\"current_rite\":" + RiteJson(c.current_rite) +
      ",\"faith_main_rite\":" + RiteJson(c.faith_main_rite) + "}";
}
} // namespace xar::ck3_12002::religion::doctrine12002

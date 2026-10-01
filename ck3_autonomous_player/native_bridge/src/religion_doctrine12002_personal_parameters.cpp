#include "xar_bridge/religion_doctrine12002_personal_parameters.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool CopyTokenKey(const void *native_string, std::string &out) {
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
bool ReadArray(const void *collection, const void *&data, std::int32_t &count) {
  if (!collection) return false;
  data = Load<const void *>(collection, 0);
  count = Load<std::int32_t>(collection, 0xC);
  return count >= 0 && count <= 8192 && (!count || data);
}
bool ArrayUnchanged(const void *collection, const void *data, std::int32_t count) {
  return Load<const void *>(collection, 0) == data &&
         Load<std::int32_t>(collection, 0xC) == count;
}
std::string ReadOnce(const religion::Bindings &r, const PersonalParameterBindings &b,
                     std::uint64_t epoch, PersonalParameterContext &out) {
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
  const auto *database = *b.database_slot;
  if (!database) return "parameter_registry_unavailable";
  const auto *supported = static_cast<const std::byte *>(database) + kPersonalParameterSupportedSetOffset;
  const void *supported_data = nullptr;
  std::int32_t supported_count = 0;
  if (!ReadArray(supported, supported_data, supported_count)) return "parameter_registry_unavailable";
  const auto *extension = Load<const void *>(character, kPersonalParameterCharacterExtensionOffset);
  out.has_character_extension = extension != nullptr;
  const void *personal_collection = nullptr, *personal_data = nullptr;
  std::int32_t personal_count = 0;
  std::vector<const void *> definitions;
  if (extension) {
    personal_collection = b.owned_tenets(character);
    if (personal_collection != static_cast<const std::byte *>(extension) + kPersonalParameterOwnedTenetsOffset ||
        !ReadArray(personal_collection, personal_data, personal_count))
      return "personal_tenet_collection_unavailable";
    for (std::int32_t n = 0; n < personal_count; ++n) {
      const auto *definition = Load<const void *>(personal_data, static_cast<std::size_t>(n) * sizeof(void *));
      std::string key;
      if (!CopyTenetDefinitionKey12002(definition, key)) return "personal_tenet_definition_unavailable";
      definitions.push_back(definition);
      out.personal_tenet_keys.push_back(std::move(key));
    }
  }
  for (std::int32_t n = 0; n < supported_count; ++n) {
    const auto token = Load<std::int32_t>(supported_data, static_cast<std::size_t>(n) * sizeof(std::int32_t));
    if (!b.contains_parameter(supported, &token)) return "parameter_registry_membership_unavailable";
    PersonalParameterValue value{};
    if (!CopyTokenKey(b.parameter_key(token), value.key)) return "parameter_key_unavailable";
    for (const auto *definition : definitions) {
      const auto *set = static_cast<const std::byte *>(definition) + kPersonalParameterDefinitionSetOffset;
      const void *set_data = nullptr;
      std::int32_t set_count = 0;
      if (!ReadArray(set, set_data, set_count)) return "personal_parameter_collection_unavailable";
      value.value = b.contains_parameter(set, &token);
      if (!ArrayUnchanged(set, set_data, set_count)) return "state_changed";
      if (value.value) break; // Exact Evaluate short-circuits on first matching owned Tenet.
    }
    out.parameters.push_back(std::move(value));
  }
  CoreSnapshotPrefix after{};
  if (*b.database_slot != database || !ArrayUnchanged(supported, supported_data, supported_count) ||
      Load<const void *>(character, kPersonalParameterCharacterExtensionOffset) != extension ||
      (personal_collection && !ArrayUnchanged(personal_collection, personal_data, personal_count)) ||
      !ReadCoreSnapshot(r.core, after) || after.clock.date_raw != frame.clock.date_raw ||
      !after.clock.paused || after.played_character_id != frame.played_character_id ||
      ResolveCoreCharacter(r.core, frame.played_character_id) != character)
    return "state_changed";
  return {};
}
bool Same(const PersonalParameterContext &a, const PersonalParameterContext &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.has_character_extension == b.has_character_extension &&
      a.personal_tenet_keys == b.personal_tenet_keys && a.parameters == b.parameters;
}
std::string Quote(std::string_view value) {
  std::string result = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const auto c : value) {
    const auto byte = static_cast<unsigned char>(c);
    if (c == '\\' || c == '"') { result += '\\'; result += c; }
    else if (byte < 32) { result += "\\u00"; result += hex[byte >> 4]; result += hex[byte & 15]; }
    else result += c;
  }
  return result + '"';
}
} // namespace

PersonalParameterBindings BindPersonalParameters12002(std::uintptr_t base, std::string_view sha) noexcept {
  if (!base || sha != kExecutableSha256) return {};
  return {true, reinterpret_cast<const void *const *>(base + kPersonalParameterDatabaseSlotRva),
      reinterpret_cast<PersonalParameterCollectionGetter>(base + kPersonalParameterCollectionGetterRva),
      reinterpret_cast<BooleanParameterMembership>(base + kBooleanParameterMembershipRva),
      reinterpret_cast<ParameterTokenKey>(base + kParameterTokenKeyRva)};
}
bool ReadPlayedPersonalParameters12002(const religion::Bindings &r, const PersonalParameterBindings &b,
                                      std::uint64_t epoch, PersonalParameterContext &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  if (!r.enabled || !r.core.enabled || !b.enabled || !b.database_slot ||
      !b.owned_tenets || !b.contains_parameter || !b.parameter_key) return false;
  PersonalParameterContext first{}, second{};
  auto failure = ReadOnce(r, b, epoch, first);
  if (failure.empty()) failure = ReadOnce(r, b, epoch, second);
  if (failure.empty() && !Same(first, second)) failure = "state_changed";
  if (!failure.empty()) { out.failure = std::move(failure); return false; }
  out = std::move(first); out.available = true; out.failure = "none"; return true;
}
PersonalParameterLookup LookupPersonalParameter12002(const PersonalParameterContext &context,
                                                    std::string_view key) noexcept {
  if (!context.available) return {};
  for (const auto &parameter : context.parameters)
    if (parameter.key == key) return {PersonalParameterLookupState::Value, parameter.value};
  return {PersonalParameterLookupState::UnsupportedKey, std::nullopt};
}
std::string SerializePersonalParameters12002(const PersonalParameterContext &c) {
  std::string result = "{\"schema\":\"ck3_12002_character_personal_parameters_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"source\":\"character_personal_tenets\",\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : Quote(c.failure)) +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"has_character_extension\":" + (c.has_character_extension ? "true" : "false") +
      ",\"supported_keys_complete\":" + (c.available ? "true" : "false") +
      ",\"personal_parameters_complete\":" + (c.available ? "true" : "false") +
      ",\"personal_tenet_keys\":[";
  for (std::size_t n = 0; n < c.personal_tenet_keys.size(); ++n) {
    if (n) result += ',';
    result += Quote(c.personal_tenet_keys[n]);
  }
  result += "],\"parameters\":[";
  for (std::size_t n = 0; n < c.parameters.size(); ++n) {
    if (n) result += ',';
    result += "{\"key\":" + Quote(c.parameters[n].key) +
              ",\"value\":" + (c.parameters[n].value ? "true" : "false") + "}";
  }
  return result + "]}";
}
} // namespace xar::ck3_12002::religion::doctrine12002

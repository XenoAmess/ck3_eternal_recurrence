#include "xar_bridge/player_epidemic_recovery_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {
namespace {

// All RVAs are bound to ck3.exe SHA-256 2D00FF31...F83DB86.
constexpr std::uintptr_t kVariableContextForScopeRva = 0x3329A40;
constexpr std::uintptr_t kGetVariableIdentifierTableRva = 0x3B971A0;
constexpr std::uintptr_t kLookupVariableIdentifierRva = 0x3B97020;
constexpr std::uintptr_t kVariableIdentifierNameRva = 0x3B97090;
constexpr std::uintptr_t kLandedTitleStoreSlotRva = 0x570C410;
constexpr std::uintptr_t kCountyModifierGetterRva = 0x1942CB0;
constexpr std::uintptr_t kModifierDatabaseRva = 0x88F370;
constexpr std::uintptr_t kStableKeyHashRva = 0x3B8B000;
constexpr std::uintptr_t kModifierLookupRva = 0xA41F10;
constexpr std::uintptr_t kModifierFallbackSlotRva = 0x570C968;

struct EventTarget16 {
  std::uint16_t kind = 0;
  std::uint16_t subtype = 0;
  std::uint32_t padding = 0;
  std::int64_t payload = 0;
};
static_assert(sizeof(EventTarget16) == 0x10);

struct NativeStringView32 {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::int32_t padding = 0;
};
static_assert(sizeof(NativeStringView32) == 0x10);

struct CountyModifierResult {
  std::uint64_t native_time = 0;
  std::uint8_t present = 0;
  std::array<std::uint8_t, 7> padding{};
};
static_assert(sizeof(CountyModifierResult) == 0x10);

using VariableContextForScope = void *(*)(const EventTarget16 *);
using GetIdentifierTable = void *(*)();
using LookupIdentifier = std::int32_t *(*)(
    void *, std::int32_t *, const NativeStringView32 *);
using IdentifierName = const std::string *(*)(void *, std::int32_t);
using GetModifierDatabase = void *(*)();
using HashStableKey = std::int32_t (*)(void *, const char *, std::uint32_t);
using LookupModifier = void *(*)(void *, std::int32_t);
using CountyModifierGetter = CountyModifierResult *(*)(
    CountyModifierResult *, void *, void *);

bool ReadCurrent(const void *address, void *out, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != nullptr && out != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(), address, out, size, &read) !=
             FALSE &&
         read == size;
}

template <typename T>
bool ReadAt(const void *base, std::size_t offset, T &out) noexcept {
  return base != nullptr &&
         ReadCurrent(static_cast<const std::byte *>(base) + offset, &out,
                     sizeof(T));
}

bool ResolveIdentifier(std::uintptr_t module, std::string_view key,
                       std::int32_t &identifier) {
  void *table = reinterpret_cast<GetIdentifierTable>(
      module + kGetVariableIdentifierTableRva)();
  if (table == nullptr ||
      key.size() > static_cast<std::size_t>(
                       std::numeric_limits<std::int32_t>::max()))
    return false;
  const NativeStringView32 view{key.data(),
                                static_cast<std::int32_t>(key.size()), 0};
  identifier = -1;
  if (reinterpret_cast<LookupIdentifier>(
          module + kLookupVariableIdentifierRva)(table, &identifier,
                                                 &view) == nullptr ||
      identifier < 0)
    return false;
  const std::string *name = reinterpret_cast<IdentifierName>(
      module + kVariableIdentifierNameRva)(table, identifier);
  return name != nullptr && *name == key;
}

bool ReadStableKey(const void *definition, std::string &key) {
  const auto *storage = static_cast<const std::byte *>(definition) + 0x18;
  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!ReadAt(storage, 0x10, size) || !ReadAt(storage, 0x18, capacity) ||
      size > 128 || capacity < size)
    return false;
  const void *data = storage;
  if (capacity >= 16 && !ReadAt(storage, 0, data))
    return false;
  key.resize(size);
  return size == 0 || ReadCurrent(data, key.data(), size);
}

bool ResolveModifier(std::uintptr_t module, void *database, void *fallback,
                     std::string_view key, void *&definition) {
  const auto hash = reinterpret_cast<HashStableKey>(
      module + kStableKeyHashRva)(database, key.data(),
                                 static_cast<std::uint32_t>(key.size()));
  definition = reinterpret_cast<LookupModifier>(
      module + kModifierLookupRva)(database, hash);
  std::string actual;
  return definition != nullptr && definition != fallback &&
         ReadStableKey(definition, actual) && actual == key;
}

bool ResolveTitle(std::uintptr_t module, std::int32_t full_id,
                  void *&title) noexcept {
  title = nullptr;
  if (full_id <= 0)
    return false;
  void *store = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadCurrent(reinterpret_cast<const void *>(module +
                   kLandedTitleStoreSlotRva), &store, sizeof(store)) ||
      store == nullptr || !ReadAt(store, 0x20, slots) || slots == nullptr ||
      !ReadAt(store, 0x2C, capacity) || capacity <= 0)
    return false;
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity))
    return false;
  const auto *slot = static_cast<const std::byte *>(slots) +
                     static_cast<std::size_t>(index) * 0x10 + 0x08;
  std::int32_t round_trip = -1;
  return ReadCurrent(slot, &title, sizeof(title)) && title != nullptr &&
         ReadAt(title, 0x10, round_trip) && round_trip == full_id;
}

bool VerifyPlayedCharacter(const Bindings &bindings,
                           std::int32_t full_id) noexcept {
  if (full_id <= 0 || bindings.character_storage_slot == nullptr)
    return false;
  void *store = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadCurrent(bindings.character_storage_slot, &store, sizeof(store)) ||
      store == nullptr || !ReadAt(store, 0x20, slots) || slots == nullptr ||
      !ReadAt(store, 0x2C, capacity) || capacity <= 0)
    return false;
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity))
    return false;
  const auto *slot = static_cast<const std::byte *>(slots) +
                     static_cast<std::size_t>(index) * 0x10 + 0x08;
  void *character = nullptr;
  std::int32_t round_trip = -1;
  return ReadCurrent(slot, &character, sizeof(character)) &&
         character != nullptr && ReadAt(character, 0x18, round_trip) &&
         round_trip == full_id;
}

bool IsCountyTitle(const void *title) noexcept {
  void *definition = nullptr;
  std::int32_t tier = -1;
  return ReadAt(title, 0x160, definition) && definition != nullptr &&
         ReadAt(definition, 0x5C, tier) && tier == 2;
}

bool ReadCountyPresence(std::uintptr_t module, void *title, void *definition,
                        bool &present) {
  CountyModifierResult result{};
  auto *returned = reinterpret_cast<CountyModifierGetter>(
      module + kCountyModifierGetterRva)(&result, title, definition);
  if (returned != &result || result.present > 1)
    return false;
  present = result.present != 0;
  return true;
}

PlayerEpidemicRecoveryV1 Unavailable(std::uint64_t revision,
                                      std::int32_t date_raw,
                                      std::int32_t character_id,
                                      std::int32_t requested_title_id,
                                      const char *reason) {
  PlayerEpidemicRecoveryV1 result{};
  result.snapshot_revision = revision;
  result.date_raw = date_raw;
  result.played_character_id = character_id;
  result.requested_title_id = requested_title_id;
  result.unavailable_reason = reason;
  return result;
}

} // namespace

bool ParsePlayerEpidemicRecoveryStepV1(
    std::string_view step, std::int32_t &requested_title_id) noexcept {
  requested_title_id = 0;
  if (step == kPlayerEpidemicRecoveryStepV1)
    return true;
  constexpr std::string_view prefix = kPlayerEpidemicRecoveryTitleStepPrefixV1;
  if (!step.starts_with(prefix) || step.size() == prefix.size())
    return false;
  const auto digits = step.substr(prefix.size());
  if (digits.size() > 10 || digits.front() == '0')
    return false;
  std::int64_t id = 0;
  for (char digit : digits) {
    if (digit < '0' || digit > '9')
      return false;
    id = id * 10 + (digit - '0');
    if (id > std::numeric_limits<std::int32_t>::max())
      return false;
  }
  if (id <= 0)
    return false;
  requested_title_id = static_cast<std::int32_t>(id);
  return true;
}

bool ReadEpidemicRecoveryListRowsV1(
    const void *context, std::int32_t list_identifier,
    std::vector<std::int32_t> &titles) {
  titles.clear();
  if (context == nullptr || list_identifier < 0)
    return false;
  const void *rows = nullptr;
  std::int32_t count = -1;
  if (!ReadAt(context, 0x30, rows) || !ReadAt(context, 0x3C, count) ||
      count < 0 || count > 16'384 || (count > 0 && rows == nullptr))
    return false;
  bool seen = false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *row = static_cast<const std::byte *>(rows) +
                      static_cast<std::size_t>(index) * 0x48;
    std::int32_t key = -1;
    if (!ReadAt(row, 0x08, key))
      return false;
    if (key != list_identifier)
      continue;
    if (seen)
      return false;
    seen = true;
    const void *elements = nullptr;
    std::int32_t size = -1;
    if (!ReadAt(row, 0x10, elements) || !ReadAt(row, 0x1C, size) ||
        size < 0 || size > 4096 || (size > 0 && elements == nullptr))
      return false;
    for (std::int32_t element = 0; element < size; ++element) {
      EventTarget16 target{};
      if (!ReadCurrent(static_cast<const std::byte *>(elements) +
                       static_cast<std::size_t>(element) * 0x10,
                       &target, sizeof(target)) ||
          target.kind != 5 || target.payload <= 0 ||
          target.payload > std::numeric_limits<std::int32_t>::max())
        return false;
      const auto full_id = static_cast<std::int32_t>(target.payload);
      if (std::find(titles.begin(), titles.end(), full_id) != titles.end())
        return false;
      titles.push_back(full_id);
    }
  }
  return true;
}

PlayerEpidemicRecoveryV1 ReadPlayerEpidemicRecoveryNativeV1(
    const Bindings &bindings,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    std::uint64_t revision, std::int32_t date_raw,
    std::int32_t played_character_id,
    std::int32_t requested_title_id) noexcept {
  try {
    if (!environment.exact_build_admitted || environment.module_base == 0 ||
        environment.offline_fixture_function_overrides || revision == 0 ||
        played_character_id <= 0 || requested_title_id < 0 ||
        bindings.character_storage_slot == nullptr)
      return Unavailable(revision, date_raw, played_character_id,
                         requested_title_id, "exact_build_or_frame_unavailable");
    const auto module = environment.module_base;
    if (!VerifyPlayedCharacter(bindings, played_character_id))
      return Unavailable(revision, date_raw, played_character_id,
                         requested_title_id, "played_character_unavailable");
    std::vector<std::int32_t> titles;
    if (requested_title_id == 0) {
      const EventTarget16 character_scope{4, 0, 0, played_character_id};
      void *context = reinterpret_cast<VariableContextForScope>(
          module + kVariableContextForScopeRva)(&character_scope);
      if (context == nullptr)
        return Unavailable(revision, date_raw, played_character_id,
                           requested_title_id, "variable_context_unavailable");
      std::int32_t identifier = -1;
      if (!ResolveIdentifier(module, kPlayerEpidemicRecoveryListKeyV1,
                             identifier) ||
          !ReadEpidemicRecoveryListRowsV1(context, identifier, titles))
        return Unavailable(revision, date_raw, played_character_id,
                           requested_title_id, "variable_list_unavailable");
    } else {
      titles.push_back(requested_title_id);
    }
    void *database = reinterpret_cast<GetModifierDatabase>(
        module + kModifierDatabaseRva)();
    void *fallback = nullptr;
    void *minor = nullptr;
    void *tiny = nullptr;
    if (database == nullptr ||
        !ReadCurrent(reinterpret_cast<const void *>(module +
                     kModifierFallbackSlotRva), &fallback, sizeof(fallback)) ||
        !ResolveModifier(module, database, fallback,
                         kPlayerEpidemicRecoveryMinorKeyV1, minor) ||
        !ResolveModifier(module, database, fallback,
                         kPlayerEpidemicRecoveryTinyKeyV1, tiny))
      return Unavailable(revision, date_raw, played_character_id,
                         requested_title_id, "modifier_definition_unavailable");
    PlayerEpidemicRecoveryV1 result{};
    result.snapshot_revision = revision;
    result.date_raw = date_raw;
    result.played_character_id = played_character_id;
    result.requested_title_id = requested_title_id;
    for (auto title_id : titles) {
      void *title = nullptr;
      if (!ResolveTitle(module, title_id, title) || !IsCountyTitle(title))
        return Unavailable(revision, date_raw, played_character_id,
                           requested_title_id, "landed_title_unavailable");
      PlayerEpidemicRecoveryCountyV1 county{};
      county.landed_title_id = title_id;
      if (!ReadCountyPresence(module, title, minor, county.minor_present) ||
          !ReadCountyPresence(module, title, tiny, county.tiny_present))
        return Unavailable(revision, date_raw, played_character_id,
                           requested_title_id, "county_modifier_unavailable");
      result.counties.push_back(county);
    }
    result.available = true;
    return result;
  } catch (...) {
    return Unavailable(revision, date_raw, played_character_id,
                       requested_title_id, "internal_error");
  }
}

std::string SerializePlayerEpidemicRecoveryV1(
    const PlayerEpidemicRecoveryV1 &value) {
  if (value.snapshot_revision == 0 || value.played_character_id <= 0 ||
      value.requested_title_id < 0 ||
      (value.available && !value.unavailable_reason.empty()) ||
      (!value.available && value.unavailable_reason.empty()) ||
      (value.requested_title_id > 0 && value.available &&
       (value.counties.size() != 1 ||
        value.counties.front().landed_title_id != value.requested_title_id)))
    return {};
  std::string json =
      "{\"schema\":\"player-epidemic-recovery-v1\",\"schema_version\":1";
  json += ",\"snapshot_revision\":" +
          std::to_string(value.snapshot_revision);
  json += ",\"date_raw\":" + std::to_string(value.date_raw);
  json += ",\"played_character_id\":" +
          std::to_string(value.played_character_id);
  json += ",\"list_key\":\"";
  json += kPlayerEpidemicRecoveryListKeyV1;
  json += "\",\"requested_title_id\":" +
          std::to_string(value.requested_title_id);
  json += ",\"status\":\"";
  json += value.available ? "available" : "unavailable";
  json += "\",\"counties\":";
  if (!value.available) {
    json += "null";
  } else {
    json += '[';
    for (std::size_t i = 0; i < value.counties.size(); ++i) {
      if (i != 0) json += ',';
      const auto &county = value.counties[i];
      if (county.landed_title_id <= 0) return {};
      json += "{\"landed_title_id\":" +
              std::to_string(county.landed_title_id);
      json += ",\"minor_present\":";
      json += county.minor_present ? "true" : "false";
      json += ",\"tiny_present\":";
      json += county.tiny_present ? "true" : "false";
      json += '}';
    }
    json += ']';
  }
  json += ",\"remaining_days\":{\"status\":\"unavailable\",";
  json += "\"value\":null,\"unavailable_reason\":\"duration_abi_not_verified\"}";
  json += ",\"unavailable_reason\":";
  if (value.available) json += "null";
  else json += "\"" + value.unavailable_reason + "\"";
  json += '}';
  return json;
}

} // namespace xar::ck3_11906

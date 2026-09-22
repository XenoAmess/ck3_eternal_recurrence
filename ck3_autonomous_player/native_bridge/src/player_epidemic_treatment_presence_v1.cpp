#include "xar_bridge/player_epidemic_treatment_presence_v1.hpp"

#include <windows.h>

#include <cstddef>
#include <cstdint>
#include <string>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kModifierDatabaseRva = 0x88F370;
constexpr std::uintptr_t kStableKeyHashRva = 0x3B8B000;
constexpr std::uintptr_t kModifierLookupRva = 0xA41F10;
constexpr std::uintptr_t kModifierFallbackSlotRva = 0x570C968;

using GetDatabase = void *(*)();
using HashStableKey = std::int32_t (*)(void *, const char *, std::uint32_t);
using LookupModifier = void *(*)(void *, std::int32_t);

bool ReadCurrent(const void *address, void *out, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != nullptr && out != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(), address, out, size, &read) !=
             FALSE &&
         read == size;
}

bool ReadStableKey(const void *definition, std::string &key) {
  const auto *storage = static_cast<const std::byte *>(definition) + 0x18;
  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!ReadCurrent(storage + 0x10, &size, sizeof(size)) ||
      !ReadCurrent(storage + 0x18, &capacity, sizeof(capacity)) ||
      size > 128 || capacity < size) {
    return false;
  }
  const void *data = storage;
  if (capacity >= 16 && !ReadCurrent(storage, &data, sizeof(data)))
    return false;
  key.resize(size);
  return size == 0 || ReadCurrent(data, key.data(), size);
}

bool ResolvePlayedCharacter(const Bindings &bindings, std::int32_t id,
                            void *&character) noexcept {
  character = nullptr;
  if (id <= 0 || bindings.character_storage_slot == nullptr)
    return false;
  void *storage = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadCurrent(bindings.character_storage_slot, &storage, sizeof(storage)) ||
      storage == nullptr ||
      !ReadCurrent(static_cast<const std::byte *>(storage) + 0x20, &slots,
                   sizeof(slots)) ||
      slots == nullptr ||
      !ReadCurrent(static_cast<const std::byte *>(storage) + 0x2C, &capacity,
                   sizeof(capacity)) ||
      capacity <= 0)
    return false;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity))
    return false;
  const auto *slot = static_cast<const std::byte *>(slots) +
                     static_cast<std::size_t>(index) * 0x10 + 0x08;
  std::int32_t round_trip = -1;
  if (!ReadCurrent(slot, &character, sizeof(character)) ||
      character == nullptr ||
      !ReadCurrent(static_cast<const std::byte *>(character) + 0x18,
                   &round_trip, sizeof(round_trip)) ||
      round_trip != id) {
    character = nullptr;
    return false;
  }
  return true;
}

PlayerEpidemicTreatmentPresenceV1 Unavailable(std::uint64_t revision,
                                               std::int32_t date,
                                               std::int32_t character,
                                               const char *reason) {
  PlayerEpidemicTreatmentPresenceV1 result{};
  result.snapshot_revision = revision;
  result.date_raw = date;
  result.played_character_id = character;
  result.unavailable_reason = reason;
  return result;
}

} // namespace

bool ScanPlayerModifierRowsV1(const void *extension, const void *definition,
                              bool &present) noexcept {
  present = false;
  if (definition == nullptr)
    return false;
  if (extension == nullptr)
    return true;
  void *rows = nullptr;
  std::int32_t count = -1;
  if (!ReadCurrent(static_cast<const std::byte *>(extension) + 0x188, &rows,
                   sizeof(rows)) ||
      !ReadCurrent(static_cast<const std::byte *>(extension) + 0x194, &count,
                   sizeof(count)) ||
      count < 0 || count > 16'384 || (count > 0 && rows == nullptr)) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *row = static_cast<const std::byte *>(rows) +
                      static_cast<std::size_t>(index) * 0x48;
    void *row_definition = nullptr;
    if (!ReadCurrent(row, &row_definition, sizeof(row_definition)))
      return false;
    if (row_definition == definition)
      present = true;
  }
  return true;
}

PlayerEpidemicTreatmentPresenceV1 ReadPlayerEpidemicTreatmentPresenceNativeV1(
    const Bindings &bindings,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    std::uint64_t revision, std::int32_t date_raw,
    std::int32_t played_character_id) noexcept {
  try {
    if (!environment.exact_build_admitted || environment.module_base == 0 ||
        environment.offline_fixture_function_overrides || revision == 0 ||
        played_character_id <= 0) {
      return Unavailable(revision, date_raw, played_character_id,
                         "exact_build_or_frame_unavailable");
    }
    void *character = nullptr;
    if (!ResolvePlayedCharacter(bindings, played_character_id, character)) {
      return Unavailable(revision, date_raw, played_character_id,
                         "played_character_unavailable");
    }
    const auto module = environment.module_base;
    void *database = reinterpret_cast<GetDatabase>(module + kModifierDatabaseRva)();
    void *fallback = nullptr;
    if (database == nullptr ||
        !ReadCurrent(reinterpret_cast<const void *>(module +
                        kModifierFallbackSlotRva),
                     &fallback, sizeof(fallback))) {
      return Unavailable(revision, date_raw, played_character_id,
                         "modifier_database_unavailable");
    }
    const auto key = kPlayerEpidemicTreatmentModifierKeyV1;
    const auto hash = reinterpret_cast<HashStableKey>(
        module + kStableKeyHashRva)(database, key.data(),
                                   static_cast<std::uint32_t>(key.size()));
    void *definition = reinterpret_cast<LookupModifier>(
        module + kModifierLookupRva)(database, hash);
    std::string actual_key;
    if (definition == nullptr || definition == fallback ||
        !ReadStableKey(definition, actual_key) || actual_key != key) {
      return Unavailable(revision, date_raw, played_character_id,
                         "modifier_definition_unavailable");
    }
    void *extension = nullptr;
    if (!ReadCurrent(static_cast<const std::byte *>(character) + 0x1A8,
                     &extension, sizeof(extension))) {
      return Unavailable(revision, date_raw, played_character_id,
                         "modifier_extension_unavailable");
    }
    bool present = false;
    if (!ScanPlayerModifierRowsV1(extension, definition, present)) {
      return Unavailable(revision, date_raw, played_character_id,
                         "modifier_rows_unavailable");
    }
    PlayerEpidemicTreatmentPresenceV1 result{};
    result.snapshot_revision = revision;
    result.date_raw = date_raw;
    result.played_character_id = played_character_id;
    result.available = true;
    result.present = present;
    return result;
  } catch (...) {
    return Unavailable(revision, date_raw, played_character_id,
                       "internal_error");
  }
}

std::string SerializePlayerEpidemicTreatmentPresenceV1(
    const PlayerEpidemicTreatmentPresenceV1 &value) {
  if (value.snapshot_revision == 0 || value.played_character_id <= 0 ||
      (value.available && !value.unavailable_reason.empty()) ||
      (!value.available && value.unavailable_reason.empty()))
    return {};
  std::string json =
      "{\"schema\":\"player-epidemic-treatment-presence-v1\",";
  json += "\"schema_version\":1,\"modifier_key\":\"";
  json += kPlayerEpidemicTreatmentModifierKeyV1;
  json += "\",\"snapshot_revision\":" +
          std::to_string(value.snapshot_revision);
  json += ",\"date_raw\":" + std::to_string(value.date_raw);
  json += ",\"played_character_id\":" +
          std::to_string(value.played_character_id);
  json += ",\"status\":\"";
  json += value.available ? "available" : "unavailable";
  json += "\",\"present\":";
  json += value.available ? (value.present ? "true" : "false") : "null";
  json += ",\"remaining_days\":{\"status\":\"unavailable\",";
  json += "\"value\":null,\"unavailable_reason\":\"duration_abi_not_verified\"},";
  json += "\"unavailable_reason\":";
  if (value.available) {
    json += "null";
  } else {
    json += "\"" + value.unavailable_reason + "\"";
  }
  json += '}';
  return json;
}

} // namespace xar::ck3_11906

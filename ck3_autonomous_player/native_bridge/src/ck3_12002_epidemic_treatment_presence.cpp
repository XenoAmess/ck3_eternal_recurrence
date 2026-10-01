#include "xar_bridge/ck3_12002_epidemic_treatment_presence.hpp"

#include <windows.h>

#include <bit>
#include <cstddef>
#include <cstdint>
#include <string>

namespace xar::ck3_12002 {
namespace {

bool ReadCurrent(const void *address, void *output, std::size_t size) noexcept {
  SIZE_T copied = 0;
  return address != nullptr && output != nullptr && size != 0 &&
      ReadProcessMemory(GetCurrentProcess(), address, output, size, &copied) != FALSE &&
      copied == size;
}

bool ReadDefinitionKey(const void *definition, std::string &key) {
  const auto *text = static_cast<const std::byte *>(definition) +
      kTreatmentModifierDefinitionKeyOffset12002;
  std::size_t size = 0, capacity = 0;
  if (!ReadCurrent(text + 0x10, &size, sizeof(size)) ||
      !ReadCurrent(text + 0x18, &capacity, sizeof(capacity)) ||
      size > 128 || capacity < size) return false;
  const void *characters = text;
  if (capacity >= 16 && !ReadCurrent(text, &characters, sizeof(characters)))
    return false;
  key.resize(size);
  return size == 0 || ReadCurrent(characters, key.data(), size);
}

ck3_11906::PlayerEpidemicTreatmentPresenceV1 Unavailable(
    std::uint64_t revision, std::int32_t date, std::int32_t actor,
    const char *reason) {
  ck3_11906::PlayerEpidemicTreatmentPresenceV1 result{};
  result.snapshot_revision = revision;
  result.date_raw = date;
  result.played_character_id = actor;
  result.unavailable_reason = reason;
  return result;
}

bool SameCoreFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}

} // namespace

TreatmentPresenceBindings12002 BindTreatmentPresenceImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  TreatmentPresenceBindings12002 result{};
  if (module_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.core = BindCoreImage(module_base, executable_sha256);
  result.get_modifier_database = reinterpret_cast<TreatmentModifierDatabaseGetter12002>(
      module_base + kTreatmentModifierDatabaseRva12002);
  result.hash_stable_key = reinterpret_cast<TreatmentModifierKeyHash12002>(
      module_base + kTreatmentStableKeyHashRva12002);
  result.lookup_modifier = reinterpret_cast<TreatmentModifierLookup12002>(
      module_base + kTreatmentModifierLookupRva12002);
  result.fallback_definition_slot = reinterpret_cast<void **>(
      module_base + kTreatmentModifierFallbackSlotRva12002);
  result.enabled = result.core.enabled;
  return result;
}

bool ScanTreatmentModifierRows12002(const void *extension, const void *definition,
                                   bool &present) noexcept {
  present = false;
  if (definition == nullptr) return false;
  if (extension == nullptr) return true;
  const auto *object = static_cast<const std::byte *>(extension);
  const void *rows = nullptr;
  std::int32_t count = -1;
  if (!ReadCurrent(object + kTreatmentModifierRowsOffset12002, &rows, sizeof(rows)) ||
      !ReadCurrent(object + kTreatmentModifierCountOffset12002, &count, sizeof(count)) ||
      count < 0 || count > 16'384 || (count > 0 && rows == nullptr)) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *row = static_cast<const std::byte *>(rows) +
        static_cast<std::size_t>(index) * kTreatmentModifierRowStride12002;
    const void *row_definition = nullptr;
    if (!ReadCurrent(row + kTreatmentModifierRowDefinitionOffset12002,
                     &row_definition, sizeof(row_definition))) return false;
    if (row_definition == definition) present = true;
  }
  return true;
}

ck3_11906::PlayerEpidemicTreatmentPresenceV1 ReadPlayerEpidemicTreatmentPresence12002(
    const TreatmentPresenceBindings12002 &bindings,
    std::uint64_t snapshot_revision, std::int32_t date_raw,
    std::int32_t played_character_id) noexcept {
  try {
    if (!bindings.enabled || !bindings.core.enabled || snapshot_revision == 0 ||
        played_character_id <= 0 || !bindings.get_modifier_database ||
        !bindings.hash_stable_key || !bindings.lookup_modifier ||
        !bindings.fallback_definition_slot)
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "exact_build_or_frame_unavailable");
    CoreSnapshotPrefix before{};
    if (!ReadCoreSnapshot(bindings.core, before) || !before.map_ready ||
        !before.has_played_character || !before.played_character_alive)
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "played_character_unavailable");
    if (!before.clock.paused)
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "frame_not_paused");
    if (before.clock.date_raw != date_raw || before.played_character_id != played_character_id)
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "frame_binding_unavailable");
    void *character = ResolveCoreCharacter(bindings.core, before.played_character_id);
    if (character == nullptr)
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "played_character_unavailable");
    void *database = bindings.get_modifier_database();
    void *fallback = nullptr;
    if (database == nullptr ||
        !ReadCurrent(bindings.fallback_definition_slot, &fallback, sizeof(fallback)))
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "modifier_database_unavailable");
    constexpr auto key = ck3_11906::kPlayerEpidemicTreatmentModifierKeyV1;
    const auto hash = bindings.hash_stable_key(database, key.data(),
                                              static_cast<std::uint32_t>(key.size()));
    void *definition = bindings.lookup_modifier(database, std::bit_cast<std::int32_t>(hash));
    std::string actual_key;
    if (definition == nullptr || definition == fallback ||
        !ReadDefinitionKey(definition, actual_key) || actual_key != key)
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "modifier_definition_unavailable");
    void *extension = nullptr;
    if (!ReadCurrent(static_cast<const std::byte *>(character) +
                         kTreatmentCharacterExtensionOffset12002,
                     &extension, sizeof(extension)))
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "modifier_extension_unavailable");
    bool present = false;
    if (!ScanTreatmentModifierRows12002(extension, definition, present))
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "modifier_rows_unavailable");
    CoreSnapshotPrefix after{};
    if (!ReadCoreSnapshot(bindings.core, after) || !SameCoreFrame(before, after))
      return Unavailable(snapshot_revision, date_raw, played_character_id,
                         "frame_changed");
    ck3_11906::PlayerEpidemicTreatmentPresenceV1 result{};
    result.snapshot_revision = snapshot_revision;
    result.date_raw = date_raw;
    result.played_character_id = played_character_id;
    result.available = true;
    result.present = present;
    return result;
  } catch (...) {
    return Unavailable(snapshot_revision, date_raw, played_character_id,
                       "internal_error");
  }
}

} // namespace xar::ck3_12002

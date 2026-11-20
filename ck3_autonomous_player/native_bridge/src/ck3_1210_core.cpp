#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210.hpp"

#include <windows.h>
#include <cstring>

namespace xar::ck3_1210 {
namespace {
template <typename T>
T LoadAt(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

void *ResolveCharacter(void *storage, std::int32_t id) noexcept {
  if (storage == nullptr || id == -1) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  const auto capacity = LoadAt<std::int32_t>(storage, kCharacterStorageCapacityOffset);
  const auto slots = LoadAt<void *>(storage, kCharacterStorageSlotsOffset);
  if (slots == nullptr || capacity <= 0 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const auto character = LoadAt<void *>(slots,
      index * kCharacterStorageSlotStride + kCharacterStorageObjectOffset);
  return character != nullptr &&
                 LoadAt<std::int32_t>(character, kCharacterFullIdOffset) == id
             ? character : nullptr;
}
} // namespace

CoreBindings BindCoreImage(std::uintptr_t image_base,
                           std::string_view executable_sha256) noexcept {
  CoreBindings result{};
  const auto build=BasicFullImageBuildForSha(executable_sha256);
  if (image_base == 0 || build==ImageBuildV1::unknown) return result;
  result.image_build=build;
  result.enabled = true;
  result.game_state_slot = reinterpret_cast<void **>(image_base + ImageRva(build,kGameStateSlotRva,hotfix26757580::kGameStateSlotRva));
  result.jomini_state_slot = reinterpret_cast<void **>(image_base + ImageRva(build,kJominiStateSlotRva,hotfix26757580::kJominiStateSlotRva));
  result.character_storage_slot = reinterpret_cast<void **>(image_base + ImageRva(build,kCharacterStorageSlotRva,hotfix26757580::kCharacterStorageSlotRva));
  result.get_local_player = reinterpret_cast<GetLocalPlayer>(
      image_base + ImageRva(build,kGetLocalPlayerRva,hotfix26757580::kGetLocalPlayerRva));
  return result;
}

void *ResolveCoreCharacter(const CoreBindings &bindings,
                           std::int32_t character_id) noexcept {
  if (!bindings.enabled || bindings.character_storage_slot == nullptr) return nullptr;
  return ResolveCharacter(*bindings.character_storage_slot, character_id);
}

bool ReadCoreSnapshot(const CoreBindings &bindings,
                      CoreSnapshotPrefix &output) noexcept {
  output = {};
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr) return false;
  const auto game_state = *bindings.game_state_slot;
  const auto jomini_state = *bindings.jomini_state_slot;
  if (game_state == nullptr || jomini_state == nullptr) return false;
  const auto players = LoadAt<void *>(jomini_state, kJominiPlayersOffset);
  if (players == nullptr ||
      !ck3_1210::DecodeClockPrefix({static_cast<const std::byte *>(game_state), 0x74},
                         {static_cast<const std::byte *>(jomini_state), 0x21},
                         output.clock)) return false;
  output.local_player_id = LoadAt<std::int32_t>(players, kPlayersLocalPlayerIdOffset);
  const auto player = bindings.get_local_player != nullptr
                          ? bindings.get_local_player(jomini_state) : nullptr;
  // Preserve the native readiness operand; Python's exact-source clock route
  // reads this expression independently of a complete gameplay snapshot.
  output.map_ready = player != nullptr && LoadAt<std::int32_t>(player, 0x70) >= 0;
  if (!output.map_ready || output.local_player_id < 0 ||
      bindings.character_storage_slot == nullptr) return true;
  const auto data = LoadAt<void *>(game_state, kGameStateDataOffset);
  if (data == nullptr) return true;
  const auto manager = static_cast<const std::byte *>(data) + kPlayerCharacterManagerOffset;
  const auto entries = LoadAt<void *>(manager, kPlayerManagerEntriesOffset);
  const auto count = LoadAt<std::int32_t>(manager, kPlayerManagerCountOffset);
  if (entries == nullptr || count <= 0 || count > 1024) return true;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto entry = LoadAt<void *>(entries,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (entry == nullptr ||
        LoadAt<std::int32_t>(entry, kPlayerEntryLocalPlayerIdOffset) !=
            output.local_player_id) continue;
    const auto id = LoadAt<std::int32_t>(entry, kPlayerEntryCharacterIdOffset);
    const auto character = ResolveCharacter(*bindings.character_storage_slot, id);
    if (character == nullptr) continue;
    output.has_played_character = true;
    output.played_character_id = id;
    output.played_character_alive =
        LoadAt<void *>(character, kCharacterDeathDataOffset) == nullptr;
    break;
  }
  return true;
}

bool DecodeClockPrefix(std::span<const std::byte> game_state,
                       std::span<const std::byte> jomini_state,
                       ClockPrefix &output) noexcept {
  output = {};
  if (game_state.size() < 0x74 || jomini_state.size() < 0x21) return false;
  std::int32_t native_speed = 0;
  std::memcpy(&native_speed, game_state.data() + 0x70, sizeof(native_speed));
  if (native_speed < 0 || native_speed > 4) return false;
  std::memcpy(&output.date_raw, game_state.data() + 0x08,
              sizeof(output.date_raw));
  output.speed = native_speed + 1;
  output.paused = jomini_state[0x20] != std::byte{};
  return true;
}
} // namespace xar::ck3_1210

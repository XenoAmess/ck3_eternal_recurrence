#pragma once

#include "xar_bridge/ck3_12004_adapter.hpp"

#include <array>
#include <cstring>
#include <vector>

namespace xar::ck3_12004::fixture {

// Caller-owned objects only. Offsets are the reached .4 reader operands from
// CORE-LAYOUT-OPERAND-PAIRS.json; the native getter is replaced by a fixture
// callback. No game module, process discovery, command or full Snapshot read.
class CoreMemory {
public:
  static constexpr std::int32_t kCharacterId = 29829;
  static constexpr std::int32_t kLocalPlayerId = 0;

  explicit CoreMemory(std::int32_t date_raw = 45000000,
                      std::int32_t native_speed = 4,
                      bool paused = true)
      : data_(kPlayerCharacterManagerOffset + kPlayerManagerCountOffset + 4),
        rows_((static_cast<std::size_t>(kCharacterId) + 1) *
              kCharacterStorageSlotStride) {
    game_slot_ = game_.data();
    jomini_slot_ = jomini_.data();
    storage_slot_ = storage_.data();
    Store(game_.data(), kGameStateDataOffset, data_.data());
    Store(jomini_.data(), kJominiPlayersOffset, players_.data());
    // Offset zero is fixture-owned callback context, never a native claim.
    Store(jomini_.data(), 0, player_.data());
    SetClock(date_raw, native_speed, paused);
    Store(players_.data(), kPlayersLocalPlayerIdOffset, kLocalPlayerId);
    Store(player_.data(), kPlayerIdOffset, kLocalPlayerId);
    entries_[0] = entry_.data();
    auto *manager = data_.data() + kPlayerCharacterManagerOffset;
    Store(manager, kPlayerManagerEntriesOffset, entries_.data());
    Store(manager, kPlayerManagerCountOffset, std::int32_t{1});
    SetEntryPlayerId(kLocalPlayerId);
    Store(entry_.data(), kPlayerEntryCharacterIdOffset, kCharacterId);
    Store(storage_.data(), kCharacterStorageSlotsOffset, rows_.data());
    Store(storage_.data(), kCharacterStorageCapacityOffset, kCharacterId + 1);
    Store(rows_.data(), static_cast<std::size_t>(kCharacterId) *
        kCharacterStorageSlotStride + kCharacterStorageObjectOffset,
        character_.data());
    SetCharacterFullId(kCharacterId);
  }

  CoreMemory(const CoreMemory &) = delete;
  CoreMemory &operator=(const CoreMemory &) = delete;
  CoreMemory(CoreMemory &&) = delete;
  CoreMemory &operator=(CoreMemory &&) = delete;

  CoreBindings Bindings() noexcept {
    return {true, &game_slot_, &jomini_slot_, &storage_slot_, GetLocalPlayer};
  }

  game::Ck3_12004AdapterBindings AdapterBindings() noexcept {
    game::Ck3_12004AdapterBindings result{};
    result.core = Bindings();
    result.read_core_snapshot = ReadCoreSnapshot;
    return result;
  }

  void SetClock(std::int32_t date_raw, std::int32_t native_speed,
                bool paused) noexcept {
    Store(game_.data(), kGameStateDateOffset, date_raw);
    Store(game_.data(), kGameStateSpeedOffset, native_speed);
    Store(jomini_.data(), kJominiPausedOffset, std::uint8_t(paused));
  }

  void SetMenu() noexcept {
    Store(players_.data(), kPlayersLocalPlayerIdOffset, std::int32_t{-1});
    Store(player_.data(), kPlayerIdOffset, std::int32_t{-1});
  }

  void SetEntryPlayerId(std::int32_t id) noexcept {
    Store(entry_.data(), kPlayerEntryLocalPlayerIdOffset, id);
  }

  void SetCharacterFullId(std::int32_t id) noexcept {
    Store(character_.data(), kCharacterFullIdOffset, id);
  }

  // The fixture row remains low24=29829; vary its generation-bearing full ID.
  void SetPlayingCharacterFullId(std::int32_t id) noexcept {
    Store(entry_.data(), kPlayerEntryCharacterIdOffset, id);
    SetCharacterFullId(id);
  }

  void SetCharacterDead(bool dead) noexcept {
    Store(character_.data(), kCharacterDeathDataOffset,
          dead ? static_cast<void *>(entry_.data()) : nullptr);
  }

private:
  template <typename T>
  static void Store(void *object, std::size_t offset, const T &value) noexcept {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
  }

  static void *GetLocalPlayer(void *jomini_state) noexcept {
    void *player = nullptr;
    std::memcpy(&player, jomini_state, sizeof(player));
    return player;
  }

  std::array<std::byte, kGameStateDataOffset + sizeof(void *)> game_{};
  std::array<std::byte, kJominiPausedOffset + 1> jomini_{};
  std::array<std::byte, kPlayersLocalPlayerIdOffset + sizeof(std::int32_t)> players_{};
  std::array<std::byte, kPlayerIdOffset + sizeof(std::int32_t)> player_{};
  std::vector<std::byte> data_;
  std::array<std::byte, kPlayerEntryLocalPlayerIdOffset + sizeof(std::int32_t)> entry_{};
  std::array<void *, 1> entries_{};
  std::array<std::byte, kCharacterDeathDataOffset + sizeof(void *)> character_{};
  std::array<std::byte, kCharacterStorageCapacityOffset + sizeof(std::int32_t)> storage_{};
  std::vector<std::byte> rows_;
  void *game_slot_ = nullptr;
  void *jomini_slot_ = nullptr;
  void *storage_slot_ = nullptr;
};

} // namespace xar::ck3_12004::fixture

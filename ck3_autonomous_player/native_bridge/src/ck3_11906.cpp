#include "xar_bridge/ck3_11906.hpp"

#include <windows.h>
#include <bcrypt.h>

#include <array>
#include <cstddef>
#include <cstring>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kGameStateSlotRva = 0x570E068;
constexpr std::uintptr_t kJominiStateSlotRva = 0x570F7B8;
constexpr std::uintptr_t kCommandManagerRva = 0x57621F0;
constexpr std::uintptr_t kPausePrimaryVtableRva = 0x432F1C8;
constexpr std::uintptr_t kPauseSecondaryVtableRva = 0x432F198;
constexpr std::uintptr_t kSetSpeedPrimaryVtableRva = 0x432F3F0;
constexpr std::uintptr_t kSetSpeedSecondaryVtableRva = 0x432F260;
constexpr std::uintptr_t kSelectEventOptionPrimaryVtableRva = 0x4335240;
constexpr std::uintptr_t kSelectEventOptionSecondaryVtableRva = 0x4335210;
constexpr std::uintptr_t kAutoSavePrimaryVtableRva = 0x40AABE8;
constexpr std::uintptr_t kAutoSaveSecondaryVtableRva = 0x40AAC80;
constexpr std::uintptr_t kReplyCharacterInteractionPrimaryVtableRva =
    0x4082930;
constexpr std::uintptr_t kReplyCharacterInteractionSecondaryVtableRva =
    0x4082900;
constexpr std::uintptr_t kPendingCharacterInteractionStorageSlotRva =
    0x57BF1C8;
constexpr std::uintptr_t kCharacterStorageSlotRva = 0x570C130;
constexpr std::uintptr_t kArmyStorageSlotRva = 0x572CC80;
constexpr std::uintptr_t kRaiseTroopsPrimaryVtableRva = 0x41226D8;
constexpr std::uintptr_t kRaiseTroopsSecondaryVtableRva = 0x41226A8;
constexpr std::uintptr_t kMoveArmyPrimaryVtableRva = 0x432BF18;
constexpr std::uintptr_t kMoveArmySecondaryVtableRva = 0x432BFB0;
constexpr std::uintptr_t kDisbandArmyPrimaryVtableRva = 0x432BFE0;
constexpr std::uintptr_t kDisbandArmySecondaryVtableRva = 0x432C078;
constexpr std::uintptr_t kSubmitCommandRva = 0x0973E00;
constexpr std::uintptr_t kGetLocalPlayerRva = 0x346B7C0;
constexpr std::uintptr_t kGetCurrentEventRva = 0x2706AD0;
constexpr std::uintptr_t kContainsWarParticipantRva = 0x2224870;
constexpr std::uintptr_t kGetWarScoreRva = 0x222A8A0;
constexpr std::uintptr_t kResolveDefaultRaiseProvinceRva = 0x224CC80;
constexpr std::uintptr_t kConstructRaiseTroopsCommandRva = 0x26D6FC0;
constexpr std::uintptr_t kValidateRaiseTroopsCommandRva = 0x26D7150;
constexpr std::uintptr_t kDestroyRaiseTroopsCommandRva = 0x10E7950;
constexpr std::uintptr_t kGetArmyMoveModeRva = 0x26B51B0;
constexpr std::uintptr_t kCanMoveArmyRva = 0x26B4610;
constexpr std::uintptr_t kInitializeArmyMovePathRva = 0x0C7BA70;
constexpr std::uintptr_t kDestroyMoveArmyCommandRva = 0x26B46D0;

constexpr std::size_t kGameStateDateOffset = 0x08;
constexpr std::size_t kGameStateSpeedOffset = 0x70;
constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kJominiPlayersOffset = 0x18;
constexpr std::size_t kJominiPausedOffset = 0x20;
constexpr std::size_t kPlayersLocalIdOffset = 0x1F0;
constexpr std::size_t kPlayerIdOffset = 0x70;
constexpr std::size_t kEventManagerOffset = 0x2F4C0;
constexpr std::size_t kPlayerCharacterManagerOffset = 0x1D4F0;
constexpr std::size_t kWarManagerOffset = 0x29C20;
constexpr std::size_t kActiveEventDataOffset = 0x1B0;
constexpr std::size_t kActiveEventInstanceIdOffset = 0x1BC;
constexpr std::size_t kEventDataOptionCountOffset = 0x1BC;
constexpr std::size_t kComponentStorageSlotsOffset = 0x20;
constexpr std::size_t kComponentStorageCapacityOffset = 0x2C;
constexpr std::size_t kComponentStorageSlotSize = 0x10;
constexpr std::size_t kComponentStorageSlotObjectOffset = 0x08;
constexpr std::size_t kPendingInteractionIdOffset = 0x10;
constexpr std::size_t kPendingInteractionSenderIdOffset = 0x2F0;
constexpr std::size_t kPendingInteractionAutoAcceptOffset = 0x5C6;
constexpr std::size_t kPlayerCharacterEntriesOffset = 0x58;
constexpr std::size_t kPlayerCharacterEntryCountOffset = 0x64;
constexpr std::size_t kPlayerCharacterIdOffset = 0xB0;
constexpr std::size_t kPlayerCharacterPlayerIdOffset = 0xD8;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterDeathDataOffset = 0x1C8;
constexpr std::size_t kWarStorageOffset = 0x20;
constexpr std::size_t kWarIdOffset = 0x08;
constexpr std::size_t kWarAttackersOffset = 0x20;
constexpr std::size_t kWarDefendersOffset = 0x80;
constexpr std::size_t kWarEndedDataOffset = 0x358;
constexpr std::size_t kArmyIdOffset = 0x10;
constexpr std::size_t kArmyCurrentProvinceOffset = 0x20;
constexpr std::size_t kArmyOwnerCharacterIdOffset = 0x174;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::int32_t kMaximumPlayerCharacterEntries = 1024;
constexpr std::int32_t kMaximumComponentCapacity = 1'000'000;

struct PauseCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t player_id = -1;
  std::uint8_t paused = 0;
  std::array<std::byte, 3> payload_padding{};
};

struct SetSpeedCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t speed = 0;
  std::array<std::byte, 4> payload_padding{};
};

struct SelectEventOptionCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t event_instance_id = -1;
  std::int32_t option_index = -1;
};

struct InlineCk3String {
  std::array<char, 16> buffer{};
  std::uint64_t size = 0;
  std::uint64_t capacity = 15;
};

struct AutoSaveCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  InlineCk3String save_name{};
};

struct ReplyCharacterInteractionCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t pending_interaction_id = -1;
  std::int32_t reply = 0;
};

struct alignas(16) RaiseTroopsCommandStorage {
  std::array<std::byte, 0x50> bytes{};
};

struct RaiseEntry {
  std::int32_t province_id = -1;
  std::int32_t regiment_id = -1;
};

struct MoveArmyCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t command_kind = 2;
  std::int32_t army_id = -1;
  std::int32_t destination_province_id = -1;
  std::int32_t move_mode = 0;
  std::int32_t route_kind = 2;
  std::int32_t direct_target = 1;
  std::array<std::byte, 0x130> path_storage{};
};

struct DisbandArmyCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t command_kind = 2;
  std::int32_t army_id = -1;
};

static_assert(sizeof(PauseCommand) == 0x28);
static_assert(offsetof(PauseCommand, secondary_vtable) == 0x18);
static_assert(offsetof(PauseCommand, player_id) == 0x20);
static_assert(offsetof(PauseCommand, paused) == 0x24);
static_assert(sizeof(SetSpeedCommand) == 0x28);
static_assert(offsetof(SetSpeedCommand, secondary_vtable) == 0x18);
static_assert(offsetof(SetSpeedCommand, speed) == 0x20);
static_assert(sizeof(SelectEventOptionCommand) == 0x28);
static_assert(offsetof(SelectEventOptionCommand, secondary_vtable) == 0x18);
static_assert(offsetof(SelectEventOptionCommand, event_instance_id) == 0x20);
static_assert(offsetof(SelectEventOptionCommand, option_index) == 0x24);
static_assert(sizeof(InlineCk3String) == 0x20);
static_assert(offsetof(InlineCk3String, size) == 0x10);
static_assert(offsetof(InlineCk3String, capacity) == 0x18);
static_assert(sizeof(AutoSaveCommand) == 0x40);
static_assert(offsetof(AutoSaveCommand, secondary_vtable) == 0x18);
static_assert(offsetof(AutoSaveCommand, save_name) == 0x20);
static_assert(sizeof(ReplyCharacterInteractionCommand) == 0x28);
static_assert(offsetof(ReplyCharacterInteractionCommand, secondary_vtable) ==
              0x18);
static_assert(
    offsetof(ReplyCharacterInteractionCommand, pending_interaction_id) ==
    0x20);
static_assert(offsetof(ReplyCharacterInteractionCommand, reply) == 0x24);
static_assert(sizeof(RaiseTroopsCommandStorage) == 0x50);
static_assert(sizeof(RaiseEntry) == 0x08);
static_assert(sizeof(MoveArmyCommand) == 0x168);
static_assert(offsetof(MoveArmyCommand, secondary_vtable) == 0x18);
static_assert(offsetof(MoveArmyCommand, command_kind) == 0x20);
static_assert(offsetof(MoveArmyCommand, army_id) == 0x24);
static_assert(offsetof(MoveArmyCommand, destination_province_id) == 0x28);
static_assert(offsetof(MoveArmyCommand, move_mode) == 0x2C);
static_assert(offsetof(MoveArmyCommand, route_kind) == 0x30);
static_assert(offsetof(MoveArmyCommand, direct_target) == 0x34);
static_assert(offsetof(MoveArmyCommand, path_storage) == 0x38);
static_assert(sizeof(DisbandArmyCommand) == 0x28);
static_assert(offsetof(DisbandArmyCommand, secondary_vtable) == 0x18);
static_assert(offsetof(DisbandArmyCommand, command_kind) == 0x20);
static_assert(offsetof(DisbandArmyCommand, army_id) == 0x24);

template <typename Value>
Value LoadAt(const void *base, std::size_t offset) noexcept {
  Value result{};
  std::memcpy(&result, static_cast<const std::byte *>(base) + offset,
              sizeof(result));
  return result;
}

void *CurrentEvent(const Bindings &bindings, void *game_state) noexcept {
  if (bindings.get_current_event == nullptr || game_state == nullptr) {
    return nullptr;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  void *const event_manager =
      static_cast<std::byte *>(game_data) + bindings.event_manager_offset;
  return bindings.get_current_event(event_manager);
}

bool ReadCurrentEvent(const Bindings &bindings, void *game_state,
                      std::int32_t &instance_id,
                      std::int32_t &option_count) noexcept {
  void *const active_event = CurrentEvent(bindings, game_state);
  if (active_event == nullptr) {
    return false;
  }
  void *const event_data =
      LoadAt<void *>(active_event, kActiveEventDataOffset);
  if (event_data == nullptr) {
    return false;
  }
  instance_id =
      LoadAt<std::int32_t>(active_event, kActiveEventInstanceIdOffset);
  option_count =
      LoadAt<std::int32_t>(event_data, kEventDataOptionCountOffset);
  return instance_id > 0 && option_count >= 0;
}

bool ReadPendingCharacterInteraction(const Bindings &bindings,
                                     std::int32_t &instance_id,
                                     std::int32_t &sender_character_id,
                                     bool &auto_accept_notification) noexcept {
  if (bindings.pending_character_interaction_storage_slot == nullptr) {
    return false;
  }
  void *const storage =
      *bindings.pending_character_interaction_storage_slot;
  if (storage == nullptr) {
    return false;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0) {
    return false;
  }

  for (std::int32_t index = 0; index < capacity; ++index) {
    const auto slot_offset = static_cast<std::size_t>(index) *
                                 kComponentStorageSlotSize +
                             kComponentStorageSlotObjectOffset;
    void *const pending = LoadAt<void *>(slots, slot_offset);
    if (pending == nullptr) {
      continue;
    }
    const std::int32_t candidate_id =
        LoadAt<std::int32_t>(pending, kPendingInteractionIdOffset);
    if ((static_cast<std::uint32_t>(candidate_id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) {
      continue;
    }
    instance_id = candidate_id;
    sender_character_id = LoadAt<std::int32_t>(
        pending, kPendingInteractionSenderIdOffset);
    auto_accept_notification =
        LoadAt<std::uint8_t>(pending,
                             kPendingInteractionAutoAcceptOffset) != 0;
    return true;
  }
  return false;
}

void *ResolveCharacter(const Bindings &bindings,
                       std::int32_t character_id) noexcept {
  if (character_id == -1 || bindings.character_storage_slot == nullptr) {
    return nullptr;
  }
  void *const storage = *bindings.character_storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const std::uint32_t index =
      static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  const auto slot_offset = static_cast<std::size_t>(index) *
                               kComponentStorageSlotSize +
                           kComponentStorageSlotObjectOffset;
  void *const character = LoadAt<void *>(slots, slot_offset);
  if (character == nullptr ||
      LoadAt<std::int32_t>(character, kCharacterIdOffset) != character_id) {
    return nullptr;
  }
  return character;
}

bool ReadPlayedCharacter(const Bindings &bindings, void *game_state,
                         std::int32_t local_player_id,
                         std::int32_t &character_id, bool &alive) noexcept {
  if (game_state == nullptr || local_player_id < 0 ||
      bindings.character_storage_slot == nullptr) {
    return false;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return false;
  }
  const auto *const manager = static_cast<const std::byte *>(game_data) +
                              bindings.player_character_manager_offset;
  void *const entries =
      LoadAt<void *>(manager, kPlayerCharacterEntriesOffset);
  const std::int32_t count =
      LoadAt<std::int32_t>(manager, kPlayerCharacterEntryCountOffset);
  if (entries == nullptr || count <= 0 ||
      count > kMaximumPlayerCharacterEntries) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    void *const entry = LoadAt<void *>(
        entries, static_cast<std::size_t>(index) * sizeof(void *));
    if (entry == nullptr ||
        LoadAt<std::int32_t>(entry, kPlayerCharacterPlayerIdOffset) !=
            local_player_id) {
      continue;
    }
    const std::int32_t candidate_id =
        LoadAt<std::int32_t>(entry, kPlayerCharacterIdOffset);
    void *const character = ResolveCharacter(bindings, candidate_id);
    if (character == nullptr) {
      continue;
    }
    character_id = candidate_id;
    alive =
        LoadAt<void *>(character, kCharacterDeathDataOffset) == nullptr;
    return true;
  }
  return false;
}

void *ResolveArmy(const Bindings &bindings, std::int32_t army_id) noexcept {
  if (army_id == -1 || bindings.army_storage_slot == nullptr) {
    return nullptr;
  }
  void *const storage = *bindings.army_storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const std::uint32_t index =
      static_cast<std::uint32_t>(army_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  const auto slot_offset = static_cast<std::size_t>(index) *
                               kComponentStorageSlotSize +
                           kComponentStorageSlotObjectOffset;
  void *const army = LoadAt<void *>(slots, slot_offset);
  if (army == nullptr || LoadAt<std::int32_t>(army, kArmyIdOffset) != army_id) {
    return nullptr;
  }
  return army;
}

void *ResolveProvince(void *game_state, std::int32_t province_id) noexcept {
  if (game_state == nullptr || province_id < 1) {
    return nullptr;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  void *const provinces =
      LoadAt<void *>(game_data, kGameDataProvinceArrayOffset);
  const std::int32_t province_count =
      LoadAt<std::int32_t>(game_data, kGameDataProvinceCountOffset);
  if (provinces == nullptr || province_count <= 1 ||
      province_id >= province_count) {
    return nullptr;
  }
  void *const province = LoadAt<void *>(
      provinces, static_cast<std::size_t>(province_id) * sizeof(void *));
  if (province == nullptr ||
      LoadAt<std::int32_t>(province, kProvinceIdOffset) != province_id) {
    return nullptr;
  }
  return province;
}

struct ResolvedArmySnapshot {
  void *army = nullptr;
  ArmySnapshot snapshot{};
};

std::vector<ResolvedArmySnapshot>
ReadArmies(const Bindings &bindings,
           std::int32_t played_character_id) noexcept {
  std::vector<ResolvedArmySnapshot> result;
  if (bindings.army_storage_slot == nullptr) {
    return result;
  }
  void *const storage = *bindings.army_storage_slot;
  if (storage == nullptr) {
    return result;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity) {
    return result;
  }
  for (std::int32_t index = 0; index < capacity; ++index) {
    const auto slot_offset = static_cast<std::size_t>(index) *
                                 kComponentStorageSlotSize +
                             kComponentStorageSlotObjectOffset;
    void *const army = LoadAt<void *>(slots, slot_offset);
    if (army == nullptr) {
      continue;
    }
    const std::int32_t army_id =
        LoadAt<std::int32_t>(army, kArmyIdOffset);
    if ((static_cast<std::uint32_t>(army_id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) {
      continue;
    }

    ArmySnapshot snapshot{};
    snapshot.army_id = army_id;
    snapshot.owner_character_id =
        LoadAt<std::int32_t>(army, kArmyOwnerCharacterIdOffset);
    snapshot.controllable =
        snapshot.owner_character_id == played_character_id;
    void *const current_province =
        LoadAt<void *>(army, kArmyCurrentProvinceOffset);
    if (current_province != nullptr) {
      const std::int32_t province_id =
          LoadAt<std::int32_t>(current_province, kProvinceIdOffset);
      if (province_id > 0) {
        snapshot.has_current_province = true;
        snapshot.current_province_id = province_id;
      }
    }
    result.push_back({army, snapshot});
  }
  return result;
}

void ReadWarsAndArmies(const Bindings &bindings, void *game_state,
                       std::int32_t played_character_id,
                       Snapshot &output) noexcept {
  output.active_wars.clear();
  output.player_armies.clear();
  const auto armies = ReadArmies(bindings, played_character_id);
  for (const auto &army : armies) {
    if (army.snapshot.controllable) {
      output.player_armies.push_back(army.snapshot);
    }
  }
  if (game_state == nullptr || bindings.contains_war_participant == nullptr ||
      bindings.get_war_score == nullptr) {
    return;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return;
  }
  auto *const war_manager =
      static_cast<std::byte *>(game_data) + bindings.war_manager_offset;
  void *const war_storage =
      LoadAt<void *>(war_manager, kWarStorageOffset);
  if (war_storage == nullptr) {
    return;
  }
  void *const slots =
      LoadAt<void *>(war_storage, kComponentStorageSlotsOffset);
  const std::int32_t capacity =
      LoadAt<std::int32_t>(war_storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity) {
    return;
  }

  for (std::int32_t index = 0; index < capacity; ++index) {
    const auto slot_offset = static_cast<std::size_t>(index) *
                                 kComponentStorageSlotSize +
                             kComponentStorageSlotObjectOffset;
    void *const war = LoadAt<void *>(slots, slot_offset);
    if (war == nullptr || LoadAt<void *>(war, kWarEndedDataOffset) != nullptr) {
      continue;
    }
    const std::int32_t war_id = LoadAt<std::int32_t>(war, kWarIdOffset);
    if ((static_cast<std::uint32_t>(war_id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) {
      continue;
    }
    void *const attackers =
        static_cast<std::byte *>(war) + kWarAttackersOffset;
    void *const defenders =
        static_cast<std::byte *>(war) + kWarDefendersOffset;
    const bool player_is_attacker =
        bindings.contains_war_participant(attackers, played_character_id);
    const bool player_is_defender =
        bindings.contains_war_participant(defenders, played_character_id);
    if (player_is_attacker == player_is_defender) {
      continue;
    }

    ActiveWarSnapshot snapshot{};
    snapshot.war_id = war_id;
    snapshot.player_side = player_is_attacker ? PlayerWarSide::attacker
                                              : PlayerWarSide::defender;
    const std::int32_t attacker_score = bindings.get_war_score(war, nullptr);
    snapshot.player_relative_war_score =
        player_is_attacker ? attacker_score : -attacker_score;
    void *const allied_participants =
        player_is_attacker ? attackers : defenders;
    void *const enemy_participants =
        player_is_attacker ? defenders : attackers;
    for (const auto &army : armies) {
      if (bindings.contains_war_participant(
              allied_participants, army.snapshot.owner_character_id)) {
        snapshot.allied_armies.push_back(army.snapshot);
      } else if (bindings.contains_war_participant(
                     enemy_participants,
                     army.snapshot.owner_character_id)) {
        snapshot.enemy_armies.push_back(army.snapshot);
      }
    }
    output.active_wars.push_back(std::move(snapshot));
  }
}

bool HashCurrentExecutable(std::array<std::uint8_t, 32> &output) noexcept {
  std::array<wchar_t, 32'768> path{};
  const DWORD path_length =
      GetModuleFileNameW(nullptr, path.data(), static_cast<DWORD>(path.size()));
  if (path_length == 0 || path_length >= path.size()) {
    return false;
  }

  HANDLE file = CreateFileW(path.data(), GENERIC_READ, FILE_SHARE_READ, nullptr,
                            OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (file == INVALID_HANDLE_VALUE) {
    return false;
  }

  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<std::uint8_t> object;
  bool ok = false;
  do {
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                    nullptr, 0) < 0) {
      break;
    }
    DWORD object_size = 0;
    DWORD copied = 0;
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_size),
                          sizeof(object_size), &copied, 0) < 0 ||
        object_size == 0) {
      break;
    }
    object.resize(object_size);
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr,
                         0, 0) < 0) {
      break;
    }

    // The bridge worker uses the default Windows thread stack. Keep the file
    // buffer comfortably below that limit; ck3.exe is streamed in chunks.
    std::array<std::uint8_t, 64U * 1024U> buffer{};
    while (true) {
      DWORD read = 0;
      if (!ReadFile(file, buffer.data(), static_cast<DWORD>(buffer.size()),
                    &read, nullptr)) {
        break;
      }
      if (read == 0) {
        ok = BCryptFinishHash(hash, output.data(),
                              static_cast<ULONG>(output.size()), 0) >= 0;
        break;
      }
      if (BCryptHashData(hash, buffer.data(), read, 0) < 0) {
        break;
      }
    }
  } while (false);

  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  if (algorithm != nullptr) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
  }
  CloseHandle(file);
  return ok;
}

bool MatchesExpectedExecutable() noexcept {
  std::array<std::uint8_t, 32> digest{};
  if (!HashCurrentExecutable(digest)) {
    return false;
  }
  constexpr char digits[] = "0123456789ABCDEF";
  std::array<char, 65> encoded{};
  for (std::size_t index = 0; index < digest.size(); ++index) {
    encoded[index * 2] = digits[digest[index] >> 4U];
    encoded[index * 2 + 1] = digits[digest[index] & 0x0fU];
  }
  return std::string(encoded.data()) == kExecutableSha256;
}

} // namespace

Bindings BindCurrentProcess() noexcept {
  Bindings result{};
  if (!MatchesExpectedExecutable()) {
    return result;
  }
  const auto module =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  if (module == 0) {
    return result;
  }
  result.enabled = true;
  result.game_state_slot =
      reinterpret_cast<void **>(module + kGameStateSlotRva);
  result.jomini_state_slot =
      reinterpret_cast<void **>(module + kJominiStateSlotRva);
  result.command_manager =
      reinterpret_cast<void *>(module + kCommandManagerRva);
  result.pause_primary_vtable = module + kPausePrimaryVtableRva;
  result.pause_secondary_vtable = module + kPauseSecondaryVtableRva;
  result.set_speed_primary_vtable = module + kSetSpeedPrimaryVtableRva;
  result.set_speed_secondary_vtable = module + kSetSpeedSecondaryVtableRva;
  result.select_event_option_primary_vtable =
      module + kSelectEventOptionPrimaryVtableRva;
  result.select_event_option_secondary_vtable =
      module + kSelectEventOptionSecondaryVtableRva;
  result.auto_save_primary_vtable = module + kAutoSavePrimaryVtableRva;
  result.auto_save_secondary_vtable = module + kAutoSaveSecondaryVtableRva;
  result.reply_character_interaction_primary_vtable =
      module + kReplyCharacterInteractionPrimaryVtableRva;
  result.reply_character_interaction_secondary_vtable =
      module + kReplyCharacterInteractionSecondaryVtableRva;
  result.raise_troops_primary_vtable =
      module + kRaiseTroopsPrimaryVtableRva;
  result.raise_troops_secondary_vtable =
      module + kRaiseTroopsSecondaryVtableRva;
  result.move_army_primary_vtable = module + kMoveArmyPrimaryVtableRva;
  result.move_army_secondary_vtable = module + kMoveArmySecondaryVtableRva;
  result.disband_army_primary_vtable =
      module + kDisbandArmyPrimaryVtableRva;
  result.disband_army_secondary_vtable =
      module + kDisbandArmySecondaryVtableRva;
  result.pending_character_interaction_storage_slot =
      reinterpret_cast<void **>(
          module + kPendingCharacterInteractionStorageSlotRva);
  result.character_storage_slot =
      reinterpret_cast<void **>(module + kCharacterStorageSlotRva);
  result.army_storage_slot =
      reinterpret_cast<void **>(module + kArmyStorageSlotRva);
  result.event_manager_offset = kEventManagerOffset;
  result.player_character_manager_offset =
      kPlayerCharacterManagerOffset;
  result.war_manager_offset = kWarManagerOffset;
  result.submit_command =
      reinterpret_cast<SubmitCommand>(module + kSubmitCommandRva);
  result.get_local_player =
      reinterpret_cast<GetLocalPlayer>(module + kGetLocalPlayerRva);
  result.get_current_event =
      reinterpret_cast<GetCurrentEvent>(module + kGetCurrentEventRva);
  result.contains_war_participant = reinterpret_cast<ContainsWarParticipant>(
      module + kContainsWarParticipantRva);
  result.get_war_score =
      reinterpret_cast<GetWarScore>(module + kGetWarScoreRva);
  result.resolve_default_raise_province =
      reinterpret_cast<ResolveDefaultRaiseProvince>(
          module + kResolveDefaultRaiseProvinceRva);
  result.construct_raise_troops_command =
      reinterpret_cast<ConstructRaiseTroopsCommand>(
          module + kConstructRaiseTroopsCommandRva);
  result.validate_raise_troops_command =
      reinterpret_cast<ValidateRaiseTroopsCommand>(
          module + kValidateRaiseTroopsCommandRva);
  result.destroy_raise_troops_command =
      reinterpret_cast<DestroyNativeCommand>(
          module + kDestroyRaiseTroopsCommandRva);
  result.get_army_move_mode =
      reinterpret_cast<GetArmyMoveMode>(module + kGetArmyMoveModeRva);
  result.can_move_army =
      reinterpret_cast<CanMoveArmy>(module + kCanMoveArmyRva);
  result.initialize_army_move_path =
      reinterpret_cast<InitializeArmyMovePath>(
          module + kInitializeArmyMovePathRva);
  result.destroy_move_army_command =
      reinterpret_cast<DestroyNativeCommand>(
          module + kDestroyMoveArmyCommandRva);
  return result;
}

bool ReadSnapshot(const Bindings &bindings, Snapshot &output) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr) {
    return false;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const jomini_state = *bindings.jomini_state_slot;
  if (game_state == nullptr || jomini_state == nullptr) {
    return false;
  }
  void *const players = LoadAt<void *>(jomini_state, kJominiPlayersOffset);
  if (players == nullptr) {
    return false;
  }

  output.date_raw = LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
  const std::int32_t native_speed =
      LoadAt<std::int32_t>(game_state, kGameStateSpeedOffset);
  if (native_speed < 0 || native_speed > 4) {
    return false;
  }
  output.speed = native_speed + 1;
  output.paused = LoadAt<std::uint8_t>(jomini_state, kJominiPausedOffset) != 0;
  output.player_id = LoadAt<std::int32_t>(players, kPlayersLocalIdOffset);
  void *const local_player = bindings.get_local_player != nullptr
                                 ? bindings.get_local_player(jomini_state)
                                 : nullptr;
  output.map_ready =
      local_player != nullptr &&
      LoadAt<std::int32_t>(local_player, kPlayerIdOffset) >= 0;
  output.has_played_character =
      output.map_ready &&
      ReadPlayedCharacter(bindings, game_state, output.player_id,
                          output.played_character_id,
                          output.played_character_alive);
  if (!output.has_played_character) {
    output.played_character_id = -1;
    output.played_character_alive = false;
  }
  output.has_active_event = ReadCurrentEvent(
      bindings, game_state, output.active_event_instance_id,
      output.active_event_option_count);
  if (!output.has_active_event) {
    output.active_event_instance_id = -1;
    output.active_event_option_count = 0;
  }
  output.has_pending_character_interaction = ReadPendingCharacterInteraction(
      bindings, output.pending_character_interaction_id,
      output.pending_sender_character_id,
      output.pending_auto_accept_notification);
  if (!output.has_pending_character_interaction) {
    output.pending_character_interaction_id = -1;
    output.pending_sender_character_id = -1;
    output.pending_auto_accept_notification = false;
  }
  if (output.has_played_character) {
    ReadWarsAndArmies(bindings, game_state, output.played_character_id,
                      output);
  } else {
    output.active_wars.clear();
    output.player_armies.clear();
  }
  return true;
}

PauseSubmitResult SubmitPauseMap(const Bindings &bindings) noexcept {
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return PauseSubmitResult::unavailable;
  }
  if (current.paused) {
    return PauseSubmitResult::already_paused;
  }
  if (bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.get_local_player == nullptr ||
      bindings.pause_primary_vtable == 0 ||
      bindings.pause_secondary_vtable == 0) {
    return PauseSubmitResult::unavailable;
  }

  void *const jomini_state = *bindings.jomini_state_slot;
  void *const player = bindings.get_local_player(jomini_state);
  if (player == nullptr) {
    return PauseSubmitResult::unavailable;
  }
  const std::int32_t player_id = LoadAt<std::int32_t>(player, kPlayerIdOffset);
  if (player_id < 0) {
    return PauseSubmitResult::unavailable;
  }

  PauseCommand command{};
  command.primary_vtable = bindings.pause_primary_vtable;
  command.flags = 0x08;
  command.secondary_vtable = bindings.pause_secondary_vtable;
  command.player_id = player_id;
  command.paused = 1;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return PauseSubmitResult::submitted;
}

ResumeSubmitResult SubmitResumeMap(const Bindings &bindings) noexcept {
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ResumeSubmitResult::unavailable;
  }
  if (!current.paused) {
    return ResumeSubmitResult::already_running;
  }
  if (bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.get_local_player == nullptr ||
      bindings.pause_primary_vtable == 0 ||
      bindings.pause_secondary_vtable == 0) {
    return ResumeSubmitResult::unavailable;
  }

  void *const jomini_state = *bindings.jomini_state_slot;
  void *const player = bindings.get_local_player(jomini_state);
  if (player == nullptr) {
    return ResumeSubmitResult::unavailable;
  }
  const std::int32_t player_id = LoadAt<std::int32_t>(player, kPlayerIdOffset);
  if (player_id < 0) {
    return ResumeSubmitResult::unavailable;
  }

  PauseCommand command{};
  command.primary_vtable = bindings.pause_primary_vtable;
  command.flags = 0x08;
  command.secondary_vtable = bindings.pause_secondary_vtable;
  command.player_id = player_id;
  command.paused = 0;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return ResumeSubmitResult::submitted;
}

bool SubmitSetSpeed(const Bindings &bindings, std::int32_t speed) noexcept {
  if (!bindings.enabled || speed < 1 || speed > 5 ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.set_speed_primary_vtable == 0 ||
      bindings.set_speed_secondary_vtable == 0) {
    return false;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return false;
  }

  SetSpeedCommand command{};
  command.primary_vtable = bindings.set_speed_primary_vtable;
  command.secondary_vtable = bindings.set_speed_secondary_vtable;
  command.speed = speed - 1;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return true;
}

SelectEventOptionResult
SubmitSelectEventOption(const Bindings &bindings,
                        std::int32_t option_index) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.select_event_option_primary_vtable == 0 ||
      bindings.select_event_option_secondary_vtable == 0 ||
      bindings.get_current_event == nullptr) {
    return SelectEventOptionResult::unavailable;
  }
  void *const game_state = *bindings.game_state_slot;
  if (game_state == nullptr) {
    return SelectEventOptionResult::unavailable;
  }

  std::int32_t event_instance_id = -1;
  std::int32_t option_count = 0;
  if (!ReadCurrentEvent(bindings, game_state, event_instance_id,
                        option_count)) {
    return SelectEventOptionResult::no_active_event;
  }
  if (option_index < 0 || option_index >= option_count) {
    return SelectEventOptionResult::option_out_of_range;
  }

  SelectEventOptionCommand command{};
  command.primary_vtable = bindings.select_event_option_primary_vtable;
  command.secondary_vtable = bindings.select_event_option_secondary_vtable;
  command.event_instance_id = event_instance_id;
  command.option_index = option_index;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return SelectEventOptionResult::submitted;
}

SaveCheckpointResult SubmitSaveCheckpoint(const Bindings &bindings) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.auto_save_primary_vtable == 0 ||
      bindings.auto_save_secondary_vtable == 0) {
    return {};
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return {};
  }
  if (!current.map_ready) {
    return {SaveCheckpointStatus::map_not_ready, current.date_raw};
  }

  AutoSaveCommand command{};
  command.primary_vtable = bindings.auto_save_primary_vtable;
  command.flags = 0x20;
  command.secondary_vtable = bindings.auto_save_secondary_vtable;
  constexpr std::size_t save_name_length = sizeof(kCheckpointSaveName) - 1U;
  static_assert(save_name_length < 16U);
  std::memcpy(command.save_name.buffer.data(), kCheckpointSaveName,
              save_name_length);
  command.save_name.size = save_name_length;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return {SaveCheckpointStatus::submitted, current.date_raw};
}

ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const Bindings &bindings, PendingInteractionReply reply) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.reply_character_interaction_primary_vtable == 0 ||
      bindings.reply_character_interaction_secondary_vtable == 0) {
    return ReplyPendingInteractionResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReplyPendingInteractionResult::unavailable;
  }
  if (!current.has_pending_character_interaction) {
    return ReplyPendingInteractionResult::no_pending_interaction;
  }
  if (current.pending_auto_accept_notification) {
    return ReplyPendingInteractionResult::acknowledgement_required;
  }

  ReplyCharacterInteractionCommand command{};
  command.primary_vtable =
      bindings.reply_character_interaction_primary_vtable;
  command.secondary_vtable =
      bindings.reply_character_interaction_secondary_vtable;
  command.pending_interaction_id =
      current.pending_character_interaction_id;
  command.reply = static_cast<std::int32_t>(reply);
  bindings.submit_command(bindings.command_manager, &command, 0x0E);
  return ReplyPendingInteractionResult::submitted;
}

RaiseTroopsResult SubmitRaiseTroopsDefault(
    const Bindings &bindings) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.resolve_default_raise_province == nullptr ||
      bindings.construct_raise_troops_command == nullptr ||
      bindings.validate_raise_troops_command == nullptr ||
      bindings.destroy_raise_troops_command == nullptr ||
      bindings.raise_troops_primary_vtable == 0 ||
      bindings.raise_troops_secondary_vtable == 0) {
    return RaiseTroopsResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return RaiseTroopsResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return RaiseTroopsResult::no_played_character;
  }
  void *const character =
      ResolveCharacter(bindings, current.played_character_id);
  if (character == nullptr) {
    return RaiseTroopsResult::no_played_character;
  }
  void *const default_province =
      bindings.resolve_default_raise_province(character);
  if (default_province == nullptr) {
    return RaiseTroopsResult::no_default_province;
  }
  const std::int32_t province_id =
      LoadAt<std::int32_t>(default_province, kProvinceIdOffset);
  void *const game_state = *bindings.game_state_slot;
  if (province_id < 1 || ResolveProvince(game_state, province_id) == nullptr) {
    return RaiseTroopsResult::no_default_province;
  }

  RaiseTroopsCommandStorage storage{};
  RaiseEntry entry{province_id, -1};
  void *const command = storage.bytes.data();
  if (bindings.construct_raise_troops_command(
          command, current.played_character_id, &entry) != command) {
    return RaiseTroopsResult::unavailable;
  }
  const bool layout_matches =
      LoadAt<std::uintptr_t>(command, 0x00) ==
          bindings.raise_troops_primary_vtable &&
      LoadAt<std::uintptr_t>(command, 0x18) ==
          bindings.raise_troops_secondary_vtable;
  if (!layout_matches) {
    bindings.destroy_raise_troops_command(command, 0);
    return RaiseTroopsResult::unavailable;
  }
  if (!bindings.validate_raise_troops_command(command, nullptr)) {
    bindings.destroy_raise_troops_command(command, 0);
    return RaiseTroopsResult::validation_failed;
  }
  bindings.submit_command(bindings.command_manager, command, 7);
  bindings.destroy_raise_troops_command(command, 0);
  return RaiseTroopsResult::submitted;
}

MoveArmyResult SubmitMoveArmy(const Bindings &bindings,
                              std::int32_t army_id,
                              std::int32_t province_id) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.get_army_move_mode == nullptr ||
      bindings.can_move_army == nullptr ||
      bindings.initialize_army_move_path == nullptr ||
      bindings.destroy_move_army_command == nullptr ||
      bindings.move_army_primary_vtable == 0 ||
      bindings.move_army_secondary_vtable == 0) {
    return MoveArmyResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return MoveArmyResult::unavailable;
  }
  void *const army = ResolveArmy(bindings, army_id);
  if (army == nullptr) {
    return MoveArmyResult::army_not_found;
  }
  bool controllable = false;
  for (const auto &candidate : current.player_armies) {
    if (candidate.army_id == army_id && candidate.controllable) {
      controllable = true;
      break;
    }
  }
  if (!controllable) {
    return MoveArmyResult::army_not_controllable;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const province = ResolveProvince(game_state, province_id);
  if (province == nullptr) {
    return MoveArmyResult::province_not_found;
  }
  constexpr std::int32_t command_kind = 2;
  constexpr std::int32_t direct_target = 1;
  const std::int32_t move_mode =
      bindings.get_army_move_mode(army, province, direct_target);
  if (!bindings.can_move_army(command_kind, army, move_mode)) {
    return MoveArmyResult::cannot_move;
  }

  MoveArmyCommand command{};
  command.primary_vtable = bindings.move_army_primary_vtable;
  command.secondary_vtable = bindings.move_army_secondary_vtable;
  command.army_id = army_id;
  command.destination_province_id = province_id;
  command.move_mode = move_mode;
  bindings.initialize_army_move_path(command.path_storage.data());
  bindings.submit_command(bindings.command_manager, &command, 7);
  bindings.destroy_move_army_command(&command, 0);
  return MoveArmyResult::submitted;
}

DisbandArmyResult SubmitDisbandArmy(const Bindings &bindings,
                                    std::int32_t army_id) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.disband_army_primary_vtable == 0 ||
      bindings.disband_army_secondary_vtable == 0) {
    return DisbandArmyResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return DisbandArmyResult::unavailable;
  }
  if (ResolveArmy(bindings, army_id) == nullptr) {
    return DisbandArmyResult::army_not_found;
  }
  bool controllable = false;
  for (const auto &candidate : current.player_armies) {
    if (candidate.army_id == army_id && candidate.controllable) {
      controllable = true;
      break;
    }
  }
  if (!controllable) {
    return DisbandArmyResult::army_not_controllable;
  }

  DisbandArmyCommand command{};
  command.primary_vtable = bindings.disband_army_primary_vtable;
  command.secondary_vtable = bindings.disband_army_secondary_vtable;
  command.army_id = army_id;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return DisbandArmyResult::submitted;
}

} // namespace xar::ck3_11906

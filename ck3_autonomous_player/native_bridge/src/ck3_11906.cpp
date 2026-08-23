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
constexpr std::uintptr_t kArmyStorageSlotRva = 0x570CC80;
constexpr std::uintptr_t kRaiseTroopsPrimaryVtableRva = 0x41226D8;
constexpr std::uintptr_t kRaiseTroopsSecondaryVtableRva = 0x41226A8;
constexpr std::uintptr_t kMoveArmyPrimaryVtableRva = 0x432BF18;
constexpr std::uintptr_t kMoveArmySecondaryVtableRva = 0x432BFB0;
constexpr std::uintptr_t kDisbandArmyPrimaryVtableRva = 0x432BFE0;
constexpr std::uintptr_t kDisbandArmySecondaryVtableRva = 0x432C078;
constexpr std::uintptr_t kSendCharacterInteractionPrimaryVtableRva =
    0x40829F8;
constexpr std::uintptr_t kSendCharacterInteractionSecondaryVtableRva =
    0x40829C8;
constexpr std::uintptr_t kWarDeclarationVtableRva = 0x411DAA0;
constexpr std::uintptr_t kValidCasusBelliConfigurationScratchRva =
    0x4FED598;
constexpr std::uintptr_t kSubmitCommandRva = 0x0973E00;
constexpr std::uintptr_t kGetLocalPlayerRva = 0x346B7C0;
constexpr std::uintptr_t kGetCurrentEventRva = 0x2706AD0;
constexpr std::uintptr_t kIsPendingInteractionForCharacterRva = 0x1266BA0;
constexpr std::uintptr_t kValidateReplyCharacterInteractionCommandRva =
    0x26B3540;
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
constexpr std::uintptr_t kGetCasusBelliTypeDatabaseRva = 0x088E260;
constexpr std::uintptr_t kGetCharacterInteractionDatabaseRva = 0x0831890;
constexpr std::uintptr_t kEvaluateCasusBelliRva = 0x2D95D00;
constexpr std::uintptr_t kDestroyValidCasusBelliConfigurationRva =
    0x101B3C0;
constexpr std::uintptr_t kConstructCharacterInteractionContextRva =
    0x2C3EE50;
constexpr std::uintptr_t kCopyNativeIntArrayRva = 0x0BDBC10;
constexpr std::uintptr_t kAppendNativeIntArrayRangeRva = 0x0975ED0;
constexpr std::uintptr_t kRefreshCharacterInteractionContextRva =
    0x2C40950;
constexpr std::uintptr_t kFinalizeCharacterInteractionContextRva =
    0x2C40B20;
constexpr std::uintptr_t kValidateCharacterInteractionContextRva =
    0x2C43F00;
constexpr std::uintptr_t kConstructSendCharacterInteractionCommandRva =
    0x26B3220;
constexpr std::uintptr_t kDestroyCharacterInteractionContextRva =
    0x2C3F380;
constexpr std::uintptr_t kDefaultConstructCharacterInteractionContextRva =
    0x2C3F300;
constexpr std::uintptr_t kConstructWarResolutionInteractionContextRva =
    0x0C569F0;

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
constexpr std::size_t kPendingInteractionRecipientIdOffset = 0x2F4;
constexpr std::size_t kPendingInteractionAlternateRecipientIdOffset = 0x300;
constexpr std::size_t kPendingInteractionRoutingKindOffset = 0x5C0;
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
constexpr std::size_t kWarPrimaryAttackerCharacterIdOffset = 0x288;
constexpr std::size_t kWarPrimaryDefenderCharacterIdOffset = 0x28C;
constexpr std::size_t kWarEndedDataOffset = 0x358;
constexpr std::size_t kArmyIdOffset = 0x10;
constexpr std::size_t kArmyCurrentProvinceOffset = 0x20;
constexpr std::size_t kArmyOwnerCharacterIdOffset = 0x174;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::size_t kArrangeMarriageInteractionOffset = 0xF48;
constexpr std::size_t kDeclareWarInteractionOffset = 0xF78;
constexpr std::size_t kCasusBelliTypeArrayOffset = 0x68;
constexpr std::size_t kCasusBelliTypeCountOffset = 0x74;
constexpr std::size_t kCasusBelliTypeKeyOffset = 0x18;
constexpr std::size_t kCasusBelliTypeRuleOffset = 0x38;
constexpr std::size_t kCasusBelliRuleDisabledOffset = 0x211;
constexpr std::size_t kCasusBelliTypeFlagsOffset = 0x1718;
constexpr std::uint32_t kCasusBelliCombinedConfigurationsFlag = 1U << 20U;
constexpr std::size_t kValidCasusBelliConfigurationSize = 0x98;
constexpr std::size_t kValidCasusBelliClaimantOffset = 0x00;
constexpr std::size_t kValidCasusBelliTargetTitlesOffset = 0x08;
constexpr std::size_t kNativeArrayDataOffset = 0x00;
constexpr std::size_t kNativeArrayCapacityOffset = 0x08;
constexpr std::size_t kNativeArrayCountOffset = 0x0C;
constexpr std::size_t kCharacterInteractionActorToMatchOffset = 0x2E0;
constexpr std::size_t kCharacterInteractionRecipientToMatchOffset = 0x2E4;
constexpr std::size_t kCharacterInteractionSpecialDataOffset = 0x330;
constexpr std::size_t kWarDeclarationCasusBelliOffset = 0x08;
constexpr std::size_t kWarDeclarationTargetTitlesOffset = 0x10;
constexpr std::size_t kWarDeclarationClaimantOffset = 0x28;
constexpr std::size_t kSendCharacterInteractionContextOffset = 0x20;
constexpr std::int32_t kMaximumPlayerCharacterEntries = 1024;
constexpr std::int32_t kMaximumComponentCapacity = 1'000'000;
constexpr std::int32_t kMaximumCasusBelliTypes = 10'000;
constexpr std::int32_t kMaximumCasusBelliConfigurations = 10'000;
constexpr std::int32_t kMaximumNativeTitleIds = 1'000'000;
constexpr std::size_t kMaximumDatabaseObjectKeyBytes = 4'096;
constexpr std::size_t kMsvcStringInlineCapacity = 15;

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

struct alignas(8) CharacterInteractionContextStorage {
  std::array<std::byte, 0x338> bytes{};
};

struct alignas(8) SendCharacterInteractionCommandStorage {
  std::array<std::byte, 0x368> bytes{};
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
static_assert(sizeof(CharacterInteractionContextStorage) == 0x338);
static_assert(sizeof(SendCharacterInteractionCommandStorage) == 0x368);

template <typename Value>
Value LoadAt(const void *base, std::size_t offset) noexcept {
  Value result{};
  std::memcpy(&result, static_cast<const std::byte *>(base) + offset,
              sizeof(result));
  return result;
}

template <typename Value>
void StoreAt(void *base, std::size_t offset, Value value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value,
              sizeof(value));
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
                                     void *played_character,
                                     std::int32_t played_character_id,
                                     std::int32_t &instance_id,
                                     std::int32_t &sender_character_id,
                                     bool &auto_accept_notification) noexcept {
  if (played_character == nullptr || played_character_id == -1 ||
      bindings.pending_character_interaction_storage_slot == nullptr ||
      bindings.is_pending_character_interaction_for_character == nullptr ||
      bindings.validate_reply_character_interaction_command == nullptr ||
      bindings.reply_character_interaction_primary_vtable == 0 ||
      bindings.reply_character_interaction_secondary_vtable == 0) {
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

    // CK3's notification enumeration calls RVA 0x1266BA0 with the pending
    // object and the currently played Character.  Cheaply reproduce its
    // routing switch first so the exact engine predicate is called only for
    // requests addressed to this player, not every global pending component.
    const std::int32_t routing_kind = LoadAt<std::int32_t>(
        pending, kPendingInteractionRoutingKindOffset);
    std::size_t recipient_offset = kPendingInteractionRecipientIdOffset;
    if (routing_kind == 1) {
      recipient_offset = kPendingInteractionAlternateRecipientIdOffset;
    } else if (routing_kind != 0 && routing_kind != 2) {
      continue;
    }
    if (LoadAt<std::int32_t>(pending, recipient_offset) !=
        played_character_id) {
      continue;
    }

    // Auto-accept notifications need reply enum 4 (acknowledge).  The public
    // agent action is deliberately accept/reject, so exposing one would leave
    // the planner parked on a request that neither public action can advance.
    if (LoadAt<std::uint8_t>(pending,
                             kPendingInteractionAutoAcceptOffset) != 0) {
      continue;
    }
    if (!bindings.is_pending_character_interaction_for_character(
            pending, played_character)) {
      continue;
    }

    ReplyCharacterInteractionCommand accept_command{};
    accept_command.primary_vtable =
        bindings.reply_character_interaction_primary_vtable;
    accept_command.secondary_vtable =
        bindings.reply_character_interaction_secondary_vtable;
    accept_command.pending_interaction_id = candidate_id;
    accept_command.reply =
        static_cast<std::int32_t>(PendingInteractionReply::accept);
    if (!bindings.validate_reply_character_interaction_command(
            &accept_command)) {
      continue;
    }
    instance_id = candidate_id;
    sender_character_id = LoadAt<std::int32_t>(
        pending, kPendingInteractionSenderIdOffset);
    auto_accept_notification = false;
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

bool HasDeclarableWarReadBindings(const Bindings &bindings) noexcept {
  return bindings.enabled && bindings.game_state_slot != nullptr &&
         bindings.character_storage_slot != nullptr &&
         bindings.valid_casus_belli_configuration_scratch != nullptr &&
         bindings.get_casus_belli_type_database != nullptr &&
         bindings.get_character_interaction_database != nullptr &&
         bindings.evaluate_casus_belli != nullptr &&
         bindings.destroy_valid_casus_belli_configuration != nullptr;
}

bool HasArrangeMarriageReadBindings(const Bindings &bindings) noexcept {
  return bindings.enabled && bindings.game_state_slot != nullptr &&
         bindings.character_storage_slot != nullptr &&
         bindings.get_character_interaction_database != nullptr &&
         bindings.arrange_marriage_interaction_offset != 0 &&
         bindings.construct_character_interaction_context != nullptr &&
         bindings.refresh_character_interaction_context != nullptr &&
         bindings.finalize_character_interaction_context != nullptr &&
         bindings.validate_character_interaction_context != nullptr &&
         bindings.destroy_character_interaction_context != nullptr;
}

void *ResolveCharacterInteraction(const Bindings &bindings,
                                  std::size_t interaction_offset) noexcept {
  if (bindings.get_character_interaction_database == nullptr ||
      interaction_offset == 0) {
    return nullptr;
  }
  void *const interaction_database =
      bindings.get_character_interaction_database();
  return interaction_database == nullptr
             ? nullptr
             : LoadAt<void *>(
                   interaction_database, interaction_offset);
}

bool PrepareArrangeMarriageContext(
    const Bindings &bindings, std::int32_t played_character_id,
    std::int32_t candidate_character_id,
    CharacterInteractionContextStorage &storage) noexcept {
  void *const interaction =
      ResolveCharacterInteraction(
          bindings, bindings.arrange_marriage_interaction_offset);
  if (interaction == nullptr) {
    return false;
  }
  void *const context = storage.bytes.data();
  if (bindings.construct_character_interaction_context(
          context, interaction, played_character_id,
          candidate_character_id, nullptr, true) != context) {
    return false;
  }
  StoreAt(context, kCharacterInteractionActorToMatchOffset,
          played_character_id);
  StoreAt(context, kCharacterInteractionRecipientToMatchOffset,
          candidate_character_id);
  bindings.refresh_character_interaction_context(context, true);
  bindings.finalize_character_interaction_context(context);
  return true;
}

bool ReadNativeIntArray(const void *native_array,
                        std::vector<std::int32_t> &output) noexcept {
  const auto capacity =
      LoadAt<std::int32_t>(native_array, kNativeArrayCapacityOffset);
  const auto count =
      LoadAt<std::int32_t>(native_array, kNativeArrayCountOffset);
  const auto *const data =
      LoadAt<const std::int32_t *>(native_array, kNativeArrayDataOffset);
  if (capacity < 0 || count < 0 || count > capacity ||
      count > kMaximumNativeTitleIds || (count > 0 && data == nullptr)) {
    return false;
  }
  output.clear();
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    output.push_back(data[index]);
  }
  return true;
}

bool ReadValidCasusBelliConfigurationArray(
    const Bindings &bindings, void *&data, std::int32_t &count) noexcept {
  void *const scratch =
      bindings.valid_casus_belli_configuration_scratch;
  const auto capacity =
      LoadAt<std::int32_t>(scratch, kNativeArrayCapacityOffset);
  count = LoadAt<std::int32_t>(scratch, kNativeArrayCountOffset);
  data = LoadAt<void *>(scratch, kNativeArrayDataOffset);
  return capacity >= 0 && count >= 0 && count <= capacity &&
         count <= kMaximumCasusBelliConfigurations &&
         (count == 0 || data != nullptr);
}

bool ClearValidCasusBelliConfigurations(
    const Bindings &bindings) noexcept {
  void *data = nullptr;
  std::int32_t count = 0;
  if (!ReadValidCasusBelliConfigurationArray(bindings, data, count)) {
    return false;
  }
  auto *configuration = static_cast<std::byte *>(data);
  for (std::int32_t index = 0; index < count; ++index) {
    bindings.destroy_valid_casus_belli_configuration(configuration);
    configuration += kValidCasusBelliConfigurationSize;
  }
  StoreAt(bindings.valid_casus_belli_configuration_scratch,
          kNativeArrayCountOffset, std::int32_t{0});
  return true;
}

bool ReadCasusBelliDatabase(void *database, void *&types,
                            std::int32_t &count) noexcept {
  if (database == nullptr) {
    return false;
  }
  types = LoadAt<void *>(database, kCasusBelliTypeArrayOffset);
  count = LoadAt<std::int32_t>(database, kCasusBelliTypeCountOffset);
  return count >= 0 && count <= kMaximumCasusBelliTypes &&
         (count == 0 || types != nullptr);
}

bool IsEnabledCasusBelliType(const void *casus_belli_type) noexcept {
  if (casus_belli_type == nullptr) {
    return false;
  }
  void *const rule =
      LoadAt<void *>(casus_belli_type, kCasusBelliTypeRuleOffset);
  return rule != nullptr &&
         LoadAt<std::uint8_t>(rule, kCasusBelliRuleDisabledOffset) == 0;
}

bool ReadCasusBelliTypeKey(const void *casus_belli_type,
                           std::string &output) noexcept {
  const auto *const string_storage =
      static_cast<const std::byte *>(casus_belli_type) +
      kCasusBelliTypeKeyOffset;
  const auto size = LoadAt<std::size_t>(string_storage, 0x10);
  const auto capacity = LoadAt<std::size_t>(string_storage, 0x18);
  if (size > capacity || size > kMaximumDatabaseObjectKeyBytes) {
    return false;
  }
  const char *data = nullptr;
  if (capacity <= kMsvcStringInlineCapacity) {
    data = reinterpret_cast<const char *>(string_storage);
  } else {
    data = LoadAt<const char *>(string_storage, 0x00);
  }
  if (size > 0 && data == nullptr) {
    return false;
  }
  output.assign(data == nullptr ? "" : data, size);
  return true;
}

bool MaterializeCasusBelliChoices(
    const Bindings &bindings, const void *casus_belli_type,
    std::int32_t target_character_id, std::int32_t casus_belli_index,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  std::string casus_belli_key;
  if (!ReadCasusBelliTypeKey(casus_belli_type, casus_belli_key)) {
    return false;
  }
  void *configuration_data = nullptr;
  std::int32_t configuration_count = 0;
  if (!ReadValidCasusBelliConfigurationArray(
          bindings, configuration_data, configuration_count)) {
    return false;
  }
  const bool combined =
      configuration_count == 0 ||
      (LoadAt<std::uint32_t>(casus_belli_type,
                             kCasusBelliTypeFlagsOffset) &
       kCasusBelliCombinedConfigurationsFlag) != 0;
  if (combined) {
    DeclarableWarSnapshot choice{};
    choice.target_character_id = target_character_id;
    choice.casus_belli_index = casus_belli_index;
    choice.casus_belli_key = casus_belli_key;
    choice.configuration_index = -1;
    choice.claimant_character_id = -1;
    for (std::int32_t index = 0; index < configuration_count; ++index) {
      const auto *const configuration =
          static_cast<const std::byte *>(configuration_data) +
          static_cast<std::size_t>(index) *
              kValidCasusBelliConfigurationSize;
      std::vector<std::int32_t> target_title_ids;
      if (!ReadNativeIntArray(
              configuration + kValidCasusBelliTargetTitlesOffset,
              target_title_ids)) {
        return false;
      }
      choice.target_title_ids.insert(choice.target_title_ids.end(),
                                     target_title_ids.begin(),
                                     target_title_ids.end());
    }
    output.push_back(std::move(choice));
    return true;
  }

  for (std::int32_t index = 0; index < configuration_count; ++index) {
    const auto *const configuration =
        static_cast<const std::byte *>(configuration_data) +
        static_cast<std::size_t>(index) *
            kValidCasusBelliConfigurationSize;
    DeclarableWarSnapshot choice{};
    choice.target_character_id = target_character_id;
    choice.casus_belli_index = casus_belli_index;
    choice.casus_belli_key = casus_belli_key;
    choice.configuration_index = index;
    choice.claimant_character_id = LoadAt<std::int32_t>(
        configuration, kValidCasusBelliClaimantOffset);
    if (!ReadNativeIntArray(
            configuration + kValidCasusBelliTargetTitlesOffset,
            choice.target_title_ids)) {
      return false;
    }
    // CDeclareWarInteractionWindow creates no selectable item for an empty
    // per-configuration target-title vector (RVA 0x10865E5).
    if (!choice.target_title_ids.empty()) {
      output.push_back(std::move(choice));
    }
  }
  return true;
}

bool ReadDeclarableWarsForTargetInternal(
    const Bindings &bindings, void *casus_belli_database,
    void *attacker_character, void *target_character,
    std::int32_t target_character_id,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  void *casus_belli_types = nullptr;
  std::int32_t casus_belli_type_count = 0;
  if (!ReadCasusBelliDatabase(casus_belli_database, casus_belli_types,
                              casus_belli_type_count)) {
    return false;
  }
  for (std::int32_t index = 0; index < casus_belli_type_count; ++index) {
    void *const casus_belli_type = LoadAt<void *>(
        casus_belli_types,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (!IsEnabledCasusBelliType(casus_belli_type)) {
      continue;
    }
    if (!ClearValidCasusBelliConfigurations(bindings)) {
      return false;
    }
    const bool available = bindings.evaluate_casus_belli(
        casus_belli_type, attacker_character, target_character,
        bindings.valid_casus_belli_configuration_scratch, false, false,
        nullptr);
    if (available && !MaterializeCasusBelliChoices(
                         bindings, casus_belli_type, target_character_id,
                         index, output)) {
      ClearValidCasusBelliConfigurations(bindings);
      return false;
    }
    if (!ClearValidCasusBelliConfigurations(bindings)) {
      return false;
    }
  }
  return true;
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

void *ResolveWar(const Bindings &bindings, void *game_state,
                 std::int32_t war_id) noexcept {
  if (game_state == nullptr || war_id == -1) {
    return nullptr;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  auto *const war_manager =
      static_cast<std::byte *>(game_data) + bindings.war_manager_offset;
  void *const storage = LoadAt<void *>(war_manager, kWarStorageOffset);
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const auto index = static_cast<std::uint32_t>(war_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const war = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kComponentStorageSlotSize +
                 kComponentStorageSlotObjectOffset);
  if (war == nullptr || LoadAt<std::int32_t>(war, kWarIdOffset) != war_id ||
      LoadAt<void *>(war, kWarEndedDataOffset) != nullptr) {
    return nullptr;
  }
  return war;
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
  result.send_character_interaction_primary_vtable =
      module + kSendCharacterInteractionPrimaryVtableRva;
  result.send_character_interaction_secondary_vtable =
      module + kSendCharacterInteractionSecondaryVtableRva;
  result.war_declaration_vtable = module + kWarDeclarationVtableRva;
  result.pending_character_interaction_storage_slot =
      reinterpret_cast<void **>(
          module + kPendingCharacterInteractionStorageSlotRva);
  result.character_storage_slot =
      reinterpret_cast<void **>(module + kCharacterStorageSlotRva);
  result.army_storage_slot =
      reinterpret_cast<void **>(module + kArmyStorageSlotRva);
  result.valid_casus_belli_configuration_scratch =
      reinterpret_cast<void *>(
          module + kValidCasusBelliConfigurationScratchRva);
  result.event_manager_offset = kEventManagerOffset;
  result.player_character_manager_offset =
      kPlayerCharacterManagerOffset;
  result.war_manager_offset = kWarManagerOffset;
  result.arrange_marriage_interaction_offset =
      kArrangeMarriageInteractionOffset;
  result.declare_war_interaction_offset = kDeclareWarInteractionOffset;
  result.submit_command =
      reinterpret_cast<SubmitCommand>(module + kSubmitCommandRva);
  result.get_local_player =
      reinterpret_cast<GetLocalPlayer>(module + kGetLocalPlayerRva);
  result.get_current_event =
      reinterpret_cast<GetCurrentEvent>(module + kGetCurrentEventRva);
  result.is_pending_character_interaction_for_character =
      reinterpret_cast<IsPendingCharacterInteractionForCharacter>(
          module + kIsPendingInteractionForCharacterRva);
  result.validate_reply_character_interaction_command =
      reinterpret_cast<ValidateReplyCharacterInteractionCommand>(
          module + kValidateReplyCharacterInteractionCommandRva);
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
  result.get_casus_belli_type_database =
      reinterpret_cast<GetCasusBelliTypeDatabase>(
          module + kGetCasusBelliTypeDatabaseRva);
  result.get_character_interaction_database =
      reinterpret_cast<GetCharacterInteractionDatabase>(
          module + kGetCharacterInteractionDatabaseRva);
  result.evaluate_casus_belli = reinterpret_cast<EvaluateCasusBelli>(
      module + kEvaluateCasusBelliRva);
  result.destroy_valid_casus_belli_configuration =
      reinterpret_cast<DestroyValidCasusBelliConfiguration>(
          module + kDestroyValidCasusBelliConfigurationRva);
  result.construct_character_interaction_context =
      reinterpret_cast<ConstructCharacterInteractionContext>(
          module + kConstructCharacterInteractionContextRva);
  result.copy_native_int_array = reinterpret_cast<CopyNativeIntArray>(
      module + kCopyNativeIntArrayRva);
  result.append_native_int_array_range =
      reinterpret_cast<AppendNativeIntArrayRange>(
          module + kAppendNativeIntArrayRangeRva);
  result.refresh_character_interaction_context =
      reinterpret_cast<RefreshCharacterInteractionContext>(
          module + kRefreshCharacterInteractionContextRva);
  result.finalize_character_interaction_context =
      reinterpret_cast<FinalizeCharacterInteractionContext>(
          module + kFinalizeCharacterInteractionContextRva);
  result.validate_character_interaction_context =
      reinterpret_cast<ValidateCharacterInteractionContext>(
          module + kValidateCharacterInteractionContextRva);
  result.construct_send_character_interaction_command =
      reinterpret_cast<ConstructSendCharacterInteractionCommand>(
          module + kConstructSendCharacterInteractionCommandRva);
  result.destroy_character_interaction_context =
      reinterpret_cast<DestroyCharacterInteractionContext>(
          module + kDestroyCharacterInteractionContextRva);
  result.default_construct_character_interaction_context =
      reinterpret_cast<DefaultConstructCharacterInteractionContext>(
          module + kDefaultConstructCharacterInteractionContextRva);
  result.construct_war_resolution_interaction_context =
      reinterpret_cast<ConstructWarResolutionInteractionContext>(
          module + kConstructWarResolutionInteractionContextRva);
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
  void *const played_character = output.has_played_character
                                     ? ResolveCharacter(
                                           bindings,
                                           output.played_character_id)
                                     : nullptr;
  output.has_pending_character_interaction = ReadPendingCharacterInteraction(
      bindings, played_character, output.played_character_id,
      output.pending_character_interaction_id,
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

ReadDeclarableWarsResult ReadDeclarableWarsForTarget(
    const Bindings &bindings, std::int32_t target_character_id,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  output.clear();
  if (!HasDeclarableWarReadBindings(bindings)) {
    return ReadDeclarableWarsResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReadDeclarableWarsResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadDeclarableWarsResult::no_played_character;
  }
  void *const attacker_character =
      ResolveCharacter(bindings, current.played_character_id);
  void *const target_character =
      ResolveCharacter(bindings, target_character_id);
  if (target_character == nullptr ||
      LoadAt<void *>(target_character, kCharacterDeathDataOffset) != nullptr) {
    return ReadDeclarableWarsResult::target_not_found;
  }
  void *const casus_belli_database =
      bindings.get_casus_belli_type_database();
  std::vector<DeclarableWarSnapshot> choices;
  if (attacker_character == nullptr ||
      !ReadDeclarableWarsForTargetInternal(
          bindings, casus_belli_database, attacker_character,
          target_character, target_character_id, choices)) {
    return ReadDeclarableWarsResult::unavailable;
  }
  output = std::move(choices);
  return ReadDeclarableWarsResult::available;
}

bool ReadDeclarableWars(
    const Bindings &bindings,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  output.clear();
  if (!HasDeclarableWarReadBindings(bindings)) {
    return false;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current) || !current.has_played_character ||
      !current.played_character_alive) {
    return false;
  }
  void *const attacker_character =
      ResolveCharacter(bindings, current.played_character_id);
  void *const storage = *bindings.character_storage_slot;
  if (attacker_character == nullptr || storage == nullptr) {
    return false;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity) {
    return false;
  }
  void *const casus_belli_database =
      bindings.get_casus_belli_type_database();
  void *casus_belli_types = nullptr;
  std::int32_t casus_belli_type_count = 0;
  if (!ReadCasusBelliDatabase(casus_belli_database, casus_belli_types,
                              casus_belli_type_count)) {
    return false;
  }

  std::vector<DeclarableWarSnapshot> choices;
  for (std::int32_t index = 0; index < capacity; ++index) {
    void *const target_character = LoadAt<void *>(
        slots, static_cast<std::size_t>(index) *
                       kComponentStorageSlotSize +
                   kComponentStorageSlotObjectOffset);
    if (target_character == nullptr ||
        target_character == attacker_character ||
        LoadAt<void *>(target_character, kCharacterDeathDataOffset) !=
            nullptr) {
      continue;
    }
    const auto target_character_id =
        LoadAt<std::int32_t>(target_character, kCharacterIdOffset);
    if ((static_cast<std::uint32_t>(target_character_id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) {
      continue;
    }
    if (!ReadDeclarableWarsForTargetInternal(
            bindings, casus_belli_database, attacker_character,
            target_character, target_character_id, choices)) {
      return false;
    }
  }
  output = std::move(choices);
  return true;
}

DeclareWarResult SubmitDeclareWar(
    const Bindings &bindings,
    const DeclarableWarSnapshot &declaration) noexcept {
  if (!HasDeclarableWarReadBindings(bindings) ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.copy_native_int_array == nullptr ||
      bindings.append_native_int_array_range == nullptr ||
      bindings.construct_character_interaction_context == nullptr ||
      bindings.refresh_character_interaction_context == nullptr ||
      bindings.finalize_character_interaction_context == nullptr ||
      bindings.validate_character_interaction_context == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.destroy_character_interaction_context == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0 ||
      bindings.war_declaration_vtable == 0) {
    return DeclareWarResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return DeclareWarResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return DeclareWarResult::no_played_character;
  }
  void *const attacker_character =
      ResolveCharacter(bindings, current.played_character_id);
  void *const target_character =
      ResolveCharacter(bindings, declaration.target_character_id);
  if (target_character == nullptr ||
      LoadAt<void *>(target_character, kCharacterDeathDataOffset) != nullptr) {
    return DeclareWarResult::target_not_found;
  }
  void *const casus_belli_database =
      bindings.get_casus_belli_type_database();
  void *casus_belli_types = nullptr;
  std::int32_t casus_belli_type_count = 0;
  if (attacker_character == nullptr ||
      !ReadCasusBelliDatabase(casus_belli_database, casus_belli_types,
                              casus_belli_type_count)) {
    return DeclareWarResult::unavailable;
  }
  if (declaration.casus_belli_index < 0 ||
      declaration.casus_belli_index >= casus_belli_type_count) {
    return DeclareWarResult::declaration_unavailable;
  }
  void *const casus_belli_type = LoadAt<void *>(
      casus_belli_types,
      static_cast<std::size_t>(declaration.casus_belli_index) *
          sizeof(void *));
  if (!IsEnabledCasusBelliType(casus_belli_type) ||
      !ClearValidCasusBelliConfigurations(bindings)) {
    return DeclareWarResult::declaration_unavailable;
  }
  const bool available = bindings.evaluate_casus_belli(
      casus_belli_type, attacker_character, target_character,
      bindings.valid_casus_belli_configuration_scratch, false, false,
      nullptr);
  std::vector<DeclarableWarSnapshot> current_choices;
  if (!available ||
      !MaterializeCasusBelliChoices(
          bindings, casus_belli_type, declaration.target_character_id,
          declaration.casus_belli_index, current_choices)) {
    ClearValidCasusBelliConfigurations(bindings);
    return DeclareWarResult::declaration_unavailable;
  }
  bool exact_choice = false;
  for (const auto &candidate : current_choices) {
    if (candidate == declaration) {
      exact_choice = true;
      break;
    }
  }
  if (!exact_choice) {
    ClearValidCasusBelliConfigurations(bindings);
    return DeclareWarResult::declaration_unavailable;
  }

  void *const interaction = ResolveCharacterInteraction(
      bindings, bindings.declare_war_interaction_offset);
  if (interaction == nullptr) {
    ClearValidCasusBelliConfigurations(bindings);
    return DeclareWarResult::unavailable;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (bindings.construct_character_interaction_context(
          context, interaction, current.played_character_id,
          declaration.target_character_id, nullptr, true) != context) {
    ClearValidCasusBelliConfigurations(bindings);
    return DeclareWarResult::unavailable;
  }
  void *const war_declaration = LoadAt<void *>(
      context, kCharacterInteractionSpecialDataOffset);
  if (war_declaration == nullptr ||
      LoadAt<std::uintptr_t>(war_declaration, 0) !=
          bindings.war_declaration_vtable) {
    ClearValidCasusBelliConfigurations(bindings);
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::unavailable;
  }

  StoreAt(war_declaration, kWarDeclarationCasusBelliOffset,
          casus_belli_type);
  void *const native_target_titles =
      static_cast<std::byte *>(war_declaration) +
      kWarDeclarationTargetTitlesOffset;
  void *configuration_data = nullptr;
  std::int32_t configuration_count = 0;
  if (!ReadValidCasusBelliConfigurationArray(
          bindings, configuration_data, configuration_count)) {
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::unavailable;
  }
  if (declaration.configuration_index >= 0) {
    if (declaration.configuration_index >= configuration_count) {
      ClearValidCasusBelliConfigurations(bindings);
      bindings.destroy_character_interaction_context(context);
      return DeclareWarResult::declaration_unavailable;
    }
    const auto *const configuration =
        static_cast<const std::byte *>(configuration_data) +
        static_cast<std::size_t>(declaration.configuration_index) *
            kValidCasusBelliConfigurationSize;
    bindings.copy_native_int_array(
        native_target_titles,
        configuration + kValidCasusBelliTargetTitlesOffset);
  } else {
    for (std::int32_t index = 0; index < configuration_count; ++index) {
      const auto *const configuration =
          static_cast<const std::byte *>(configuration_data) +
          static_cast<std::size_t>(index) *
              kValidCasusBelliConfigurationSize;
      const void *const source =
          configuration + kValidCasusBelliTargetTitlesOffset;
      const auto source_count =
          LoadAt<std::int32_t>(source, kNativeArrayCountOffset);
      const auto *const source_data =
          LoadAt<const std::int32_t *>(source, kNativeArrayDataOffset);
      if (source_count <= 0) {
        continue;
      }
      const auto destination_count = LoadAt<std::int32_t>(
          native_target_titles, kNativeArrayCountOffset);
      bindings.append_native_int_array_range(
          native_target_titles, destination_count, source_data,
          source_data + source_count);
    }
  }
  StoreAt(war_declaration, kWarDeclarationClaimantOffset,
          declaration.claimant_character_id);
  if (!ClearValidCasusBelliConfigurations(bindings)) {
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::unavailable;
  }

  bindings.refresh_character_interaction_context(context, true);
  bindings.finalize_character_interaction_context(context);
  if (!bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::validation_failed;
  }

  SendCharacterInteractionCommandStorage command_storage{};
  void *const command = command_storage.bytes.data();
  if (bindings.construct_send_character_interaction_command(command,
                                                             context) !=
          command ||
      LoadAt<std::uintptr_t>(command, 0) !=
          bindings.send_character_interaction_primary_vtable ||
      LoadAt<std::uintptr_t>(command, 0x18) !=
          bindings.send_character_interaction_secondary_vtable) {
    if (LoadAt<void *>(command,
                       kSendCharacterInteractionContextOffset) != nullptr) {
      bindings.destroy_character_interaction_context(
          static_cast<std::byte *>(command) +
          kSendCharacterInteractionContextOffset);
    }
    bindings.destroy_character_interaction_context(context);
    return DeclareWarResult::unavailable;
  }
  bindings.submit_command(bindings.command_manager, command, 0x0E);
  bindings.destroy_character_interaction_context(
      static_cast<std::byte *>(command) +
      kSendCharacterInteractionContextOffset);
  bindings.destroy_character_interaction_context(context);
  return DeclareWarResult::submitted;
}

ReadArrangeMarriageChoicesResult ReadArrangeMarriageChoices(
    const Bindings &bindings,
    std::vector<ArrangeMarriageChoice> &output) noexcept {
  output.clear();
  if (!HasArrangeMarriageReadBindings(bindings)) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadArrangeMarriageChoicesResult::no_played_character;
  }
  if (ResolveCharacterInteraction(
          bindings, bindings.arrange_marriage_interaction_offset) ==
      nullptr) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }
  void *const played_character =
      ResolveCharacter(bindings, current.played_character_id);
  void *const storage = *bindings.character_storage_slot;
  if (played_character == nullptr || storage == nullptr) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity) {
    return ReadArrangeMarriageChoicesResult::unavailable;
  }

  std::vector<ArrangeMarriageChoice> choices;
  for (std::int32_t index = 0; index < capacity; ++index) {
    void *const candidate_character = LoadAt<void *>(
        slots, static_cast<std::size_t>(index) *
                       kComponentStorageSlotSize +
                   kComponentStorageSlotObjectOffset);
    if (candidate_character == nullptr ||
        candidate_character == played_character ||
        LoadAt<void *>(candidate_character, kCharacterDeathDataOffset) !=
            nullptr) {
      continue;
    }
    const auto candidate_character_id =
        LoadAt<std::int32_t>(candidate_character, kCharacterIdOffset);
    if ((static_cast<std::uint32_t>(candidate_character_id) &
         0x00FFFFFFU) != static_cast<std::uint32_t>(index)) {
      continue;
    }

    CharacterInteractionContextStorage context_storage{};
    void *const context = context_storage.bytes.data();
    if (!PrepareArrangeMarriageContext(
            bindings, current.played_character_id,
            candidate_character_id, context_storage)) {
      return ReadArrangeMarriageChoicesResult::unavailable;
    }
    const bool available =
        bindings.validate_character_interaction_context(context, nullptr);
    bindings.destroy_character_interaction_context(context);
    if (!available) {
      continue;
    }
    choices.push_back(
        {current.played_character_id, candidate_character_id});
  }
  output = std::move(choices);
  return ReadArrangeMarriageChoicesResult::available;
}

ArrangeMarriageResult SubmitArrangeMarriage(
    const Bindings &bindings,
    const ArrangeMarriageChoice &choice) noexcept {
  if (!HasArrangeMarriageReadBindings(bindings) ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0) {
    return ArrangeMarriageResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ArrangeMarriageResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ArrangeMarriageResult::no_played_character;
  }
  if (choice.played_character_id != current.played_character_id ||
      choice.candidate_character_id == current.played_character_id) {
    return ArrangeMarriageResult::choice_unavailable;
  }
  void *const candidate_character =
      ResolveCharacter(bindings, choice.candidate_character_id);
  if (candidate_character == nullptr ||
      LoadAt<void *>(candidate_character, kCharacterDeathDataOffset) !=
          nullptr) {
    return ArrangeMarriageResult::candidate_not_found;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (!PrepareArrangeMarriageContext(
          bindings, choice.played_character_id,
          choice.candidate_character_id, context_storage)) {
    return ArrangeMarriageResult::unavailable;
  }
  if (!bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return ArrangeMarriageResult::choice_unavailable;
  }

  SendCharacterInteractionCommandStorage command_storage{};
  void *const command = command_storage.bytes.data();
  if (bindings.construct_send_character_interaction_command(command,
                                                             context) !=
          command ||
      LoadAt<std::uintptr_t>(command, 0) !=
          bindings.send_character_interaction_primary_vtable ||
      LoadAt<std::uintptr_t>(command, 0x18) !=
          bindings.send_character_interaction_secondary_vtable) {
    if (LoadAt<void *>(command,
                       kSendCharacterInteractionContextOffset) != nullptr) {
      bindings.destroy_character_interaction_context(
          static_cast<std::byte *>(command) +
          kSendCharacterInteractionContextOffset);
    }
    bindings.destroy_character_interaction_context(context);
    return ArrangeMarriageResult::unavailable;
  }
  bindings.submit_command(bindings.command_manager, command, 0x0E);
  bindings.destroy_character_interaction_context(
      static_cast<std::byte *>(command) +
      kSendCharacterInteractionContextOffset);
  bindings.destroy_character_interaction_context(context);
  return ArrangeMarriageResult::submitted;
}

EnforceDemandsResult SubmitEnforceDemands(const Bindings &bindings,
                                          std::int32_t war_id) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.contains_war_participant == nullptr ||
      bindings.default_construct_character_interaction_context == nullptr ||
      bindings.construct_war_resolution_interaction_context == nullptr ||
      bindings.validate_character_interaction_context == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.destroy_character_interaction_context == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0) {
    return EnforceDemandsResult::unavailable;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return EnforceDemandsResult::unavailable;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return EnforceDemandsResult::no_played_character;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const war = ResolveWar(bindings, game_state, war_id);
  if (war == nullptr) {
    return EnforceDemandsResult::war_not_found;
  }
  void *const attackers =
      static_cast<std::byte *>(war) + kWarAttackersOffset;
  void *const defenders =
      static_cast<std::byte *>(war) + kWarDefendersOffset;
  if (!bindings.contains_war_participant(
          attackers, current.played_character_id) &&
      !bindings.contains_war_participant(
          defenders, current.played_character_id)) {
    return EnforceDemandsResult::player_not_participant;
  }
  if (LoadAt<std::int32_t>(war, kWarPrimaryAttackerCharacterIdOffset) !=
          current.played_character_id &&
      LoadAt<std::int32_t>(war, kWarPrimaryDefenderCharacterIdOffset) !=
          current.played_character_id) {
    return EnforceDemandsResult::player_not_war_leader;
  }

  CharacterInteractionContextStorage context_storage{};
  void *const context = context_storage.bytes.data();
  if (bindings.default_construct_character_interaction_context(context) !=
      context) {
    return EnforceDemandsResult::unavailable;
  }
  bindings.construct_war_resolution_interaction_context(context, war,
                                                        false);
  if (!bindings.validate_character_interaction_context(context, nullptr)) {
    bindings.destroy_character_interaction_context(context);
    return EnforceDemandsResult::validation_failed;
  }

  SendCharacterInteractionCommandStorage command_storage{};
  void *const command = command_storage.bytes.data();
  if (bindings.construct_send_character_interaction_command(command,
                                                             context) !=
          command ||
      LoadAt<std::uintptr_t>(command, 0) !=
          bindings.send_character_interaction_primary_vtable ||
      LoadAt<std::uintptr_t>(command, 0x18) !=
          bindings.send_character_interaction_secondary_vtable) {
    if (LoadAt<void *>(command,
                       kSendCharacterInteractionContextOffset) != nullptr) {
      bindings.destroy_character_interaction_context(
          static_cast<std::byte *>(command) +
          kSendCharacterInteractionContextOffset);
    }
    bindings.destroy_character_interaction_context(context);
    return EnforceDemandsResult::unavailable;
  }
  bindings.submit_command(bindings.command_manager, command, 0x0E);
  bindings.destroy_character_interaction_context(
      static_cast<std::byte *>(command) +
      kSendCharacterInteractionContextOffset);
  bindings.destroy_character_interaction_context(context);
  return EnforceDemandsResult::submitted;
}

} // namespace xar::ck3_11906

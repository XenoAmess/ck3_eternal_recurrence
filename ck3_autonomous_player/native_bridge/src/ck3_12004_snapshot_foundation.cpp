#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"

#include <windows.h>

#include <cstring>

namespace xar::ck3_12004 {

ck3_12002::CommandBindings BindCommandImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ck3_12002::CommandBindings bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return bindings;
  bindings.command_manager = reinterpret_cast<void *>(
      image_base + kCommandManagerRva12004);
  bindings.queue_owned_command = reinterpret_cast<ck3_12002::QueueOwnedCommand>(
      image_base + kQueueOwnedCommandRva12004);
  bindings.pause_primary_vtable = image_base + kPausePrimaryVtableRva12004;
  bindings.pause_secondary_vtable = image_base + kPauseSecondaryVtableRva12004;
  bindings.set_speed_primary_vtable = image_base + kSetSpeedPrimaryVtableRva12004;
  bindings.set_speed_secondary_vtable = image_base + kSetSpeedSecondaryVtableRva12004;
  bindings.auto_save_primary_vtable = image_base + kAutoSavePrimaryVtableRva12004;
  bindings.auto_save_secondary_vtable = image_base + kAutoSaveSecondaryVtableRva12004;
  bindings.enabled = true;
  return bindings;
}

namespace {
template <typename T>
T LoadEventField(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

bool ReadResourceMemory(void *, std::uintptr_t address, void *output,
                        std::size_t size) noexcept {
  SIZE_T copied = 0;
  return output != nullptr && address != 0 && size != 0 &&
      ReadProcessMemory(GetCurrentProcess(),
          reinterpret_cast<const void *>(address), output, size, &copied) != FALSE &&
      copied == size;
}

bool ReadActiveEvent(const SnapshotEventBindings &bindings,
    game::Snapshot &output) noexcept {
  if (!bindings.core.enabled || bindings.get_current_event == nullptr ||
      bindings.core.game_state_slot == nullptr ||
      *bindings.core.game_state_slot == nullptr) return false;
  void *data = LoadEventField<void *>(*bindings.core.game_state_slot, 0xA0);
  if (data == nullptr) return false;
  void *event = bindings.get_current_event(
      static_cast<std::byte *>(data) + kEventManagerOffset12004);
  if (event == nullptr) return true;
  const auto definition = LoadEventField<void *>(event, 0x1B0);
  if (definition == nullptr) return false;
  const auto id = LoadEventField<std::int32_t>(event, 0x1BC);
  const auto count = LoadEventField<std::int32_t>(definition, 0x1AC);
  if (id <= 0 || count < 0) return false;
  output.has_active_event = true;
  output.active_event_instance_id = id;
  output.active_event_option_count = count;
  return true;
}

bool ReadPendingInteraction(const SnapshotEventBindings &bindings,
    const CoreSnapshotPrefix &core, game::Snapshot &output) noexcept {
  if (!core.has_played_character) return true;
  if (bindings.pending_interaction_storage_slot == nullptr ||
      *bindings.pending_interaction_storage_slot == nullptr ||
      bindings.is_pending_for_character == nullptr ||
      bindings.validate_reply == nullptr) return false;
  void *character = ck3_12004::ResolveCoreCharacter(
      bindings.core, core.played_character_id);
  if (character == nullptr) return false;
  const auto storage = *bindings.pending_interaction_storage_slot;
  const auto slots = LoadEventField<void *>(storage, 0x20);
  const auto capacity = LoadEventField<std::int32_t>(storage, 0x2C);
  if (capacity < 0 || (capacity > 0 && slots == nullptr)) return false;
  for (std::int32_t index = 0; index < capacity; ++index) {
    void *pending = LoadEventField<void *>(slots,
        static_cast<std::size_t>(index) * 0x10 + 8);
    if (pending == nullptr) continue;
    const auto id = LoadEventField<std::int32_t>(pending, 0x10);
    if (id == -1 || (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) !=
        static_cast<std::uint32_t>(index)) continue;
    const auto kind = LoadEventField<std::int32_t>(pending, 0x5C0);
    const auto recipient_offset = kind == 1 ? 0x300U : 0x2F4U;
    if ((kind != 0 && kind != 1 && kind != 2) ||
        LoadEventField<std::int32_t>(pending, recipient_offset) !=
            core.played_character_id ||
        !bindings.is_pending_for_character(pending, character)) continue;
    const bool notification = LoadEventField<std::uint8_t>(pending, 0x5C6) != 0;
    if (!notification) {
      // EVENTS-FIELD-MAP.json closes the actual .4 typed constructor tables
      // and +20 full-ID/+24 enum payload. This command is validated only;
      // no native command is queued or submitted by this reader.
      ck3_12002::EventCommand command{};
      command.primary_vtable = bindings.reply_primary_vtable;
      command.secondary_vtable = bindings.reply_secondary_vtable;
      command.instance_id = id;
      command.choice = 0;
      if (!bindings.validate_reply(&command)) continue;
    }
    output.has_pending_character_interaction = true;
    output.pending_character_interaction_id = id;
    output.pending_sender_character_id =
        LoadEventField<std::int32_t>(pending, 0x2F0);
    output.pending_auto_accept_notification = notification;
    return true;
  }
  return true;
}
} // namespace

SnapshotEventBindings BindSnapshotEventsImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  SnapshotEventBindings bindings{};
  bindings.core = ck3_12004::BindCoreImage(image_base, executable_sha256);
  if (!bindings.core.enabled) return bindings;
  bindings.get_current_event = reinterpret_cast<ck3_12002::GetCurrentEvent>(
      image_base + kGetCurrentEventRva12004);
  bindings.pending_interaction_storage_slot = reinterpret_cast<void **>(
      image_base + kPendingInteractionStorageSlotRva12004);
  bindings.is_pending_for_character =
      reinterpret_cast<ck3_12002::IsPendingInteractionForCharacter>(
          image_base + kIsPendingInteractionForCharacterRva12004);
  bindings.validate_reply = reinterpret_cast<ck3_12002::ValidateReplyInteraction>(
      image_base + kValidateReplyInteractionRva12004);
  bindings.reply_primary_vtable = image_base + kReplyInteractionPrimaryVtableRva12004;
  bindings.reply_secondary_vtable = image_base + kReplyInteractionSecondaryVtableRva12004;
  return bindings;
}

bool ReadEventsSnapshot(const SnapshotEventBindings &bindings,
    game::Snapshot &output) noexcept {
  output.has_active_event = false;
  output.active_event_instance_id = -1;
  output.active_event_option_count = 0;
  output.has_pending_character_interaction = false;
  output.pending_character_interaction_id = -1;
  output.pending_sender_character_id = -1;
  output.pending_auto_accept_notification = false;
  CoreSnapshotPrefix core{};
  if (!ck3_12004::ReadCoreSnapshot(bindings.core, core)) return false;
  if (!core.map_ready) return true;
  return ReadActiveEvent(bindings, output) &&
      ReadPendingInteraction(bindings, core, output);
}

bool ReadActorResourceBalances(const CoreBindings &core,
    std::int32_t played_character_id, ActorResourceBalances &output) noexcept {
  output = {};
  const auto actor = reinterpret_cast<std::uintptr_t>(
      ck3_12004::ResolveCoreCharacter(core, played_character_id));
  // RESOURCE-FAMILY-STRESS-MAP.json proves actual .4 Character+1B0 and
  // extension+100/+130/+110 QWORDs and +2F8 signed DWORD, including lawful
  // null-extension zero. The shared leaf reads only those proven fields;
  // it performs no old-image binding, hash substitution or native dispatch.
  return ck3_12002::ReadActorResourceBalances12002(ReadResourceMemory, nullptr,
      actor, played_character_id, output);
}

bool ReadWarCashTreasury(const CoreBindings &core,
    std::int32_t played_character_id, std::int64_t &gold_raw) noexcept {
  gold_raw = 0;
  ActorResourceBalances resources{};
  if (!ck3_12004::ReadActorResourceBalances(core, played_character_id, resources))
    return false;
  gold_raw = resources.gold_raw;
  return true;
}

SettlementBindings BindSnapshotSettlementImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return {};
  return {true,
      reinterpret_cast<ck3_12002::SettlementGlobalAccessor *>(
          image_base + kSettlementGlobalAccessorSlotRva12004),
      reinterpret_cast<ck3_12002::SettlementIdentifierTableGetter>(
          image_base + kSettlementIdentifierTableGetterRva12004),
      reinterpret_cast<ck3_12002::SettlementIdentifierLookup>(
          image_base + kSettlementIdentifierLookupRva12004)};
}

SettlementReadResult ReadSettlement(const SettlementBindings &bindings,
    const CoreBindings &core, game::Snapshot &output) noexcept {
  // SETTLEMENT-39-PIN-JOIN.json closes NameView, container/entry/variant
  // operands and retained-character identity. The shared software reader
  // calls only the selected .4 accessor/getter/lookup supplied above.
  return ck3_12002::ReadSettlement(bindings, core, output);
}

SnapshotFoundationBindings BindSnapshotFoundationImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  SnapshotFoundationBindings bindings{};
  bindings.core = ck3_12004::BindCoreImage(image_base, executable_sha256);
  if (!bindings.core.enabled) return bindings;
  bindings.events = ck3_12004::BindSnapshotEventsImage(
      image_base, executable_sha256);
  bindings.settlement = ck3_12004::BindSnapshotSettlementImage(
      image_base, executable_sha256);
  bindings.event_traits = person_events::BindImage(image_base, executable_sha256);
  return bindings;
}

} // namespace xar::ck3_12004

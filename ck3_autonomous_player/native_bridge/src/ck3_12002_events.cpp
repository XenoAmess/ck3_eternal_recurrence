#include "xar_bridge/ck3_12002_events.hpp"

#include <cstring>

namespace xar::ck3_12002 {
namespace {
template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset,
              sizeof(result));
  return result;
}

void *Resolve(void **storage_slot, std::int32_t id,
              std::size_t identity_offset) noexcept {
  if (storage_slot == nullptr || *storage_slot == nullptr || id == -1) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  const auto *storage = *storage_slot;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto *slots = Load<void *>(storage, 0x20);
  if (capacity <= 0 || index >= static_cast<std::uint32_t>(capacity) ||
      slots == nullptr) {
    return nullptr;
  }
  void *object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return object != nullptr && Load<std::int32_t>(object, identity_offset) == id
             ? object
             : nullptr;
}

EventCommand MakeReply(const EventsBindings &bindings,
                       std::int32_t id, std::int32_t choice) noexcept {
  EventCommand command{};
  command.primary_vtable = bindings.image_base + kReplyInteractionPrimaryVtableRva;
  command.secondary_vtable = bindings.image_base + kReplyInteractionSecondaryVtableRva;
  command.instance_id = id;
  command.choice = choice;
  return command;
}

bool ReadEvent(const EventsBindings &bindings, bool &found,
               std::int32_t &id, std::int32_t &count) noexcept {
  found = false;
  id = -1;
  count = 0;
  if (!bindings.core.enabled || bindings.get_current_event == nullptr ||
      bindings.core.game_state_slot == nullptr ||
      *bindings.core.game_state_slot == nullptr) {
    return false;
  }
  const auto *state = *bindings.core.game_state_slot;
  const auto *data = Load<void *>(state, 0xA0);
  if (data == nullptr) {
    return false;
  }
  void *event = bindings.get_current_event(
      static_cast<std::byte *>(const_cast<void *>(data)) + kEventManagerOffset);
  if (event == nullptr) {
    return true;
  }
  const auto *definition = Load<void *>(event, 0x1B0);
  if (definition == nullptr) {
    return false;
  }
  id = Load<std::int32_t>(event, 0x1BC);
  count = Load<std::int32_t>(definition, kEventDataOptionCountOffset);
  if (id <= 0 || count < 0) {
    return false;
  }
  found = true;
  return true;
}

bool ReadPending(const EventsBindings &bindings,
                 const CoreSnapshotPrefix &core, game::Snapshot &output) noexcept {
  if (!core.has_played_character) {
    return true;
  }
  if (bindings.pending_interaction_storage_slot == nullptr ||
      *bindings.pending_interaction_storage_slot == nullptr ||
      bindings.is_pending_for_character == nullptr ||
      bindings.validate_reply == nullptr) {
    return false;
  }
  void *character = ResolveEventsCharacter(bindings.core, core.played_character_id);
  if (character == nullptr) {
    return false;
  }
  const auto *storage = *bindings.pending_interaction_storage_slot;
  const auto *slots = Load<void *>(storage, 0x20);
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  if (capacity < 0 || (capacity > 0 && slots == nullptr)) {
    return false;
  }
  for (std::int32_t index = 0; index < capacity; ++index) {
    void *pending = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
    if (pending == nullptr) {
      continue;
    }
    const auto id = Load<std::int32_t>(pending, 0x10);
    if (id == -1 || (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) !=
                       static_cast<std::uint32_t>(index)) {
      continue;
    }
    const auto kind = Load<std::int32_t>(pending, 0x5C0);
    const auto recipient_offset = kind == 1 ? 0x300U : 0x2F4U;
    if ((kind != 0 && kind != 1 && kind != 2) ||
        Load<std::int32_t>(pending, recipient_offset) != core.played_character_id ||
        !bindings.is_pending_for_character(pending, character)) {
      continue;
    }
    const bool notification = Load<std::uint8_t>(pending, 0x5C6) != 0;
    if (!notification) {
      auto command = MakeReply(bindings, id, 0);
      if (!bindings.validate_reply(&command)) {
        continue;
      }
    }
    output.has_pending_character_interaction = true;
    output.pending_character_interaction_id = id;
    output.pending_sender_character_id = Load<std::int32_t>(pending, 0x2F0);
    output.pending_auto_accept_notification = notification;
    return true;
  }
  return true;
}
} // namespace

EventsBindings BindEventsImage(std::uintptr_t image_base,
                              std::string_view sha256) noexcept {
  EventsBindings bindings{};
  bindings.core = BindCoreImage(image_base, sha256);
  if (!bindings.core.enabled) {
    return bindings;
  }
  bindings.image_base = image_base;
  bindings.get_current_event = reinterpret_cast<GetCurrentEvent>(
      image_base + kGetCurrentEventRva);
  bindings.pending_interaction_storage_slot = reinterpret_cast<void **>(
      image_base + kPendingInteractionStorageSlotRva);
  bindings.is_pending_for_character = reinterpret_cast<IsPendingInteractionForCharacter>(
      image_base + kIsPendingInteractionForCharacterRva);
  bindings.validate_reply = reinterpret_cast<ValidateReplyInteraction>(
      image_base + kValidateReplyInteractionRva);
  return bindings;
}

void *ResolveEventsCharacter(const CoreBindings &bindings,
                             std::int32_t id) noexcept {
  return bindings.enabled ? Resolve(bindings.character_storage_slot, id, 0x18)
                          : nullptr;
}
void *ResolveEventsPending(const EventsBindings &bindings,
                           std::int32_t id) noexcept {
  return bindings.core.enabled ? Resolve(bindings.pending_interaction_storage_slot, id, 0x10)
                               : nullptr;
}
void *CurrentEvent(const EventsBindings &bindings) noexcept {
  if (!bindings.core.enabled || bindings.get_current_event == nullptr ||
      bindings.core.game_state_slot == nullptr || *bindings.core.game_state_slot == nullptr) {
    return nullptr;
  }
  void *data = Load<void *>(*bindings.core.game_state_slot, 0xA0);
  return data == nullptr ? nullptr : bindings.get_current_event(
      static_cast<std::byte *>(data) + kEventManagerOffset);
}

bool ReadEventsSnapshot(const EventsBindings &bindings,
                        game::Snapshot &output) noexcept {
  output.has_active_event = false;
  output.active_event_instance_id = -1;
  output.active_event_option_count = 0;
  output.has_pending_character_interaction = false;
  output.pending_character_interaction_id = -1;
  output.pending_sender_character_id = -1;
  output.pending_auto_accept_notification = false;
  CoreSnapshotPrefix core{};
  if (!ReadCoreSnapshot(bindings.core, core)) {
    return false;
  }
  if (!core.map_ready) {
    return true;
  }
  return ReadEvent(bindings, output.has_active_event,
                   output.active_event_instance_id, output.active_event_option_count) &&
         ReadPending(bindings, core, output);
}

game::SelectEventOptionResult SubmitSelectEventOption(
    const EventsBindings &bindings, std::int32_t option_index) noexcept {
  if (bindings.image_base == 0 || bindings.submit_command == nullptr) {
    return game::SelectEventOptionResult::unavailable;
  }
  bool found = false;
  std::int32_t id = -1, count = 0;
  if (!ReadEvent(bindings, found, id, count)) {
    return game::SelectEventOptionResult::unavailable;
  }
  if (!found) {
    return game::SelectEventOptionResult::no_active_event;
  }
  if (option_index < 0 || option_index >= count) {
    return game::SelectEventOptionResult::option_out_of_range;
  }
  EventCommand command{};
  command.primary_vtable = bindings.image_base + kSelectEventOptionPrimaryVtableRva;
  command.secondary_vtable = bindings.image_base + kSelectEventOptionSecondaryVtableRva;
  command.instance_id = id;
  command.choice = option_index;
  return bindings.submit_command(bindings.submit_context, &command, 7)
             ? game::SelectEventOptionResult::submitted
             : game::SelectEventOptionResult::unavailable;
}

game::ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const EventsBindings &bindings, game::PendingInteractionReply reply) noexcept {
  if (bindings.image_base == 0 || bindings.submit_command == nullptr ||
      bindings.validate_reply == nullptr ||
      (reply != game::PendingInteractionReply::accept && reply != game::PendingInteractionReply::reject)) {
    return game::ReplyPendingInteractionResult::unavailable;
  }
  game::Snapshot snapshot{};
  if (!ReadEventsSnapshot(bindings, snapshot)) {
    return game::ReplyPendingInteractionResult::unavailable;
  }
  if (!snapshot.has_pending_character_interaction) {
    return game::ReplyPendingInteractionResult::no_pending_interaction;
  }
  if (snapshot.pending_auto_accept_notification) {
    return game::ReplyPendingInteractionResult::acknowledgement_required;
  }
  auto command = MakeReply(bindings, snapshot.pending_character_interaction_id,
                           static_cast<std::int32_t>(reply));
  if (!bindings.validate_reply(&command)) {
    return game::ReplyPendingInteractionResult::unavailable;
  }
  return bindings.submit_command(bindings.submit_context, &command, 0x0E)
             ? game::ReplyPendingInteractionResult::submitted
             : game::ReplyPendingInteractionResult::unavailable;
}

game::AcknowledgePendingInteractionResult SubmitAcknowledgePendingInteraction(
    const EventsBindings &bindings, std::int32_t id) noexcept {
  using Result = game::AcknowledgePendingInteractionResult;
  if (bindings.image_base == 0 || id == -1 || bindings.submit_command == nullptr) {
    return Result::unavailable;
  }
  CoreSnapshotPrefix core{};
  game::Snapshot snapshot{};
  if (!ReadCoreSnapshot(bindings.core, core) || !ReadEventsSnapshot(bindings, snapshot)) {
    return Result::unavailable;
  }
  if (!core.clock.paused) {
    return Result::requires_paused;
  }
  if (!snapshot.has_pending_character_interaction) {
    return Result::no_pending_interaction;
  }
  if (snapshot.pending_character_interaction_id != id) {
    return Result::pending_interaction_mismatch;
  }
  if (!snapshot.pending_auto_accept_notification) {
    return Result::acknowledgement_not_required;
  }
  void *pending = ResolveEventsPending(bindings, id);
  void *character = ResolveEventsCharacter(bindings.core, core.played_character_id);
  if (pending == nullptr) {
    return Result::state_changed;
  }
  if (character == nullptr || !bindings.is_pending_for_character(pending, character)) {
    return Result::not_for_played_character;
  }
  if (Load<std::int32_t>(pending, 0x10) != id || Load<std::uint8_t>(pending, 0x5C6) == 0) {
    return Result::state_changed;
  }
  auto command = MakeReply(bindings, id, 4);
  return bindings.submit_command(bindings.submit_context, &command, 0x0E)
             ? Result::submitted
             : Result::queue_rejected;
}
} // namespace xar::ck3_12002

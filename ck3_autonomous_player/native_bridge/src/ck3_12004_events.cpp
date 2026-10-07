#include "xar_bridge/ck3_12004_events.hpp"

#include <cstring>

namespace xar::ck3_12004 {
namespace {
template <typename T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

SnapshotEventBindings ReadonlyBindings(const EventsBindings &bindings) noexcept {
  SnapshotEventBindings observed{};
  observed.core = bindings.core;
  observed.get_current_event = bindings.get_current_event;
  observed.pending_interaction_storage_slot =
      bindings.pending_interaction_storage_slot;
  observed.is_pending_for_character = bindings.is_pending_for_character;
  observed.validate_reply = bindings.validate_reply;
  observed.reply_primary_vtable =
      bindings.image_base + kReplyInteractionPrimaryVtableRva12004;
  observed.reply_secondary_vtable =
      bindings.image_base + kReplyInteractionSecondaryVtableRva12004;
  return observed;
}

EventCommand MakeReply(const EventsBindings &bindings, std::int32_t full_id,
                      std::int32_t reply) noexcept {
  EventCommand command{};
  command.primary_vtable =
      bindings.image_base + kReplyInteractionPrimaryVtableRva12004;
  command.secondary_vtable =
      bindings.image_base + kReplyInteractionSecondaryVtableRva12004;
  command.instance_id = full_id;
  command.choice = reply;
  return command;
}

bool ReadPlayedEvent(const EventsBindings &bindings, bool &found,
    std::int32_t &full_id, std::int32_t &option_count) noexcept {
  found = false;
  full_id = -1;
  option_count = 0;
  CoreSnapshotPrefix core{};
  if (!ck3_12004::ReadCoreSnapshot(bindings.core, core) || !core.map_ready ||
      !core.has_played_character || bindings.get_current_event == nullptr ||
      bindings.core.game_state_slot == nullptr ||
      *bindings.core.game_state_slot == nullptr) return false;
  void *data = Load<void *>(*bindings.core.game_state_slot, 0xA0);
  if (data == nullptr) return false;
  void *event = bindings.get_current_event(
      static_cast<std::byte *>(data) + kEventManagerOffset12004);
  if (event == nullptr) return true;
  // The actual .4 native Select UI checks Event+1B8 against the local played
  // CharacterID before constructing its ordinary option command.
  if (Load<std::int32_t>(event, 0x1B8) != core.played_character_id) return false;
  const auto definition = Load<void *>(event, 0x1B0);
  if (definition == nullptr) return false;
  full_id = Load<std::int32_t>(event, 0x1BC);
  option_count = Load<std::int32_t>(definition, 0x1AC);
  if (full_id <= 0 || option_count < 0) return false;
  found = true;
  return true;
}
} // namespace

EventsBindings BindEventsImage(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  EventsBindings bindings{};
  const auto observed = ck3_12004::BindSnapshotEventsImage(
      image_base, executable_sha256);
  bindings.core = observed.core;
  if (!bindings.core.enabled) return bindings;
  bindings.image_base = image_base;
  bindings.get_current_event = observed.get_current_event;
  bindings.pending_interaction_storage_slot =
      observed.pending_interaction_storage_slot;
  bindings.is_pending_for_character = observed.is_pending_for_character;
  bindings.validate_reply = observed.validate_reply;
  // The concrete adapter assigns its member command bundle after move. Never
  // point submit_context at this local temporary or at the binder's caller.
  return bindings;
}

game::SelectEventOptionResult SubmitSelectEventOption(
    const EventsBindings &bindings, std::int32_t option_index) noexcept {
  using Result = game::SelectEventOptionResult;
  if (bindings.image_base == 0 || bindings.submit_command == nullptr)
    return Result::unavailable;
  bool found = false;
  std::int32_t full_id = -1, count = 0;
  if (!ReadPlayedEvent(bindings, found, full_id, count))
    return Result::unavailable;
  if (!found) return Result::no_active_event;
  if (option_index < 0 || option_index >= count)
    return Result::option_out_of_range;
  EventCommand command{};
  command.primary_vtable =
      bindings.image_base + kSelectEventOptionPrimaryVtableRva12004;
  command.secondary_vtable =
      bindings.image_base + kSelectEventOptionSecondaryVtableRva12004;
  command.instance_id = full_id;
  command.choice = option_index;
  return bindings.submit_command(bindings.submit_context, &command, 7)
      ? Result::submitted : Result::unavailable;
}

game::ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const EventsBindings &bindings, game::PendingInteractionReply reply) noexcept {
  using Result = game::ReplyPendingInteractionResult;
  if (bindings.image_base == 0 || bindings.submit_command == nullptr ||
      bindings.validate_reply == nullptr ||
      (reply != game::PendingInteractionReply::accept &&
       reply != game::PendingInteractionReply::reject)) return Result::unavailable;
  game::Snapshot snapshot{};
  if (!ck3_12004::ReadEventsSnapshot(ReadonlyBindings(bindings), snapshot))
    return Result::unavailable;
  if (!snapshot.has_pending_character_interaction)
    return Result::no_pending_interaction;
  if (snapshot.pending_auto_accept_notification)
    return Result::acknowledgement_required;
  auto command = MakeReply(bindings, snapshot.pending_character_interaction_id,
      static_cast<std::int32_t>(reply));
  if (!bindings.validate_reply(&command)) return Result::unavailable;
  return bindings.submit_command(bindings.submit_context, &command, 0x0E)
      ? Result::submitted : Result::unavailable;
}

game::AcknowledgePendingInteractionResult SubmitAcknowledgePendingInteraction(
    const EventsBindings &bindings, std::int32_t full_id) noexcept {
  using Result = game::AcknowledgePendingInteractionResult;
  if (bindings.image_base == 0 || full_id == -1 ||
      bindings.submit_command == nullptr) return Result::unavailable;
  CoreSnapshotPrefix core{};
  game::Snapshot snapshot{};
  if (!ck3_12004::ReadCoreSnapshot(bindings.core, core) ||
      !ck3_12004::ReadEventsSnapshot(ReadonlyBindings(bindings), snapshot))
    return Result::unavailable;
  if (!core.clock.paused) return Result::requires_paused;
  if (!snapshot.has_pending_character_interaction)
    return Result::no_pending_interaction;
  if (snapshot.pending_character_interaction_id != full_id)
    return Result::pending_interaction_mismatch;
  if (!snapshot.pending_auto_accept_notification)
    return Result::acknowledgement_not_required;
  // This shared resolver only reads the caller-supplied storage and compares
  // the complete generation ID; it binds no old image and calls no native code.
  void *pending = ck3_12002::ResolveEventsPending(bindings, full_id);
  void *character = ck3_12004::ResolveCoreCharacter(
      bindings.core, core.played_character_id);
  if (pending == nullptr) return Result::state_changed;
  if (character == nullptr ||
      !bindings.is_pending_for_character(pending, character))
    return Result::not_for_played_character;
  if (Load<std::int32_t>(pending, 0x10) != full_id ||
      Load<std::uint8_t>(pending, 0x5C6) == 0) return Result::state_changed;
  auto command = MakeReply(bindings, full_id, 4);
  return bindings.submit_command(bindings.submit_context, &command, 0x0E)
      ? Result::submitted : Result::queue_rejected;
}

} // namespace xar::ck3_12004

#include "xar_bridge/ck3_1210_commands.hpp"
#include <cstring>

namespace xar::ck3_1210 {
namespace {

template <typename T> T LoadAt(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset,
              sizeof(result));
  return result;
}


} // namespace

TimeCommand MakePauseCommand(const CommandBindings &bindings,
                           std::int32_t player_id, bool paused) noexcept {
  TimeCommand command{};
  command.primary_vtable = bindings.pause_primary_vtable;
  command.secondary_vtable = bindings.pause_secondary_vtable;
  command.flags = 8;
  command.value = player_id;
  command.paused = paused ? 1 : 0;
  return command;
}


CommandBindings BindCommandImage(std::uintptr_t image_base,
                                 std::string_view executable_sha256) noexcept {
  CommandBindings bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return bindings;
  }
  bindings.command_manager =
      reinterpret_cast<void *>(image_base + kCommandManagerRva);
  bindings.queue_owned_command = reinterpret_cast<QueueOwnedCommand>(
      image_base + kQueueOwnedCommandRva);
  bindings.pause_primary_vtable = image_base + kPausePrimaryVtableRva;
  bindings.pause_secondary_vtable = image_base + kPauseSecondaryVtableRva;
  bindings.set_speed_primary_vtable = image_base + kSetSpeedPrimaryVtableRva;
  bindings.set_speed_secondary_vtable = image_base + kSetSpeedSecondaryVtableRva;
  bindings.auto_save_primary_vtable = image_base + kAutoSavePrimaryVtableRva;
  bindings.auto_save_secondary_vtable = image_base + kAutoSaveSecondaryVtableRva;
  bindings.game_speed_count = reinterpret_cast<const std::int32_t *>(
      image_base + kGameSpeedCountRva);
  bindings.enabled = true;
  return bindings;
}

bool DestroyOwnedCommand(void *&command) noexcept {
  if (command == nullptr) {
    return true;
  }
  const auto table = LoadAt<const void *>(command, 0);
  if (table == nullptr) {
    return false;
  }
  const auto destroy = LoadAt<DeleteCommand>(table, 0);
  if (destroy == nullptr) {
    return false;
  }
  void *const owned = command;
  command = nullptr;
  destroy(owned, 1);
  return true;
}

CommandSubmitResult SubmitCommandCopy(const CommandBindings &bindings,
                                      const void *command,
                                      std::uint32_t channel_flags, BeforeQueueV1 before_queue,
                                      void *before_queue_context) noexcept {
  if (!bindings.enabled || bindings.command_manager == nullptr ||
      bindings.queue_owned_command == nullptr || command == nullptr) {
    return CommandSubmitResult::unavailable;
  }
  const auto table = LoadAt<const void *>(command, 0);
  if (table == nullptr) {
    return CommandSubmitResult::unavailable;
  }
  const auto clone = LoadAt<CloneCommand>(table, 0x40);
  if (clone == nullptr) {
    return CommandSubmitResult::unavailable;
  }
  void *clone_storage = nullptr;
  void **const returned_storage = clone(command, &clone_storage);
  if (returned_storage == nullptr || *returned_storage == nullptr) {
    DestroyOwnedCommand(clone_storage);
    return CommandSubmitResult::unavailable;
  }
  // Match Florin A46420..A46498: move ownership out of the clone's return
  // storage before invoking the manager. No bridge allocator participates.
  void *queued_command = *returned_storage;
  *returned_storage = nullptr;
  if (before_queue != nullptr && !before_queue(before_queue_context)) {
    DestroyOwnedCommand(queued_command);
    DestroyOwnedCommand(clone_storage);
    return CommandSubmitResult::unavailable;
  }
  const bool accepted = bindings.queue_owned_command(
      bindings.command_manager, &queued_command, channel_flags);
  DestroyOwnedCommand(queued_command);
  DestroyOwnedCommand(clone_storage);
  return accepted ? CommandSubmitResult::submitted
                  : CommandSubmitResult::rejected;
}

TimeCommand MakeSetSpeedCommand(const CommandBindings &bindings,
    std::int32_t public_speed) noexcept {
  TimeCommand command{};
  command.primary_vtable = bindings.set_speed_primary_vtable;
  command.secondary_vtable = bindings.set_speed_secondary_vtable;
  command.value = public_speed - 1;
  return command;
}

AutoSaveCommand MakeSaveCheckpointCommand(const CommandBindings &bindings) noexcept {
  AutoSaveCommand command{};
  command.primary_vtable = bindings.auto_save_primary_vtable;
  command.secondary_vtable = bindings.auto_save_secondary_vtable;
  constexpr std::size_t length = sizeof(kCheckpointSaveName) - 1;
  static_assert(length < 16);
  std::memcpy(command.save_name.buffer.data(), kCheckpointSaveName, length);
  command.save_name.size = length;
  return command;
}
} // namespace xar::ck3_1210

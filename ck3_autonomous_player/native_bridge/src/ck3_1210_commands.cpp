#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
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
  const auto build=ImageBuildForSha(executable_sha256);
  if (image_base == 0 || build==ImageBuildV1::unknown) {
    return bindings;
  }
  bindings.command_manager =
      reinterpret_cast<void *>(image_base + ImageRva(build,kCommandManagerRva,0x69DBAE0));
  bindings.queue_owned_command = reinterpret_cast<QueueOwnedCommand>(
      image_base + ImageRva(build,kQueueOwnedCommandRva,0x3E184D0));
  bindings.pause_primary_vtable = image_base + ImageRva(build,kPausePrimaryVtableRva,0x4E8C908);
  bindings.pause_secondary_vtable = image_base + ImageRva(build,kPauseSecondaryVtableRva,0x4E8C8D0);
  bindings.set_speed_primary_vtable = image_base + ImageRva(build,kSetSpeedPrimaryVtableRva,0x4E8C838);
  bindings.set_speed_secondary_vtable = image_base + ImageRva(build,kSetSpeedSecondaryVtableRva,0x4E8CA38);
  bindings.auto_save_primary_vtable = image_base + ImageRva(build,kAutoSavePrimaryVtableRva,0x4B3EAA8);
  bindings.auto_save_secondary_vtable = image_base + ImageRva(build,kAutoSaveSecondaryVtableRva,0x4B3EA70);
  bindings.game_speed_count = reinterpret_cast<const std::int32_t *>(
      image_base + ImageRva(build,kGameSpeedCountRva,0x5D3F3EC));
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
  // Match original Florin A46420..A46498 / hotfix A464A0..A46518: move ownership out of the clone's return
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

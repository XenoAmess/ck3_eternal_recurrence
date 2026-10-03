#include "xar_bridge/ck3_12002_commands.hpp"

#include <cstring>

namespace xar::ck3_12002 {
namespace {

template <typename T> T LoadAt(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset,
              sizeof(result));
  return result;
}

TimeCommand MakeBoundPause(const CommandBindings &bindings,
                           std::int32_t player_id, bool paused) noexcept {
  TimeCommand command{};
  command.primary_vtable = bindings.pause_primary_vtable;
  command.secondary_vtable = bindings.pause_secondary_vtable;
  command.flags = 8;
  command.value = player_id;
  command.paused = paused ? 1 : 0;
  return command;
}

} // namespace

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
                                      std::uint32_t channel_flags) noexcept {
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
  // Match 0x9E16C8..0x9E16E7: move ownership out of the clone's return
  // storage before invoking the manager. No bridge allocator participates.
  void *queued_command = *returned_storage;
  *returned_storage = nullptr;
  const bool accepted = bindings.queue_owned_command(
      bindings.command_manager, &queued_command, channel_flags);
  DestroyOwnedCommand(queued_command);
  DestroyOwnedCommand(clone_storage);
  return accepted ? CommandSubmitResult::submitted
                  : CommandSubmitResult::rejected;
}

bool SubmitCommandCopyCompat(void *context, void *command,
                             std::uint32_t channel_flags) noexcept {
  if (context == nullptr) {
    return false;
  }
  return SubmitCommandCopy(*static_cast<CommandBindings *>(context), command,
                           channel_flags) == CommandSubmitResult::submitted;
}

AutoSaveCommand MakeSaveCheckpointCommand(const CommandBindings &bindings)
    noexcept {
  AutoSaveCommand command{};
  command.primary_vtable = bindings.auto_save_primary_vtable;
  command.secondary_vtable = bindings.auto_save_secondary_vtable;
  constexpr std::size_t length = sizeof(kCheckpointSaveName) - 1;
  static_assert(length < 16);
  std::memcpy(command.save_name.buffer.data(), kCheckpointSaveName, length);
  command.save_name.size = length;
  return command;
}

game::PauseSubmitResult SubmitPauseMap(const CommandBindings &commands,
                                     const CoreBindings &core) noexcept {
  CoreSnapshotPrefix snapshot{};
  if (!commands.enabled || commands.pause_primary_vtable == 0 ||
      commands.pause_secondary_vtable == 0 ||
      !ReadCoreSnapshot(core, snapshot) || !snapshot.map_ready ||
      snapshot.local_player_id < 0) {
    return game::PauseSubmitResult::unavailable;
  }
  if (snapshot.clock.paused) {
    return game::PauseSubmitResult::already_paused;
  }
  auto command = MakeBoundPause(commands, snapshot.local_player_id, true);
  return SubmitCommandCopy(commands, &command) == CommandSubmitResult::submitted
             ? game::PauseSubmitResult::submitted
             : game::PauseSubmitResult::unavailable;
}

game::ResumeSubmitResult SubmitResumeMap(const CommandBindings &commands,
                                       const CoreBindings &core) noexcept {
  CoreSnapshotPrefix snapshot{};
  if (!commands.enabled || commands.pause_primary_vtable == 0 ||
      commands.pause_secondary_vtable == 0 ||
      !ReadCoreSnapshot(core, snapshot) || !snapshot.map_ready ||
      snapshot.local_player_id < 0) {
    return game::ResumeSubmitResult::unavailable;
  }
  if (!snapshot.clock.paused) {
    return game::ResumeSubmitResult::already_running;
  }
  auto command = MakeBoundPause(commands, snapshot.local_player_id, false);
  return SubmitCommandCopy(commands, &command) == CommandSubmitResult::submitted
             ? game::ResumeSubmitResult::submitted
             : game::ResumeSubmitResult::unavailable;
}

bool SubmitSetSpeed(const CommandBindings &commands, const CoreBindings &core,
                    std::int32_t public_speed) noexcept {
  CoreSnapshotPrefix snapshot{};
  if (!commands.enabled || commands.set_speed_primary_vtable == 0 ||
      commands.set_speed_secondary_vtable == 0 || public_speed < 1 ||
      public_speed > 5 || !ReadCoreSnapshot(core, snapshot) ||
      !snapshot.map_ready) {
    return false;
  }
  TimeCommand command{};
  command.primary_vtable = commands.set_speed_primary_vtable;
  command.secondary_vtable = commands.set_speed_secondary_vtable;
  command.value = public_speed - 1;
  return SubmitCommandCopy(commands, &command) == CommandSubmitResult::submitted;
}

game::SaveCheckpointResult
SubmitSaveCheckpoint(const CommandBindings &commands,
                     const CoreBindings &core) noexcept {
  CoreSnapshotPrefix snapshot{};
  if (!commands.enabled || commands.auto_save_primary_vtable == 0 ||
      commands.auto_save_secondary_vtable == 0 ||
      !ReadCoreSnapshot(core, snapshot)) {
    return {};
  }
  if (!snapshot.map_ready) {
    return {game::SaveCheckpointStatus::map_not_ready, snapshot.clock.date_raw};
  }
  auto command = MakeSaveCheckpointCommand(commands);
  // The source uses native std::string's 15-byte SSO layout. It never owns
  // a heap allocation; the native clone performs its own deep string copy.
  const auto result = SubmitCommandCopy(commands, &command);
  return {result == CommandSubmitResult::submitted
              ? game::SaveCheckpointStatus::submitted
              : game::SaveCheckpointStatus::unavailable,
          snapshot.clock.date_raw};
}

} // namespace xar::ck3_12002

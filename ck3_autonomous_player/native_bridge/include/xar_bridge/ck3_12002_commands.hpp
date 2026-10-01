#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/game_contract.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr char kCheckpointSaveName[] = "xar_checkpoint";
inline constexpr std::uintptr_t kCommandManagerRva = 0x5CC1240;
inline constexpr std::uintptr_t kQueueOwnedCommandRva = 0x37F06F0;
inline constexpr std::uintptr_t kAutoSavePrimaryVtableRva = 0x44B5148;
inline constexpr std::uintptr_t kAutoSaveSecondaryVtableRva = 0x44B51E0;

// Win64's native command clone writes an owning pointer into its return
// storage and returns the address of that storage (primary vtable +0x40).
using CloneCommand = void **(*)(const void *command, void **return_storage);
using DeleteCommand = void *(*)(void *command, std::uint32_t delete_flags);
// Native queue consumes *owned_command on both acceptance and rejection.
// Its explicit AL return is a queue result, not a gameplay-state result.
using QueueOwnedCommand = bool (*)(void *manager, void **owned_command,
                                  std::uint32_t channel_flags);

struct CommandBindings {
  bool enabled = false;
  void *command_manager = nullptr; // Embedded native object, not a pointer slot.
  QueueOwnedCommand queue_owned_command = nullptr;
  std::uintptr_t pause_primary_vtable = 0;
  std::uintptr_t pause_secondary_vtable = 0;
  std::uintptr_t set_speed_primary_vtable = 0;
  std::uintptr_t set_speed_secondary_vtable = 0;
  std::uintptr_t auto_save_primary_vtable = 0;
  std::uintptr_t auto_save_secondary_vtable = 0;
};

// Address calculation only: no process lookup, module reads or game mutation.
CommandBindings BindCommandImage(std::uintptr_t image_base,
                                 std::string_view executable_sha256) noexcept;

enum class CommandSubmitResult { unavailable, rejected, submitted };

// Owning-thread callers provide a native-layout source object that remains
// caller-owned. The synchronous native clone, queue and residual deleting
// destructor all run through the game's allocator/ownership machinery.
CommandSubmitResult SubmitCommandCopy(const CommandBindings &bindings,
                                      const void *command,
                                      std::uint32_t channel_flags = 7) noexcept;

// For domain bindings that accept a bool(context, command, flags) callback.
// context points to a CommandBindings object owned by the selected adapter.
bool SubmitCommandCopyCompat(void *context, void *command,
                             std::uint32_t channel_flags) noexcept;

// Same scalar-deleting-destructor path used by CK3's owning smart pointer.
// Only for game-allocated command clones; never pass caller-owned storage.
bool DestroyOwnedCommand(void *&command) noexcept;

struct InlineSaveName {
  std::array<char, 16> buffer{};
  std::uint64_t size = 0;
  std::uint64_t capacity = 15;
};

struct alignas(8) AutoSaveCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0x20;
  std::array<std::byte, 15> metadata{};
  std::uintptr_t secondary_vtable = 0;
  InlineSaveName save_name;
};
static_assert(sizeof(InlineSaveName) == 0x20);
static_assert(sizeof(AutoSaveCommand) == 0x40);
static_assert(offsetof(AutoSaveCommand, secondary_vtable) == 0x18);
static_assert(offsetof(AutoSaveCommand, save_name) == 0x20);

AutoSaveCommand MakeSaveCheckpointCommand(const CommandBindings &bindings)
    noexcept;

game::PauseSubmitResult SubmitPauseMap(const CommandBindings &commands,
                                     const CoreBindings &core) noexcept;
game::ResumeSubmitResult SubmitResumeMap(const CommandBindings &commands,
                                       const CoreBindings &core) noexcept;
bool SubmitSetSpeed(const CommandBindings &commands, const CoreBindings &core,
                    std::int32_t public_speed) noexcept;
game::SaveCheckpointResult
SubmitSaveCheckpoint(const CommandBindings &commands,
                     const CoreBindings &core) noexcept;

} // namespace xar::ck3_12002

#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <array>

namespace xar::ck3_1210 {
inline constexpr char kCheckpointSaveName[] = "xar_checkpoint";
inline constexpr std::uintptr_t kCommandManagerRva = 0x69DA8A0;
inline constexpr std::uintptr_t kQueueOwnedCommandRva = 0x3E17850;
inline constexpr std::uintptr_t kPausePrimaryVtableRva = 0x4E8B990;
inline constexpr std::uintptr_t kPauseSecondaryVtableRva = 0x4E8B958;
inline constexpr std::uintptr_t kSetSpeedPrimaryVtableRva = 0x4E8B7F0;
inline constexpr std::uintptr_t kSetSpeedSecondaryVtableRva = 0x4E8B7B8;
inline constexpr std::uintptr_t kAutoSavePrimaryVtableRva = 0x4B3DAA0;
inline constexpr std::uintptr_t kAutoSaveSecondaryVtableRva = 0x4B3DA68;
inline constexpr std::uintptr_t kGameSpeedCountRva = 0x5D3E3EC;
using CloneCommand = void **(*)(const void *, void **);
using DeleteCommand = void *(*)(void *, std::uint32_t);
using QueueOwnedCommand = bool (*)(void *, void **, std::uint32_t);
struct CommandBindings {
  bool enabled = false;
  void *command_manager = nullptr;
  QueueOwnedCommand queue_owned_command = nullptr;
  std::uintptr_t pause_primary_vtable = 0, pause_secondary_vtable = 0;
  std::uintptr_t set_speed_primary_vtable = 0, set_speed_secondary_vtable = 0;
  std::uintptr_t auto_save_primary_vtable = 0, auto_save_secondary_vtable = 0;
  const std::int32_t *game_speed_count = nullptr;
};
struct alignas(8) TimeCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 15> metadata{};
  std::uintptr_t secondary_vtable = 0;
  std::int32_t value = 0;
  std::uint8_t paused = 0;
  std::array<std::byte, 3> tail{};
};
struct InlineSaveName {
  std::array<char, 16> buffer{};
  std::uint64_t size = 0, capacity = 15;
};
struct alignas(8) AutoSaveCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0x20;
  std::array<std::byte, 15> metadata{};
  std::uintptr_t secondary_vtable = 0;
  InlineSaveName save_name;
};
static_assert(sizeof(TimeCommand) == 0x28);
static_assert(offsetof(TimeCommand, secondary_vtable) == 0x18);
static_assert(offsetof(TimeCommand, value) == 0x20);
static_assert(offsetof(TimeCommand, paused) == 0x24);
static_assert(sizeof(AutoSaveCommand) == 0x40);
static_assert(offsetof(AutoSaveCommand, save_name) == 0x20);
static_assert(sizeof(InlineSaveName) == 0x20);
enum class CommandSubmitResult { unavailable, rejected, submitted };
CommandBindings BindCommandImage(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
TimeCommand MakePauseCommand(const CommandBindings &, std::int32_t player_id,
    bool paused) noexcept;
TimeCommand MakeSetSpeedCommand(const CommandBindings &, std::int32_t public_speed) noexcept;
AutoSaveCommand MakeSaveCheckpointCommand(const CommandBindings &) noexcept;
using BeforeQueueV1 = bool (*)(void *) noexcept;
CommandSubmitResult SubmitCommandCopy(const CommandBindings &, const void *,
    std::uint32_t channel_flags = 7, BeforeQueueV1 before_queue = nullptr,
    void *before_queue_context = nullptr) noexcept;
} // namespace xar::ck3_1210

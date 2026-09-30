#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

// Private live-fixture inbox runner. Call only from the existing verified
// paused owning-thread semantic executor; it is not an adapter capability.
inline constexpr char kPrivateFixtureInboxCommand[] = "run xar_mcp_inbox.txt";
inline constexpr std::uintptr_t kConsoleFixtureSlotRva = 0x5C6A590;
inline constexpr std::uintptr_t kConsoleFixtureExecuteRva = 0x388A460;
inline constexpr std::uintptr_t kConsoleFixtureStringAssignRva = 0x855DB0;
inline constexpr std::uintptr_t kConsoleFixtureStringDestroyRva = 0x856050;
inline constexpr std::uintptr_t kConsoleFixtureRandomWrapperSlotRva = 0x54DEFC0;
inline constexpr std::uintptr_t kConsoleFixtureRandomScopeEnterRva = 0x3940340;
inline constexpr std::uintptr_t kConsoleFixtureRandomScopeExitRva = 0xF1B1A0;

struct ConsoleFixtureNativeString {
  std::array<char, 16> storage{};
  std::uint64_t size = 0;
  std::uint64_t capacity = 15;
};
static_assert(sizeof(ConsoleFixtureNativeString) == 0x20);
static_assert(offsetof(ConsoleFixtureNativeString, size) == 0x10);
static_assert(offsetof(ConsoleFixtureNativeString, capacity) == 0x18);

using ConsoleFixtureStringAssign = ConsoleFixtureNativeString *(*)(
    ConsoleFixtureNativeString *, const char *, std::uint64_t length);
using ConsoleFixtureStringDestroy = void (*)(ConsoleFixtureNativeString *);
using ConsoleFixtureExecute = bool (*)(void *console,
                                      const ConsoleFixtureNativeString *command);

// Exact native ALLOW_RANDOM_IN_SCOPE owner + pointer-restoration object.
// The entry function initializes the first 16 bytes. The caller installs the
// owning wrapper, and the native exit restores its prior pointer/ownership.
struct alignas(8) ConsoleFixtureRandomScope {
  void *owner_state = nullptr;
  std::uint8_t owns_owner = 0;
  std::array<std::byte, 7> owner_padding{};
  void **previous_slot_target = nullptr;
  void *previous_value = nullptr;
  std::uint8_t restore_slot = 0;
  std::array<std::byte, 7> tail{};
};
struct alignas(8) ConsoleFixtureSourceLocation {
  std::uint32_t line = 0;
  std::uint32_t column = 0;
  const char *path = nullptr;
  const char *function = nullptr;
  std::uint64_t reserved = 0;
};
static_assert(sizeof(ConsoleFixtureRandomScope) == 0x28);
static_assert(offsetof(ConsoleFixtureRandomScope, owns_owner) == 0x08);
static_assert(offsetof(ConsoleFixtureRandomScope, previous_slot_target) == 0x10);
static_assert(offsetof(ConsoleFixtureRandomScope, previous_value) == 0x18);
static_assert(offsetof(ConsoleFixtureRandomScope, restore_slot) == 0x20);
static_assert(sizeof(ConsoleFixtureSourceLocation) == 0x20);
static_assert(offsetof(ConsoleFixtureSourceLocation, path) == 0x08);
static_assert(offsetof(ConsoleFixtureSourceLocation, function) == 0x10);
using ConsoleFixtureRandomScopeEnter = ConsoleFixtureRandomScope *(*)(
    ConsoleFixtureRandomScope *, void *unused,
    const ConsoleFixtureSourceLocation *);
using ConsoleFixtureRandomScopeExit = void (*)(ConsoleFixtureRandomScope *);

struct ConsoleFixtureBindings {
  bool enabled = false;
  void **console_slot = nullptr;
  ConsoleFixtureStringAssign assign_string = nullptr;
  ConsoleFixtureStringDestroy destroy_string = nullptr;
  ConsoleFixtureExecute execute = nullptr;
  void **random_wrapper_slot = nullptr;
  ConsoleFixtureRandomScopeEnter enter_random_scope = nullptr;
  ConsoleFixtureRandomScopeExit exit_random_scope = nullptr;
};

// Pure exact-build address calculation; never discovers or reads a process.
ConsoleFixtureBindings
BindConsoleFixtureImage(std::uintptr_t image_base,
                        std::string_view executable_sha256) noexcept;

enum class ConsoleFixtureResult {
  unavailable,
  console_unavailable,
  command_rejected,
  executed,
};

// No command/path argument is accepted. The sole operation runs the existing
// mod_bridge inbox in the fixture's CK3 userdir, on the native owning thread.
// executed is the native console-command bool, not a seed-postcondition claim.
ConsoleFixtureResult
RunPrivateInboxFixture(const ConsoleFixtureBindings &bindings) noexcept;

} // namespace xar::ck3_12002

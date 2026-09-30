#include "xar_bridge/ck3_12002_console_fixture.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <atomic>

namespace xar::ck3_12002 {

ConsoleFixtureBindings
BindConsoleFixtureImage(std::uintptr_t image_base,
                        std::string_view executable_sha256) noexcept {
  ConsoleFixtureBindings bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return bindings;
  }
  bindings.console_slot =
      reinterpret_cast<void **>(image_base + kConsoleFixtureSlotRva);
  bindings.assign_string = reinterpret_cast<ConsoleFixtureStringAssign>(
      image_base + kConsoleFixtureStringAssignRva);
  bindings.destroy_string = reinterpret_cast<ConsoleFixtureStringDestroy>(
      image_base + kConsoleFixtureStringDestroyRva);
  bindings.execute = reinterpret_cast<ConsoleFixtureExecute>(
      image_base + kConsoleFixtureExecuteRva);
  bindings.random_wrapper_slot =
      reinterpret_cast<void **>(image_base + kConsoleFixtureRandomWrapperSlotRva);
  bindings.enter_random_scope = reinterpret_cast<ConsoleFixtureRandomScopeEnter>(
      image_base + kConsoleFixtureRandomScopeEnterRva);
  bindings.exit_random_scope = reinterpret_cast<ConsoleFixtureRandomScopeExit>(
      image_base + kConsoleFixtureRandomScopeExitRva);
  bindings.enabled = true;
  return bindings;
}

ConsoleFixtureResult
RunPrivateInboxFixture(const ConsoleFixtureBindings &bindings) noexcept {
  if (!bindings.enabled || bindings.console_slot == nullptr ||
      bindings.assign_string == nullptr || bindings.destroy_string == nullptr ||
      bindings.execute == nullptr || bindings.random_wrapper_slot == nullptr ||
      bindings.enter_random_scope == nullptr ||
      bindings.exit_random_scope == nullptr) {
    return ConsoleFixtureResult::unavailable;
  }
  void *const console = *bindings.console_slot;
  if (console == nullptr) {
    return ConsoleFixtureResult::console_unavailable;
  }
  try {
    ConsoleFixtureRandomScope random_scope{};
    const ConsoleFixtureSourceLocation source{
        __LINE__, 0, "ck3_12002_console_fixture.cpp", "RunPrivateInboxFixture", 0};
    bindings.enter_random_scope(&random_scope, nullptr, &source);
    random_scope.previous_slot_target = bindings.random_wrapper_slot;
    random_scope.previous_value =
        std::atomic_ref<void *>(*bindings.random_wrapper_slot)
            .exchange(&random_scope, std::memory_order_seq_cst);
    random_scope.restore_slot = 1;
    struct NativeRandomScopeLifetime {
      const ConsoleFixtureBindings &bindings;
      ConsoleFixtureRandomScope &scope;
      ~NativeRandomScopeLifetime() { bindings.exit_random_scope(&scope); }
    } random_lifetime{bindings, random_scope};
    ConsoleFixtureNativeString command{};
    struct NativeStringLifetime {
      const ConsoleFixtureBindings &bindings;
      ConsoleFixtureNativeString &command;
      ~NativeStringLifetime() { bindings.destroy_string(&command); }
    } string_lifetime{bindings, command};
    constexpr std::uint64_t length = sizeof(kPrivateFixtureInboxCommand) - 1;
    static_assert(length == 21);
    // Native std::string assignment allocates its 21-byte payload through
    // the game allocator, and the native destructor releases that payload.
    bindings.assign_string(&command, kPrivateFixtureInboxCommand, length);
    return bindings.execute(console, &command)
               ? ConsoleFixtureResult::executed
               : ConsoleFixtureResult::command_rejected;
  } catch (...) {
    return ConsoleFixtureResult::unavailable;
  }
}

} // namespace xar::ck3_12002

#include "xar_bridge/ck3_12002_console_fixture.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace {
using namespace xar::ck3_12002;
struct FixtureConsole {
  bool accept = true;
  bool throw_execution = false;
  std::size_t calls = 0;
  std::size_t allocations = 0;
  std::size_t frees = 0;
  std::size_t scope_enters = 0;
  std::size_t scope_exits = 0;
  std::uint32_t random_owner = 0;
  void *random_wrapper = nullptr;
  std::string_view last_command;
};
FixtureConsole *fixture = nullptr;

ConsoleFixtureRandomScope *EnterFixtureRandomScope(
    ConsoleFixtureRandomScope *scope, void *unused,
    const ConsoleFixtureSourceLocation *source) {
  if (unused != nullptr || source == nullptr || source->path == nullptr ||
      source->function == nullptr || source->line == 0 ||
      (fixture->random_owner != 0 && fixture->random_owner != 77)) {
    std::terminate();
  }
  scope->owner_state = &fixture->random_owner;
  scope->owns_owner = fixture->random_owner == 0 ? 1 : 0;
  fixture->random_owner = 77;
  ++fixture->scope_enters;
  return scope;
}
void ExitFixtureRandomScope(ConsoleFixtureRandomScope *scope) {
  if (scope->owner_state != &fixture->random_owner ||
      fixture->random_wrapper != scope || !scope->restore_slot ||
      scope->previous_slot_target != &fixture->random_wrapper ||
      fixture->random_owner != 77) {
    std::terminate();
  }
  *scope->previous_slot_target = scope->previous_value;
  if (scope->owns_owner) {
    fixture->random_owner = 0;
  }
  ++fixture->scope_exits;
}

ConsoleFixtureNativeString *AssignFixtureString(
    ConsoleFixtureNativeString *output, const char *input, std::uint64_t size) {
  if (output->size != 0 || output->capacity != 15 || size != 21 ||
      std::string_view(input, size) != kPrivateFixtureInboxCommand) {
    std::terminate();
  }
  auto *heap = new char[32];
  std::memcpy(heap, input, size);
  heap[size] = '\0';
  std::memcpy(output->storage.data(), &heap, sizeof(heap));
  output->size = size;
  output->capacity = 31;
  ++fixture->allocations;
  return output;
}
void DestroyFixtureString(ConsoleFixtureNativeString *command) {
  if (command->capacity >= 16) {
    char *heap = nullptr;
    std::memcpy(&heap, command->storage.data(), sizeof(heap));
    delete[] heap;
    ++fixture->frees;
  }
  *command = {};
}
bool ExecuteFixtureConsole(void *console,
                          const ConsoleFixtureNativeString *command) {
  if (console != fixture || command->size != 21 || command->capacity != 31) {
    std::terminate();
  }
  const auto *scope = static_cast<const ConsoleFixtureRandomScope *>(
      fixture->random_wrapper);
  if (scope == nullptr || scope->owner_state != &fixture->random_owner ||
      fixture->random_owner != 77 || !scope->restore_slot) {
    std::terminate();
  }
  const char *heap = nullptr;
  std::memcpy(&heap, command->storage.data(), sizeof(heap));
  if (std::string_view(heap, command->size) != kPrivateFixtureInboxCommand ||
      heap[command->size] != '\0') {
    std::terminate();
  }
  ++fixture->calls;
  // Store a view to the immutable fixed literal, rather than retaining the
  // native temporary after the executor returns.
  fixture->last_command = kPrivateFixtureInboxCommand;
  if (fixture->throw_execution) {
    throw std::runtime_error("synthetic native execution failure");
  }
  return fixture->accept;
}
bool CheckFixture() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto native = BindConsoleFixtureImage(base, kExecutableSha256);
  if (!native.enabled ||
      reinterpret_cast<std::uintptr_t>(native.console_slot) !=
          base + kConsoleFixtureSlotRva ||
      reinterpret_cast<std::uintptr_t>(native.execute) !=
          base + kConsoleFixtureExecuteRva ||
      reinterpret_cast<std::uintptr_t>(native.random_wrapper_slot) !=
          base + kConsoleFixtureRandomWrapperSlotRva ||
      reinterpret_cast<std::uintptr_t>(native.enter_random_scope) !=
          base + kConsoleFixtureRandomScopeEnterRva ||
      reinterpret_cast<std::uintptr_t>(native.exit_random_scope) !=
          base + kConsoleFixtureRandomScopeExitRva ||
      BindConsoleFixtureImage(0, kExecutableSha256).enabled ||
      BindConsoleFixtureImage(base, "1.19.0.6").enabled) {
    return false;
  }
  FixtureConsole console{};
  fixture = &console;
  void *console_pointer = &console;
  ConsoleFixtureBindings bindings{true, &console_pointer, &AssignFixtureString,
                                  &DestroyFixtureString, &ExecuteFixtureConsole,
                                  &console.random_wrapper,
                                  &EnterFixtureRandomScope,
                                  &ExitFixtureRandomScope};
  if (RunPrivateInboxFixture(bindings) != ConsoleFixtureResult::executed ||
      console.calls != 1 || console.allocations != 1 || console.frees != 1 ||
      console.last_command != kPrivateFixtureInboxCommand ||
      console.scope_enters != 1 || console.scope_exits != 1 ||
      console.random_owner != 0 || console.random_wrapper != nullptr) {
    return false;
  }
  console.accept = false;
  if (RunPrivateInboxFixture(bindings) !=
          ConsoleFixtureResult::command_rejected ||
      console.calls != 2 || console.allocations != 2 || console.frees != 2 ||
      console.scope_enters != 2 || console.scope_exits != 2 ||
      console.random_owner != 0 || console.random_wrapper != nullptr) {
    return false;
  }
  ConsoleFixtureRandomScope outer_scope{};
  outer_scope.owner_state = &console.random_owner;
  console.random_owner = 77;
  console.random_wrapper = &outer_scope;
  console.accept = true;
  if (RunPrivateInboxFixture(bindings) != ConsoleFixtureResult::executed ||
      console.calls != 3 || console.allocations != 3 || console.frees != 3 ||
      console.scope_enters != 3 || console.scope_exits != 3 ||
      console.random_owner != 77 || console.random_wrapper != &outer_scope) {
    return false;
  }
  console.random_owner = 0;
  console.random_wrapper = nullptr;
  console.throw_execution = true;
  if (RunPrivateInboxFixture(bindings) != ConsoleFixtureResult::unavailable ||
      console.calls != 4 || console.allocations != 4 || console.frees != 4 ||
      console.scope_enters != 4 || console.scope_exits != 4 ||
      console.random_owner != 0 || console.random_wrapper != nullptr) {
    return false;
  }
  console_pointer = nullptr;
  if (RunPrivateInboxFixture(bindings) !=
          ConsoleFixtureResult::console_unavailable ||
      console.calls != 4 || console.allocations != 4 || console.frees != 4 ||
      console.scope_enters != 4 || console.scope_exits != 4) {
    return false;
  }
  bindings.enabled = false;
  return RunPrivateInboxFixture(bindings) == ConsoleFixtureResult::unavailable;
}
} // namespace

int main() {
  if (!CheckFixture()) {
    std::cerr << "Private fixed inbox console fixture failed\n";
    return 1;
  }
  std::cout << "Private fixed inbox console fixture passed: exact fixed "
               "21-byte command, native allocation/execute/destruction shape, "
               "native RNG owner/scope installation/restoration, acceptance, "
               "rejection, nesting and exception cleanup; no game access\n";
  return 0;
}

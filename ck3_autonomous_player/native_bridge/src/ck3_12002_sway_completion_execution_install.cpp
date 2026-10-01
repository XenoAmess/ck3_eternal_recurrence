#include "xar_bridge/ck3_12002_sway_completion_execution_install.hpp"

#include <atomic>
#include <cstring>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
std::atomic<SwayCompletionExecutionInstall12002 *> observer{nullptr};
// Retain the original target through uninstall so a wrapper already entered
// can still forward. The root pins the DLL and owns state through process exit.
std::array<SwayCompletionNativeExecute12002, 3> native_originals{};

void Invoke(std::size_t index, const void *effect, const void *context) {
  const auto original = native_originals[index];
  auto *const state = observer.load(std::memory_order_acquire);
  if (state != nullptr && state->attached && state->recorder != nullptr) {
    (void)CaptureAndRecordSwayCompletionExecution12002(
        state->bindings, effect, context, *state->recorder);
  }
  // The original callback is never skipped for ignored/unavailable captures.
  if (original != nullptr) original(effect, context);
}
void Message(const void *effect, const void *context) { Invoke(0, effect, context); }
void Toast(const void *effect, const void *context) { Invoke(1, effect, context); }
void Popup(const void *effect, const void *context) { Invoke(2, effect, context); }
constexpr std::array<SwayCompletionNativeExecute12002, 3> wrappers{
    &Message, &Toast, &Popup};

bool LoadSlot(SwayCompletionNativeExecute12002 *slot,
              SwayCompletionNativeExecute12002 &value) noexcept {
  if (slot == nullptr) return false;
  __try { std::memcpy(&value, slot, sizeof(value)); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

bool WriteSlot(SwayCompletionNativeExecute12002 *slot,
               SwayCompletionNativeExecute12002 expected,
               SwayCompletionNativeExecute12002 replacement,
               bool &changed) noexcept {
  changed = false;
  DWORD previous{};
  if (!VirtualProtect(slot, sizeof(*slot), PAGE_READWRITE, &previous)) return false;
  const auto found = InterlockedCompareExchangePointer(
      reinterpret_cast<void *volatile *>(slot),
      reinterpret_cast<void *>(replacement), reinterpret_cast<void *>(expected));
  changed = found == reinterpret_cast<void *>(expected);
  DWORD ignored{};
  const bool restored = VirtualProtect(slot, sizeof(*slot), previous, &ignored) != FALSE;
  return changed && restored;
}

bool Install(const SwayExecutionBindings12002 &bindings,
             const std::array<SwayCompletionNativeExecute12002 *, 3> &slots,
             const std::array<SwayCompletionNativeExecute12002, 3> &originals,
             SwayExecutionRecorder12002 &recorder,
             SwayCompletionExecutionInstall12002 &state,
             bool fixture) noexcept {
  if (observer.load(std::memory_order_acquire) != nullptr || state.attached) {
    state.unavailable_reason = "sway_execution_observer_already_installed";
    return false;
  }
  if (!bindings.enabled || !bindings.core.enabled || bindings.image_base == 0) {
    state.unavailable_reason = "sway_execution_install_unsupported_build";
    return false;
  }
  for (std::size_t index = 0; index < slots.size(); ++index) {
    SwayCompletionNativeExecute12002 current{};
    if (originals[index] == nullptr || !LoadSlot(slots[index], current) ||
        current != originals[index]) {
      state.unavailable_reason = "sway_execution_install_native_slot_mismatch";
      return false;
    }
  }
  state.bindings = bindings;
  state.recorder = &recorder;
  state.slots = slots;
  state.originals = originals;
  state.fixture_slots = fixture;
  native_originals = originals;
  recorder.SetObserverAttached(false);
  observer.store(&state, std::memory_order_release);
  for (std::size_t index = 0; index < slots.size(); ++index) {
    bool changed{};
    const bool written = WriteSlot(slots[index], originals[index], wrappers[index], changed);
    state.patched[index] = changed;
    if (!written) {
      (void)UninstallSwayCompletionExecution12002(state);
      state.unavailable_reason = "sway_execution_install_slot_write_failed";
      return false;
    }
  }
  state.attached = true;
  state.unavailable_reason = "";
  recorder.SetObserverAttached(true);
  return true;
}
} // namespace

bool InstallSwayCompletionExecution12002(
    std::uintptr_t base, std::string_view sha, SwayExecutionRecorder12002 &recorder,
    SwayCompletionExecutionInstall12002 &state) noexcept {
  const auto bindings = BindSwayExecutionImage12002(base, sha);
  if (!bindings.enabled) {
    state.unavailable_reason = "sway_execution_install_unsupported_build";
    return false;
  }
  std::array<SwayCompletionNativeExecute12002 *, 3> slots{};
  std::array<SwayCompletionNativeExecute12002, 3> originals{};
  for (std::size_t index = 0; index < slots.size(); ++index) {
    slots[index] = reinterpret_cast<SwayCompletionNativeExecute12002 *>(
        base + kSwayCompletionExecuteSlotRvas12002[index]);
    originals[index] = reinterpret_cast<SwayCompletionNativeExecute12002>(
        base + kSwayCompletionExecuteRvas12002[index]);
  }
  return Install(bindings, slots, originals, recorder, state, false);
}

bool InstallSwayCompletionExecutionFixture12002(
    const SwayExecutionBindings12002 &bindings,
    const std::array<SwayCompletionNativeExecute12002 *, 3> &slots,
    const std::array<SwayCompletionNativeExecute12002, 3> &originals,
    SwayExecutionRecorder12002 &recorder,
    SwayCompletionExecutionInstall12002 &state) noexcept {
  return Install(bindings, slots, originals, recorder, state, true);
}

bool UninstallSwayCompletionExecution12002(
    SwayCompletionExecutionInstall12002 &state) noexcept {
  auto *const current = observer.load(std::memory_order_acquire);
  if (current != nullptr && current != &state) {
    state.unavailable_reason = "sway_execution_install_state_not_owner";
    return false;
  }
  state.attached = false;
  if (state.recorder != nullptr) state.recorder->SetObserverAttached(false);
  bool complete = true;
  for (std::size_t index = 0; index < state.slots.size(); ++index) {
    if (!state.patched[index]) continue;
    bool changed{};
    const bool written = WriteSlot(state.slots[index], wrappers[index],
                                  state.originals[index], changed);
    if (changed) state.patched[index] = false;
    complete = complete && written;
  }
  if (complete) {
    observer.store(nullptr, std::memory_order_release);
    state.unavailable_reason = "sway_execution_observer_not_installed";
  } else {
    state.unavailable_reason = "sway_execution_uninstall_slot_restore_failed";
  }
  return complete;
}

} // namespace xar::ck3_12002

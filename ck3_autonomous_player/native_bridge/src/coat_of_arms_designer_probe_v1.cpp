#include "xar_bridge/coat_of_arms_designer_probe_v1.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_11906 {
namespace {

using NativeUpdatePasteContentsV1 = void(__fastcall *)(void *);
using NativePasteFromClipboardV1 = void(__fastcall *)(void *);
using NativeCopyToClipboardV1 = void(__fastcall *)(void *);
using NativeClipboardWriteV1 = void(__fastcall *)(const char *);
using NativeClipboardReadV1 = char *(__fastcall *)();
using NativeClipboardFreeV1 = void(__fastcall *)(char *);

std::atomic<CoatOfArmsDesignerProbeHookStateV1 *> g_active_hook_state{nullptr};

constexpr std::array<std::uint8_t, kCoatOfArmsUpdatePastePatchBytesV1>
    kExpectedUpdatePastePrologueV1{
        0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x7C, 0x24, 0x18,
        0x55, 0x48, 0x8D, 0xAC, 0x24, 0x40, 0xFE, 0xFF, 0xFF,
    };
constexpr std::array<std::uint8_t, 23> kExpectedPastePrologueV1{
    0x48, 0x89, 0x5C, 0x24, 0x18, 0x57, 0x48, 0x81, 0xEC, 0x90, 0x00, 0x00,
    0x00, 0x48, 0x8B, 0xF9, 0x80, 0xB9, 0xEF, 0x00, 0x00, 0x00, 0x00,
};
constexpr std::array<std::uint8_t, 22> kExpectedCopyPrologueV1{
    0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57,
    0x48, 0x81, 0xEC, 0xD0, 0x00, 0x00, 0x00, 0x48, 0x8B, 0xF1,
};

constexpr std::size_t kAbsoluteJumpBytesV1 = 14;
constexpr std::size_t kTrampolineBytesV1 =
    kCoatOfArmsUpdatePastePatchBytesV1 + kAbsoluteJumpBytesV1;

void WriteAbsoluteJump(std::uint8_t *destination, const void *target) noexcept {
  destination[0] = 0xFF;
  destination[1] = 0x25;
  destination[2] = 0;
  destination[3] = 0;
  destination[4] = 0;
  destination[5] = 0;
  const auto address = reinterpret_cast<std::uintptr_t>(target);
  std::memcpy(destination + 6, &address, sizeof(address));
}

bool IsReadableRange(const void *address, std::size_t bytes) noexcept {
  if (address == nullptr || bytes == 0)
    return false;
  MEMORY_BASIC_INFORMATION information{};
  if (VirtualQuery(address, &information, sizeof(information)) !=
          sizeof(information) ||
      information.State != MEM_COMMIT ||
      (information.Protect & (PAGE_GUARD | PAGE_NOACCESS)) != 0) {
    return false;
  }
  const auto begin = reinterpret_cast<std::uintptr_t>(address);
  const auto region_begin =
      reinterpret_cast<std::uintptr_t>(information.BaseAddress);
  const auto region_end = region_begin + information.RegionSize;
  return begin >= region_begin && begin <= region_end &&
         bytes <= region_end - begin;
}

bool IsExecutableAddress(const void *address) noexcept {
  if (!IsReadableRange(address, 1))
    return false;
  MEMORY_BASIC_INFORMATION information{};
  if (VirtualQuery(address, &information, sizeof(information)) !=
      sizeof(information)) {
    return false;
  }
  const DWORD protection = information.Protect & 0xFFU;
  return protection == PAGE_EXECUTE || protection == PAGE_EXECUTE_READ ||
         protection == PAGE_EXECUTE_READWRITE ||
         protection == PAGE_EXECUTE_WRITECOPY;
}

bool ClipboardFunctionsAvailable(
    const CoatOfArmsDesignerProbeHookStateV1 &hook) noexcept {
  if (!IsReadableRange(hook.clipboard_write_slot, sizeof(void *)) ||
      !IsReadableRange(hook.clipboard_read_slot, sizeof(void *)) ||
      !IsReadableRange(hook.clipboard_free_slot, sizeof(void *))) {
    return false;
  }
  auto *const write = *static_cast<void *const *>(hook.clipboard_write_slot);
  auto *const read = *static_cast<void *const *>(hook.clipboard_read_slot);
  auto *const free = *static_cast<void *const *>(hook.clipboard_free_slot);
  return IsExecutableAddress(write) && IsExecutableAddress(read) &&
         IsExecutableAddress(free);
}

bool ClipboardReadbackMatches(const CoatOfArmsDesignerProbeHookStateV1 &hook,
                              std::string_view expected) noexcept {
  const auto read = reinterpret_cast<NativeClipboardReadV1>(
      *static_cast<void *const *>(hook.clipboard_read_slot));
  const auto free = reinterpret_cast<NativeClipboardFreeV1>(
      *static_cast<void *const *>(hook.clipboard_free_slot));
  char *const text = read();
  if (text == nullptr)
    return false;
  bool matches = false;
  if (IsReadableRange(text, expected.size() + 1)) {
    matches = std::memcmp(text, expected.data(), expected.size()) == 0 &&
              text[expected.size()] == '\0';
  }
  free(text);
  return matches;
}

bool ClipboardReadText(const CoatOfArmsDesignerProbeHookStateV1 &hook,
                       std::string &output) noexcept {
  const auto read = reinterpret_cast<NativeClipboardReadV1>(
      *static_cast<void *const *>(hook.clipboard_read_slot));
  const auto free = reinterpret_cast<NativeClipboardFreeV1>(
      *static_cast<void *const *>(hook.clipboard_free_slot));
  char *const text = read();
  if (text == nullptr)
    return false;
  bool valid = false;
  output.clear();
  if (IsReadableRange(text, 1)) {
    for (std::size_t index = 0;
         index <= kCoatOfArmsProbeMaximumSourceBytesV1; ++index) {
      if (!IsReadableRange(text + index, 1))
        break;
      const auto byte = static_cast<unsigned char>(text[index]);
      if (byte == 0) {
        valid = !output.empty();
        break;
      }
      if (byte >= 0x80U)
        break;
      output.push_back(static_cast<char>(byte));
    }
  }
  free(text);
  if (!valid)
    output.clear();
  return valid;
}

void CompleteRequest(CoatOfArmsDesignerProbeHookStateV1 &hook,
                     CoatOfArmsDesignerProbeRequestV1 &request) noexcept {
  request.state.store(CoatOfArmsDesignerProbeRequestStateV1::completed,
                      std::memory_order_release);
  auto *expected = &request;
  hook.pending_request.compare_exchange_strong(
      expected, nullptr, std::memory_order_acq_rel, std::memory_order_acquire);
  if (request.completion_event != nullptr)
    SetEvent(request.completion_event);
}

} // namespace

bool InstallCoatOfArmsDesignerProbeHookV1(
    CoatOfArmsDesignerProbeHookStateV1 &state, std::uintptr_t module_base,
    bool exact_build_admitted) noexcept {
  if (state.installed.load(std::memory_order_acquire))
    return true;
  state.module_base = module_base;
  state.exact_build_admitted = exact_build_admitted;
  if (!exact_build_admitted || module_base == 0) {
    state.failure_flags.fetch_or(coat_of_arms_probe_install_failure_exact_build,
                                 std::memory_order_release);
    return false;
  }
  state.failure_flags.store(coat_of_arms_probe_install_failure_none,
                            std::memory_order_release);

  auto *const update_target = reinterpret_cast<std::uint8_t *>(
      module_base + kCoatOfArmsUpdatePasteContentsRvaV1);
  auto *const paste_target = reinterpret_cast<std::uint8_t *>(
      module_base + kCoatOfArmsPasteFromClipboardRvaV1);
  auto *const copy_target = reinterpret_cast<std::uint8_t *>(
      module_base + kCoatOfArmsCopyToClipboardRvaV1);
  auto *const write_slot =
      reinterpret_cast<void **>(module_base + kClipboardWriteFunctionSlotRvaV1);
  auto *const read_slot =
      reinterpret_cast<void **>(module_base + kClipboardReadFunctionSlotRvaV1);
  auto *const free_slot =
      reinterpret_cast<void **>(module_base + kClipboardFreeFunctionSlotRvaV1);
  if (!IsReadableRange(update_target, kExpectedUpdatePastePrologueV1.size()) ||
      std::memcmp(update_target, kExpectedUpdatePastePrologueV1.data(),
                  kExpectedUpdatePastePrologueV1.size()) != 0) {
    state.failure_flags.fetch_or(
        coat_of_arms_probe_install_failure_update_target_identity,
        std::memory_order_release);
    return false;
  }
  if (!IsReadableRange(paste_target, kExpectedPastePrologueV1.size()) ||
      std::memcmp(paste_target, kExpectedPastePrologueV1.data(),
                  kExpectedPastePrologueV1.size()) != 0) {
    state.failure_flags.fetch_or(
        coat_of_arms_probe_install_failure_paste_target_identity,
        std::memory_order_release);
    return false;
  }
  if (!IsReadableRange(copy_target, kExpectedCopyPrologueV1.size()) ||
      std::memcmp(copy_target, kExpectedCopyPrologueV1.data(),
                  kExpectedCopyPrologueV1.size()) != 0) {
    state.failure_flags.fetch_or(
        coat_of_arms_probe_install_failure_copy_target_identity,
        std::memory_order_release);
    return false;
  }
  state.clipboard_write_slot = write_slot;
  state.clipboard_read_slot = read_slot;
  state.clipboard_free_slot = free_slot;
  if (!ClipboardFunctionsAvailable(state)) {
    state.failure_flags.fetch_or(
        coat_of_arms_probe_install_failure_clipboard_functions,
        std::memory_order_release);
    return false;
  }

  auto *const trampoline = static_cast<std::uint8_t *>(
      VirtualAlloc(nullptr, kTrampolineBytesV1, MEM_COMMIT | MEM_RESERVE,
                   PAGE_EXECUTE_READWRITE));
  if (trampoline == nullptr) {
    state.failure_flags.fetch_or(coat_of_arms_probe_install_failure_trampoline,
                                 std::memory_order_release);
    return false;
  }
  std::memcpy(state.original_bytes.data(), update_target,
              kCoatOfArmsUpdatePastePatchBytesV1);
  std::memcpy(trampoline, state.original_bytes.data(),
              kCoatOfArmsUpdatePastePatchBytesV1);
  WriteAbsoluteJump(trampoline + kCoatOfArmsUpdatePastePatchBytesV1,
                    update_target + kCoatOfArmsUpdatePastePatchBytesV1);

  DWORD old_protect = 0;
  if (VirtualProtect(update_target, kCoatOfArmsUpdatePastePatchBytesV1,
                     PAGE_EXECUTE_READWRITE, &old_protect) == FALSE) {
    VirtualFree(trampoline, 0, MEM_RELEASE);
    state.failure_flags.fetch_or(
        coat_of_arms_probe_install_failure_page_protect,
        std::memory_order_release);
    return false;
  }

  state.update_target = update_target;
  state.update_trampoline = trampoline;
  state.paste_from_clipboard = paste_target;
  state.copy_to_clipboard = copy_target;
  g_active_hook_state.store(&state, std::memory_order_release);
  WriteAbsoluteJump(update_target, &XarCoatOfArmsUpdatePasteContentsHookV1);
  for (std::size_t index = kAbsoluteJumpBytesV1;
       index < kCoatOfArmsUpdatePastePatchBytesV1; ++index) {
    update_target[index] = 0x90;
  }
  FlushInstructionCache(GetCurrentProcess(), update_target,
                        kCoatOfArmsUpdatePastePatchBytesV1);
  DWORD ignored = 0;
  VirtualProtect(update_target, kCoatOfArmsUpdatePastePatchBytesV1, old_protect,
                 &ignored);
  state.installed.store(true, std::memory_order_release);
  return true;
}

bool RetryDeferredCoatOfArmsDesignerProbeHookV1(
    CoatOfArmsDesignerProbeHookStateV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire))
    return true;
  if (state.failure_flags.load(std::memory_order_acquire) !=
      coat_of_arms_probe_install_failure_clipboard_functions) {
    return false;
  }
  return InstallCoatOfArmsDesignerProbeHookV1(
      state, state.module_base, state.exact_build_admitted);
}

CoatOfArmsDesignerProbeSubmitResultV1 TrySubmitCoatOfArmsDesignerProbeV1(
    CoatOfArmsDesignerProbeHookStateV1 &hook,
    CoatOfArmsDesignerProbeRequestV1 &request) noexcept {
  if (!hook.installed.load(std::memory_order_acquire) ||
      hook.failure_flags.load(std::memory_order_acquire) != 0) {
    return CoatOfArmsDesignerProbeSubmitResultV1::hook_unavailable;
  }
  const bool valid_probe =
      request.operation == CoatOfArmsDesignerOperationV1::probe_source &&
      !request.source.empty() &&
      request.source.size() <= kCoatOfArmsProbeMaximumSourceBytesV1 &&
      request.source.find('\0') == std::string::npos;
  const bool valid_export =
      request.operation == CoatOfArmsDesignerOperationV1::export_current &&
      request.source.empty() && !request.apply;
  if ((!valid_probe && !valid_export) ||
      request.state.load(std::memory_order_acquire) !=
          CoatOfArmsDesignerProbeRequestStateV1::idle ||
      request.completion_event != nullptr) {
    return CoatOfArmsDesignerProbeSubmitResultV1::invalid_request;
  }
  request.completion_event = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  if (request.completion_event == nullptr) {
    return CoatOfArmsDesignerProbeSubmitResultV1::event_unavailable;
  }
  request.result = {};
  request.result.snapshot_revision = request.expected_snapshot_revision;
  request.result.date_raw = request.date_raw;
  request.result.source_bytes = request.source.size();
  request.result.apply_requested = request.apply;
  request.state.store(CoatOfArmsDesignerProbeRequestStateV1::queued,
                      std::memory_order_release);
  CoatOfArmsDesignerProbeRequestV1 *expected = nullptr;
  if (!hook.pending_request.compare_exchange_strong(
          expected, &request, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    request.state.store(CoatOfArmsDesignerProbeRequestStateV1::idle,
                        std::memory_order_release);
    CloseHandle(request.completion_event);
    request.completion_event = nullptr;
    return CoatOfArmsDesignerProbeSubmitResultV1::busy;
  }
  return CoatOfArmsDesignerProbeSubmitResultV1::submitted;
}

CoatOfArmsDesignerProbeWaitResultV1
WaitForCoatOfArmsDesignerProbeV1(CoatOfArmsDesignerProbeRequestV1 &request,
                                 std::uint32_t timeout_milliseconds) noexcept {
  if (request.completion_event == nullptr) {
    return CoatOfArmsDesignerProbeWaitResultV1::infrastructure_failed;
  }
  const DWORD wait =
      WaitForSingleObject(request.completion_event, timeout_milliseconds);
  if (wait == WAIT_OBJECT_0 &&
      request.state.load(std::memory_order_acquire) ==
          CoatOfArmsDesignerProbeRequestStateV1::completed) {
    return CoatOfArmsDesignerProbeWaitResultV1::completed;
  }
  if (wait != WAIT_TIMEOUT) {
    return CoatOfArmsDesignerProbeWaitResultV1::infrastructure_failed;
  }
  auto expected = CoatOfArmsDesignerProbeRequestStateV1::queued;
  if (request.state.compare_exchange_strong(
          expected, CoatOfArmsDesignerProbeRequestStateV1::cancelled,
          std::memory_order_acq_rel, std::memory_order_acquire)) {
    return CoatOfArmsDesignerProbeWaitResultV1::
        timeout_cancelled_before_execution;
  }
  if (expected == CoatOfArmsDesignerProbeRequestStateV1::executing) {
    return CoatOfArmsDesignerProbeWaitResultV1::
        timeout_executor_already_running;
  }
  if (expected == CoatOfArmsDesignerProbeRequestStateV1::completed) {
    return CoatOfArmsDesignerProbeWaitResultV1::completed;
  }
  return CoatOfArmsDesignerProbeWaitResultV1::infrastructure_failed;
}

bool ReclaimCoatOfArmsDesignerProbeV1(
    CoatOfArmsDesignerProbeHookStateV1 &hook,
    CoatOfArmsDesignerProbeRequestV1 &request) noexcept {
  const auto state = request.state.load(std::memory_order_acquire);
  if (state != CoatOfArmsDesignerProbeRequestStateV1::completed &&
      state != CoatOfArmsDesignerProbeRequestStateV1::cancelled) {
    return false;
  }
  auto *expected = &request;
  hook.pending_request.compare_exchange_strong(
      expected, nullptr, std::memory_order_acq_rel, std::memory_order_acquire);
  if (request.completion_event != nullptr) {
    CloseHandle(request.completion_event);
    request.completion_event = nullptr;
  }
  request.state.store(CoatOfArmsDesignerProbeRequestStateV1::idle,
                      std::memory_order_release);
  return true;
}

std::string_view CoatOfArmsDesignerProbeFailureMessageV1(
    CoatOfArmsDesignerProbeWaitResultV1 wait) noexcept {
  switch (wait) {
  case CoatOfArmsDesignerProbeWaitResultV1::completed:
    return "coat-of-arms probe result is inconsistent";
  case CoatOfArmsDesignerProbeWaitResultV1::timeout_cancelled_before_execution:
    return "active coat-of-arms designer was not observed before timeout";
  case CoatOfArmsDesignerProbeWaitResultV1::timeout_executor_already_running:
    return "coat-of-arms designer probe is still executing";
  case CoatOfArmsDesignerProbeWaitResultV1::infrastructure_failed:
    return "coat-of-arms designer probe infrastructure failed";
  }
  return "coat-of-arms designer probe failed";
}

extern "C" void __fastcall
XarCoatOfArmsUpdatePasteContentsHookV1(void *designer) noexcept {
  auto *const hook = g_active_hook_state.load(std::memory_order_acquire);
  if (hook == nullptr || hook->update_trampoline == nullptr)
    return;
  const auto update =
      reinterpret_cast<NativeUpdatePasteContentsV1>(hook->update_trampoline);
  hook->active_hook_calls.fetch_add(1, std::memory_order_acq_rel);
  hook->observed_calls.fetch_add(1, std::memory_order_acq_rel);

  auto *request = hook->pending_request.load(std::memory_order_acquire);
  auto expected = CoatOfArmsDesignerProbeRequestStateV1::queued;
  if (request == nullptr ||
      !request->state.compare_exchange_strong(
          expected, CoatOfArmsDesignerProbeRequestStateV1::executing,
          std::memory_order_acq_rel, std::memory_order_acquire)) {
    update(designer);
    hook->active_hook_calls.fetch_sub(1, std::memory_order_acq_rel);
    return;
  }

  request->result.designer_observed = true;
  if (request->operation == CoatOfArmsDesignerOperationV1::export_current) {
    update(designer);
    if (!ClipboardFunctionsAvailable(*hook) ||
        hook->copy_to_clipboard == nullptr) {
      request->result.reason = "clipboard_functions_unavailable";
    } else {
      const auto copy = reinterpret_cast<NativeCopyToClipboardV1>(
          hook->copy_to_clipboard);
      copy(designer);
      request->result.copy_invoked = true;
      request->result.clipboard_read =
          ClipboardReadText(*hook, request->result.exported_source);
      request->result.source_bytes = request->result.exported_source.size();
      if (!request->result.clipboard_read)
        request->result.reason = "clipboard_export_read_failed";
    }
    hook->executed_requests.fetch_add(1, std::memory_order_acq_rel);
    hook->active_hook_calls.fetch_sub(1, std::memory_order_acq_rel);
    CompleteRequest(*hook, *request);
    return;
  }
  if (!ClipboardFunctionsAvailable(*hook)) {
    request->result.reason = "clipboard_functions_unavailable";
    update(designer);
  } else {
    const auto clipboard_write = reinterpret_cast<NativeClipboardWriteV1>(
        *static_cast<void *const *>(hook->clipboard_write_slot));
    clipboard_write(request->source.c_str());
    request->result.clipboard_written = true;
    request->result.clipboard_readback_matched =
        ClipboardReadbackMatches(*hook, request->source);
    update(designer);
    if (!request->result.clipboard_readback_matched) {
      request->result.reason = "clipboard_readback_mismatch";
    } else {
      auto *const bytes = static_cast<std::uint8_t *>(designer);
      request->result.detected = bytes[0xEF] != 0;
      request->result.candidate_index =
          *reinterpret_cast<const std::uint32_t *>(bytes + 0xF0);
      request->result.preview_coat_of_arms_handle =
          *reinterpret_cast<const std::uint32_t *>(bytes + 0x100);
      if (!request->result.detected) {
        request->result.reason = "engine_did_not_detect_coat_of_arms";
      } else if (request->apply) {
        const auto paste = reinterpret_cast<NativePasteFromClipboardV1>(
            hook->paste_from_clipboard);
        paste(designer);
        request->result.paste_invoked = true;
        request->result.active_coat_of_arms_index =
            *reinterpret_cast<const std::uint32_t *>(bytes + 0xE8);
        request->result.applied =
            bytes[0xEC] != 0 && request->result.active_coat_of_arms_index ==
                                    request->result.candidate_index;
        if (!request->result.applied) {
          request->result.reason = "paste_postcondition_not_observed";
        }
      }
    }
  }
  hook->executed_requests.fetch_add(1, std::memory_order_acq_rel);
  hook->active_hook_calls.fetch_sub(1, std::memory_order_acq_rel);
  CompleteRequest(*hook, *request);
}

} // namespace xar::ck3_11906

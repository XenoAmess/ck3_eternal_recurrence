#pragma once
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#include <string>

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kPollEventDispatchSlotRvaV1 = 0x5D0AE28;
inline constexpr std::uintptr_t kPollEventResolvedRvaV1 = 0x4719600;
inline constexpr std::uintptr_t kPollEventFirstReturnRvaV1 = 0x438D22E;
inline constexpr std::uintptr_t kPollEventLoopReturnRvaV1 = 0x438DE57;

// This is an exact build-profile tuple, not a blanket exception for profiles.
inline bool IsFlorinEventPumpProfileV1(
    const ck3_11906::MainThreadQueryBuildProfileV1 *p) noexcept {
  return p != nullptr && p->pump_exact_return_rva == kSdlWindowsPumpFirstPeekReturnRva &&
      p->peek_message_iat_slot_rva == kPeekMessageWIatSlotRva &&
      p->global_rng_wrapper_slot_rva == kGlobalRngWrapperSlotRva &&
      p->jomini_state_slot_rva == kJominiStateSlotRva && p->game_state_slot_rva == kGameStateSlotRva &&
      p->tls_initialized_flag_rva == kMainThreadTlsInitializedFlagRva &&
      p->tls_context_getter_rva == kMainThreadTlsContextGetterRva && p->verify_pump_anchors != nullptr;
}

inline bool IsFlorinPollMailboxV1(const ck3_11906::MainThreadQueryMailboxV1 &m) noexcept {
  return m.pump_exact_return_rva == kSdlWindowsPumpFirstPeekReturnRva &&
      m.sdl_poll_event_exact_return_rva == kPollEventFirstReturnRvaV1;
}

inline bool IsFlorinPollReturnV1(const ck3_11906::MainThreadQueryMailboxV1 &m,
    std::uintptr_t rva) noexcept {
  if (!IsFlorinPollMailboxV1(m) || !m.sdl_poll_event_hook_installed.load(std::memory_order_acquire) ||
      (rva != kPollEventFirstReturnRvaV1 && rva != kPollEventLoopReturnRvaV1)) return false;
  if (m.offline_fixture) return true; // Only the existing isolated mailbox test seam.
  return m.module_base != 0 && m.sdl_poll_event_slot ==
      reinterpret_cast<void **>(m.module_base + kPollEventDispatchSlotRvaV1) &&
      reinterpret_cast<std::uintptr_t>(m.original_sdl_poll_event) == m.module_base + kPollEventResolvedRvaV1 &&
      m.peek_message_iat_slot == reinterpret_cast<void **>(m.module_base + kPeekMessageWIatSlotRva) &&
      m.jomini_state_slot == m.module_base + kJominiStateSlotRva &&
      m.game_state_slot == m.module_base + kGameStateSlotRva &&
      m.tls_initialized_flag == m.module_base + kMainThreadTlsInitializedFlagRva &&
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter) == m.module_base + kMainThreadTlsContextGetterRva;
}
} // namespace xar::ck3_1210

namespace xar::ck3_11906 {
// Passive per-process owner-hook entries/completions; never a readiness proof.
std::string SerializeOwnerHookEntriesV1();
} // namespace xar::ck3_11906

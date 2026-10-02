#pragma once
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <atomic>

namespace xar::ck3_11906 {
struct VerifiedOwnerWakeResultV1 {
  bool attempted = false;
  bool posted = false;
  bool owner_stable = false;
  std::uint32_t owner_before = 0;
  std::uint32_t owner_after = 0;
  std::uint32_t last_error = 0;
};
struct VerifiedOwnerPostResultV1 { bool posted = false; std::uint32_t last_error = 0; };
using VerifiedOwnerPosterV1 = VerifiedOwnerPostResultV1 (*)(void *, std::uint32_t) noexcept;
inline VerifiedOwnerPostResultV1 PostVerifiedOwnerNullMessageV1(void *, std::uint32_t owner) noexcept {
  const auto previous_error = GetLastError();
  const bool posted = PostThreadMessageW(owner, WM_NULL, 0, 0) != FALSE;
  const auto error = posted ? 0u : GetLastError();
  SetLastError(previous_error);
  return {posted, error};
}
// Installation already verified the exact-build image/anchor. No ticket,
// native executor, game command, snapshot mutation or wait is performed here.
inline bool VerifiedOwnerWakeGuardV1(const MainThreadQueryMailboxV1 &mailbox,
                                     std::uint32_t owner) noexcept {
  return owner != 0 && mailbox.iat_hook_installed.load(std::memory_order_acquire) &&
      mailbox.state.load(std::memory_order_acquire) != MainThreadQueryMailboxStateV1::detached &&
      !mailbox.stop_requested.load(std::memory_order_acquire) &&
      mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
      !mailbox.proof_reset_requested.load(std::memory_order_acquire) &&
      mailbox.owner_thread_id.load(std::memory_order_acquire) == owner &&
      mailbox.owner_verified_pump_epochs.load(std::memory_order_acquire) >= kMainThreadQueryMinimumOwnerVerifiedPumpEpochs &&
      mailbox.observed_stamp_read_success.load(std::memory_order_acquire) &&
      mailbox.observed_current_thread_id.load(std::memory_order_acquire) == owner &&
      mailbox.observed_tls_initialized.load(std::memory_order_acquire) == 1 &&
      mailbox.observed_tls_main_thread_marker.load(std::memory_order_acquire) == 1 &&
      mailbox.observed_tls_context.load(std::memory_order_acquire) != 0;
}
inline VerifiedOwnerWakeResultV1 WakeVerifiedApplicationMainOwnerV1(
    const MainThreadQueryMailboxV1 &mailbox,
    VerifiedOwnerPosterV1 poster = &PostVerifiedOwnerNullMessageV1,
    void *context = nullptr) noexcept {
  VerifiedOwnerWakeResultV1 result{};
  result.owner_before = mailbox.owner_thread_id.load(std::memory_order_acquire);
  if (poster == nullptr || !VerifiedOwnerWakeGuardV1(mailbox, result.owner_before)) {
    result.owner_after = mailbox.owner_thread_id.load(std::memory_order_acquire);
    return result;
  }
  // Repeat the same-owner/stop/failure proof immediately before the single
  // best-effort post; concurrent drift after this point is diagnostic only.
  if (!VerifiedOwnerWakeGuardV1(mailbox, result.owner_before)) {
    result.owner_after = mailbox.owner_thread_id.load(std::memory_order_acquire);
    return result;
  }
  result.attempted = true;
  const auto actual = poster(context, result.owner_before);
  result.posted = actual.posted;
  result.last_error = actual.last_error;
  result.owner_after = mailbox.owner_thread_id.load(std::memory_order_acquire);
  result.owner_stable = VerifiedOwnerWakeGuardV1(mailbox, result.owner_before) &&
      result.owner_after == result.owner_before;
  return result;
}
struct VerifiedOwnerWakeDiagnosticsV1 {
  std::uint64_t attempts = 0, posted = 0, guard_rejections = 0, owner_drift = 0;
  std::uint32_t owner_before = 0, owner_after = 0, last_error = 0;
};
struct VerifiedOwnerWakeCountersV1 {
  std::atomic<std::uint64_t> attempts{0}, posted{0}, guard_rejections{0}, owner_drift{0};
  std::atomic<std::uint32_t> owner_before{0}, owner_after{0}, last_error{0};
  void Record(const VerifiedOwnerWakeResultV1 &result) noexcept {
    if (result.attempted) ++attempts; else ++guard_rejections;
    if (result.posted) ++posted;
    if (result.attempted && !result.owner_stable) ++owner_drift;
    owner_before.store(result.owner_before); owner_after.store(result.owner_after); last_error.store(result.last_error);
  }
  VerifiedOwnerWakeDiagnosticsV1 Read() const noexcept {
    return {attempts.load(), posted.load(), guard_rejections.load(), owner_drift.load(),
            owner_before.load(), owner_after.load(), last_error.load()};
  }
};
} // namespace xar::ck3_11906

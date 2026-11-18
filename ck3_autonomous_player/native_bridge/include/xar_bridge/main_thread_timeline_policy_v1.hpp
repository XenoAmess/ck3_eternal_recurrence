#pragma once
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

namespace xar::ck3_11906 {
// A bounded sidecar for exact-build clock-only providers. It changes no legacy
// mailbox ABI and never admits a frontend, domain or complete snapshot reader.
// The selected backend registers its two actual reviewed function addresses
// only after the normal IAT/profile installation has succeeded.
inline std::atomic<const MainThreadQueryMailboxV1 *> g_timeline_mailbox_v1{nullptr};
inline std::atomic<MainThreadQueryExecutorV1> g_timeline_read_v1{nullptr};
inline std::atomic<MainThreadQueryExecutorV1> g_timeline_control_v1{nullptr};
inline bool RegisterMainThreadTimelineExecutorsV1(MainThreadQueryMailboxV1 &mailbox,
    MainThreadQueryExecutorV1 read, MainThreadQueryExecutorV1 control=nullptr) noexcept {
  if (!mailbox.iat_hook_installed.load(std::memory_order_acquire) || read==nullptr || (control!=nullptr && control==read)) return false;
  g_timeline_mailbox_v1.store(nullptr,std::memory_order_release);
  g_timeline_read_v1.store(read,std::memory_order_release);
  g_timeline_control_v1.store(control,std::memory_order_release);
  g_timeline_mailbox_v1.store(&mailbox,std::memory_order_release);
  return true;
}
inline bool IsMainThreadTimelineExecutorV1(const MainThreadQueryMailboxV1 &mailbox,
    MainThreadQueryExecutorV1 executor) noexcept {
  return executor!=nullptr && g_timeline_mailbox_v1.load(std::memory_order_acquire)==&mailbox &&
      (executor==g_timeline_read_v1.load(std::memory_order_acquire) ||
       executor==g_timeline_control_v1.load(std::memory_order_acquire));
}
// The read role is distinct from registered clock/control callbacks.
// No payload or context shape can opt another executor into this role.
inline bool IsMainThreadTimelineReadExecutorV1(const MainThreadQueryMailboxV1 &mailbox,
    MainThreadQueryExecutorV1 executor) noexcept {
  return executor!=nullptr && g_timeline_mailbox_v1.load(std::memory_order_acquire)==&mailbox &&
      executor==g_timeline_read_v1.load(std::memory_order_acquire);
}
inline void UnregisterMainThreadTimelineExecutorsV1(const MainThreadQueryMailboxV1 &mailbox) noexcept {
  auto *expected=&mailbox;
  (void)g_timeline_mailbox_v1.compare_exchange_strong(expected,nullptr,std::memory_order_acq_rel);
}
} // namespace xar::ck3_11906

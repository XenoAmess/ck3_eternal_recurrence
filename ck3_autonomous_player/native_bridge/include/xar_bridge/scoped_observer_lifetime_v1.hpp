#pragma once
#include <windows.h>
#include <cstdint>
#include <memory>

namespace xar::ck3_11906 {
// One gate covers both observers: their original calls can recursively enter
// one another. Admission happens before loading any session or trampoline.
inline SRWLOCK g_scoped_observer_lifetime_gate_v1 = SRWLOCK_INIT;
inline thread_local std::uint32_t g_scoped_observer_shared_depth_v1 = 0;
inline thread_local std::uint32_t g_scoped_observer_exclusive_depth_v1 = 0;
inline void EnterScopedObserverCallbackV1() noexcept {
  if (g_scoped_observer_shared_depth_v1++ == 0 &&
      g_scoped_observer_exclusive_depth_v1 == 0)
    AcquireSRWLockShared(&g_scoped_observer_lifetime_gate_v1);
}
inline void LeaveScopedObserverCallbackV1() noexcept {
  if (--g_scoped_observer_shared_depth_v1 == 0 &&
      g_scoped_observer_exclusive_depth_v1 == 0)
    ReleaseSRWLockShared(&g_scoped_observer_lifetime_gate_v1);
}
inline bool TryEnterScopedObserverMutationV1() noexcept {
  if (g_scoped_observer_exclusive_depth_v1 != 0) {
    ++g_scoped_observer_exclusive_depth_v1;
    return true;
  }
  if (g_scoped_observer_shared_depth_v1 != 0 ||
      !TryAcquireSRWLockExclusive(&g_scoped_observer_lifetime_gate_v1)) return false;
  g_scoped_observer_exclusive_depth_v1 = 1;
  return true;
}
inline void LeaveScopedObserverMutationV1() noexcept {
  if (--g_scoped_observer_exclusive_depth_v1 == 0)
    ReleaseSRWLockExclusive(&g_scoped_observer_lifetime_gate_v1);
}
struct ScopedObserverMutationV1 {
  bool acquired = TryEnterScopedObserverMutationV1();
  ~ScopedObserverMutationV1() { if (acquired) LeaveScopedObserverMutationV1(); }
  explicit operator bool() const noexcept { return acquired; }
};
// Failure paths cannot delete a parent whose plan/ring/child can still be
// referenced by an admitted callback. The isolated owned CK3 process is the
// reclamation boundary; SDK cleanup terminates that process.
template<class T> void RetainScopedObserverParentUntilProcessExitV1(
    std::unique_ptr<T> &parent, bool may_be_referenced) noexcept {
  if (may_be_referenced) (void)parent.release();
}
inline bool PinScopedObserverModuleUntilProcessExitV1(const void *address) noexcept {
  HMODULE module = nullptr;
  return GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                           GET_MODULE_HANDLE_EX_FLAG_PIN,
      reinterpret_cast<LPCWSTR>(address), &module) != FALSE && module != nullptr;
}
} // namespace xar::ck3_11906

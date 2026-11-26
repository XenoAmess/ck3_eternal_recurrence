#include "xar_bridge/ck3_12002_adapter.hpp"
#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_marriage_probe.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include <cstdio>
#include <cstdlib>

#if defined(XAR_CK3_TEST_WORKER_SNAPSHOT_WAIT)
namespace xar::ck3_12002 {
namespace {
thread_local void *worker_wait_context = nullptr;
thread_local WorkerSnapshotWaitObserver worker_wait_observer = nullptr;
}

void BindWorkerSnapshotWaitObserver(void *context, WorkerSnapshotWaitObserver observer) noexcept {
  worker_wait_context = context;
  worker_wait_observer = observer;
}

void ObserveWorkerSnapshotWaitBoundary(
    WorkerSnapshotWaitBoundary boundary, std::unique_lock<std::mutex> &lock) noexcept {
  if (worker_wait_observer) worker_wait_observer(worker_wait_context, boundary, lock);
}
} // namespace xar::ck3_12002
#endif

namespace xar::game {

[[noreturn]] static void TrapNonFreshAdapterExtension() {
  std::printf("UNEXPECTED_NON_FRESH_ADAPTER_EXTENSION\n");
  std::abort();
}

bool ReadCk3_12002TimelineCoreSnapshot(
    const GameAdapter &,
    Snapshot &) noexcept {
  TrapNonFreshAdapterExtension();
}

PauseSubmitResult SubmitCk3_12002PauseMapObserved(
    const GameAdapter &,
    const Snapshot &) noexcept {
  TrapNonFreshAdapterExtension();
}

ResumeSubmitResult SubmitCk3_12002ResumeMapObserved(
    const GameAdapter &,
    const Snapshot &) noexcept {
  TrapNonFreshAdapterExtension();
}

ReadArmyStrengthsResult ReadCk3_12004ArmyStrengthsPrivateAutoScalar(
    const GameAdapter &,
    std::vector<ArmyStrengthSnapshot> &) noexcept {
  TrapNonFreshAdapterExtension();
}

} // namespace xar::game

namespace xar::ck3_12002 {

ContextBindings BindContextImage(
    std::uintptr_t,
    std::string_view) noexcept {
  xar::game::TrapNonFreshAdapterExtension();
}

bool CollectMarriageProbe12002(
    const ContextBindings &,
    std::string &) noexcept {
  xar::game::TrapNonFreshAdapterExtension();
}

} // namespace xar::ck3_12002

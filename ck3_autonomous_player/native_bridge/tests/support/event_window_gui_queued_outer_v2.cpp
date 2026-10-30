#include "xar_bridge/ck3_12002_event_window_context.hpp"
#include "xar_bridge/ck3_12002_faction_alerts.hpp"
#include <cstdlib>

unsigned g_unused_outer_calls90=0;
namespace {
[[noreturn]] void UnusedOuter90() noexcept {++g_unused_outer_calls90;std::abort();}
}
namespace xar::ck3_12002 {
// Exact declared types; unused outer seams abort instead of returning data.
// This separate TU avoids inlining abort into the unexecuted outer reader.
bool ReadCoreSnapshot(const CoreBindings&,CoreSnapshotPrefix&) noexcept {UnusedOuter90();}
}

#include "xar_bridge/ck3_12002_adapter.hpp"
#include <cstdlib>

namespace xar::game {
// This fixture exercises full_snapshot only. Abort if the untested core_frame
// producer is ever reached; it must not synthesize a timeline observation.
bool ReadCk3_12002TimelineCoreSnapshot(const GameAdapter &, Snapshot &) noexcept {
  std::abort();
}
}

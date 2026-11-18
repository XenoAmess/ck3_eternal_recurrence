#pragma once
#include "xar_bridge/ck3_1210_actor_foundation_v1.hpp"
#include "xar_bridge/ck3_1210_current_event_snapshot_v1.hpp"
#include "xar_bridge/ck3_1210_pending_snapshot_v1.hpp"
#include "xar_bridge/ck3_1210_military_empty_v1.hpp"
#include "xar_bridge/game_contract.hpp"
namespace xar::ck3_1210 {
struct FullSnapshotBindingsV1 {
  bool exact_build_admitted = false;
  CoreBindings core{};
  ActorFoundationBindingsV1 foundation{};
  CurrentEventSnapshotBindingsV1 event{};
  PendingSnapshotBindingsV1 pending{};
  MilitaryEmptyBindingsV1 military{};
};
struct FullSnapshotDiagnosticsV1 {
  bool complete = false;
  std::uint32_t completed_passes = 0;
  std::uint32_t pending_slots_scanned = 0;
  std::int32_t unit_slots_scanned = 0;
  std::int32_t war_slots_scanned = 0;
  std::string_view stage = "full_snapshot_not_read";
  std::string_view reason = "full_snapshot_not_read";
};
FullSnapshotBindingsV1 BindFullSnapshotImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Integration requires actual paused application-main/TLS custody and exact
// mapped-image guards. Two complete equal observations are required; unknown
// or nonempty military returns unavailable rather than fabricated arrays.
// Optional settlement is unsupported (no capability), event traits omitted.
bool ReadFullSnapshotV1(const FullSnapshotBindingsV1 &bindings,
    xar::game::Snapshot &output, FullSnapshotDiagnosticsV1 &diagnostics) noexcept;
} // namespace xar::ck3_1210

#pragma once

#include "xar_bridge/ck3_12004_battle.hpp"
#include "xar_bridge/entry_preceding_capture_12004.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12004 {

// A synchronous private collector. The borrowed Combat pointer is valid only
// during this call; it is never retained by the owning query carrier.
struct BattleAcceptedCombatCollector12004 {
  void *context = nullptr;
  void (*collect)(void *, const void *, std::uint32_t) noexcept = nullptr;
};

// The existing query owns this carrier until its ordinary terminal wait and
// reclaim. The public BattleControlSnapshot contract is unchanged.
struct BattleControlOwnedEntryPreceding12004 {
  game::BattleControlSnapshot snapshot{};
  std::optional<EntryPrecedingQuery12004> entry_preceding_capture;
};

game::BattleControlSnapshotStatus ReadBattleControlOwnedEntryPreceding12004(
    const BattleBindings &, const game::Snapshot &paused_scope,
    const game::BattleControlRequest &, bool exact_12004_admitted,
    std::uint64_t snapshot_revision,
    BattleControlOwnedEntryPreceding12004 &) noexcept;

// The raw retained sidecar remains independent of the old battle known bools.
// Optional failure/size limits keep the base serializer result unchanged.
std::string SerializeBattleControlOwnedEntryPreceding12004(
    const BattleControlOwnedEntryPreceding12004 &);

} // namespace xar::ck3_12004

namespace xar::ck3_12002 {
// Private accepted-frame seam shared by the actual4 owning wrapper. Existing
// readers call their unchanged API with no collector.
game::BattleControlSnapshotStatus ReadBattleControlSnapshotWithOwnedCombat12004(
    const BattleBindings &, const game::Snapshot &paused_scope,
    const game::BattleControlRequest &, game::BattleControlSnapshot &,
    const ck3_12004::BattleAcceptedCombatCollector12004 &) noexcept;
} // namespace xar::ck3_12002

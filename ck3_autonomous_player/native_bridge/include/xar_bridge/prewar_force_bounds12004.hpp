#pragma once

#include "xar_bridge/prewar_owner_inventory12004.hpp"
#include "xar_bridge/prewar_levy_inventory12004.hpp"
#include "xar_bridge/prewar_hired_inventory12004.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

struct PrewarForceOwnerBounds12004 {
  std::int32_t owner_character_id = -1;
  // A deduplicated known unassigned inventory floor. This flag qualifies
  // arithmetic and source identity, never CanRaise, delivery or battle entry.
  // The business consumer separately requires its native final legality.
  std::optional<std::int64_t> actor_lower_soldiers;
  bool actor_lower_ready = false;
  // A conservative cap on this current owner's inventory. Capacity is used
  // only as an upper cap, not labelled observed current or future soldiers.
  std::optional<std::int64_t> inventory_upper_soldiers;
  bool inventory_upper_ready = false;
  std::string inventory_scope =
      "current_owner_inventory_with_known_unassigned_floor";
  std::vector<std::string> unavailable_reasons;
  bool operator==(const PrewarForceOwnerBounds12004 &) const = default;
};

// Pure copied-value projection: no native callbacks, pointers, game writes or
// cache are read. The caller owns one paused ticket and compares the complete
// owner/levy/hired DTOs twice; hired has no independent frame envelope.
// Physical identity is (full Regi ID, ordinal), independent of source category
// or employer. Full Character IDs in the whole +38 knight list count once;
// hired stock scalars already include holder knights and are never added.
// True means a safe projection was produced. A partial source may retain a
// reliable lower floor while the upper optional remains absent.
bool ProjectPrewarForceOwnerBounds12004(
    const PrewarOwnerInventory12004 &owner,
    const PrewarLevyInventorySnapshot12004 &levy,
    const PrewarHiredInventory12004 &hired,
    PrewarForceOwnerBounds12004 &output) noexcept;

} // namespace xar::ck3_12004

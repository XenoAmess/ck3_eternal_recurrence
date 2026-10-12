#pragma once

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12003_army_reserve.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

enum class PrewarForceMilitaryStatus12004 { available, partial, unavailable };

struct PrewarForceMilitaryRequest12004 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  // The public actor root requires a positive character ID. Explicit owner
  // IDs retain the native signed32 full generation (including zero/high bit),
  // with only -1 treated as absent; world.resolve_character authenticates each
  // full ID. No inferred ally/vassal contribution.
  std::vector<std::int32_t> owner_character_ids;
};

struct PrewarForceRegiment12004 {
  std::int32_t army_regiment_id = -1;
  std::optional<std::int32_t> observed_full_id;
  std::optional<std::int32_t> current_soldiers;
  std::optional<std::int32_t> maximum_soldiers;
  bool full_generation_ready = false;
  std::string failure;
  bool operator==(const PrewarForceRegiment12004 &) const = default;
};

struct PrewarForceRaisedArmy12004 {
  std::int32_t public_unit_id = -1;
  std::int32_t native_carmy_id = -1;
  std::int32_t owner_character_id = -1;
  std::optional<std::int32_t> observed_carmy_full_id;
  std::optional<std::int32_t> observed_carmy_public_unit_id;
  std::optional<std::int32_t> unit_state_code;
  // Present headcount of this CArmy, including already delivered gathering
  // troops. These are neither a future muster nor a battle-ready forecast.
  std::optional<std::int32_t> current_soldiers;
  std::optional<std::int32_t> maximum_soldiers;
  // Preserve returned native scalars even when their agreement check fails.
  std::optional<std::int32_t> observed_native_current_soldiers;
  std::optional<std::int32_t> observed_native_maximum_soldiers;
  std::vector<PrewarForceRegiment12004> regiments;
  // Native getter sums roster occurrences. Preserve intra-CArmy duplicates
  // explicitly and require occurrence-sum agreement, rather than deduplicating
  // its operands. Cross-CArmy duplicate references invalidate both rows.
  std::int32_t duplicate_regiment_occurrences = 0;
  bool available = false;
  // Available native occurrence totals alone do not prove distinct physical
  // troops. Duplicate occurrences withdraw this row's lower-bound credit.
  bool current_lower_bound_ready = false;
  std::string failure;
  bool operator==(const PrewarForceRaisedArmy12004 &) const = default;
};

struct PrewarForceOwnerMilitary12004 {
  std::int32_t owner_character_id = -1;
  bool character_identity_ready = false;
  bool raised_scan_complete = false;
  // Validated, distinct current CArmy rows only. Partial scans retain a
  // conservative observed subtotal, never an asserted full owner strength.
  bool raised_current_lower_bound_ready = false;
  std::int64_t raised_current_lower_bound = 0;
  std::int64_t observed_raised_current_sum = 0;
  std::int64_t observed_raised_maximum_sum = 0;
  // Unraised levy/MAA capacity is not observed by this reader.
  std::optional<std::int64_t> total_military_upper_bound;
  std::vector<PrewarForceRaisedArmy12004> raised_armies;
  std::string failure;
  bool operator==(const PrewarForceOwnerMilitary12004 &) const = default;
};

struct PrewarForceMalformedUnitSlot12004 {
  std::int32_t slot_index = -1;
  std::int32_t full_id = -1;
  std::uint32_t magic = 0;
  std::optional<std::int32_t> owner_character_id;
  bool operator==(const PrewarForceMalformedUnitSlot12004 &) const = default;
};

struct PrewarForceMilitarySnapshot12004 {
  PrewarForceMilitaryStatus12004 status =
      PrewarForceMilitaryStatus12004::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  bool exact_build_ready = false;
  // Scope equality of the before/after paused snapshots, not a substitute
  // for the caller's aggregate two-pass comparison and owning-thread ticket.
  bool source_frame_ready = false;
  bool unit_scan_complete = false;
  // Only selected owners' CArmy rosters are sampled. No complete physical
  // ownership proof across selected/unselected owners is claimed; owner force
  // floors and the combined actor floor stay unqualified until that is closed.
  std::string force_scope = "selected_owner_carmy_native_scalar_observation";
  bool global_physical_ownership_ready = false;
  std::int32_t malformed_unit_slots = 0;
  std::vector<PrewarForceMalformedUnitSlot12004> malformed_unit_slot_observations;
  std::vector<PrewarForceOwnerMilitary12004> owners;
  std::optional<std::int32_t> actor_unraised_current;
  bool actor_unraised_ready = false;
  std::string actor_unraised_failure;
  std::optional<bool> native_default_raise_legal;
  bool default_raise_legality_ready = false;
  // Only qualified when final native default-raise legality is true. Unknown
  // legality leaves this null and the sample partial. Pending undelivered
  // chunks are excluded by the existing native reserve getter.
  std::optional<std::int64_t> actor_mobilizable_lower_bound;
  bool actor_mobilizable_lower_bound_ready = false;
  std::string actor_lower_bound_failure;
  std::string failure;
  bool operator==(const PrewarForceMilitarySnapshot12004 &) const = default;
};

// One synchronous sample using caller-owned exact .4 bindings and world.
// The caller MUST own the paused application-main ticket, collect all other
// domains twice, compare complete DTOs, and reject aggregate drift. This reader
// never calls the broad manager/ReadArmyStrengthsForScope path or submits raise.
PrewarForceMilitaryStatus12004 ReadPrewarForceMilitary12004(
    const ck3_12002::ArmyBindings &armies,
    const ck3_12002::MilitaryBindings &military,
    const ck3_12003::PlayerArmyReserveBindingsV1 &reserve,
    const ck3_12002::MilitaryWorldAccess &world,
    std::string_view executable_sha256,
    const PrewarForceMilitaryRequest12004 &request,
    PrewarForceMilitarySnapshot12004 &output) noexcept;

} // namespace xar::ck3_12004

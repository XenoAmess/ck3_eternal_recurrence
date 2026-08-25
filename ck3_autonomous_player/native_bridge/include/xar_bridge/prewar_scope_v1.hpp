#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

// This is a declaration-bound, read-only prewar scope skeleton.  It is
// deliberately not a bridge capability yet: the exact primary CUnit slice is
// useful RE input, but callability, objective/contact selection and arrival
// timing are still required before a declaration forecast can consume it.
inline constexpr char kPrewarScopeV1GameVersion[] = "1.19.0.6";
inline constexpr char kPrewarScopeV1ExecutableSha256[] =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::uintptr_t kPrewarScopeV1UnitStorageSlotRva =
    0x570CC80;
inline constexpr std::uintptr_t kPrewarScopeV1ArmyStorageSlotRva =
    0x570C730;
inline constexpr std::size_t kPrewarScopeV1MaximumComponentCapacity =
    1'000'000;
inline constexpr std::size_t kPrewarScopeV1MaximumRouteProvinceCount =
    4'096;

enum class PrewarSideV1 : std::uint8_t {
  attacker = 0,
  defender = 1,
};

enum class ReadPrewarScopeStatusV1 : std::uint8_t {
  available_primary_scope = 0,
  invalid_request = 1,
  requires_paused = 2,
  unavailable = 3,
};

struct PrewarScopeRequestV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t effective_target_character_id = -1;
};

struct PrewarPrimaryParticipantV1 {
  std::int32_t character_id = -1;
  PrewarSideV1 side = PrewarSideV1::attacker;
  std::string source;

  friend bool operator==(const PrewarPrimaryParticipantV1 &,
                         const PrewarPrimaryParticipantV1 &) = default;
};

struct PrewarRaisedArmyV1 {
  std::int32_t army_id = -1; // public full-generation CUnitID
  std::int32_t native_carmy_id = -1; // internal full-generation CArmyID
  std::int32_t owner_character_id = -1;
  PrewarSideV1 side = PrewarSideV1::attacker;
  bool has_current_province = false;
  std::int32_t current_province_id = -1;
  bool has_move_target_province = false;
  std::int32_t move_target_province_id = -1;
  // Complete paused CUnit remaining route in native order.  Empty is a
  // positive observation that no remaining route rows exist.
  std::vector<std::int32_t> route_province_ids;

  friend bool operator==(const PrewarRaisedArmyV1 &,
                         const PrewarRaisedArmyV1 &) = default;
};

struct PrewarScopeReadinessV1 {
  bool exact_build_ready = false;
  bool primary_participants_ready = false;
  bool primary_raised_armies_ready = false;
  bool native_join_bounds_ready = false;
  bool declaration_objective_provinces_ready = false;
  bool contact_geometry_ready = false;
  bool native_arrival_timeline_ready = false;
  bool combat_v3_prewar_scope_ready = false;
  bool war_entry_forecast_inputs_ready = false;

  friend bool operator==(const PrewarScopeReadinessV1 &,
                         const PrewarScopeReadinessV1 &) = default;
};

struct PrewarScopeObservationV1 {
  ReadPrewarScopeStatusV1 status = ReadPrewarScopeStatusV1::unavailable;
  std::string failure_stage;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::vector<PrewarPrimaryParticipantV1> primary_participants;
  std::vector<PrewarRaisedArmyV1> primary_raised_armies;
  PrewarScopeReadinessV1 readiness;
};

using ResolvePrewarProvinceV1 = void *(*)(void *game_state,
                                          std::int32_t province_id);

struct PrewarScopeBindingsV1 {
  // Address of the exact-build CUnit storage singleton slot.
  void **unit_storage_slot = nullptr;
  // Address of the exact-build CArmy storage singleton slot.  The adjacent
  // module+0x570C720 fallback is deliberately not accepted.
  void **carmy_storage_slot = nullptr;
  ResolvePrewarProvinceV1 resolve_province = nullptr;
};

// Reads the complete current CUnit set twice and accepts it only when both
// declaration-primary projections are byte-for-value identical.  The
// function calls no CK3 native helper other than the injected read-only
// Province resolver and performs no game-world writes.
ReadPrewarScopeStatusV1 ReadDeclarationBoundPrewarScopeV1(
    const PrewarScopeBindingsV1 &bindings, void *game_state,
    bool environment_exact, bool paused, const PrewarScopeRequestV1 &request,
    PrewarScopeObservationV1 &output) noexcept;

} // namespace xar::ck3_11906

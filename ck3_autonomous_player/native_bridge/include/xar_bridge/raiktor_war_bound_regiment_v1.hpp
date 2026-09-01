#pragma once

#include "xar_bridge/ck3_11906.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view kRaiktorWarBoundRegimentV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view
    kRaiktorWarBoundRegimentV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kRaiktorWarBoundRegimentV1BackendId =
    "ck3-1.19.0.6-native-raiktor-war-bound-regiment-v1";
inline constexpr std::string_view kRaiktorAuthoredArmyName =
    "norman_highwaymen";
inline constexpr std::int32_t kRaiktorAuthoredSpawnArmyCount = 6;
inline constexpr std::int32_t kRaiktorAuthoredSoldiersPerArmy = 500;
inline constexpr std::int32_t kRaiktorAuthoredTotalSoldiers = 3000;

enum class RaiktorWarBoundRegimentStatusV1 : std::uint8_t {
  unavailable = 0,
  generic_war_bound_visible_source_unattributed = 1,
};

enum class RaiktorWarBoundRegimentFailureV1 : std::uint8_t {
  none = 0,
  invalid_raiktor_frame,
  raiktor_frame_changed,
  invalid_generic_active_observation,
  duplicate_generation_id,
  current_soldier_sample_mismatch,
  current_soldier_overflow,
  invalid_postwar_frame,
  postwar_frame_changed,
  invalid_cleanup_observation,
  cleanup_identity_mismatch,
  cleanup_state_mismatch,
};

struct RaiktorWarBoundFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t war_id = -1;
  std::int32_t active_casus_belli_database_index = -1;
  bool exact_raiktor_claim_cb = false;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;

  friend bool operator==(const RaiktorWarBoundFrameV1 &,
                         const RaiktorWarBoundFrameV1 &) = default;
};

struct RaiktorWarBoundPostwarFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t frozen_war_id = -1;
  bool frozen_war_absent_from_active_wars = false;

  friend bool operator==(const RaiktorWarBoundPostwarFrameV1 &,
                         const RaiktorWarBoundPostwarFrameV1 &) = default;
};

struct RaiktorWarBoundCurrentSoldierSampleV1 {
  std::int32_t current_army_regiment_id = -1;
  std::int32_t current_soldiers = -1;

  friend bool operator==(const RaiktorWarBoundCurrentSoldierSampleV1 &,
                         const RaiktorWarBoundCurrentSoldierSampleV1 &) =
      default;
};

struct RaiktorWarBoundCompositionRowV1 {
  std::int32_t composition_ordinal = -1;
  std::int32_t current_army_regiment_id = -1;
  std::int32_t raised_carmy_id = -1;
  std::int32_t current_soldiers = -1;
  FrozenWarBoundIdState current_army_regiment_state =
      FrozenWarBoundIdState::not_present;
  FrozenWarBoundIdState raised_carmy_state =
      FrozenWarBoundIdState::not_present;
  FrozenWarBoundArmyRosterEvidence frozen_carmy_roster_evidence =
      FrozenWarBoundArmyRosterEvidence::not_present;

  friend bool operator==(const RaiktorWarBoundCompositionRowV1 &,
                         const RaiktorWarBoundCompositionRowV1 &) = default;
};

struct RaiktorWarBoundPersistentRegimentV1 {
  std::int32_t persistent_regiment_id = -1;
  std::int32_t bound_war_id = -1;
  bool war_keep_on_attacker_victory = false;
  std::int64_t current_soldiers = 0;
  FrozenWarBoundIdState postwar_persistent_state =
      FrozenWarBoundIdState::unavailable;
  std::array<RaiktorWarBoundCompositionRowV1,
             kWarBoundRegimentCompositionRowCount>
      composition_rows{};

  friend bool operator==(const RaiktorWarBoundPersistentRegimentV1 &,
                         const RaiktorWarBoundPersistentRegimentV1 &) =
      default;
};

struct RaiktorWarBoundRegimentReadinessV1 {
  bool exact_raiktor_war_context_ready = false;
  bool generic_war_bound_identity_ready = false;
  bool current_soldiers_ready = false;
  bool postwar_cleanup_ready = false;
  bool source_specific_attribution_ready = false;
  bool pre_soldiers_ready = false;
  bool proven_soldier_loss_ready = false;
  bool independently_visible_value_ready = false;
  bool raiktor_source_specific_domain_ready = false;

  friend bool operator==(const RaiktorWarBoundRegimentReadinessV1 &,
                         const RaiktorWarBoundRegimentReadinessV1 &) =
      default;
};

struct RaiktorWarBoundRegimentObservationV1 {
  RaiktorWarBoundRegimentStatusV1 status =
      RaiktorWarBoundRegimentStatusV1::unavailable;
  RaiktorWarBoundRegimentFailureV1 failure =
      RaiktorWarBoundRegimentFailureV1::invalid_raiktor_frame;
  RaiktorWarBoundFrameV1 active_frame;
  RaiktorWarBoundPostwarFrameV1 postwar_frame;
  std::int32_t owner_character_id = -1;
  std::int32_t war_id = -1;
  std::int32_t authored_spawn_army_count =
      kRaiktorAuthoredSpawnArmyCount;
  std::int32_t authored_soldiers_per_army =
      kRaiktorAuthoredSoldiersPerArmy;
  std::int32_t authored_total_soldiers = kRaiktorAuthoredTotalSoldiers;
  std::int64_t observed_current_soldiers = -1;
  std::int64_t observed_pre_soldiers = -1;
  std::int64_t proven_soldiers_lost = -1;
  WarBoundRegimentCleanupStatus cleanup_status =
      WarBoundRegimentCleanupStatus::unavailable;
  std::vector<RaiktorWarBoundPersistentRegimentV1> regiments;
  RaiktorWarBoundRegimentReadinessV1 readiness;

  friend bool operator==(const RaiktorWarBoundRegimentObservationV1 &,
                         const RaiktorWarBoundRegimentObservationV1 &) =
      default;
};

std::string_view RaiktorWarBoundRegimentFailureReasonV1(
    RaiktorWarBoundRegimentFailureV1 failure) noexcept;

bool BuildRaiktorWarBoundRegimentActiveObservationV1(
    const RaiktorWarBoundFrameV1 &first_frame,
    const RaiktorWarBoundFrameV1 &second_frame,
    const WarBoundRegimentObservation &generic_observation,
    const std::vector<RaiktorWarBoundCurrentSoldierSampleV1> &soldier_samples,
    RaiktorWarBoundRegimentObservationV1 &output) noexcept;

bool ApplyRaiktorWarBoundRegimentCleanupObservationV1(
    const RaiktorWarBoundRegimentObservationV1 &active_observation,
    const RaiktorWarBoundPostwarFrameV1 &first_frame,
    const RaiktorWarBoundPostwarFrameV1 &second_frame,
    const FrozenWarBoundRegimentCleanupObservation &generic_cleanup,
    RaiktorWarBoundRegimentObservationV1 &output) noexcept;

} // namespace xar::ck3_11906

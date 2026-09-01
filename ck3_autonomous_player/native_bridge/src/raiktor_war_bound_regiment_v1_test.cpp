#include "xar_bridge/raiktor_war_bound_regiment_v1.hpp"

#include <cstdint>
#include <iostream>
#include <string_view>
#include <vector>

namespace {

using namespace xar::ck3_11906;

constexpr std::int32_t kWarId = 50'331'699;
constexpr std::int32_t kOwnerId = 29'829;

RaiktorWarBoundFrameV1 ActiveFrame() {
  return {
      91,
      7,
      53'175'816,
      true,
      kWarId,
      411,
      true,
      kOwnerId,
      17'116,
  };
}

RaiktorWarBoundPostwarFrameV1 PostwarFrame() {
  return {96, 8, 53'175'816, true, kWarId, true};
}

WarBoundRegimentObservation ActiveGeneric() {
  WarBoundRegimentObservation value;
  value.provenance =
      WarBoundRegimentProvenance::war_bound_not_event_specific;
  value.owner_character_id = kOwnerId;
  value.war_id = kWarId;
  WarBoundPersistentRegimentSnapshot first;
  first.persistent_regiment_id = 0x01000010;
  first.bound_war_id = kWarId;
  first.current_rows[0] = {0x02000020, 0x03000030};
  first.current_rows[3] = {0x02000021, 0x03000030};
  WarBoundPersistentRegimentSnapshot second;
  second.persistent_regiment_id = 0x01000011;
  second.bound_war_id = kWarId;
  second.current_rows[6] = {0x02000022, 0x03000031};
  value.regiments = {first, second};
  return value;
}

std::vector<RaiktorWarBoundCurrentSoldierSampleV1> SoldierSamples() {
  return {
      {0x02000020, 80},
      {0x02000021, 60},
      {0x02000022, 40},
  };
}

FrozenWarBoundRegimentCleanupObservation DestroyedCleanup() {
  FrozenWarBoundRegimentCleanupObservation value;
  value.provenance =
      WarBoundRegimentProvenance::war_bound_not_event_specific;
  value.status = WarBoundRegimentCleanupStatus::destroyed;
  value.owner_character_id = kOwnerId;
  value.war_id = kWarId;
  for (const auto &active : ActiveGeneric().regiments) {
    FrozenWarBoundPersistentCleanupSnapshot persistent;
    persistent.persistent_regiment_id = active.persistent_regiment_id;
    persistent.persistent_regiment_state = FrozenWarBoundIdState::destroyed;
    for (std::size_t ordinal = 0;
         ordinal < kWarBoundRegimentCompositionRowCount; ++ordinal) {
      const auto &active_row = active.current_rows[ordinal];
      auto &cleanup_row = persistent.current_rows[ordinal];
      cleanup_row.current_army_regiment_id =
          active_row.current_army_regiment_id;
      cleanup_row.raised_carmy_id = active_row.raised_carmy_id;
      if (active_row.current_army_regiment_id != -1) {
        cleanup_row.current_army_regiment_state =
            FrozenWarBoundIdState::destroyed;
        cleanup_row.raised_carmy_state = FrozenWarBoundIdState::destroyed;
        cleanup_row.frozen_carmy_roster_evidence =
            FrozenWarBoundArmyRosterEvidence::frozen_army_destroyed;
      }
    }
    value.regiments.push_back(persistent);
  }
  return value;
}

bool BuildActive(RaiktorWarBoundRegimentObservationV1 &output) {
  const auto frame = ActiveFrame();
  return BuildRaiktorWarBoundRegimentActiveObservationV1(
      frame, frame, ActiveGeneric(), SoldierSamples(), output);
}

bool ExpectFailure(bool returned,
                   const RaiktorWarBoundRegimentObservationV1 &value,
                   RaiktorWarBoundRegimentFailureV1 failure,
                   std::string_view label) {
  if (returned || value.status != RaiktorWarBoundRegimentStatusV1::unavailable ||
      value.failure != failure) {
    std::cerr << label << ": expected "
              << RaiktorWarBoundRegimentFailureReasonV1(failure) << ", got "
              << RaiktorWarBoundRegimentFailureReasonV1(value.failure) << '\n';
    return false;
  }
  return true;
}

} // namespace

int main() {
  RaiktorWarBoundRegimentObservationV1 active;
  if (!BuildActive(active) ||
      active.status != RaiktorWarBoundRegimentStatusV1::
                           generic_war_bound_visible_source_unattributed ||
      active.failure != RaiktorWarBoundRegimentFailureV1::none ||
      active.owner_character_id != kOwnerId || active.war_id != kWarId ||
      active.regiments.size() != 2 ||
      active.regiments[0].current_soldiers != 140 ||
      active.regiments[1].current_soldiers != 40 ||
      active.observed_current_soldiers != 180 ||
      active.observed_pre_soldiers != -1 ||
      active.proven_soldiers_lost != -1 ||
      active.cleanup_status != WarBoundRegimentCleanupStatus::unavailable ||
      !active.readiness.exact_raiktor_war_context_ready ||
      !active.readiness.generic_war_bound_identity_ready ||
      !active.readiness.current_soldiers_ready ||
      !active.readiness.independently_visible_value_ready ||
      active.readiness.postwar_cleanup_ready ||
      active.readiness.source_specific_attribution_ready ||
      active.readiness.pre_soldiers_ready ||
      active.readiness.proven_soldier_loss_ready ||
      active.readiness.raiktor_source_specific_domain_ready) {
    std::cerr << "active generic-visible observation contract failed\n";
    return 1;
  }

  {
    auto second = ActiveFrame();
    ++second.snapshot_revision;
    RaiktorWarBoundRegimentObservationV1 value;
    if (!ExpectFailure(
            BuildRaiktorWarBoundRegimentActiveObservationV1(
                ActiveFrame(), second, ActiveGeneric(), SoldierSamples(),
                value),
            value, RaiktorWarBoundRegimentFailureV1::raiktor_frame_changed,
            "active frame drift")) {
      return 1;
    }
  }
  {
    auto samples = SoldierSamples();
    samples.pop_back();
    RaiktorWarBoundRegimentObservationV1 value;
    const auto frame = ActiveFrame();
    if (!ExpectFailure(
            BuildRaiktorWarBoundRegimentActiveObservationV1(
                frame, frame, ActiveGeneric(), samples, value),
            value,
            RaiktorWarBoundRegimentFailureV1::
                current_soldier_sample_mismatch,
            "missing soldier sample")) {
      return 1;
    }
  }
  {
    auto samples = SoldierSamples();
    samples.push_back(samples.front());
    RaiktorWarBoundRegimentObservationV1 value;
    const auto frame = ActiveFrame();
    if (!ExpectFailure(
            BuildRaiktorWarBoundRegimentActiveObservationV1(
                frame, frame, ActiveGeneric(), samples, value),
            value,
            RaiktorWarBoundRegimentFailureV1::
                current_soldier_sample_mismatch,
            "duplicate soldier sample")) {
      return 1;
    }
  }
  {
    auto generic = ActiveGeneric();
    generic.regiments[1].persistent_regiment_id =
        generic.regiments[0].persistent_regiment_id;
    RaiktorWarBoundRegimentObservationV1 value;
    const auto frame = ActiveFrame();
    if (!ExpectFailure(
            BuildRaiktorWarBoundRegimentActiveObservationV1(
                frame, frame, generic, SoldierSamples(), value),
            value, RaiktorWarBoundRegimentFailureV1::duplicate_generation_id,
            "duplicate persistent generation")) {
      return 1;
    }
  }

  const auto postwar = PostwarFrame();
  RaiktorWarBoundRegimentObservationV1 destroyed;
  if (!ApplyRaiktorWarBoundRegimentCleanupObservationV1(
          active, postwar, postwar, DestroyedCleanup(), destroyed) ||
      destroyed.cleanup_status != WarBoundRegimentCleanupStatus::destroyed ||
      !destroyed.readiness.postwar_cleanup_ready ||
      !destroyed.readiness.independently_visible_value_ready ||
      destroyed.readiness.source_specific_attribution_ready ||
      destroyed.readiness.pre_soldiers_ready ||
      destroyed.readiness.proven_soldier_loss_ready ||
      destroyed.readiness.raiktor_source_specific_domain_ready ||
      destroyed.regiments[0].postwar_persistent_state !=
          FrozenWarBoundIdState::destroyed ||
      destroyed.regiments[0]
              .composition_rows[0]
              .current_army_regiment_state !=
          FrozenWarBoundIdState::destroyed) {
    std::cerr << "destroyed cleanup projection failed\n";
    return 1;
  }
  {
    auto cleanup = DestroyedCleanup();
    cleanup.status = WarBoundRegimentCleanupStatus::still_alive;
    cleanup.regiments[0].current_rows[0].current_army_regiment_state =
        FrozenWarBoundIdState::still_alive;
    cleanup.regiments[0].current_rows[0].raised_carmy_state =
        FrozenWarBoundIdState::still_alive;
    cleanup.regiments[0].current_rows[0].frozen_carmy_roster_evidence =
        FrozenWarBoundArmyRosterEvidence::still_attached;
    RaiktorWarBoundRegimentObservationV1 value;
    if (!ApplyRaiktorWarBoundRegimentCleanupObservationV1(
            active, postwar, postwar, cleanup, value) ||
        value.cleanup_status != WarBoundRegimentCleanupStatus::still_alive ||
        value.regiments[0]
                .composition_rows[0]
                .current_army_regiment_state !=
            FrozenWarBoundIdState::still_alive) {
      std::cerr << "still-alive cleanup projection failed\n";
      return 1;
    }
  }
  {
    auto cleanup = DestroyedCleanup();
    cleanup.regiments[0].persistent_regiment_id ^= 0x01000000;
    RaiktorWarBoundRegimentObservationV1 value;
    if (!ExpectFailure(
            ApplyRaiktorWarBoundRegimentCleanupObservationV1(
                active, postwar, postwar, cleanup, value),
            value,
            RaiktorWarBoundRegimentFailureV1::cleanup_identity_mismatch,
            "cleanup generation drift")) {
      return 1;
    }
  }
  {
    auto cleanup = DestroyedCleanup();
    cleanup.regiments[0].current_rows[0].frozen_carmy_roster_evidence =
        FrozenWarBoundArmyRosterEvidence::still_attached;
    RaiktorWarBoundRegimentObservationV1 value;
    if (!ExpectFailure(
            ApplyRaiktorWarBoundRegimentCleanupObservationV1(
                active, postwar, postwar, cleanup, value),
            value, RaiktorWarBoundRegimentFailureV1::cleanup_state_mismatch,
            "stale destroyed roster")) {
      return 1;
    }
  }
  {
    auto second = postwar;
    ++second.native_revision;
    RaiktorWarBoundRegimentObservationV1 value;
    if (!ExpectFailure(
            ApplyRaiktorWarBoundRegimentCleanupObservationV1(
                active, postwar, second, DestroyedCleanup(), value),
            value,
            RaiktorWarBoundRegimentFailureV1::postwar_frame_changed,
            "postwar frame drift")) {
      return 1;
    }
  }
  return 0;
}

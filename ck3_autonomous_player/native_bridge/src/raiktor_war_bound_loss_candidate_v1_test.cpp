#include "xar_bridge/raiktor_war_bound_loss_candidate_v1.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace {

using namespace xar::ck3_11906;

constexpr std::int32_t kWarId = 50'331'699;
constexpr std::int32_t kOwnerId = 29'829;

RaiktorWarBoundFrameV1 ActiveFrame() {
  return {91, 7, 53'175'816, true, kWarId, 411, true, kOwnerId, 17'116};
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
  WarBoundPersistentRegimentSnapshot persistent;
  persistent.persistent_regiment_id = 0x01000010;
  persistent.bound_war_id = kWarId;
  persistent.current_rows[0] = {0x02000020, 0x03000030};
  persistent.current_rows[3] = {0x02000021, 0x03000030};
  value.regiments = {persistent};
  return value;
}

FrozenWarBoundRegimentCleanupObservation Cleanup(bool still_alive) {
  FrozenWarBoundRegimentCleanupObservation value;
  value.provenance =
      WarBoundRegimentProvenance::war_bound_not_event_specific;
  value.status = still_alive ? WarBoundRegimentCleanupStatus::still_alive
                             : WarBoundRegimentCleanupStatus::destroyed;
  value.owner_character_id = kOwnerId;
  value.war_id = kWarId;
  FrozenWarBoundPersistentCleanupSnapshot persistent;
  persistent.persistent_regiment_id = 0x01000010;
  persistent.persistent_regiment_state = FrozenWarBoundIdState::destroyed;
  persistent.current_rows[0] = {
      0x02000020,
      0x03000030,
      still_alive ? FrozenWarBoundIdState::still_alive
                  : FrozenWarBoundIdState::destroyed,
      still_alive ? FrozenWarBoundIdState::still_alive
                  : FrozenWarBoundIdState::destroyed,
      still_alive ? FrozenWarBoundArmyRosterEvidence::still_attached
                  : FrozenWarBoundArmyRosterEvidence::frozen_army_destroyed,
  };
  persistent.current_rows[3] = {
      0x02000021,
      0x03000030,
      FrozenWarBoundIdState::destroyed,
      still_alive ? FrozenWarBoundIdState::still_alive
                  : FrozenWarBoundIdState::destroyed,
      still_alive ? FrozenWarBoundArmyRosterEvidence::detached
                  : FrozenWarBoundArmyRosterEvidence::frozen_army_destroyed,
  };
  value.regiments.push_back(persistent);
  return value;
}

bool MakeBaseline(RaiktorWarBoundLossBaselineV1 &baseline) {
  RaiktorWarBoundRegimentObservationV1 active;
  const auto frame = ActiveFrame();
  if (!BuildRaiktorWarBoundRegimentActiveObservationV1(
          frame, frame, ActiveGeneric(),
          {{0x02000020, 400}, {0x02000021, 198}}, active)) {
    return false;
  }
  return FreezeRaiktorWarBoundLossBaselineV1(active, baseline);
}

xar::game::WarRaiktorWarBoundCurrentSnapshot TermsProjection() {
  xar::game::WarRaiktorWarBoundCurrentSnapshot value;
  value.date_raw = ActiveFrame().date_raw;
  value.war_id = kWarId;
  value.active_casus_belli_database_index = 411;
  value.primary_attacker_character_id = kOwnerId;
  value.primary_defender_character_id = 17'116;
  value.owner_character_id = kOwnerId;
  value.observed_current_soldiers = 598;
  xar::game::WarRaiktorWarBoundRegimentSnapshot regiment;
  regiment.persistent_regiment_id = 0x01000010;
  regiment.bound_war_id = kWarId;
  regiment.current_soldiers = 598;
  regiment.composition_rows.resize(kWarBoundRegimentCompositionRowCount);
  for (std::size_t ordinal = 0;
       ordinal < kWarBoundRegimentCompositionRowCount; ++ordinal) {
    regiment.composition_rows[ordinal].composition_ordinal =
        static_cast<std::int32_t>(ordinal);
  }
  regiment.composition_rows[0].current_army_regiment_id = 0x02000020;
  regiment.composition_rows[0].raised_carmy_id = 0x03000030;
  regiment.composition_rows[0].current_soldiers = 400;
  regiment.composition_rows[3].current_army_regiment_id = 0x02000021;
  regiment.composition_rows[3].raised_carmy_id = 0x03000030;
  regiment.composition_rows[3].current_soldiers = 198;
  value.regiments.push_back(std::move(regiment));
  return value;
}

} // namespace

int main() {
  RaiktorWarBoundLossBaselineV1 baseline;
  if (!MakeBaseline(baseline) ||
      baseline.pre_termination_soldiers != 598 ||
      baseline.frozen_active.observed_pre_soldiers != -1 ||
      baseline.frozen_active.proven_soldiers_lost != -1) {
    std::cerr << "measured pre-termination baseline freeze failed\n";
    return 1;
  }

  RaiktorWarBoundLossBaselineV1 projected_baseline;
  if (!FreezeRaiktorWarBoundLossBaselineV1(
          TermsProjection(), 7, projected_baseline) ||
      projected_baseline.pre_termination_soldiers != 598 ||
      projected_baseline.frozen_active.active_frame.snapshot_revision != 7 ||
      projected_baseline.frozen_active.active_frame.native_revision != 7 ||
      projected_baseline.frozen_active.regiments !=
          baseline.frozen_active.regiments) {
    std::cerr << "terms projection did not freeze the exact baseline\n";
    return 1;
  }
  {
    auto drifted = TermsProjection();
    drifted.regiments[0].current_soldiers = 597;
    RaiktorWarBoundLossBaselineV1 rejected;
    if (FreezeRaiktorWarBoundLossBaselineV1(drifted, 7, rejected)) {
      std::cerr << "per-regiment soldier drift was accepted\n";
      return 1;
    }
  }

  const auto postwar = PostwarFrame();
  RaiktorWarBoundLossResultV1 destroyed;
  if (!ApplyRaiktorWarBoundLossCleanupV1(
          baseline, postwar, postwar, Cleanup(false), destroyed) ||
      destroyed.status !=
          RaiktorWarBoundLossStatusV1::destroyed_boundary_loss_proven ||
      destroyed.failure != RaiktorWarBoundLossFailureV1::none ||
      destroyed.pre_termination_soldiers != 598 ||
      destroyed.current_at_pre_termination_soldiers != 598 ||
      destroyed.post_termination_soldiers != 0 ||
      destroyed.proven_boundary_soldiers_lost != 598 ||
      destroyed.cleanup_status != WarBoundRegimentCleanupStatus::destroyed ||
      !destroyed.pre_termination_checkpoint_ready ||
      !destroyed.postwar_cleanup_ready ||
      !destroyed.proven_boundary_loss_ready ||
      destroyed.source_specific_attribution_ready ||
      destroyed.termination_action_bound || destroyed.public_terms_ready) {
    std::cerr << "destroyed boundary proof failed\n";
    return 1;
  }
  const std::string destroyed_wire =
      SerializeRaiktorWarBoundLossCleanupV1(destroyed);
  if (destroyed_wire.empty() ||
      destroyed_wire.find("\"status\":\"destroyed\"") ==
          std::string::npos ||
      destroyed_wire.find("\"snapshot_revision\":96") ==
          std::string::npos ||
      destroyed_wire.find("\"proven_soldier_loss_observable\":false") ==
          std::string::npos) {
    std::cerr << "destroyed cleanup serialization overclaimed or drifted\n";
    return 1;
  }

  RaiktorWarBoundLossResultV1 surviving;
  if (!ApplyRaiktorWarBoundLossCleanupV1(
          baseline, postwar, postwar, Cleanup(true), surviving) ||
      surviving.status !=
          RaiktorWarBoundLossStatusV1::cleanup_still_alive ||
      surviving.cleanup_status !=
          WarBoundRegimentCleanupStatus::still_alive ||
      surviving.post_termination_soldiers != -1 ||
      surviving.proven_boundary_soldiers_lost != -1 ||
      surviving.proven_boundary_loss_ready) {
    std::cerr << "still-alive result must remain incomplete\n";
    return 1;
  }

  {
    auto invalid = baseline;
    invalid.pre_termination_soldiers = 3000;
    RaiktorWarBoundLossResultV1 value;
    if (ApplyRaiktorWarBoundLossCleanupV1(
            invalid, postwar, postwar, Cleanup(false), value) ||
        value.failure != RaiktorWarBoundLossFailureV1::
                             invalid_pre_termination_baseline) {
      std::cerr << "authored total must not replace measured baseline\n";
      return 1;
    }
  }
  {
    auto cleanup = Cleanup(false);
    cleanup.regiments[0].persistent_regiment_id ^= 0x01000000;
    RaiktorWarBoundLossResultV1 value;
    if (ApplyRaiktorWarBoundLossCleanupV1(
            baseline, postwar, postwar, cleanup, value) ||
        value.failure !=
            RaiktorWarBoundLossFailureV1::cleanup_contract_rejected) {
      std::cerr << "generation drift must reject the pair\n";
      return 1;
    }
  }
  return 0;
}

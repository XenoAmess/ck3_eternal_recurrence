#include "xar_bridge/raiktor_war_bound_regiment_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kMaximumWarBoundPersistentRegiments = 4096;

bool ActiveFrameIsValid(const RaiktorWarBoundFrameV1 &frame) noexcept {
  return frame.snapshot_revision != 0 && frame.native_revision != 0 &&
         frame.paused && frame.war_id != -1 &&
         frame.active_casus_belli_database_index >= 0 &&
         frame.exact_raiktor_claim_cb &&
         frame.primary_attacker_character_id != -1 &&
         frame.primary_defender_character_id != -1 &&
         frame.primary_attacker_character_id !=
             frame.primary_defender_character_id;
}

bool PostwarFrameIsValid(
    const RaiktorWarBoundPostwarFrameV1 &frame) noexcept {
  return frame.snapshot_revision != 0 && frame.native_revision != 0 &&
         frame.paused && frame.frozen_war_id != -1 &&
         frame.frozen_war_absent_from_active_wars;
}

bool CheckedAdd(std::int64_t value, std::int64_t &sum) noexcept {
  if (value < 0 ||
      sum > (std::numeric_limits<std::int64_t>::max)() - value) {
    return false;
  }
  sum += value;
  return true;
}

bool Contains(const std::vector<std::int32_t> &values,
              std::int32_t value) noexcept {
  return std::find(values.begin(), values.end(), value) != values.end();
}

const RaiktorWarBoundCurrentSoldierSampleV1 *FindSoldierSample(
    const std::vector<RaiktorWarBoundCurrentSoldierSampleV1> &samples,
    std::int32_t id) noexcept {
  const auto found = std::find_if(
      samples.begin(), samples.end(), [id](const auto &candidate) {
        return candidate.current_army_regiment_id == id;
      });
  return found == samples.end() ? nullptr : &*found;
}

bool Fail(RaiktorWarBoundRegimentFailureV1 failure,
          RaiktorWarBoundRegimentObservationV1 &output) noexcept {
  output = {};
  output.failure = failure;
  return false;
}

} // namespace

std::string_view RaiktorWarBoundRegimentFailureReasonV1(
    RaiktorWarBoundRegimentFailureV1 failure) noexcept {
  switch (failure) {
  case RaiktorWarBoundRegimentFailureV1::none:
    return "none";
  case RaiktorWarBoundRegimentFailureV1::invalid_raiktor_frame:
    return "invalid_raiktor_frame";
  case RaiktorWarBoundRegimentFailureV1::raiktor_frame_changed:
    return "raiktor_frame_changed";
  case RaiktorWarBoundRegimentFailureV1::invalid_generic_active_observation:
    return "invalid_generic_active_observation";
  case RaiktorWarBoundRegimentFailureV1::duplicate_generation_id:
    return "duplicate_generation_id";
  case RaiktorWarBoundRegimentFailureV1::current_soldier_sample_mismatch:
    return "current_soldier_sample_mismatch";
  case RaiktorWarBoundRegimentFailureV1::current_soldier_overflow:
    return "current_soldier_overflow";
  case RaiktorWarBoundRegimentFailureV1::invalid_postwar_frame:
    return "invalid_postwar_frame";
  case RaiktorWarBoundRegimentFailureV1::postwar_frame_changed:
    return "postwar_frame_changed";
  case RaiktorWarBoundRegimentFailureV1::invalid_cleanup_observation:
    return "invalid_cleanup_observation";
  case RaiktorWarBoundRegimentFailureV1::cleanup_identity_mismatch:
    return "cleanup_identity_mismatch";
  case RaiktorWarBoundRegimentFailureV1::cleanup_state_mismatch:
    return "cleanup_state_mismatch";
  }
  return "unknown";
}

bool BuildRaiktorWarBoundRegimentActiveObservationV1(
    const RaiktorWarBoundFrameV1 &first_frame,
    const RaiktorWarBoundFrameV1 &second_frame,
    const WarBoundRegimentObservation &generic_observation,
    const std::vector<RaiktorWarBoundCurrentSoldierSampleV1> &soldier_samples,
    RaiktorWarBoundRegimentObservationV1 &output) noexcept {
  output = {};
  if (!ActiveFrameIsValid(first_frame) ||
      !ActiveFrameIsValid(second_frame)) {
    return Fail(RaiktorWarBoundRegimentFailureV1::invalid_raiktor_frame,
                output);
  }
  if (first_frame != second_frame) {
    return Fail(RaiktorWarBoundRegimentFailureV1::raiktor_frame_changed,
                output);
  }
  if (generic_observation.provenance !=
          WarBoundRegimentProvenance::war_bound_not_event_specific ||
      generic_observation.owner_character_id !=
          first_frame.primary_attacker_character_id ||
      generic_observation.war_id != first_frame.war_id ||
      generic_observation.regiments.empty() ||
      generic_observation.regiments.size() >
          kMaximumWarBoundPersistentRegiments) {
    return Fail(
        RaiktorWarBoundRegimentFailureV1::invalid_generic_active_observation,
        output);
  }

  std::vector<std::int32_t> persistent_ids;
  std::vector<std::int32_t> current_ids;
  persistent_ids.reserve(generic_observation.regiments.size());
  current_ids.reserve(generic_observation.regiments.size() *
                      kWarBoundRegimentCompositionRowCount);
  for (const auto &sample : soldier_samples) {
    if (sample.current_army_regiment_id == -1 ||
        sample.current_soldiers < 0 ||
        std::count_if(soldier_samples.begin(), soldier_samples.end(),
                      [&sample](const auto &candidate) {
                        return candidate.current_army_regiment_id ==
                               sample.current_army_regiment_id;
                      }) != 1) {
      return Fail(
          RaiktorWarBoundRegimentFailureV1::current_soldier_sample_mismatch,
          output);
    }
  }

  RaiktorWarBoundRegimentObservationV1 observed;
  observed.active_frame = first_frame;
  observed.owner_character_id = generic_observation.owner_character_id;
  observed.war_id = generic_observation.war_id;
  observed.regiments.reserve(generic_observation.regiments.size());
  std::int64_t total_current_soldiers = 0;

  for (const auto &generic_regiment : generic_observation.regiments) {
    if (generic_regiment.persistent_regiment_id == -1 ||
        generic_regiment.bound_war_id != generic_observation.war_id ||
        generic_regiment.war_keep_on_attacker_victory ||
        Contains(persistent_ids, generic_regiment.persistent_regiment_id)) {
      return Fail(
          Contains(persistent_ids,
                   generic_regiment.persistent_regiment_id)
              ? RaiktorWarBoundRegimentFailureV1::duplicate_generation_id
              : RaiktorWarBoundRegimentFailureV1::
                    invalid_generic_active_observation,
          output);
    }
    persistent_ids.push_back(generic_regiment.persistent_regiment_id);

    RaiktorWarBoundPersistentRegimentV1 regiment;
    regiment.persistent_regiment_id =
        generic_regiment.persistent_regiment_id;
    regiment.bound_war_id = generic_regiment.bound_war_id;
    regiment.war_keep_on_attacker_victory = false;
    for (std::size_t ordinal = 0;
         ordinal < kWarBoundRegimentCompositionRowCount; ++ordinal) {
      const auto &generic_row = generic_regiment.current_rows[ordinal];
      auto &row = regiment.composition_rows[ordinal];
      row.composition_ordinal = static_cast<std::int32_t>(ordinal);
      row.current_army_regiment_id =
          generic_row.current_army_regiment_id;
      row.raised_carmy_id = generic_row.raised_carmy_id;
      if ((generic_row.current_army_regiment_id == -1) !=
          (generic_row.raised_carmy_id == -1)) {
        return Fail(
            RaiktorWarBoundRegimentFailureV1::
                invalid_generic_active_observation,
            output);
      }
      if (generic_row.current_army_regiment_id == -1) {
        continue;
      }
      if (Contains(current_ids, generic_row.current_army_regiment_id)) {
        return Fail(RaiktorWarBoundRegimentFailureV1::duplicate_generation_id,
                    output);
      }
      current_ids.push_back(generic_row.current_army_regiment_id);
      const auto *const soldier_sample = FindSoldierSample(
          soldier_samples, generic_row.current_army_regiment_id);
      if (soldier_sample == nullptr) {
        return Fail(
            RaiktorWarBoundRegimentFailureV1::current_soldier_sample_mismatch,
            output);
      }
      row.current_soldiers = soldier_sample->current_soldiers;
      if (!CheckedAdd(row.current_soldiers, regiment.current_soldiers) ||
          !CheckedAdd(row.current_soldiers, total_current_soldiers)) {
        return Fail(
            RaiktorWarBoundRegimentFailureV1::current_soldier_overflow,
            output);
      }
    }
    observed.regiments.push_back(std::move(regiment));
  }

  if (current_ids.size() != soldier_samples.size()) {
    return Fail(
        RaiktorWarBoundRegimentFailureV1::current_soldier_sample_mismatch,
        output);
  }
  observed.status = RaiktorWarBoundRegimentStatusV1::
      generic_war_bound_visible_source_unattributed;
  observed.failure = RaiktorWarBoundRegimentFailureV1::none;
  observed.observed_current_soldiers = total_current_soldiers;
  observed.readiness.exact_raiktor_war_context_ready = true;
  observed.readiness.generic_war_bound_identity_ready = true;
  observed.readiness.current_soldiers_ready = true;
  observed.readiness.independently_visible_value_ready = true;
  // CK3 1.19.0.6 does not persist the spawn_army display-name/source on the
  // frozen CRegiment/CArmyRegiment objects.  Do not infer event provenance
  // from WarID, keep=false, authored totals, ArmyID, or display text.
  observed.readiness.source_specific_attribution_ready = false;
  observed.readiness.pre_soldiers_ready = false;
  observed.readiness.proven_soldier_loss_ready = false;
  observed.readiness.raiktor_source_specific_domain_ready = false;
  output = std::move(observed);
  return true;
}

bool ApplyRaiktorWarBoundRegimentCleanupObservationV1(
    const RaiktorWarBoundRegimentObservationV1 &active_observation,
    const RaiktorWarBoundPostwarFrameV1 &first_frame,
    const RaiktorWarBoundPostwarFrameV1 &second_frame,
    const FrozenWarBoundRegimentCleanupObservation &generic_cleanup,
    RaiktorWarBoundRegimentObservationV1 &output) noexcept {
  output = {};
  if (active_observation.status !=
          RaiktorWarBoundRegimentStatusV1::
              generic_war_bound_visible_source_unattributed ||
      active_observation.failure !=
          RaiktorWarBoundRegimentFailureV1::none ||
      !active_observation.readiness.exact_raiktor_war_context_ready ||
      !active_observation.readiness.generic_war_bound_identity_ready ||
      !active_observation.readiness.current_soldiers_ready ||
      !active_observation.readiness.independently_visible_value_ready ||
      active_observation.readiness.source_specific_attribution_ready ||
      active_observation.readiness.pre_soldiers_ready ||
      active_observation.readiness.proven_soldier_loss_ready ||
      active_observation.readiness.raiktor_source_specific_domain_ready ||
      active_observation.regiments.empty()) {
    return Fail(
        RaiktorWarBoundRegimentFailureV1::invalid_generic_active_observation,
        output);
  }
  if (!PostwarFrameIsValid(first_frame) ||
      !PostwarFrameIsValid(second_frame) ||
      first_frame.frozen_war_id != active_observation.war_id ||
      second_frame.frozen_war_id != active_observation.war_id) {
    return Fail(RaiktorWarBoundRegimentFailureV1::invalid_postwar_frame,
                output);
  }
  if (first_frame != second_frame) {
    return Fail(RaiktorWarBoundRegimentFailureV1::postwar_frame_changed,
                output);
  }
  if (generic_cleanup.provenance !=
          WarBoundRegimentProvenance::war_bound_not_event_specific ||
      generic_cleanup.status == WarBoundRegimentCleanupStatus::unavailable ||
      generic_cleanup.owner_character_id !=
          active_observation.owner_character_id ||
      generic_cleanup.war_id != active_observation.war_id ||
      generic_cleanup.regiments.size() !=
          active_observation.regiments.size()) {
    return Fail(
        RaiktorWarBoundRegimentFailureV1::invalid_cleanup_observation,
        output);
  }

  auto observed = active_observation;
  observed.postwar_frame = first_frame;
  bool any_exact_regiment_still_alive = false;
  for (std::size_t regiment_index = 0;
       regiment_index < observed.regiments.size(); ++regiment_index) {
    auto &regiment = observed.regiments[regiment_index];
    const auto &cleanup = generic_cleanup.regiments[regiment_index];
    if (cleanup.persistent_regiment_id !=
        regiment.persistent_regiment_id) {
      return Fail(
          RaiktorWarBoundRegimentFailureV1::cleanup_identity_mismatch,
          output);
    }
    if (cleanup.persistent_regiment_state !=
            FrozenWarBoundIdState::destroyed &&
        cleanup.persistent_regiment_state !=
            FrozenWarBoundIdState::still_alive) {
      return Fail(RaiktorWarBoundRegimentFailureV1::cleanup_state_mismatch,
                  output);
    }
    regiment.postwar_persistent_state =
        cleanup.persistent_regiment_state;
    any_exact_regiment_still_alive |=
        cleanup.persistent_regiment_state ==
        FrozenWarBoundIdState::still_alive;

    for (std::size_t ordinal = 0;
         ordinal < kWarBoundRegimentCompositionRowCount; ++ordinal) {
      auto &row = regiment.composition_rows[ordinal];
      const auto &cleanup_row = cleanup.current_rows[ordinal];
      if (cleanup_row.current_army_regiment_id !=
              row.current_army_regiment_id ||
          cleanup_row.raised_carmy_id != row.raised_carmy_id) {
        return Fail(
            RaiktorWarBoundRegimentFailureV1::cleanup_identity_mismatch,
            output);
      }
      if (row.current_army_regiment_id == -1) {
        if (cleanup_row.current_army_regiment_state !=
                FrozenWarBoundIdState::not_present ||
            cleanup_row.raised_carmy_state !=
                FrozenWarBoundIdState::not_present ||
            cleanup_row.frozen_carmy_roster_evidence !=
                FrozenWarBoundArmyRosterEvidence::not_present) {
          return Fail(
              RaiktorWarBoundRegimentFailureV1::cleanup_state_mismatch,
              output);
        }
        continue;
      }
      const auto current_state = cleanup_row.current_army_regiment_state;
      const auto army_state = cleanup_row.raised_carmy_state;
      const auto roster = cleanup_row.frozen_carmy_roster_evidence;
      if ((current_state != FrozenWarBoundIdState::destroyed &&
           current_state != FrozenWarBoundIdState::still_alive) ||
          (army_state != FrozenWarBoundIdState::destroyed &&
           army_state != FrozenWarBoundIdState::still_alive) ||
          (army_state == FrozenWarBoundIdState::destroyed &&
           roster !=
               FrozenWarBoundArmyRosterEvidence::frozen_army_destroyed) ||
          (army_state == FrozenWarBoundIdState::still_alive &&
           roster != FrozenWarBoundArmyRosterEvidence::detached &&
           roster != FrozenWarBoundArmyRosterEvidence::still_attached) ||
          (current_state == FrozenWarBoundIdState::destroyed &&
           roster == FrozenWarBoundArmyRosterEvidence::still_attached)) {
        return Fail(RaiktorWarBoundRegimentFailureV1::cleanup_state_mismatch,
                    output);
      }
      row.current_army_regiment_state = current_state;
      row.raised_carmy_state = army_state;
      row.frozen_carmy_roster_evidence = roster;
      any_exact_regiment_still_alive |=
          current_state == FrozenWarBoundIdState::still_alive;
    }
  }

  const auto expected_status = any_exact_regiment_still_alive
                                   ? WarBoundRegimentCleanupStatus::still_alive
                                   : WarBoundRegimentCleanupStatus::destroyed;
  if (generic_cleanup.status != expected_status) {
    return Fail(RaiktorWarBoundRegimentFailureV1::cleanup_state_mismatch,
                output);
  }
  observed.cleanup_status = generic_cleanup.status;
  observed.readiness.postwar_cleanup_ready = true;
  // Source attribution, a measured pre-spawn soldier baseline, and therefore
  // proven loss intentionally remain unavailable after cleanup.
  observed.readiness.source_specific_attribution_ready = false;
  observed.readiness.pre_soldiers_ready = false;
  observed.readiness.proven_soldier_loss_ready = false;
  observed.readiness.raiktor_source_specific_domain_ready = false;
  output = std::move(observed);
  return true;
}

} // namespace xar::ck3_11906

#include "xar_bridge/raiktor_war_bound_loss_candidate_v1.hpp"

#include <utility>

namespace xar::ck3_11906 {
namespace {

bool BaselineIsValid(
    const RaiktorWarBoundLossBaselineV1 &baseline) noexcept {
  const auto &active = baseline.frozen_active;
  return active.status ==
             RaiktorWarBoundRegimentStatusV1::
                 generic_war_bound_visible_source_unattributed &&
         active.failure == RaiktorWarBoundRegimentFailureV1::none &&
         active.owner_character_id != -1 && active.war_id != -1 &&
         !active.regiments.empty() && active.observed_current_soldiers >= 0 &&
         active.observed_pre_soldiers == -1 &&
         active.proven_soldiers_lost == -1 &&
         active.cleanup_status == WarBoundRegimentCleanupStatus::unavailable &&
         active.readiness.exact_raiktor_war_context_ready &&
         active.readiness.generic_war_bound_identity_ready &&
         active.readiness.current_soldiers_ready &&
         active.readiness.independently_visible_value_ready &&
         !active.readiness.postwar_cleanup_ready &&
         !active.readiness.source_specific_attribution_ready &&
         !active.readiness.pre_soldiers_ready &&
         !active.readiness.proven_soldier_loss_ready &&
         !active.readiness.raiktor_source_specific_domain_ready &&
         baseline.pre_termination_soldiers ==
             active.observed_current_soldiers;
}

bool Fail(RaiktorWarBoundLossFailureV1 failure,
          RaiktorWarBoundLossResultV1 &output) noexcept {
  output = {};
  output.failure = failure;
  return false;
}

WarBoundRegimentObservation RebuildFrozenGeneric(
    const RaiktorWarBoundLossBaselineV1 &baseline) {
  WarBoundRegimentObservation frozen;
  frozen.provenance =
      WarBoundRegimentProvenance::war_bound_not_event_specific;
  frozen.owner_character_id = baseline.frozen_active.owner_character_id;
  frozen.war_id = baseline.frozen_active.war_id;
  frozen.regiments.reserve(baseline.frozen_active.regiments.size());
  for (const auto &source : baseline.frozen_active.regiments) {
    WarBoundPersistentRegimentSnapshot target;
    target.persistent_regiment_id = source.persistent_regiment_id;
    target.bound_war_id = source.bound_war_id;
    target.war_keep_on_attacker_victory =
        source.war_keep_on_attacker_victory;
    for (std::size_t ordinal = 0;
         ordinal < kWarBoundRegimentCompositionRowCount; ++ordinal) {
      target.current_rows[ordinal] = {
          source.composition_rows[ordinal].current_army_regiment_id,
          source.composition_rows[ordinal].raised_carmy_id,
      };
    }
    frozen.regiments.push_back(std::move(target));
  }
  return frozen;
}

} // namespace

std::string_view RaiktorWarBoundLossFailureReasonV1(
    RaiktorWarBoundLossFailureV1 failure) noexcept {
  switch (failure) {
  case RaiktorWarBoundLossFailureV1::none:
    return "none";
  case RaiktorWarBoundLossFailureV1::invalid_pre_termination_baseline:
    return "invalid_pre_termination_baseline";
  case RaiktorWarBoundLossFailureV1::cleanup_read_unavailable:
    return "cleanup_read_unavailable";
  case RaiktorWarBoundLossFailureV1::cleanup_contract_rejected:
    return "cleanup_contract_rejected";
  }
  return "unknown";
}

bool FreezeRaiktorWarBoundLossBaselineV1(
    const RaiktorWarBoundRegimentObservationV1 &active,
    RaiktorWarBoundLossBaselineV1 &output) noexcept {
  output = {};
  RaiktorWarBoundLossBaselineV1 frozen;
  frozen.frozen_active = active;
  frozen.pre_termination_soldiers = active.observed_current_soldiers;
  if (!BaselineIsValid(frozen)) {
    return false;
  }
  output = std::move(frozen);
  return true;
}

bool ApplyRaiktorWarBoundLossCleanupV1(
    const RaiktorWarBoundLossBaselineV1 &baseline,
    const RaiktorWarBoundPostwarFrameV1 &first_postwar_frame,
    const RaiktorWarBoundPostwarFrameV1 &second_postwar_frame,
    const FrozenWarBoundRegimentCleanupObservation &cleanup,
    RaiktorWarBoundLossResultV1 &output) noexcept {
  output = {};
  if (!BaselineIsValid(baseline)) {
    return Fail(
        RaiktorWarBoundLossFailureV1::invalid_pre_termination_baseline,
        output);
  }

  RaiktorWarBoundRegimentObservationV1 strict_cleanup;
  if (!ApplyRaiktorWarBoundRegimentCleanupObservationV1(
          baseline.frozen_active, first_postwar_frame,
          second_postwar_frame, cleanup, strict_cleanup)) {
    return Fail(RaiktorWarBoundLossFailureV1::cleanup_contract_rejected,
                output);
  }

  RaiktorWarBoundLossResultV1 observed;
  observed.failure = RaiktorWarBoundLossFailureV1::none;
  observed.owner_character_id = baseline.frozen_active.owner_character_id;
  observed.war_id = baseline.frozen_active.war_id;
  observed.pre_termination_soldiers =
      baseline.pre_termination_soldiers;
  observed.current_at_pre_termination_soldiers =
      baseline.frozen_active.observed_current_soldiers;
  observed.cleanup_status = strict_cleanup.cleanup_status;
  observed.pre_termination_checkpoint_ready = true;
  observed.postwar_cleanup_ready = true;
  observed.strict_cleanup = std::move(strict_cleanup);

  // Generic war-bound identity is intentionally not event/source identity.
  // Nor does this pure read-only pair prove which command occurred between
  // its checkpoints; that causal binding belongs to the future live runner.
  observed.source_specific_attribution_ready = false;
  observed.termination_action_bound = false;
  observed.public_terms_ready = false;

  if (observed.cleanup_status == WarBoundRegimentCleanupStatus::destroyed) {
    observed.status =
        RaiktorWarBoundLossStatusV1::destroyed_boundary_loss_proven;
    observed.post_termination_soldiers = 0;
    observed.proven_boundary_soldiers_lost =
        observed.pre_termination_soldiers;
    observed.proven_boundary_loss_ready = true;
  } else {
    observed.status = RaiktorWarBoundLossStatusV1::cleanup_still_alive;
  }
  output = std::move(observed);
  return true;
}

#if defined(XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1)
bool ReadRaiktorWarBoundLossCleanupV1(
    const Bindings &bindings,
    const RaiktorWarBoundLossBaselineV1 &baseline,
    const RaiktorWarBoundPostwarFrameV1 &first_postwar_frame,
    const RaiktorWarBoundPostwarFrameV1 &second_postwar_frame,
    RaiktorWarBoundLossResultV1 &output) noexcept {
  output = {};
  if (!BaselineIsValid(baseline)) {
    return Fail(
        RaiktorWarBoundLossFailureV1::invalid_pre_termination_baseline,
        output);
  }
  const auto frozen = RebuildFrozenGeneric(baseline);
  FrozenWarBoundRegimentCleanupObservation cleanup;
  if (!ReadFrozenWarBoundRegimentCleanupObservation(
          bindings, frozen, cleanup)) {
    return Fail(RaiktorWarBoundLossFailureV1::cleanup_read_unavailable,
                output);
  }
  return ApplyRaiktorWarBoundLossCleanupV1(
      baseline, first_postwar_frame, second_postwar_frame, cleanup, output);
}
#endif

} // namespace xar::ck3_11906

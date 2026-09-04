#include "xar_bridge/raiktor_war_bound_loss_candidate_v1.hpp"

#include <string>
#include <utility>
#include <vector>

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

bool FreezeRaiktorWarBoundLossBaselineV1(
    const game::WarRaiktorWarBoundCurrentSnapshot &active,
    std::uint64_t transport_native_revision,
    RaiktorWarBoundLossBaselineV1 &output) noexcept {
  output = {};
  if (transport_native_revision == 0 || active.regiments.empty()) return false;

  RaiktorWarBoundFrameV1 frame;
  frame.snapshot_revision = transport_native_revision;
  frame.native_revision = transport_native_revision;
  frame.date_raw = active.date_raw;
  frame.paused = true;
  frame.war_id = active.war_id;
  frame.active_casus_belli_database_index =
      active.active_casus_belli_database_index;
  frame.exact_raiktor_claim_cb = true;
  frame.primary_attacker_character_id =
      active.primary_attacker_character_id;
  frame.primary_defender_character_id =
      active.primary_defender_character_id;

  WarBoundRegimentObservation generic;
  generic.provenance =
      WarBoundRegimentProvenance::war_bound_not_event_specific;
  generic.owner_character_id = active.owner_character_id;
  generic.war_id = active.war_id;
  std::vector<RaiktorWarBoundCurrentSoldierSampleV1> samples;
  generic.regiments.reserve(active.regiments.size());
  for (const auto &source_regiment : active.regiments) {
    if (source_regiment.composition_rows.size() !=
        kWarBoundRegimentCompositionRowCount) {
      return false;
    }
    WarBoundPersistentRegimentSnapshot regiment;
    regiment.persistent_regiment_id =
        source_regiment.persistent_regiment_id;
    regiment.bound_war_id = source_regiment.bound_war_id;
    regiment.war_keep_on_attacker_victory =
        source_regiment.war_keep_on_attacker_victory;
    for (std::size_t ordinal = 0;
         ordinal < kWarBoundRegimentCompositionRowCount; ++ordinal) {
      const auto &source_row = source_regiment.composition_rows[ordinal];
      if (source_row.composition_ordinal !=
          static_cast<std::int32_t>(ordinal)) {
        return false;
      }
      regiment.current_rows[ordinal] = {
          source_row.current_army_regiment_id,
          source_row.raised_carmy_id,
      };
      if (source_row.current_army_regiment_id != -1) {
        samples.push_back({source_row.current_army_regiment_id,
                           source_row.current_soldiers});
      }
    }
    generic.regiments.push_back(std::move(regiment));
  }
  RaiktorWarBoundRegimentObservationV1 strict;
  if (!BuildRaiktorWarBoundRegimentActiveObservationV1(
          frame, frame, generic, samples, strict) ||
      strict.observed_current_soldiers !=
          active.observed_current_soldiers) {
    return false;
  }
  for (std::size_t index = 0; index < active.regiments.size(); ++index) {
    if (strict.regiments[index].current_soldiers !=
        active.regiments[index].current_soldiers) {
      return false;
    }
  }
  return FreezeRaiktorWarBoundLossBaselineV1(strict, output);
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

namespace {

void AppendNumber(std::string &result, std::int64_t value) {
  result += std::to_string(value);
}

void AppendOptionalId(std::string &result, std::int32_t value) {
  if (value == -1) {
    result += "null";
  } else {
    AppendNumber(result, value);
  }
}

std::string_view IdStateName(FrozenWarBoundIdState value) noexcept {
  switch (value) {
  case FrozenWarBoundIdState::not_present:
    return "not_present";
  case FrozenWarBoundIdState::destroyed:
    return "destroyed";
  case FrozenWarBoundIdState::still_alive:
    return "still_alive";
  case FrozenWarBoundIdState::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

std::string_view RosterEvidenceName(
    FrozenWarBoundArmyRosterEvidence value) noexcept {
  switch (value) {
  case FrozenWarBoundArmyRosterEvidence::not_present:
    return "not_present";
  case FrozenWarBoundArmyRosterEvidence::frozen_army_destroyed:
    return "frozen_army_destroyed";
  case FrozenWarBoundArmyRosterEvidence::detached:
    return "detached";
  case FrozenWarBoundArmyRosterEvidence::still_attached:
    return "still_attached";
  case FrozenWarBoundArmyRosterEvidence::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

} // namespace

std::string SerializeRaiktorWarBoundLossCleanupV1(
    const RaiktorWarBoundLossResultV1 &value) {
  const auto &observed = value.strict_cleanup;
  if (value.failure != RaiktorWarBoundLossFailureV1::none ||
      value.status == RaiktorWarBoundLossStatusV1::unavailable ||
      observed.failure != RaiktorWarBoundRegimentFailureV1::none ||
      !observed.readiness.postwar_cleanup_ready) {
    return {};
  }
  std::string result;
  result.reserve(4096);
  result +=
      "{\"schema_version\":1,\"backend_id\":\""
      "ck3-1.19.0.6-native-raiktor-war-bound-regiment-v1\","
      "\"status\":\"generic_war_bound_visible_source_unattributed\","
      "\"failure\":null,\"active_frame\":{\"snapshot_revision\":";
  AppendNumber(result, observed.active_frame.snapshot_revision);
  result += ",\"native_revision\":";
  AppendNumber(result, observed.active_frame.native_revision);
  result += ",\"date_raw\":";
  AppendNumber(result, observed.active_frame.date_raw);
  result += ",\"paused\":true,\"war_id\":";
  AppendNumber(result, observed.active_frame.war_id);
  result += ",\"active_casus_belli_database_index\":";
  AppendNumber(result, observed.active_frame.active_casus_belli_database_index);
  result +=
      ",\"active_casus_belli_key\":\"raiktor_claim_cb\","
      "\"primary_attacker_character_id\":";
  AppendNumber(result, observed.active_frame.primary_attacker_character_id);
  result += ",\"primary_defender_character_id\":";
  AppendNumber(result, observed.active_frame.primary_defender_character_id);
  result += "},\"postwar_frame\":{\"snapshot_revision\":";
  AppendNumber(result, observed.postwar_frame.snapshot_revision);
  result += ",\"native_revision\":";
  AppendNumber(result, observed.postwar_frame.native_revision);
  result += ",\"date_raw\":";
  AppendNumber(result, observed.postwar_frame.date_raw);
  result += ",\"paused\":true,\"frozen_war_id\":";
  AppendNumber(result, observed.postwar_frame.frozen_war_id);
  result +=
      ",\"frozen_war_absent_from_active_wars\":true},"
      "\"owner_character_id\":";
  AppendNumber(result, observed.owner_character_id);
  result += ",\"war_id\":";
  AppendNumber(result, observed.war_id);
  result +=
      ",\"source_attribution\":{\"mode\":\"authored_candidate_only\","
      "\"authored_candidate_name\":\"norman_highwaymen\","
      "\"authored_spawn_army_count\":6,"
      "\"authored_soldiers_per_army\":500,"
      "\"authored_total_soldiers\":3000},"
      "\"soldiers\":{\"current_soldiers_observable\":true,"
      "\"observed_current_soldiers\":";
  AppendNumber(result, observed.observed_current_soldiers);
  result +=
      ",\"pre_soldiers_observable\":false,\"observed_pre_soldiers\":null,"
      "\"proven_soldier_loss_observable\":false,"
      "\"proven_soldiers_lost\":null},\"cleanup\":{\"observable\":true,"
      "\"status\":\"";
  result += observed.cleanup_status == WarBoundRegimentCleanupStatus::destroyed
                ? "destroyed"
                : "still_alive";
  result += "\"},\"regiments\":[";
  for (std::size_t regiment_index = 0;
       regiment_index < observed.regiments.size(); ++regiment_index) {
    if (regiment_index != 0) result += ',';
    const auto &regiment = observed.regiments[regiment_index];
    result += "{\"persistent_regiment_id\":";
    AppendNumber(result, regiment.persistent_regiment_id);
    result += ",\"bound_war_id\":";
    AppendNumber(result, regiment.bound_war_id);
    result += ",\"war_keep_on_attacker_victory\":";
    result += regiment.war_keep_on_attacker_victory ? "true" : "false";
    result += ",\"current_soldiers\":";
    AppendNumber(result, regiment.current_soldiers);
    result += ",\"postwar_persistent_state\":\"";
    result += IdStateName(regiment.postwar_persistent_state);
    result += "\",\"composition_rows\":[";
    for (std::size_t ordinal = 0;
         ordinal < regiment.composition_rows.size(); ++ordinal) {
      if (ordinal != 0) result += ',';
      const auto &row = regiment.composition_rows[ordinal];
      result += "{\"composition_ordinal\":";
      AppendNumber(result, row.composition_ordinal);
      result += ",\"current_army_regiment_id\":";
      AppendOptionalId(result, row.current_army_regiment_id);
      result += ",\"raised_carmy_id\":";
      AppendOptionalId(result, row.raised_carmy_id);
      result += ",\"current_soldiers\":";
      AppendOptionalId(result, row.current_soldiers);
      result += ",\"current_army_regiment_state\":\"";
      result += IdStateName(row.current_army_regiment_state);
      result += "\",\"raised_carmy_state\":\"";
      result += IdStateName(row.raised_carmy_state);
      result += "\",\"frozen_carmy_roster_evidence\":\"";
      result += RosterEvidenceName(row.frozen_carmy_roster_evidence);
      result += "\"}";
    }
    result += "]}";
  }
  result +=
      "],\"readiness\":{"
      "\"exact_raiktor_war_context_ready\":true,"
      "\"generic_war_bound_identity_ready\":true,"
      "\"current_soldiers_ready\":true,"
      "\"postwar_cleanup_ready\":true,"
      "\"source_specific_attribution_ready\":false,"
      "\"pre_soldiers_ready\":false,"
      "\"proven_soldier_loss_ready\":false,"
      "\"independently_visible_value_ready\":true,"
      "\"raiktor_source_specific_domain_ready\":false}}";
  return result;
}

} // namespace xar::ck3_11906
